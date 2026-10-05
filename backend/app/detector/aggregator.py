"""
Hybrid Risk Aggregation Engine.
Combines ML probability, rule-based penalties, and domain verification
into a single calibrated risk score (0–100) with a clear verdict.
"""

from typing import Dict, Any, List

from backend.app.detector import ml, rules, verifier

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

def _verdict(score: int, flag_count: int) -> str:
    if score >= 76:
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
        recs.append("Never pay any registration fee, security deposit, or training charge to get a job.")
    if "Suspicious Communication" in categories:
        recs.append("Verify the recruiter via the company's official careers page before responding on WhatsApp or Telegram.")
    if "Fake Urgency" in categories:
        recs.append("Ignore artificial urgency — legitimate employers give adequate time to evaluate offers.")
    if "Unrealistic Offer" in categories:
        recs.append("Cross-check the salary on Glassdoor or Naukri for the role and experience level described.")
    if "Identity Harvesting" in categories:
        recs.append("Never share Aadhaar, PAN, bank details, or OTP with an unverified recruiter.")
    if "DOMAIN_MISMATCH" in domain_types or "FREE_WEBMAIL" in domain_types:
        recs.append("Verify recruiter identity by contacting the company directly through their official website.")
    if "DISPOSABLE_EMAIL" in domain_types:
        recs.append("The contact email is a disposable/burner address. Report this posting to cybercrime.gov.in.")

    if not recs:
        recs.append("Always verify the company independently before sharing personal information.")

    return recs


def analyse(
    text: str,
    declared_company: str = "",
    contact_email: str = "",
) -> Dict[str, Any]:
    """
    Full hybrid analysis pipeline.

    Parameters
    ----------
    text              : Raw job posting text.
    declared_company  : Optional company name (from user input or extracted).
    contact_email     : Optional contact email (from user input or extracted).

    Returns
    -------
    Structured analysis result dict matching the API response schema.
    """
    if not text or not text.strip():
        return {
            "error": "No text provided for analysis.",
            "risk_score": 0,
            "risk_level": "Unknown",
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

    # --- Scoring Formula ---
    # ML contributes 40%, Rules 40%, Domain 20%
    # This prevents ML alone or rules alone from being gamed
    ml_contribution  = ml_prob * 40
    rule_contribution = (rule_penalty / 100) * 40
    domain_contribution = (domain_penalty / 50) * 20

    raw_score = ml_contribution + rule_contribution + domain_contribution
    risk_score = min(100, round(raw_score))

    level   = _risk_level(risk_score)
    verdict = _verdict(risk_score, rule_result["flag_count"])
    recs    = _recommendations(rule_result["red_flags"], domain_result["flags"])

    return {
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
