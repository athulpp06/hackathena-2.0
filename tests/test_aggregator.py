import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.detector.aggregator import aggregate, analyse


def test_aggregate_safe():
    ml_score = 0.1
    rule_flags = []
    verifier_result = {"domain_mismatch": False, "suspicious_email": False}

    result = aggregate(ml_score, rule_flags, verifier_result)

    assert result["risk_score"] == 6  # 0.1 * 60
    assert result["risk_level"] == "Safe"
    assert "This job posting appears legitimate." in result["verdict"]


def test_aggregate_critical():
    ml_score = 0.95
    rule_flags = [{"category": "Financial Demand", "severity": "CRITICAL"}]
    verifier_result = {"domain_mismatch": True, "suspicious_email": True}

    result = aggregate(ml_score, rule_flags, verifier_result)

    # 0.95 * 60 = 57
    # CRITICAL rule = 20
    # Mismatch = 10
    # Total = 87
    assert result["risk_score"] == 87
    assert result["risk_level"] == "High Risk"
    assert "Critical Scam Indicators" in result["verdict"]


def test_aggregate_rule_cap():
    ml_score = 0.0
    rule_flags = [
        {"severity": "CRITICAL"},
        {"severity": "CRITICAL"},
        {"severity": "CRITICAL"}
    ]
    verifier_result = {"domain_mismatch": False, "suspicious_email": False}

    result = aggregate(ml_score, rule_flags, verifier_result)

    # Rules score: 3 * 20 = 60, capped at 40.
    # CRITICAL floor applies: at least one CRITICAL rule → score bumped to >= 51.
    assert result["risk_score"] == 51
    assert result["risk_level"] == "Suspicious"


def test_aggregate_critical_floor():
    """A single CRITICAL rule must always produce at least 51 (Suspicious), even with ML=0."""
    ml_score = 0.0
    rule_flags = [{"severity": "CRITICAL", "category": "Financial Demand"}]
    verifier_result = {"domain_mismatch": False, "suspicious_email": False}

    result = aggregate(ml_score, rule_flags, verifier_result)

    # CRITICAL rule = 20pts; ML=0; no domain penalty → raw=20, but floor kicks in → 51
    assert result["risk_score"] == 51
    assert result["risk_level"] == "Suspicious"


def test_aggregate_no_critical_no_floor():
    """Without any CRITICAL rules, a HIGH rule alone should NOT trigger the floor."""
    ml_score = 0.0
    rule_flags = [{"severity": "HIGH", "category": "Urgency / Pressure"}]
    verifier_result = {"domain_mismatch": False, "suspicious_email": False}

    result = aggregate(ml_score, rule_flags, verifier_result)

    # HIGH = 10 pts, no floor → stays at 10
    assert result["risk_score"] == 10
    assert result["risk_level"] == "Safe"


def test_analyse_scam_job():
    sample_scam = """
    URGENT HIRING: Data entry operator at TCS!
    Earn Rs 45000 per week working from home 2 hours a day. No experience required.
    Direct selection without interview! 
    Only 3 seats left - offer expires within 24 hours.
    To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit.
    Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com.
    """
    scam_result = analyse(sample_scam, declared_company="TCS")
    assert scam_result["risk_score"] >= 80
    assert scam_result["risk_level"] == "High Risk"
    assert "Critical Scam Indicators" in scam_result["verdict"]
    assert scam_result["rule_flag_count"] >= 5
    assert scam_result["company_mismatch"] is True


def test_analyse_legit_job():
    sample_legit = """
    We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.
    Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.
    Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.
    Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off.
    To apply, submit your resume on our careers portal at https://stripe.com/jobs or contact recruiting@stripe.com.
    """
    legit_result = analyse(sample_legit)
    assert legit_result["risk_score"] <= 25, f"Legit job score too high: {legit_result['risk_score']}"
    assert legit_result["risk_level"] == "Safe"
    assert legit_result["rule_flag_count"] == 0


def test_analyse_student_internship_scam():
    sample_intern_scam = """
    We are happy to offer you an opportunity to work as a Marketing intern for pursuing students (part-time job) where you can earn more than your Pocket money. Immediate Hiring, just pay 5000 initially

    Your opportunity involves

    * Work from home
    * Branding/Promotion
    * Good Stipend (2500-21000)
    * Marketing Intern certificate 
    * Free internship opportunity
    * Letter of recommendation 

    TO APPLY FILL

    NAME:
    COLLEGE:
    BRANCH&YEAR:
    PH:
    EMAIL:
    COMFORTABLE LANGUAGE:
    STATE YOU BELONG TO:
    """
    intern_result = analyse(sample_intern_scam)
    assert intern_result["risk_score"] >= 85
    assert intern_result["risk_level"] == "High Risk"
    assert "Critical scam indicators" in intern_result["verdict"]
    assert intern_result["rule_penalty"] >= 80

    # Safety advice & emergency guidance
    assert "helpline" in intern_result and intern_result["helpline"]["number"] == "1930"
    assert len(intern_result["emergency_steps"]) >= 1
    assert "1930" in intern_result["police_complaint_draft"]
