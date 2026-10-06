"""
ml.py - ML inference wrapper for LeakedIn fraud detector.

Loads pre-trained scikit-learn Pipeline (TF-IDF + CalibratedClassifierCV)
and provides:
  - predict(text, ...): fraud probability + XAI top explaining n-grams
  - get_model_metadata(): version info from models/metadata.json
  - is_model_ready(): checks if model artifact exists and can be loaded
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "job_detector_model.joblib"
_METADATA_PATH = Path(__file__).resolve().parents[2] / "models" / "metadata.json"

_model = None
_model_loaded = False
_feature_names: list[str] = []
_coef: Optional[np.ndarray] = None


def _load_model() -> None:
    """Load model and extract feature names + coefficients for explainability."""
    global _model, _model_loaded, _feature_names, _coef

    if _model_loaded:
        return
    _model_loaded = True

    if not _MODEL_PATH.exists():
        logger.warning(
            "Model file not found at %s. ML predictions will return neutral score (0.5).",
            _MODEL_PATH,
        )
        return

    try:
        _model = joblib.load(_MODEL_PATH)
        tfidf = _model.named_steps["tfidf"]
        _feature_names = tfidf.get_feature_names_out().tolist()

        # Extract coefficients: CalibratedClassifierCV wraps base estimators
        clf = _model.named_steps["clf"]
        if hasattr(clf, "calibrated_classifiers_"):
            coefs = []
            for cc in clf.calibrated_classifiers_:
                estimator = getattr(cc, "estimator", getattr(cc, "base_estimator", None))
                if estimator is not None and hasattr(estimator, "coef_"):
                    coefs.append(estimator.coef_[0])
            if coefs:
                _coef = np.mean(coefs, axis=0)
            else:
                logger.warning("Could not extract coefficients from calibrated classifier.")
        elif hasattr(clf, "coef_"):
            _coef = clf.coef_[0]
        else:
            logger.warning("Classifier does not expose coef_.")

        logger.info("ML model loaded successfully from %s", _MODEL_PATH)
    except Exception as exc:
        logger.error("Failed to load model from %s: %s", _MODEL_PATH, exc)
        _model = None


def is_model_ready() -> bool:
    """Checks whether the ML model artifact exists on disk."""
    return _MODEL_PATH.exists()


def _get_top_ngrams(text: str, top_n: int = 5) -> dict[str, Any]:
    """
    Computes top fraud-associated and legit-associated n-grams present in text.
    Uses TF-IDF feature weights x classifier coefficients (linear XAI).
    """
    if _model is None or _coef is None or not _feature_names:
        return {"top_fraud_signals": [], "top_legit_signals": []}

    try:
        tfidf = _model.named_steps["tfidf"]
        vec = tfidf.transform([text])
        cx = vec.tocsr()
        nonzero_indices = cx.indices
        nonzero_values = np.array(cx.data)

        if len(nonzero_indices) == 0:
            return {"top_fraud_signals": [], "top_legit_signals": []}

        scores = nonzero_values * _coef[nonzero_indices]
        sorted_idx = np.argsort(scores)[::-1]

        fraud_signals = []
        legit_signals = []
        for i in sorted_idx[:top_n]:
            if scores[i] > 0:
                fraud_signals.append({
                    "ngram": _feature_names[nonzero_indices[i]],
                    "score": round(float(scores[i]), 4),
                })

        for i in sorted_idx[-top_n:][::-1]:
            if scores[i] < 0:
                legit_signals.append({
                    "ngram": _feature_names[nonzero_indices[i]],
                    "score": round(float(abs(scores[i])), 4),
                })

        return {
            "top_fraud_signals": fraud_signals[:top_n],
            "top_legit_signals": legit_signals[:top_n],
        }
    except Exception as exc:
        logger.warning("Failed to compute n-gram explanation: %s", exc)
        return {"top_fraud_signals": [], "top_legit_signals": []}


def get_model_metadata() -> dict[str, Any]:
    """Return training metadata from models/metadata.json if available."""
    if _METADATA_PATH.exists():
        try:
            with open(_METADATA_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "version": "2.0.0",
        "description": "TF-IDF + CalibratedClassifierCV Fraud Detector",
    }


def predict(
    text: str,
    title: str = "",
    company_profile: str = "",
    requirements: str = "",
    benefits: str = "",
) -> dict[str, Any]:
    """
    Run ML inference on job posting text.

    Supports optional structured breakdowns (title, company_profile, etc.)
    and returns both legacy and v2 keys for maximum compatibility.
    """
    _load_model()

    # Build combined text if structured fields provided
    full_text = text
    if title or company_profile or requirements or benefits:
        parts = [title, company_profile, text, requirements, benefits]
        full_text = " ".join(p.strip() for p in parts if p.strip())

    if _model is None:
        return {
            "fraud_probability": 0.5,
            "ml_fraud_probability": 0.5,
            "is_fraud": False,
            "ml_score_pct": 50,
            "ml_verdict": "Indeterminate (Model Unavailable)",
            "ml_confidence_level": "LOW",
            "top_scam_signals": [],
            "model_explanation": {"top_fraud_signals": [], "top_legit_signals": []},
            "model_version": "unavailable",
        }

    try:
        prob = float(_model.predict_proba([full_text])[0][1])
        prob_rounded = round(prob, 4)
        explanation = _get_top_ngrams(full_text)
        top_scam_signals = [item["ngram"] for item in explanation.get("top_fraud_signals", [])]

        if prob >= 0.75:
            verdict = "High probability of recruitment fraud"
            confidence = "HIGH"
        elif prob >= 0.50:
            verdict = "Elevated fraud probability (Suspicious)"
            confidence = "MEDIUM"
        elif prob >= 0.25:
            verdict = "Low fraud probability (Likely Legitimate)"
            confidence = "MEDIUM"
        else:
            verdict = "Minimal fraud probability (Legitimate)"
            confidence = "HIGH"

        metadata = get_model_metadata()

        return {
            "fraud_probability": prob_rounded,
            "ml_fraud_probability": prob_rounded,
            "is_fraud": prob >= 0.5,
            "ml_score_pct": int(round(prob * 100)),
            "ml_verdict": verdict,
            "ml_confidence_level": confidence,
            "top_scam_signals": top_scam_signals,
            "model_explanation": explanation,
            "model_version": metadata.get("version", "2.0.0"),
        }
    except Exception as exc:
        logger.warning("Model inference failed: %s. Returning neutral score.", exc)
        return {
            "fraud_probability": 0.5,
            "ml_fraud_probability": 0.5,
            "is_fraud": False,
            "ml_score_pct": 50,
            "ml_verdict": "Neutral",
            "ml_confidence_level": "LOW",
            "top_scam_signals": [],
            "model_explanation": {"top_fraud_signals": [], "top_legit_signals": []},
            "model_version": "2.0.0",
        }
