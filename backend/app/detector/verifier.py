"""
Domain & Contact Verification Engine.
Detects corporate identity mismatches, free webmail abuse, and suspicious contact channels.
No external API calls — entirely offline rule-based verification.
"""

import re
from typing import Dict, Any, List, Optional

# Free / consumer webmail providers that should NOT be used for corporate hiring
FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.in", "yahoo.co.in",
    "hotmail.com", "outlook.com", "live.com", "msn.com",
    "rediffmail.com", "rediff.com", "protonmail.com", "proton.me",
    "aol.com", "icloud.com", "me.com", "ymail.com",
    "inbox.com", "mail.com", "zohomail.com", "tutanota.com",
    "guerrillamail.com", "mailinator.com", "tempmail.com",
    "10minutemail.com", "throwam.com", "dispostable.com",
}

# Disposable / burner email domains (high severity)
DISPOSABLE_EMAIL_DOMAINS = {
    "guerrillamail.com", "mailinator.com", "tempmail.com",
    "10minutemail.com", "throwam.com", "dispostable.com",
    "sharklasers.com", "yopmail.com", "trashmail.com",
}

# Well-known large companies whose name is commonly impersonated in scams
# Maps company name keywords → their official email domain(s)
KNOWN_COMPANY_DOMAINS = {
    "tcs": ["tcs.com"],
    "tata consultancy": ["tcs.com"],
    "infosys": ["infosys.com"],
    "wipro": ["wipro.com"],
    "accenture": ["accenture.com"],
    "cognizant": ["cognizant.com"],
    "ibm": ["ibm.com"],
    "google": ["google.com", "alphabet.com"],
    "amazon": ["amazon.com"],
    "microsoft": ["microsoft.com"],
    "apple": ["apple.com"],
    "meta": ["meta.com", "fb.com"],
    "facebook": ["meta.com", "fb.com"],
    "netflix": ["netflix.com"],
    "deloitte": ["deloitte.com"],
    "pwc": ["pwc.com"],
    "kpmg": ["kpmg.com"],
    "ernst": ["ey.com"],
    "capgemini": ["capgemini.com"],
    "hcl": ["hcltech.com"],
    "tech mahindra": ["techmahindra.com"],
    "reliance": ["ril.com"],
    "hdfc": ["hdfcbank.com"],
    "icici": ["icicibank.com"],
    "sbi": ["sbi.co.in"],
    "upsc": ["upsc.gov.in"],
    "ssc": ["ssc.nic.in"],
    "railways": ["indianrailways.gov.in"],
    "rbi": ["rbi.org.in"],
}

_EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+\-]+@([a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)"
)


def _extract_emails(text: str) -> List[str]:
    return _EMAIL_REGEX.findall(text.lower())


def _extract_email_addresses(text: str) -> List[str]:
    return re.findall(
        r"[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?",
        text.lower()
    )


def _detect_company_mention(text: str) -> Optional[str]:
    """Finds the first well-known company name mentioned in the text."""
    text_lower = text.lower()
    for company_key in KNOWN_COMPANY_DOMAINS:
        if company_key in text_lower:
            return company_key
    return None


def verify(text: str, declared_company: str = "", contact_email: str = "") -> Dict[str, Any]:
    """
    Performs offline domain and contact verification.

    Parameters
    ----------
    text              : Full job posting text.
    declared_company  : Optional company name provided separately.
    contact_email     : Optional contact email provided separately.

    Returns
    -------
    Dict with:
        - flags (list)          : Verification issues found.
        - penalty (int)         : Score penalty contribution (0-50).
        - emails_found (list)   : All emails extracted from text.
        - has_free_email (bool)
        - has_disposable_email (bool)
        - company_mismatch (bool)
    """
    flags = []
    penalty = 0
    all_email_addresses = _extract_email_addresses(text)
    if contact_email:
        all_email_addresses.append(contact_email.lower().strip())
    all_email_addresses = list(set(all_email_addresses))

    all_domains = [addr.split("@")[-1] for addr in all_email_addresses]

    has_free_email = False
    has_disposable_email = False
    company_mismatch = False

    # --- Check 1: Free webmail domains ---
    free_emails_found = [
        addr for addr in all_email_addresses
        if addr.split("@")[-1] in FREE_EMAIL_DOMAINS
    ]
    if free_emails_found:
        has_free_email = True
        penalty += 20
        flags.append({
            "type": "FREE_WEBMAIL",
            "severity": "HIGH",
            "title": "Free Webmail Used for Corporate Contact",
            "detail": f"Email(s) {free_emails_found} use consumer webmail services. Legitimate companies use their own domain.",
            "emails": free_emails_found,
        })

    # --- Check 2: Disposable / burner email ---
    disposable_found = [
        addr for addr in all_email_addresses
        if addr.split("@")[-1] in DISPOSABLE_EMAIL_DOMAINS
    ]
    if disposable_found:
        has_disposable_email = True
        penalty += 40
        flags.append({
            "type": "DISPOSABLE_EMAIL",
            "severity": "CRITICAL",
            "title": "Disposable / Temporary Email Address",
            "detail": f"Email(s) {disposable_found} are disposable addresses. This is an extreme red flag for recruitment fraud.",
            "emails": disposable_found,
        })

    # --- Check 3: Company name vs email domain mismatch ---
    mentioned_company = declared_company.strip().lower() or _detect_company_mention(text)
    if mentioned_company:
        expected_domains = None
        for key, domains in KNOWN_COMPANY_DOMAINS.items():
            if key in mentioned_company:
                expected_domains = domains
                break

        if expected_domains:
            # Check if any found email uses the expected corporate domain
            has_matching_domain = any(
                any(exp in domain for exp in expected_domains)
                for domain in all_domains
            )
            if not has_matching_domain and all_email_addresses:
                company_mismatch = True
                penalty += 35
                flags.append({
                    "type": "DOMAIN_MISMATCH",
                    "severity": "CRITICAL",
                    "title": f"Company Identity Mismatch",
                    "detail": (
                        f"Posting claims to be from '{mentioned_company.title()}', "
                        f"but contact email(s) {all_email_addresses} do not use the expected "
                        f"official domain(s): {expected_domains}. "
                        "This is a classic impersonation scam."
                    ),
                    "expected_domains": expected_domains,
                    "found_emails": all_email_addresses,
                })

    # --- Check 4: No email at all (suspicious if professional role) ---
    if not all_email_addresses:
        penalty += 5
        flags.append({
            "type": "NO_CONTACT_INFO",
            "severity": "LOW",
            "title": "No Verifiable Contact Email Found",
            "detail": "No email address was provided. Legitimate postings include official contact channels.",
            "emails": [],
        })

    return {
        "flags": flags,
        "flag_count": len(flags),
        "penalty": min(penalty, 50),
        "emails_found": all_email_addresses,
        "has_free_email": has_free_email,
        "has_disposable_email": has_disposable_email,
        "company_mismatch": company_mismatch,
    }
