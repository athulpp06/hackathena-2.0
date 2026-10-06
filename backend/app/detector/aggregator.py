"""
Hybrid Risk Aggregation Engine (Unified v1 + v2).
Combines AI Gatekeeper, Calibrated ML, Multilingual YAML Heuristics,
Domain Typosquatting, and Community Threat Intelligence into a calibrated risk score (0–100).
"""

from typing import Any, Dict, List, Optional

from backend.app.config import (
    AGGREGATOR_DOMAIN_MISMATCH_PENALTY,
    AGGREGATOR_ML_WEIGHT,
    AGGREGATOR_RULE_MAX_CAP,
    AGGREGATOR_RULE_SEVERITY_POINTS,
)
from backend.app.detector import advice, gatekeeper, ml, rules, verifier
from backend.app.utils.normalizer import detect_language

_RULE_ENGINE = rules.RuleEngine()
_LOW_CONFIDENCE_LANGS = {"hi", "ml", "mr", "ta", "te", "kn", "gu", "bn"}
_SHORT_TEXT_WORD_THRESHOLD = 25


def _risk_level(score: int) -> str:
    if score >= 76:
        return "High Risk"
    elif score >= 51:
        return "Suspicious"
    elif score >= 26:
        return "Low Risk"
    else:
        return "Safe"


def _verdict(score: int, flag_count: int = 0, has_critical: bool = False) -> str:
    if score >= 76 or has_critical:
        return "Critical scam indicators detected. Do NOT respond or pay anything."
    elif score >= 51:
        return "Suspicious posting with multiple scam signals. Verify independently before proceeding."
    elif score >= 26:
        return "Some minor anomalies found. Exercise caution and verify the company."
    else:
        return "No significant fraud signals detected. Always verify independently."


def aggregate(
    ml_score: float,
    rule_flags: list[dict[str, Any]],
    verifier_result: dict[str, Any],
    text: str = "",
) -> dict[str, Any]:
    """
    Unified score aggregation with language-aware weights, combination bonuses, and risk floors.
    """
    lang = detect_language(text) if text else "en"
    word_count = len(text.split()) if text else 100

    # 1. Language-aware weight selection
    if lang in _LOW_CONFIDENCE_LANGS or word_count < _SHORT_TEXT_WORD_THRESHOLD:
        ml_weight = AGGREGATOR_ML_WEIGHT * 0.5    # 30.0
        rule_cap = AGGREGATOR_RULE_MAX_CAP * 1.5  # 60.0
    else:
        ml_weight = AGGREGATOR_ML_WEIGHT          # 60.0
        rule_cap = AGGREGATOR_RULE_MAX_CAP        # 40.0

    # 2. Base ML score
    risk_score = ml_score * ml_weight

    # 3. Rule penalties
    rule_score = 0.0
    categories_hit = set()
    has_critical = False

    for flag in rule_flags:
        severity = str(flag.get("severity", "LOW")).upper()
        category = str(flag.get("category", ""))
        rule_score += AGGREGATOR_RULE_SEVERITY_POINTS.get(severity, 0.0)
        categories_hit.add(category)
        if severity == "CRITICAL":
            has_critical = True

    rule_score = min(rule_score, rule_cap)
    risk_score += rule_score

    # 4. Rule combination bonuses
    if any("Financial" in c or "Payment" in c for c in categories_hit) and any("Identity" in c for c in categories_hit):
        risk_score += 10.0
    if any("Financial" in c or "Payment" in c for c in categories_hit) and any(c in categories_hit for c in ("Suspicious Contact", "Too Good To Be True", "Contradictory Claims")):
        risk_score += 10.0
    if any("Work-from-Home" in c for c in categories_hit) and any("Suspicious" in c or "Contact" in c for c in categories_hit):
        risk_score += 5.0

    # 5. Domain / reputation mismatches
    if verifier_result.get("domain_mismatch", False) or verifier_result.get("company_mismatch", False) or verifier_result.get("suspicious_email", False):
        risk_score += AGGREGATOR_DOMAIN_MISMATCH_PENALTY
    if verifier_result.get("reputation_hits"):
        risk_score += 15.0

    # 6. Clamp to 0-100 and apply critical risk floor
    final_score = int(round(max(0, min(100, risk_score))))
    if has_critical and final_score < 51:
        final_score = 51

    # 7. Risk level and verdict
    if final_score <= 25:
        level = "Safe"
        verdict_text = "This job posting appears legitimate. No significant fraud signals detected."
    elif final_score <= 50:
        level = "Low Risk"
        verdict_text = "This posting has minor concerns. Research the company and recruiter before sharing sensitive information."
    elif final_score <= 75:
        level = "Suspicious"
        verdict_text = "Probable Scam Detected. Proceed with extreme caution."
    else:
        level = "High Risk"
        verdict_text = "Critical Scam Indicators Detected (Critical scam indicators). Do not engage or send money."

    # 7. Recommendations
    recommendations: List[str] = []
    if final_score > 25:
        recommendations.append("Verify the employer on their official corporate portal and LinkedIn before applying.")
    if any("Financial" in c or "Payment" in c for c in categories_hit):
        recommendations.append("Never pay money to secure a job or internship — legitimate employers never demand fees.")
    if any("Identity" in c for c in categories_hit):
        recommendations.append("Do not share Aadhaar, PAN, or bank credentials before a formal contract and interview.")
    if verifier_result.get("company_mismatch") or verifier_result.get("domain_mismatch"):
        recommendations.append("Be wary of recruiters using free webmail (Gmail/Yahoo) claiming to represent major corporations.")
    if not recommendations:
        recommendations.append("Use official company career portals to apply and verify recruiter identities.")

    return {
        "risk_score": final_score,
        "risk_level": level,
        "verdict": verdict_text,
        "recommendations": recommendations,
        "_debug": {
            "ml_weight_used": ml_weight,
            "rule_cap_used": rule_cap,
            "lang_detected": lang,
            "word_count": word_count,
            "has_critical_rule": has_critical,
            "categories_hit": sorted(list(categories_hit)),
        },
    }


def analyse(
    text: str,
    declared_company: str = "",
    contact_email: str = "",
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png",
    skip_gatekeeper: bool = False,
) -> Dict[str, Any]:
    """
    Full hybrid analysis pipeline featuring AI Gatekeeper, ML XAI, multilingual rules,
    domain & reputation verification, and automated cybercrime complaint drafting.
    """
    if not text or not text.strip():
        return {
            "error": "No text provided for analysis.",
            "is_job_posting": False,
            "risk_score": 0,
            "risk_level": "Unknown",
        }

    # --- Layer 0: AI Gatekeeper & Content Relevance Verification ---
    gate_res = {
        "is_job_posting": True,
        "content_type": "job_posting",
        "confidence": 1.0,
        "reasoning": "Gatekeeper bypassed",
        "provider": "bypassed",
        "gemini_scam_assessment": None,
    }
    if not skip_gatekeeper:
        gate_res = gatekeeper.classify_job_relevance(text, image_bytes=image_bytes, mime_type=mime_type)
        if not gate_res.get("is_job_posting", True):
            detected_type = gate_res.get("content_type", "unrelated_content").replace("_", " ").title()
            reasoning = gate_res.get("reasoning", "Input does not match recruitment patterns.")
            return {
                "is_job_posting": False,
                "content_type": gate_res.get("content_type"),
                "gatekeeper_reasoning": reasoning,
                "gatekeeper_confidence": gate_res.get("confidence", 0.9),
                "gatekeeper_provider": gate_res.get("provider", "offline_heuristic"),
                "risk_score": None,
                "risk_level": "Invalid Content",
                "verdict": f"The submitted content appears to be a {detected_type.lower()} rather than a job vacancy or employment offer. Fraud analysis withheld.",
                "red_flags": [],
                "domain_flags": [],
                "highlighted_spans": [],
                "recommendations": [
                    f"The submitted text or document appears to be a {detected_type.lower()} rather than a recruitment advertisement or offer.",
                    "Please submit a genuine job posting, internship offer, or recruiter chat to perform fraud analysis.",
                ],
                "advice": [],
                "emergency_steps": [],
                "police_complaint_draft": "",
            }

    # --- Layer 1: Language Detection & Normalization ---
    detected_lang = detect_language(text)

    # --- Layer 2: Machine Learning Inference ---
    ml_result = ml.predict(text)
    ml_prob = ml_result.get("fraud_probability", 0.5)

    # --- Layer 3: Rule-Based Heuristic Detection ---
    rule_analysis = _RULE_ENGINE.analyze(text)
    red_flags = rule_analysis["red_flags"]
    rule_penalty = rule_analysis["total_penalty"]
    highlighted_spans = rule_analysis["highlighted_spans"]

    # --- Layer 4: Domain & Contact Verification ---
    verifier_result = verifier.verify(text, declared_company=declared_company, contact_email=contact_email)
    domain_flags = verifier_result["flags"]
    domain_penalty = verifier_result["penalty"]
    entities = verifier_result.get("entities", {})
    reputation_hits = verifier_result.get("reputation_hits", [])

    # --- Layer 5: Calibrated Risk Aggregation ---
    agg_result = aggregate(
        ml_score=ml_prob,
        rule_flags=red_flags,
        verifier_result=verifier_result,
        text=text,
    )
    final_score = agg_result["risk_score"]
    risk_level_str = agg_result["risk_level"]
    verdict_str = agg_result["verdict"]

    # --- Layer 6: Contextual Advice & Complaint Draft ---
    advice_info = advice.generate_advice(
        red_flags=red_flags,
        domain_flags=domain_flags,
        risk_level=risk_level_str,
        entities=entities,
        company_name=declared_company,
        reputation_hits=reputation_hits,
    )

    # Clean display title for company
    claimed_display = declared_company.strip().title() if declared_company else "Not Specified"

    return {
        "is_job_posting": True,
        "content_type": gate_res.get("content_type", "job_posting"),
        "gatekeeper": gate_res,
        "language": detected_lang,
        "risk_score": final_score,
        "risk_level": risk_level_str,
        "verdict": verdict_str,
        # ML metrics
        "ml_probability": ml_prob,
        "ml_score_pct": ml_result.get("ml_score_pct", int(round(ml_prob * 100))),
        "ml_verdict": ml_result.get("ml_verdict", "N/A"),
        "ml_confidence": ml_result.get("ml_confidence_level", "MEDIUM"),
        "ml_top_signals": ml_result.get("top_scam_signals", []),
        "top_scam_signals": ml_result.get("top_scam_signals", []),
        "model_explanation": ml_result.get("model_explanation", {}),
        "model_version": ml_result.get("model_version", "2.0.0"),
        # Rule breakdown
        "rule_penalty": rule_penalty,
        "rule_flag_count": len(red_flags),
        "red_flags": red_flags,
        "highlighted_spans": highlighted_spans,
        # Domain & Contact breakdown
        "domain_penalty": domain_penalty,
        "domain_flag_count": len(domain_flags),
        "domain_flags": domain_flags,
        "company_name": claimed_display,
        "company_mismatch": verifier_result.get("company_mismatch", False),
        "has_free_email": verifier_result.get("has_free_email", False),
        "has_disposable_email": verifier_result.get("has_disposable_email", False),
        "typosquat_detected": verifier_result.get("typosquat_detected", False),
        "entities": entities,
        "reputation_hits": reputation_hits,
        # Guidance & Recovery
        "recommendations": agg_result["recommendations"],
        "advice": advice_info["advice"],
        "emergency_steps": advice_info["emergency_steps"],
        "helpline": advice_info["helpline"],
        "police_complaint_draft": advice_info["police_complaint_draft"],
    }
