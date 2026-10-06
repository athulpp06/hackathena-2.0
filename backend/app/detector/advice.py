"""
advice.py - Contextual victim safety advice, 1930 cybercrime guidance, and police complaint draft generator.
"""

from typing import Any, Dict, List, Optional


def generate_advice(
    red_flags: List[Dict[str, Any]],
    domain_flags: Optional[Any] = None,
    risk_level: str = "Safe",
    entities: Optional[Dict[str, Any]] = None,
    company_name: str = "",
    reputation_hits: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Generates actionable safety recommendations, emergency victim recovery steps,
    and a ready-to-copy police/cybercrime complaint draft.

    Compatible with both v1 and v2 caller signatures:
      v1: generate_advice(red_flags, domain_flags, risk_level, entities, company_name)
      v2: generate_advice(red_flags, reputation_hits, risk_level)
    """
    # Detect if second argument was reputation_hits (v2 signature)
    actual_domain_flags: List[Dict[str, Any]] = []
    actual_reputation_hits: List[Dict[str, Any]] = []

    if isinstance(domain_flags, list) and domain_flags:
        if isinstance(domain_flags[0], dict) and "entity_type" in domain_flags[0]:
            actual_reputation_hits = domain_flags
        elif isinstance(domain_flags[0], dict):
            actual_domain_flags = domain_flags
        elif isinstance(domain_flags[0], str):
            actual_domain_flags = [{"type": s, "category": s} for s in domain_flags]

    if reputation_hits:
        actual_reputation_hits.extend(reputation_hits)

    entities = entities or {}
    categories = {f.get("category", "") for f in red_flags}
    for df in actual_domain_flags:
        categories.add(df.get("type", ""))
        categories.add(df.get("category", ""))

    advice_items: List[str] = []
    emergency_steps: List[str] = []

    # Risk-based baseline advice
    if risk_level in ("High Risk", "Suspicious"):
        advice_items.append("Do NOT send money or share bank/identity details with this recruiter.")
        advice_items.append("Report this fraudulent posting immediately on the platform where you encountered it.")

    # Financial demand detection
    has_financial_demand = any("Payment" in c or "Financial" in c or "UPI" in c for c in categories)
    if has_financial_demand:
        advice_items.append("Legitimate employers never demand registration fees, security deposits, or kit charges.")
        emergency_steps.append(
            "If money was already paid: Dial the National Cyber Crime Helpline '1930' immediately. "
            "Report the transaction at cybercrime.gov.in and request your bank/UPI app to freeze or reverse the transaction."
        )

    # Identity theft / Aadhaar / PAN detection
    has_identity_theft = any("Identity" in c for c in categories)
    if has_identity_theft:
        advice_items.append("Never share Aadhaar, PAN card, or bank credentials before a formal interview and background check.")
        emergency_steps.append(
            "If Aadhaar was shared: Immediately lock your Aadhaar biometrics via the mAadhaar app or "
            "UIDAI portal (uidai.gov.in) to prevent unauthorized SIM issuance or e-KYC misuse."
        )

    # Domain mismatch / Free webmail
    has_domain_mismatch = any("DOMAIN_MISMATCH" in c or "TYPOSQUAT" in c for c in categories)
    if has_domain_mismatch:
        advice_items.append(
            "The recruiter is using an unofficial or lookalike domain. Verify recruiter identity directly on the company's official careers portal."
        )

    # Reputation hits
    if actual_reputation_hits:
        advice_items.append(
            f"Caution: {len(actual_reputation_hits)} identifier(s) in this posting have been reported as known scams by community members."
        )

    # Default fallback advice if clean
    if not advice_items:
        advice_items.append("Always verify job postings and recruiter email domains against the official company website before applying.")

    # Generate pre-formatted cybercrime complaint draft
    complaint_draft = _generate_complaint_draft(
        company_name=company_name,
        red_flags=red_flags,
        entities=entities,
        domain_flags=actual_domain_flags,
        reputation_hits=actual_reputation_hits,
    )

    return {
        "advice": advice_items,
        "emergency_steps": emergency_steps,
        "emergency": emergency_steps,  # v2 alias
        "helpline": {
            "number": "1930",
            "name": "Indian National Cyber Crime Reporting Helpline",
            "portal": "https://cybercrime.gov.in",
        },
        "police_complaint_draft": complaint_draft,
        "complaint_draft": complaint_draft,  # alias
    }


def _generate_complaint_draft(
    company_name: str,
    red_flags: List[Dict[str, Any]],
    entities: Dict[str, Any],
    domain_flags: List[Dict[str, Any]],
    reputation_hits: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Pre-formats an incident complaint draft for cybercrime.gov.in or local police."""
    claimed = company_name.strip() if company_name else "Unknown (Impersonating corporate recruiter)"
    phones = ", ".join(entities.get("phones", [])) or "Not provided"
    upi_ids = ", ".join(entities.get("upi_ids", [])) or "Not provided"
    emails = ", ".join(entities.get("emails", [])) or "Not provided"
    telegram = ", ".join(entities.get("telegram_handles", [])) or "Not provided"

    flag_summaries = [f"• {f.get('title') or f.get('message') or f.get('category')}: '{f.get('matched_text', '')}'" for f in red_flags[:4]]
    flags_text = "\n".join(flag_summaries) if flag_summaries else "• Suspicious recruitment scam communications."

    rep_text = ""
    if reputation_hits:
        rep_text = f"\nCOMMUNITY THREAT MATCHES:\n• Identified {len(reputation_hits)} previously reported scam identifier(s) in community threat registry.\n"

    return (
        f"SUBJECT: Report of Online Recruitment Fraud / Cyber Scam claiming '{claimed}'\n\n"
        f"RESPECTED OFFICER / CYBER CRIME CELL,\n\n"
        f"I wish to report an incident of fraudulent job solicitation / recruitment scam. "
        f"The suspect claimed to represent '{claimed}' and engaged via online messaging channels.\n\n"
        f"INCIDENT DETAILS & FRAUDULENT INDICATORS:\n"
        f"{flags_text}\n"
        f"{rep_text}\n"
        f"SUSPECT CONTACT IDENTIFIERS:\n"
        f"- Contact Phone(s): {phones}\n"
        f"- UPI ID(s): {upi_ids}\n"
        f"- Contact Email(s): {emails}\n"
        f"- Telegram / WhatsApp: {telegram}\n\n"
        f"PRAYER / REQUEST:\n"
        f"1. Kindly register this cyber fraud complaint and block the associated UPI and mobile numbers under the IT Act.\n"
        f"2. Initiate appropriate legal proceedings against the perpetrators to protect other job seekers from financial exploitation.\n\n"
        f"Helpline Reference: National Cyber Crime Helpline 1930 / cybercrime.gov.in\n"
        f"Complainant Name: [Insert Your Name]\n"
        f"Date: [Insert Date]\n"
        f"Evidence Attached: Screenshots of job posting and recruiter chats\n"
    )
