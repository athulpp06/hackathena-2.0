import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.detector.rules import RuleEngine


@pytest.fixture(scope="module")
def engine():
    return RuleEngine()


def test_rules_scam_job(engine):
    sample_scam = """
    URGENT HIRING: Data entry operator at TCS!
    Earn Rs 45000 per week working from home 2 hours a day. No experience required.
    Direct selection without interview! 
    Only 3 seats left - offer expires within 24 hours.
    To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit.
    Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com.
    """
    result = engine.analyze(sample_scam)
    assert result["flag_count"] >= 5
    assert result["total_penalty"] >= 80
    assert any("Upfront Fee" in f["title"] or "security deposit" in f["title"].lower() for f in result["red_flags"])
    assert any("WhatsApp" in f["title"] or "Telegram" in f["title"] for f in result["red_flags"])


def test_rules_legit_job(engine):
    sample_legit = """
    We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.
    Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.
    Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.
    Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off.
    To apply, submit your resume on our careers portal at https://stripe.com/jobs.
    """
    legit_result = engine.analyze(sample_legit)
    assert legit_result["flag_count"] == 0
    assert legit_result["total_penalty"] == 0


def test_rules_malayalam_scam(engine):
    malayalam_sample = "വർക്ക് ഫ്രം ഹോം ജോലി. രജിസ്ട്രേഷൻ ഫീസ് 1500 രൂപ അടക്കണം. ആധാർ അയക്കൂ."
    ml_result = engine.analyze(malayalam_sample)
    assert ml_result["flag_count"] >= 2
    assert any("Malayalam" in f["title"] for f in ml_result["red_flags"])
    assert any("Aadhaar" in f["title"] for f in ml_result["red_flags"])
    assert ml_result["total_penalty"] > 0


def test_rules_hindi_scam(engine):
    hindi_sample = "घर बैठे जॉब। रजिस्ट्रेशन फीस 2000 रुपये जमा करें और पैन कार्ड शेयर करें।"
    hi_result = engine.analyze(hindi_sample)
    assert hi_result["flag_count"] >= 2
    assert any("Fee Demand" in f["title"] or "Hindi" in f["title"] for f in hi_result["red_flags"])
    assert hi_result["total_penalty"] > 0


def test_rules_highlight_spans(engine):
    sample = "URGENT HIRING: Earn Rs 45000 per week. Security deposit required."
    result = engine.analyze(sample)
    assert len(result["highlighted_spans"]) > 0
    for span in result["highlighted_spans"]:
        assert span["start"] < span["end"]
        assert span["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def test_rules_penalty_cap(engine):
    sample = """
    URGENT HIRING! Direct selection! No interview! Security deposit of Rs 1500!
    WhatsApp: +91 9999999999! Telegram only! Earn 50000 daily! Only 1 seat left!
    Send registration fee! Buy training kit!
    """
    result = engine.analyze(sample)
    assert result["total_penalty"] <= 100
