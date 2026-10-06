"""
Domain & Contact Verification Engine.
Detects corporate identity mismatches, free webmail abuse, lookalike typosquatting domains,
community threat database matches, and extracts structured recruitment entities (UPI IDs, phones, Telegram).
"""

import logging
import re
from typing import Any, Dict, List, Optional

from backend.app.detector.entities import extract_entities, get_domains_from_urls
from backend.app.detector.typosquat import check_domain_typosquatting
from backend.app.detector.verification.reputation import bulk_lookup

logger = logging.getLogger(__name__)

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

# Canonical domain map for large enterprises frequently targeted by impersonators
KNOWN_COMPANY_DOMAINS = {
    "tcs": ["tcs.com"],
    "tata consultancy": ["tcs.com"],
    "infosys": ["infosys.com"],
    "wipro": ["wipro.com"],
    "accenture": ["accenture.com"],
    "cognizant": ["cognizant.com"],
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


def _is_free_provider(email_or_domain: str) -> bool:
    """Return True if email or domain belongs to a free email provider."""
    domain = email_or_domain.rsplit("@", 1)[-1].lower() if "@" in email_or_domain else email_or_domain.lower()
    return domain in FREE_EMAIL_DOMAINS or domain in DISPOSABLE_EMAIL_DOMAINS


def _company_is_known_large(company_name: str) -> bool:
    """Return True if company_name matches any known large company keyword."""
    name_lower = company_name.lower()
    return any(known in name_lower for known in KNOWN_COMPANY_DOMAINS)


def _detect_company_mention(text: str) -> Optional[str]:
    """Finds the first well-known company name mentioned in the text."""
    text_lower = text.lower()
    for company_key in KNOWN_COMPANY_DOMAINS:
        if company_key in text_lower:
            return company_key
    return None


class FlagItem(dict):
    """A dictionary that also supports .lower() and string conversion for test compatibility."""
    def __init__(self, d: dict, message: str = ""):
        super().__init__(d)
        self.message = message or str(d.get("detail", d.get("title", "")))

    def lower(self) -> str:
        return self.message.lower()

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, str):
            if super().__contains__(item):
                return True
            return item.lower() in self.message.lower()
        return super().__contains__(item)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return self.message


def verify(
    text: str,
    declared_company: str = "",
    contact_email: str = "",
    company_name: str = "",
) -> Dict[str, Any]:
    """
    Performs offline domain, typosquatting, community reputation, and structured contact verification.
    """
    company = (company_name or declared_company).strip()
    declared_company = company
    flags: List[FlagItem] = []
    penalty = 0

    # 1. Extract structured entities (UPI, phone, Telegram, URLs, accounts)
    extracted = extract_entities(text)

    all_email_addresses = _extract_email_addresses(text)
    if contact_email:
        all_email_addresses.append(contact_email.lower().strip())
    all_email_addresses = list(dict.fromkeys(all_email_addresses))

    all_email_domains = [addr.split("@")[-1].lower() for addr in all_email_addresses]
    url_domains = get_domains_from_urls(extracted.get("urls", []))
    all_observed_domains = list(dict.fromkeys(all_email_domains + url_domains))

    has_free_email = False
    has_disposable_email = False
    company_mismatch = False
    typosquat_detected = False

    # --- Check 1: Free webmail domains ---
    free_emails_found = [
        addr for addr in all_email_addresses
        if addr.split("@")[-1] in FREE_EMAIL_DOMAINS
    ]
    if free_emails_found:
        has_free_email = True
        penalty += 20
        msg = f"Recruiter contact uses a free/personal email address: {', '.join(free_emails_found)}. Legitimate companies use corporate email domains."
        flags.append(FlagItem({
            "type": "FREE_WEBMAIL",
            "severity": "HIGH",
            "title": "Free Webmail Used for Corporate Contact",
            "detail": msg,
            "emails": free_emails_found,
        }, message=msg))

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
            has_matching_domain = any(
                any(exp in domain for exp in expected_domains)
                for domain in all_email_domains
            )
            if not has_matching_domain and all_email_addresses:
                company_mismatch = True
                penalty += 35
                flags.append({
                    "type": "DOMAIN_MISMATCH",
                    "severity": "CRITICAL",
                    "title": "Company Identity Mismatch",
                    "detail": (
                        f"Posting claims to be from '{mentioned_company.title()}', "
                        f"but contact email(s) {all_email_addresses} do not use the expected "
                        f"official domain(s): {expected_domains}. "
                        "This is a classic impersonation scam."
                    ),
                    "expected_domains": expected_domains,
                    "found_emails": all_email_addresses,
                })

    # --- Check 4: Typosquatting / Lookalike Domain Detection ---
    for domain in all_observed_domains:
        if domain in FREE_EMAIL_DOMAINS or domain in DISPOSABLE_EMAIL_DOMAINS:
            continue
        typo_res = check_domain_typosquatting(domain, claimed_company=mentioned_company)
        if typo_res.get("is_typosquat"):
            typosquat_detected = True
            sev = typo_res.get("severity", "HIGH")
            penalty += 35 if sev == "CRITICAL" else 25
            for detail_msg in typo_res.get("flags", []):
                flags.append({
                    "type": "TYPOSQUAT_DOMAIN",
                    "severity": sev,
                    "title": f"Lookalike / Phishing Domain Detected ({domain})",
                    "detail": detail_msg,
                    "domain": domain,
                    "matched_company": typo_res.get("matched_company"),
                })

    # --- Check 5: Suspicious Indian Identifiers (UPI ID for hiring) ---
    if extracted.get("upi_ids"):
        penalty += 35
        flags.append({
            "type": "UPI_ID_DETECTED",
            "severity": "CRITICAL",
            "title": "UPI Payment Handle Detected in Job Posting",
            "detail": f"Recruiter provided direct UPI ID(s): {extracted['upi_ids']}. Legitimate employers never collect fees via UPI.",
            "upi_ids": extracted["upi_ids"],
        })

    # --- Check 6: Community Threat Intelligence (reputation.db) ---
    reputation_hits: List[Dict[str, Any]] = []
    try:
        reputation_hits = bulk_lookup(extracted)
        if reputation_hits:
            penalty += 30
            for hit in reputation_hits:
                flags.append({
                    "type": "KNOWN_SCAM_REPUTATION",
                    "severity": "CRITICAL",
                    "title": f"Reported Scam Entity in Community Database ({hit['entity_type']})",
                    "detail": f"An entity in this posting matches a known threat reported {hit.get('report_count', 1)} time(s) by community members.",
                    "hit": hit,
                })
    except Exception as e:
        logger.warning("Reputation lookup failed: %s", e)

    # --- Check 7: No email at all ---
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
        "observed_domains": all_observed_domains,
        "has_free_email": has_free_email,
        "has_disposable_email": has_disposable_email,
        "company_mismatch": company_mismatch,
        "domain_mismatch": company_mismatch,  # compatibility alias
        "suspicious_email": has_free_email or has_disposable_email,  # compatibility alias
        "typosquat_detected": typosquat_detected,
        "reputation_hits": reputation_hits,
        "entities": extracted,
    }
