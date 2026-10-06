"""
typosquat.py - Typosquatting and lookalike domain detection.
"""

import json
import os
import re


# Levenshtein distance (pure Python, no external library needed)
def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev_row: list[int] = list(range(len(b) + 1))
    for i, c in enumerate(a):
        curr_row = [i + 1]
        for j, d in enumerate(b):
            curr_row.append(min(prev_row[j + 1] + 1, curr_row[j] + 1, prev_row[j] + (c != d)))
        prev_row = curr_row
    return prev_row[-1]

# Homoglyph mapping for domain comparison
_HOMOGLYPHS = str.maketrans({
    '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's',
})

_KNOWN_COMPANIES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "data", "known_companies.json"
)

_known_companies: list[dict] = []

def _load_known_companies() -> list[dict]:
    global _known_companies
    if not _known_companies:
        try:
            path = os.path.abspath(_KNOWN_COMPANIES_PATH)
            with open(path, encoding="utf-8") as f:
                _known_companies = json.load(f)
        except Exception:
            _known_companies = []
    return _known_companies

SUSPICIOUS_TLDS = {".xyz", ".top", ".club", ".work", ".online", ".site", ".info", ".biz", ".click", ".link"}
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "short.io"}

def _normalize_domain(domain: str) -> str:
    """Apply homoglyph map and lowercase for comparison."""
    d = domain.lower().replace("rn", "m")
    return d.translate(_HOMOGLYPHS)

def check_domain(domain: str) -> dict:
    """
    Check a domain against known company domains for typosquatting.
    Returns flags dict.
    """
    companies = _load_known_companies()
    flags = []
    is_typosquat = False
    matched_company = None

    norm_domain = _normalize_domain(domain)
    raw_domain_base = re.sub(r'\.[a-z]{2,6}$', '', domain.lower())
    domain_base = re.sub(r'\.[a-z]{2,6}$', '', norm_domain)

    # Punycode / IDN check
    if domain.startswith("xn--") or ".xn--" in domain:
        is_typosquat = True
        flags.append(f"Domain '{domain}' uses an Internationalized Domain Name (Punycode) representation — common phishing technique")

    for company in companies:
        for official_domain in company["domains"]:
            official_base = re.sub(r'\.[a-z]{2,6}$', '', official_domain.lower())
            dist = _levenshtein(domain_base, official_base)

            # Homoglyph lookalike: distance is 0 after normalization, but raw string differs
            if dist == 0 and raw_domain_base != official_base:
                is_typosquat = True
                matched_company = company["name"]
                flags.append(
                    f"Domain '{domain}' is a homoglyph lookalike of official '{official_domain}' "
                    f"({company['name']}) — typosquatting attempt"
                )
            # Threshold: edit distance <= 2 and NOT an exact match
            elif 0 < dist <= 2:
                is_typosquat = True
                matched_company = company["name"]
                flags.append(
                    f"Domain '{domain}' looks similar to official '{official_domain}' "
                    f"({company['name']}) — possible typosquat (edit distance: {dist})"
                )
            # Keyword stuffing: domain contains official name but has extra junk
            elif official_base in domain_base and domain_base != official_base:
                is_typosquat = True
                matched_company = company["name"]
                flags.append(
                    f"Domain '{domain}' contains '{official_base}' but is not the official domain — "
                    f"possible impersonation of {company['name']}"
                )

    # Suspicious TLD
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            flags.append(f"Domain uses suspicious TLD '{tld}'")

    # URL shortener
    if domain in URL_SHORTENERS:
        flags.append(f"'{domain}' is a URL shortener — real destination is hidden")

    # IP address as domain
    if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', domain):
        flags.append(f"URL uses a raw IP address ({domain}) instead of a domain name")

    # Excessive subdomains
    parts = domain.split(".")
    if len(parts) > 4:
        flags.append(f"Domain has excessive subdomains ({len(parts) - 2}) — potential phishing indicator")

    return {
        "is_typosquat": is_typosquat,
        "matched_company": matched_company,
        "domain_flags": flags
    }


def check_company_claim(company_name: str, emails: list[str]) -> list[str]:
    """
    Check if a claimed company name is from a known company but uses a free email.
    """
    companies = _load_known_companies()
    flags: list[str] = []

    if not company_name or not emails:
        return flags

    # Find if the claimed company is a known company
    company_name_lower = company_name.lower()
    matched = None
    for c in companies:
        if c["name"].lower() in company_name_lower or company_name_lower in c["name"].lower():
            matched = c
            break

    if matched:
        free_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "rediffmail.com"]
        for email in emails:
            domain = email.split("@")[-1].lower() if "@" in email else ""
            if domain in free_providers:
                flags.append(
                    f"'{company_name}' is a major company, but recruiter is using free email '{email}'. "
                    f"Official domain should be @{matched['domains'][0]}"
                )
    return flags
