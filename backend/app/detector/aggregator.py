"""
Hybrid Risk Aggregation Engine.
Combines ML probability, rule-based penalties, and domain verification
into a single calibrated risk score (0–100) with a clear verdict.
"""

from typing import Dict, Any, List, Optional

from backend.app.detector import ml, rules, verifier, gatekeeper

_RULE_ENGINE = rules.RuleEngine()

# Risk level thresholds
def _risk_level(score: int) -> str:
    if score >= 76:
        return "High Risk"
    elif score >= 51:
        return "Suspicious"
    elif score >= 26:
        return "Low Risk"
    else:
        return "Safe"

def _verdict(score: int, flag_count: int, has_critical: bool = False) -> str:
    if score >= 76 or has_critical:
        return "Critical scam indicators detected. Do NOT respond or pay anything."
    elif score >= 51:
        return "Suspicious posting with multiple scam signals. Verify independently before proceeding."
    elif score >= 26:
        return "Some minor anomalies found. Exercise caution and verify the company."
    else:
        return "No significant fraud signals detected. Always verify independently."

def _recommendations(red_flags: list, domain_flags: list) -> List[str]:
    recs = []
    categories = {f["category"] for f in red_flags}
    domain_types = {f["type"] for f in domain_flags}

    if "Payment Demand" in categories:
        recs.append("Never pay any registration fee, security deposit, or training charge to get a job or internship.")
    if "Student Exploitation" in categories:
        recs.append("Legitimate internships evaluate skills through interviews — they never demand upfront money or lure students with 'easy pocket money'.")
    if "Contradictory Claims" in categories:
        recs.append("Beware of fraudulent postings that claim to be a 'free internship' while demanding initial charges or deposits.")
    if "Suspicious Application Method" in categories:
        recs.append("Never send personal details via informal chat forms or questionnaires. Apply only through formal company career portals.")
    if "Suspicious Communication" in categories:
        recs.append("Verify the recruiter via the company's official careers page before responding on WhatsApp or Telegram.")
    if "Fake Urgency" in categories:
        recs.append("Ignore artificial urgency — legitimate employers give adequate time to evaluate offers.")
    if "Unrealistic Offer" in categories:
        recs.append("Cross-check the salary or stipend on Glassdoor, LinkedIn, or AmbitionBox for the role and experience level described.")
    if "Identity Harvesting" in categories:
        recs.append("Never share Aadhaar, PAN, bank details, or OTP with an unverified recruiter.")
    if "DOMAIN_MISMATCH" in domain_types or "FREE_WEBMAIL" in domain_types:
        recs.append("Verify recruiter identity by contacting the company directly through their official website.")
    if "DISPOSABLE_EMAIL" in domain_types:
        recs.append("The contact email is a disposable/burner address. Report this posting to cybercrime.gov.in.")

    if not recs:
        recs.append("Always verify the company independently before sharing personal information.")

    return recs


def _compute_risk_score(
    ml_prob: float,
    rule_penalty: int,
    domain_penalty: int,
    red_flags: list,
    domain_flags: list,
) -> int:
    """
    Computes a calibrated multi-layer risk score (0-100).
    Ensures:
    1. Critical severity rules (upfront fee, identity theft, cheque fraud, disposable email)
       always trigger High Risk (>=85-95) with zero chance of being diluted.
    2. High ML probability or strong heuristic rules can independently indicate fraud.
    3. Completely clean legitimate postings remain low (<=25, Safe).
    """
    # 1. Calibrated ML risk
    if ml_prob <= 0.40:
        ml_risk = max(0.0, (ml_prob - 0.15) / 0.25) * 25.0
    else:
        ml_risk = 25.0 + min(1.0, (ml_prob - 0.40) / 0.60) * 75.0

    # 2. Rule penalty (0-100)
    rule_score = float(rule_penalty)

    # 3. Domain penalty (0-50 scaled to 0-100)
    domain_score = min(100.0, (float(domain_penalty) / 50.0) * 100.0)

    # Multi-signal fusion: primary signal drives the assessment, secondary corroborates
    signals = sorted([rule_score, ml_risk, domain_score], reverse=True)
    primary, secondary, tertiary = signals[0], signals[1], signals[2]

    blended = primary * 0.70 + secondary * 0.20 + tertiary * 0.10
    score = max(blended, primary * 0.88)

    # Severity analysis
    critical_rules = [f for f in red_flags if f.get("severity") == "CRITICAL"]
    critical_domain = [f for f in domain_flags if f.get("severity") == "CRITICAL"]
    high_rules = [f for f in red_flags if f.get("severity") == "HIGH"]

    # Hard guardrails for deterministic fraud patterns
    if critical_rules or critical_domain:
        if len(critical_rules) + len(critical_domain) >= 2 or rule_penalty >= 80 or ml_prob >= 0.75:
            base_floor = 94.0
        elif rule_penalty >= 50 or ml_prob >= 0.50:
            base_floor = 90.0
        else:
            base_floor = 85.0
        score = max(score, base_floor)
    elif len(high_rules) >= 2 or (len(high_rules) >= 1 and rule_penalty >= 50) or ml_prob >= 0.85:
        score = max(score, 78.0)
    elif rule_penalty >= 35 or len(high_rules) >= 1 or ml_prob >= 0.65:
        score = max(score, 55.0)

    return min(100, max(0, round(score)))


def analyse(
    text: str,
    declared_company: str = "",
    contact_email: str = "",
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png",
    skip_gatekeeper: bool = False,
) -> Dict[str, Any]:
    """
    Full hybrid analysis pipeline with AI Gatekeeper.

    Parameters
    ----------
    text              : Raw job posting text.
    declared_company  : Optional company name (from user input or extracted).
    contact_email     : Optional contact email (from user input or extracted).
    image_bytes       : Optional raw image bytes for Gemini multimodal vision.
    mime_type         : MIME type of uploaded image.
    skip_gatekeeper   : Set True to bypass gatekeeper relevance check (e.g. forced re-run).

    Returns
    -------
    Structured analysis result dict matching the API response schema.
    """
    if not text or not text.strip():
        return {
            "error": "No text provided for analysis.",
            "is_job_posting": False,
            "risk_score": 0,
            "risk_level": "Unknown",
        }

    # --- Layer 0: AI Gatekeeper & Content Relevance Verification ---
    gate_res = {"is_job_posting": True, "content_type": "job_posting", "confidence": 1.0, "reasoning": "Gatekeeper bypassed", "provider": "bypassed", "gemini_scam_assessment": None}
    if not skip_gatekeeper:
        gate_res = gatekeeper.classify_job_relevance(text, image_bytes=image_bytes, mime_type=mime_type)
        if not gate_res.get("is_job_posting", True):
            detected_type = gate_res.get("content_type", "unrelated_content").replace("_", " ").title()
            reasoning = gate_res.get("reasoning", "Input does not match recruitment patterns.")
            return {
                "is_job_posting": False,
                "content_type": gate_res.get("content_type", "unrelated_content"),
                "gatekeeper_reasoning": reasoning,
                "gatekeeper_provider": gate_res.get("provider", "offline_gatekeeper"),
                "risk_score": None,
                "risk_level": "Invalid Content",
                "verdict": f"The input appears to be {detected_type} rather than a job vacancy or recruitment offer.",
                "recommendations": [
                    "Please provide an actual job offer, employment advertisement, or internship posting to evaluate recruitment fraud.",
                    f"Current input was detected as: {detected_type}."
                ],
                "red_flags": [],
                "rule_flag_count": 0,
                "rule_penalty": 0,
                "highlighted_spans": [],
                "domain_flags": [],
                "domain_flag_count": 0,
                "emails_found": [],
                "company_mismatch": False,
                "ml_fraud_probability": 0.0,
                "ml_score_pct": 0,
                "ml_verdict": "Analysis Skipped (Not a job posting)",
                "ml_confidence_level": "N/A",
                "ml_top_signals": [],
                "model_version": "tfidf-logreg-v2.0",
                "gemini_scam_assessment": gate_res.get("gemini_scam_assessment"),
            }

    # --- Layer 1: ML Inference ---
    ml_result = ml.predict(text)
    ml_prob = ml_result["ml_fraud_probability"]   # 0.0 – 1.0

    # --- Layer 2: Rule-Based Heuristics ---
    rule_result = _RULE_ENGINE.analyze(text)
    rule_penalty = rule_result["total_penalty"]    # 0 – 100

    # --- Layer 3: Domain / Contact Verification ---
    domain_result = verifier.verify(text, declared_company, contact_email)
    domain_penalty = domain_result["penalty"]      # 0 – 50

    # --- Scoring Formula with Multi-Signal Fusion & Critical Guardrails ---
    has_critical = any(f.get("severity") == "CRITICAL" for f in rule_result["red_flags"]) or \
                   any(f.get("severity") == "CRITICAL" for f in domain_result["flags"])

    risk_score = _compute_risk_score(
        ml_prob=ml_prob,
        rule_penalty=rule_penalty,
        domain_penalty=domain_penalty,
        red_flags=rule_result["red_flags"],
        domain_flags=domain_result["flags"],
    )

    level   = _risk_level(risk_score)
    verdict = _verdict(risk_score, rule_result["flag_count"], has_critical=has_critical)
    recs    = _recommendations(rule_result["red_flags"], domain_result["flags"])

    return {
        # Gatekeeper layer output
        "is_job_posting": True,
        "content_type": gate_res.get("content_type", "job_posting"),
        "gatekeeper_reasoning": gate_res.get("reasoning", "Verified as recruitment posting."),
        "gatekeeper_provider": gate_res.get("provider", "offline_gatekeeper"),
        "gemini_scam_assessment": gate_res.get("gemini_scam_assessment"),

        # Risk scoring
        "risk_score": risk_score,
        "risk_level": level,
        "verdict": verdict,

        # ML layer output
        "ml_fraud_probability": ml_result["ml_fraud_probability"],
        "ml_score_pct": ml_result["ml_score_pct"],
        "ml_verdict": ml_result["ml_verdict"],
        "ml_confidence_level": ml_result["ml_confidence_level"],
        "ml_top_signals": ml_result["top_scam_signals"],

        # Rule layer output
        "red_flags": rule_result["red_flags"],
        "rule_flag_count": rule_result["flag_count"],
        "rule_penalty": rule_result["total_penalty"],
        "highlighted_spans": rule_result["highlighted_spans"],

        # Domain layer output
        "domain_flags": domain_result["flags"],
        "domain_flag_count": domain_result["flag_count"],
        "emails_found": domain_result["emails_found"],
        "company_mismatch": domain_result["company_mismatch"],

        # Guidance
        "recommendations": recs,
        "model_version": ml_result["model_version"],
    }
