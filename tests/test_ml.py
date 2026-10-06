import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.detector.ml import predict, is_model_ready


def test_ml_model_ready():
    assert is_model_ready() is True


def test_ml_predict_scam():
    sample_scam = """
    URGENT HIRING: Data entry operator at TCS!
    Earn Rs 45000 per week working from home 2 hours a day. No experience required.
    Direct selection without interview! 
    Only 3 seats left - offer expires within 24 hours.
    To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit.
    Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com.
    """
    result = predict(sample_scam)
    assert result["is_fraud"] is True
    assert result["fraud_probability"] >= 0.50
    assert result["ml_score_pct"] >= 50
    assert "top_scam_signals" in result


def test_ml_predict_legit():
    sample_legit = """
    We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.
    Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.
    Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.
    Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off.
    To apply, submit your resume on our careers portal at https://stripe.com/jobs.
    """
    result = predict(sample_legit)
    assert result["is_fraud"] is False
    assert result["fraud_probability"] < 0.50
    assert result["ml_score_pct"] < 50
