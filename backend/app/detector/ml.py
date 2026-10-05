"""
ML Inference Wrapper for LeakedIn Job Posting Scanner.
Loads the trained TF-IDF + Classifier pipeline and exposes a clean inference API.
"""

import os
import re
from typing import Dict, Any, Optional

import joblib

# Path to the serialized model
_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "job_detector_model.joblib"
)
_MODEL_PATH = os.path.normpath(_MODEL_PATH)

# Lazy-load the model once on first inference call (avoids startup penalty)
_pipeline = None


def _load_pipeline():
    global _pipeline
    if _pipeline is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"ML model not found at '{_MODEL_PATH}'. "
                "Please run: python backend/scripts/train_pipeline.py"
            )
        _pipeline = joblib.load(_MODEL_PATH)
    return _pipeline


def _build_combined_text(
    title: str,
    description: str,
    company_profile: str = "",
    requirements: str = "",
    benefits: str = "",
) -> str:
    """Concatenates the same fields used during training."""
    parts = [title, company_profile, description, requirements, benefits]
    return " ".join(p.strip() for p in parts if p).lower()


def predict(
    text: str,
    title: str = "",
    company_profile: str = "",
    requirements: str = "",
    benefits: str = "",
) -> Dict[str, Any]:
    """
    Runs ML inference on a job posting.

    Parameters
    ----------
    text         : Full raw job posting text (primary input).
    title        : Optional extracted job title.
    company_profile : Optional company description text.
    requirements : Optional requirements section.
    benefits     : Optional benefits / compensation section.

    Returns
    -------
    Dict with keys:
        - ml_fraud_probability (float 0.0-1.0)  : Model confidence that this is fraudulent.
        - ml_score_pct (int 0-100)              : Percentage rounded for display.
        - ml_verdict (str)                       : Human-readable ML verdict label.
        - ml_confidence_level (str)              : Confidence tier: HIGH/MEDIUM/LOW.
        - top_scam_signals (list[str])           : Up to 5 top scam-correlated n-grams found in text.
        - model_version (str)                    : Identifier for reproducibility.
    """
    pipeline = _load_pipeline()

    # Prefer structured breakdown; fall back to raw text
    if title or company_profile or requirements or benefits:
        combined = _build_combined_text(title, text, company_profile, requirements, benefits)
    else:
        combined = text.lower().strip()

    prob = float(pipeline.predict_proba([combined])[0, 1])
    pct = round(prob * 100)

    # Confidence tiers based on distance from the decision boundary (0.5)
    distance = abs(prob - 0.5)
    if distance >= 0.35:
        confidence = "HIGH"
    elif distance >= 0.15:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Verdict label
    if prob >= 0.75:
        verdict = "ML Model Suspects Fraudulent Posting"
    elif prob >= 0.45:
        verdict = "ML Model Detects Suspicious Patterns"
    elif prob >= 0.20:
        verdict = "ML Model Finds Minor Anomalies"
    else:
        verdict = "ML Model Suggests Legitimate Posting"

    # Extract top correlated scam n-grams found in the actual input text
    top_signals = _extract_top_signals(combined, pipeline)

    return {
        "ml_fraud_probability": round(prob, 4),
        "ml_score_pct": pct,
        "ml_verdict": verdict,
        "ml_confidence_level": confidence,
        "top_scam_signals": top_signals,
        "model_version": "tfidf-logreg-v1.0",
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

_SCAM_FEATURE_WORDS = [
    # Financial scam indicators commonly seen in training corpus
    "registration fee", "security deposit", "training fee", "processing charge",
    "wire transfer", "western union", "moneygram", "bitcoin", "crypto",
    # Communication red flags
    "whatsapp", "telegram", "personal email", "gmail", "yahoo",
    # Unrealistic job signals
    "earn weekly", "daily income", "earn per day", "no experience required",
    "no interview", "direct selection", "urgent hiring", "spot offer",
    "work from home typing", "data entry earn", "form filling",
    "guaranteed income", "100 percent guaranteed",
]


def _extract_top_signals(text: str, pipeline) -> list:
    """
    Finds which known scam-correlated phrases are actually present in the text.
    Returns up to 5 matched signals for display to the user.
    """
    found = []
    text_lower = text.lower()
    for phrase in _SCAM_FEATURE_WORDS:
        if phrase in text_lower and len(found) < 5:
            found.append(phrase)
    return found


def is_model_ready() -> bool:
    """Health-check: returns True if the model file exists and can be loaded."""
    try:
        _load_pipeline()
        return True
    except Exception:
        return False
