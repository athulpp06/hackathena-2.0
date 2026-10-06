"""
Test Suite for Multilingual Rules Engine (tests/test_rules.py)
"""

import pytest
from backend.app.detector.rules import RuleEngine


@pytest.fixture(scope="module")
def engine():
    return RuleEngine()


def test_rules_scam_detection(engine):
    sample_scam = (
        "URGENT HIRING: Data entry operator at TCS!\n"
        "Earn Rs 45000 per week working from home 2 hours a day. No experience required.\n"
        "Direct selection without interview!\n"
        "Only 3 seats left - offer expires within 24 hours.\n"
        "To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit.\n"
        "Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com."
    )
    result = engine.analyze(sample_scam)
    assert result["flag_count"] > 0
    assert result["total_penalty"] > 50
    assert len(result["highlighted_spans"]) > 0


def test_rules_legit_job(engine):
    sample_legit = (
        "We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.\n"
        "Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.\n"
        "Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.\n"
        "Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off.\n"
        "To apply, submit your resume on our careers portal at https://stripe.com/jobs."
    )
    legit_result = engine.analyze(sample_legit)
    assert legit_result["flag_count"] == 0
    assert legit_result["total_penalty"] == 0


def test_rules_malayalam_scam(engine):
    malayalam_sample = "വർക്ക് ഫ്രം ഹോം ജോലി. രജിസ്ട്രേഷൻ ഫീസ് 1500 രൂപ അടക്കണം. ആധാർ അയക്കൂ."
    ml_result = engine.analyze(malayalam_sample)
    assert ml_result["flag_count"] >= 2
    assert any("Malayalam" in f["title"] for f in ml_result["red_flags"])
    assert any("Aadhaar" in f["title"] for f in ml_result["red_flags"])


def test_rules_hindi_scam(engine):
    hindi_sample = "घर बैठे जॉब। रजिस्ट्रेशन फीस 2000 रुपये जमा करें और पैन कार्ड शेयर करें।"
    hi_result = engine.analyze(hindi_sample)
    assert hi_result["flag_count"] >= 2
    assert any("Fee Demand" in f["title"] for f in hi_result["red_flags"])
