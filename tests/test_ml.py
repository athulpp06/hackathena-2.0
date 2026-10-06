"""
Test Suite for Machine Learning Model (tests/test_ml.py)
"""

import pytest
from backend.app.detector.ml import predict, is_model_ready


def test_ml_is_ready():
    assert is_model_ready() is True


def test_ml_scam_prediction():
    sample_scam = (
        "URGENT HIRING: Data entry operator at TCS!\n"
        "Earn Rs 45000 per week working from home 2 hours a day. No experience required.\n"
        "Direct selection without interview!\n"
        "Only 3 seats left - offer expires within 24 hours.\n"
        "To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit.\n"
        "Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com."
    )
    result = predict(sample_scam)
    assert result["is_fraud"] is True
    assert result["fraud_probability"] > 0.70
    assert result["ml_score_pct"] > 70
    assert len(result["top_scam_signals"]) > 0


def test_ml_legit_prediction():
    sample_legit = (
        "We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.\n"
        "Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.\n"
        "Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.\n"
        "Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off.\n"
        "To apply, submit your resume on our careers portal at https://stripe.com/jobs."
    )
    result = predict(sample_legit)
    assert result["is_fraud"] is False
    assert result["fraud_probability"] < 0.35
    assert result["ml_score_pct"] < 35
