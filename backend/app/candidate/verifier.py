"""
Reference & Digital Footprint Verifier Engine (Day 2 - Module 4).
Verifies:
1. Reference email integrity (detects free webmail or disposable burner domains
   used as official corporate HR / Engineering Manager references).
2. Candidate primary contact domain risk.
3. Professional social profile integrity (LinkedIn / GitHub handle validation and placeholders).
"""

import re
from typing import Dict, Any, List, Optional
from backend.app.detector.verifier import FREE_EMAIL_DOMAINS, DISPOSABLE_EMAIL_DOMAINS, KNOWN_COMPANY_DOMAINS

# Placeholder handles that signify template fabrication
SUSPICIOUS_PROFILE_HANDLES = {
    "your-profile", "username", "yourname", "john-doe", "johndoe",
    "placeholder", "your-username", "user-id", "insert-name", "xyz",
}


def _extract_domain(email: str) -> Optional[str]:
    """Extracts lowercase domain from email address."""
    parts = email.strip().split("@")
    if len(parts) == 2:
        return parts[1].lower().strip()
    return None


def verify_references(references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Examines candidate references for fraudulent contact patterns:
    - Corporate / managerial titles using personal webmail (@gmail.com, etc.)
    - Disposable burner emails used as official references.
    """
    flags = []

    for ref in references:
        name = ref.get("name", "Reference")
        email = ref.get("email", "")
        domain = _extract_domain(email)

        if not domain:
            continue

        # Check for disposable emails (Critical severity)
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            flags.append({
                "category": "Reference Fraud",
                "severity": "CRITICAL",
                "title": f"Disposable Email Used for Reference ({domain})",
                "description": (
                    f"Reference '{name}' listed disposable burner address '{email}'. "
                    f"Legitimate corporate referees do not use burner email providers."
                ),
                "reference_name": name,
                "email": email,
            })
            continue

        # Check for free webmail with corporate title
        if domain in FREE_EMAIL_DOMAINS:
            # Check if referee has managerial/corporate keywords
            ref_lower = (name + " " + email).lower()
            is_corporate_claim = any(
                w in ref_lower for w in [
                    "director", "manager", "vp", "lead", "head", "hr", "recruiter",
                    "tcs", "infosys", "google", "microsoft", "amazon", "flipkart", "stripe",
                ]
            )
            severity = "HIGH" if is_corporate_claim else "MEDIUM"
            flags.append({
                "category": "Reference Verification",
                "severity": severity,
                "title": f"Generic Consumer Webmail for Referee ({domain})",
                "description": (
                    f"Reference '{name}' provided personal webmail '{email}' instead of an official "
                    f"corporate email domain. Independent verification required."
                ),
                "reference_name": name,
                "email": email,
            })

    return flags


def verify_digital_footprint(contact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validates candidate's contact email, LinkedIn, and GitHub profile handles.
    """
    flags = []

    # 1. Candidate primary email checks
    primary_email = contact.get("primary_email") or ""
    cand_domain = _extract_domain(primary_email)
    if cand_domain and cand_domain in DISPOSABLE_EMAIL_DOMAINS:
        flags.append({
            "category": "Candidate Identity",
            "severity": "CRITICAL",
            "title": f"Candidate Uses Disposable Burner Email ({cand_domain})",
            "description": f"Primary contact email '{primary_email}' belongs to a temporary/burner email service.",
            "email": primary_email,
        })

    # 2. LinkedIn handle validation
    linkedin_handle = (contact.get("linkedin_handle") or "").lower()
    if linkedin_handle:
        if linkedin_handle in SUSPICIOUS_PROFILE_HANDLES or len(linkedin_handle) < 3:
            flags.append({
                "category": "Digital Footprint",
                "severity": "HIGH",
                "title": "Placeholder LinkedIn Profile URL",
                "description": f"LinkedIn profile contains placeholder handle: '{linkedin_handle}'.",
                "handle": linkedin_handle,
            })

    # 3. GitHub handle validation
    github_handle = (contact.get("github_handle") or "").lower()
    if github_handle:
        if github_handle in SUSPICIOUS_PROFILE_HANDLES or len(github_handle) < 3:
            flags.append({
                "category": "Digital Footprint",
                "severity": "HIGH",
                "title": "Placeholder GitHub Profile URL",
                "description": f"GitHub profile contains placeholder handle: '{github_handle}'.",
                "handle": github_handle,
            })

    return flags


def verify_candidate_profiles(parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Reference & Digital Footprint Verification.
    """
    contact = parsed_resume.get("contact", {})
    references = parsed_resume.get("references", [])

    ref_flags = verify_references(references)
    footprint_flags = verify_digital_footprint(contact)

    all_flags = ref_flags + footprint_flags

    # Calculate penalty (0 - 50)
    penalty = 0
    for f in all_flags:
        if f["severity"] == "CRITICAL":
            penalty += 35
        elif f["severity"] == "HIGH":
            penalty += 20
        elif f["severity"] == "MEDIUM":
            penalty += 10
    penalty = min(50, penalty)

    return {
        "footprint_flag_count": len(all_flags),
        "footprint_penalty": penalty,
        "flags": all_flags,
        "reference_issues": len(ref_flags),
        "footprint_issues": len(footprint_flags),
    }
