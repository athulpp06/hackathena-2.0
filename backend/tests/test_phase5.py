"""Tests for Phase 5: ML explainability."""


def test_predict_returns_explanation():
    from backend.app.detector.ml import predict
    result = predict("Send Aadhaar and registration fee to get your job offer")
    assert "model_explanation" in result
    assert "top_fraud_signals" in result["model_explanation"]
    assert "top_legit_signals" in result["model_explanation"]
    assert isinstance(result["model_explanation"]["top_fraud_signals"], list)


def test_predict_returns_probability():
    from backend.app.detector.ml import predict
    result = predict("Senior engineer with 5+ years Python experience required")
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert isinstance(result["is_fraud"], bool)


def test_scam_text_higher_prob():
    from backend.app.detector.ml import predict
    scam = predict("No experience needed, work from home, earn Rs 5000/day. Pay registration fee.")
    legit = predict("Senior Software Engineer, 5+ years experience required. Competitive salary.")
    # Scam should score higher than legit
    assert scam["fraud_probability"] > legit["fraud_probability"]


def test_model_metadata_exists():
    import json
    import os
    meta_path = os.path.join("backend", "models", "metadata.json")
    assert os.path.exists(meta_path), f"Model metadata file {meta_path} must exist! Run train_pipeline first."
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    assert "version" in meta
    assert "trained_at" in meta
    assert "metrics" in meta
