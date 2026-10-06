"""
document_checks.py - Forensic checks for employment offer letters and contracts.

Checks for:
- Free-email contact addresses
- Missing company address / registration (MCA CIN / GST)
- Missing signatory name
- Generic placeholder names (e.g. "[Your Name]", "[Company Name]", "____")
- Urgent payment clauses
- Metadata anomalies (suspicious creator tool, creation date)
"""

import re
from datetime import datetime
from typing import Any, Optional

# --- Patterns ---
_FREE_EMAIL_RE = re.compile(
    r"[\w.\-+]+@(?:gmail|yahoo|hotmail|outlook|rediffmail|yopmail)\.com",
    re.IGNORECASE
)

_PLACEHOLDER_RE = re.compile(
    r"\[(?:candidate(?:\s*name)?|your\s*name|company(?:\s*name)?|insert\s*\w+|date|salary|designation|title|\.\.\.)\]|"
    r"\{(?:candidate(?:\s*name)?|your\s*name|company(?:\s*name)?)\}|___{2,}|<.*?>",
    re.IGNORECASE
)

_CIN_RE = re.compile(r"\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b")  # India MCA CIN format
_GST_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b")  # Indian GST format

_SIGNATORY_PATTERNS = [
    re.compile(
        r"(?:sincerely|regards|yours\s+(?:truly|faithfully)|authorized\s+signatory|hr\s+manager|"
        r"head\s+of\s+talent|talent\s+acquisition|managing\s+director|signed\s+by|warm\s+regards)",
        re.IGNORECASE
    ),
]

_URGENT_PAYMENT_RE = re.compile(
    r"(?:pay|deposit|transfer|send)\s+(?:immediately|within\s+\d+\s+(?:hour|day|hrs)|urgently|now|asap)|"
    r"(?:fee|deposit|amount)\s+(?:must|should)\s+(?:be\s+)?(?:paid|cleared|sent)\s+(?:before|within)",
    re.IGNORECASE
)

_SUSPICIOUS_CREATOR_TOOLS = {
    "microsoft word 2007", "libreoffice", "wps office", "kingsoft",
    "foxit", "smallpdf", "ilovepdf", "pdf24"
}


def check_document(text: str, metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """
    Run document-specific fraud checks.

    Returns a dict with:
    - document_flags: list of human-readable warning strings
    - placeholders_found: list of placeholder strings detected
    - has_registration: bool
    - has_signatory: bool
    """
    metadata = metadata or {}
    flags: list[str] = []
    placeholders: list[str] = []

    # 1. Free email in document body
    free_emails = _FREE_EMAIL_RE.findall(text)
    if free_emails:
        flags.append(
            f"Document contains free email address(es): {', '.join(free_emails[:3])} — "
            "legitimate offer letters use official corporate email domains."
        )

    # 2. Placeholder text (unfilled templates)
    placeholder_matches = _PLACEHOLDER_RE.findall(text)
    if placeholder_matches:
        unique = list(dict.fromkeys(placeholder_matches[:5]))
        placeholders = unique
        flags.append(
            f"Document contains {len(placeholder_matches)} unfilled placeholder(s): "
            f"{', '.join(unique)} — suggests a generic scam template."
        )

    # 3. Missing company registration (CIN/GST)
    has_cin = bool(_CIN_RE.search(text))
    has_gst = bool(_GST_RE.search(text))
    has_registration = has_cin or has_gst
    if not has_registration:
        flags.append(
            "No corporate registration number (MCA CIN/GST) found. "
            "Legitimate Indian offer letters typically include CIN or GST details."
        )

    # 4. Missing signatory
    has_signatory = any(p.search(text) for p in _SIGNATORY_PATTERNS)
    if not has_signatory:
        flags.append(
            "No formal signatory or authorization salutation detected. "
            "Legitimate offer letters are signed by an authorized HR representative."
        )

    # 5. Urgent payment clauses
    if _URGENT_PAYMENT_RE.search(text):
        flags.append(
            "Document contains urgent payment clauses — "
            "a critical red flag; legitimate employers never demand deposits or fees to issue employment offers."
        )

    # 6. Metadata anomalies
    if metadata:
        creator = str(metadata.get("Creator", metadata.get("Producer", ""))).lower()
        if any(tool in creator for tool in _SUSPICIOUS_CREATOR_TOOLS):
            flags.append(
                f"Document was generated with '{creator}' — "
                "scammers frequently use free conversion utilities to forge offer letters."
            )

        created_raw = str(metadata.get("CreationDate", metadata.get("created", "")))
        if created_raw:
            try:
                date_str = created_raw.replace("D:", "").split("+")[0].split("-")[0][:14]
                created_dt = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                age_days = (datetime.now() - created_dt).days
                if age_days < 3:
                    flags.append(
                        f"Document was created very recently ({age_days} day(s) ago). "
                        "Freshly generated offer letters are a common scam indicator."
                    )
            except Exception:
                pass

    return {
        "document_flags": flags,
        "placeholders_found": placeholders,
        "has_registration": has_registration,
        "has_signatory": has_signatory,
    }


def check_offer_letter_document(text: str) -> dict[str, Any]:
    """Compatibility alias for check_document without metadata."""
    return check_document(text, metadata={})
