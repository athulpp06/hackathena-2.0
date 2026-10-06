"""
typosquat.py - Typosquatting and lookalike corporate domain detection engine.

Detects:
- Levenshtein / edit distance lookalikes (e.g. googel.com, infosyys.com)
- Homoglyph character substitutions (e.g. g00gle.com, micr0s0ft.com)
- Punycode / IDN spoofing (xn--)
- Keyword stuffing in unofficial domains (e.g. amazon-career-jobs.xyz)
- Suspicious top-level domains (.xyz, .top, .work, .biz, .club, .click)
"""

import os
import json
import re
from typing import Dict, List, Any, Optional

# Homoglyph translation table
_HOMOGLYPHS = str.maketrans({
    "0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "@": "a",
})

SUSPICIOUS_TLDS = {".xyz", ".top", ".club", ".work", ".online", ".site", ".info", ".biz", ".click", ".link"}

_KNOWN_COMPANIES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "known_companies.json"
)

_known_companies: List[Dict[str, Any]] = []


def _load_known_companies() -> List[Dict[str, Any]]:
    global _known_companies
    if not _known_companies:
        try:
            path = os.path.abspath(_KNOWN_COMPANIES_PATH)
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    _known_companies = json.load(f)
        except Exception:
            _known_companies = []
    return _known_companies


def _levenshtein(a: str, b: str) -> int:
    """Pure Python Levenshtein distance."""
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev_row: List[int] = list(range(len(b) + 1))
    for i, c in enumerate(a):
        curr_row = [i + 1]
        for j, d in enumerate(b):
            curr_row.append(min(prev_row[j + 1] + 1, curr_row[j] + 1, prev_row[j] + (c != d)))
        prev_row = curr_row
    return prev_row[-1]


def _normalize_domain(domain: str) -> str:
    """Normalizes domain by lowercasing and applying homoglyph mapping."""
    d = domain.lower().replace("rn", "m")
    return d.translate(_HOMOGLYPHS)


def check_domain_typosquatting(domain: str, claimed_company: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks if a domain is an impersonation or typosquat of a known major employer.
    """
    companies = _load_known_companies()
    flags: List[str] = []
    is_typosquat = False
    matched_company: Optional[str] = None
    severity = "NONE"

    domain_lower = domain.lower().strip()
    norm_domain = _normalize_domain(domain_lower)
    raw_domain_base = re.sub(r"\.[a-z]{2,8}$", "", domain_lower)
    norm_domain_base = re.sub(r"\.[a-z]{2,8}$", "", norm_domain)

    # 1. Punycode check
    if domain_lower.startswith("xn--") or ".xn--" in domain_lower:
        is_typosquat = True
        severity = "CRITICAL"
        flags.append(
            f"Domain '{domain_lower}' uses an Internationalized Domain Name (Punycode / xn--) lookalike."
        )

    # 2. Suspicious TLD check
    tld_match = re.search(r"(\.[a-z]{2,8})$", domain_lower)
    tld = tld_match.group(1) if tld_match else ""
    if tld in SUSPICIOUS_TLDS:
        flags.append(f"Domain '{domain_lower}' uses high-risk TLD '{tld}' commonly abused in recruitment phishing.")
        if severity == "NONE":
            severity = "HIGH"

    # 3. Check against known corporate domains
    claimed_norm = (claimed_company or "").lower().strip()

    for comp in companies:
        comp_name = comp["name"]
        aliases = [a.lower() for a in comp.get("aliases", [])] + [comp_name.lower()]
        official_domains = comp.get("domains", [])

        # Is this company specifically claimed or relevant?
        is_claimed = any(a in claimed_norm for a in aliases) if claimed_norm else False

        for off_dom in official_domains:
            off_dom_lower = off_dom.lower()
            off_base = re.sub(r"\.[a-z]{2,8}$", "", off_dom_lower)

            if domain_lower == off_dom_lower:
                # Exact official match
                return {
                    "is_typosquat": False,
                    "is_official": True,
                    "matched_company": comp_name,
                    "official_domain": off_dom_lower,
                    "flags": [],
                    "severity": "NONE",
                }

            dist = _levenshtein(norm_domain_base, off_base)

            # Homoglyph lookalike (e.g. g00gle.com)
            if dist == 0 and raw_domain_base != off_base:
                is_typosquat = True
                matched_company = comp_name
                severity = "CRITICAL"
                flags.append(
                    f"Domain '{domain_lower}' is a homoglyph lookalike of official '{off_dom_lower}' "
                    f"({comp_name}) — character substitution detected."
                )
                break

            # Edit distance <= 2 (e.g. infossys.com, amzon.com)
            elif 0 < dist <= 2 and len(off_base) >= 4:
                is_typosquat = True
                matched_company = comp_name
                severity = "CRITICAL" if is_claimed else "HIGH"
                flags.append(
                    f"Domain '{domain_lower}' closely mimics official '{off_dom_lower}' "
                    f"({comp_name}) with edit distance {dist}."
                )
                break

            # Keyword stuffing: domain embeds official brand name with extra junk (e.g. amazon-jobs-portal.xyz)
            elif off_base in domain_lower and domain_lower != off_dom_lower and len(off_base) >= 4:
                is_typosquat = True
                matched_company = comp_name
                severity = "CRITICAL" if is_claimed else "HIGH"
                flags.append(
                    f"Domain '{domain_lower}' embeds brand '{off_base}' but is not an official domain of {comp_name}."
                )
                break

    return {
        "is_typosquat": is_typosquat,
        "is_official": False,
        "matched_company": matched_company,
        "flags": flags,
        "severity": severity,
    }
