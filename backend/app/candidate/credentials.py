"""
Credential Inflation & Diploma Mill Detection Engine (Day 2 - Module 3).
Detects:
1. Degrees from known unaccredited diploma mills and counterfeit university mills.
2. Anachronistic tech stack claims (technologies claimed before their release year).
3. AI/LLM synthetic resume artifacts and prompt leakage markers.
4. Unrealistic credential inflation and placeholder text.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# ── Known Diploma Mills & Counterfeit Degree Mills Blacklist ─────────────────

KNOWN_DIPLOMA_MILLS = {
    "almeda university", "rochville university", "belford university", "corllins university",
    "breyer state university", "must university", "ashley university", "northern port university",
    "paramount california university", "university of berkley", "kingsbridge university",
    "california south university", "columbus international university", "glendale university",
    "lacrosse university", "st. regis university", "american world university",
    "trinity college & university", "panworld university", "concordia college & university",
}

BOGUS_ACCREDITATION_MARKERS = [
    r"\buniversal\s+accreditation\b",
    r"\bglobal\s+accreditation\s+commission\b",
    r"\binternational\s+accreditation\s+organization\s*\(iao\)\b",
    r"\bworld\s+council\s+for\s+excellence\b",
    r"\blife\s+experience\s+degree\b",
    r"\bdegree\s+in\s+7\s+days\b",
]

# ── Tech Stack Invention / Public Release Year Baseline ──────────────────────

TECH_RELEASE_YEARS = {
    "kubernetes": 2014,
    "docker": 2013,
    "react": 2013,
    "react native": 2015,
    "flutter": 2018,
    "golang": 2009,
    "go": 2009,
    "rust": 2015,
    "typescript": 2012,
    "swift": 2014,
    "kotlin": 2011,
    "next.js": 2016,
    "fastapi": 2018,
    "pytorch": 2016,
    "tensorflow": 2015,
    "vue": 2014,
    "vue.js": 2014,
    "solidity": 2014,
    "graphql": 2015,
    "kafka": 2011,
    "terraform": 2014,
}

# ── AI / Synthetic Generation & Prompt Leakage Markers ──────────────────────

SYNTHETIC_AI_MARKERS = [
    (r"\bas\s+an\s+ai\s+language\s+model\b", "ChatGPT Self-Identification Leakage", "CRITICAL"),
    (r"\bhere\s+is\s+(?:a|an|the|your)\s+(?:tailored|optimized|customized|professional)?\s*(?:resume|cv|summary)\b", "AI Assistant Response Header", "CRITICAL"),
    (r"\bcertainly!?\s*(?:here\s+is|below\s+is)\b", "Chatbot Conversational Opening", "HIGH"),
    (r"\bfeel\s+free\s+to\s+(?:adjust|customize|tweak)\s+(?:the\s+details|the\s+metrics|any\s+numbers)\b", "AI Assistant Advice Footnote", "HIGH"),
    (r"\[insert\s+(?:company(?:\s+name)?|job\s+title|your\s+name|university|degree|metric|date|year)\]", "Unfilled Template Placeholder Token", "CRITICAL"),
    (r"\[your\s+name\]", "Unfilled Candidate Name Placeholder", "CRITICAL"),
    (r"\bx%\s+increase\b|\by%\s+growth\b", "Generic Placeholder Percentage", "HIGH"),
]


def check_diploma_mills(education: List[Dict[str, Any]], raw_text: str) -> List[Dict[str, Any]]:
    """
    Checks education history against known unaccredited diploma mills
    and detects suspicious bogus accreditation phrases.
    """
    flags = []
    text_lower = raw_text.lower()

    # 1. Check institutions against known diploma mills
    for edu in education:
        inst = (edu.get("institution") or "").lower()
        context = (edu.get("raw_context") or "").lower()

        matched_mill = None
        for mill in KNOWN_DIPLOMA_MILLS:
            if mill in inst or mill in context:
                matched_mill = mill.title()
                break

        if matched_mill:
            flags.append({
                "category": "Bogus Degree / Diploma Mill",
                "severity": "CRITICAL",
                "title": f"Degree from Blacklisted Diploma Mill ({matched_mill})",
                "description": (
                    f"Institution '{matched_mill}' is a globally blacklisted unaccredited diploma mill "
                    f"associated with counterfeit credentials and fraudulent certifications."
                ),
                "institution": matched_mill,
            })

    # 2. Check for bogus accreditation phrases
    for pattern in BOGUS_ACCREDITATION_MARKERS:
        match = re.search(pattern, text_lower)
        if match:
            flags.append({
                "category": "Bogus Accreditation",
                "severity": "CRITICAL",
                "title": "Unrecognized / Counterfeit Accreditation Board",
                "description": f"Contains phrase '{match.group(0).title()}' commonly used by fraudulent degree operations.",
            })

    return flags


def check_anachronistic_tech_claims(
    experiences: List[Dict[str, Any]],
    raw_text: str,
) -> List[Dict[str, Any]]:
    """
    Detects claims of using technical tools or frameworks before they were publicly released.
    Also detects claiming impossible durations (e.g. 15 years experience with Flutter in 2024).
    """
    flags = []
    current_year = datetime.now().year

    # 1. Experience date vs tech release year
    for exp in experiences:
        start_year = exp.get("start_year")
        context = (exp.get("raw_context") or "").lower()

        if not start_year:
            continue

        for tech, release_year in TECH_RELEASE_YEARS.items():
            pattern = rf"\b{re.escape(tech)}\b"
            if re.search(pattern, context):
                if start_year < release_year:
                    diff = release_year - start_year
                    severity = "CRITICAL" if diff >= 2 else "HIGH"
                    flags.append({
                        "category": "Anachronistic Tech Claim",
                        "severity": severity,
                        "title": f"Pre-Invention Tech Claim ({tech.title()})",
                        "description": (
                            f"Role starting in {start_year} claims experience with {tech.title()}, "
                            f"which was not invented or publicly released until {release_year} ({diff} years later)."
                        ),
                        "technology": tech.title(),
                        "claimed_start": start_year,
                        "release_year": release_year,
                    })

    # 2. Duration exaggeration regex: e.g. "10+ years experience in Flutter"
    duration_pattern = re.compile(
        r"\b(\d{1,2})\+?\s*(?:years|yrs)\s+(?:of\s+)?(?:experience\s+(?:in|with)\s+)?([a-zA-Z0-9#+.]+)\b",
        re.IGNORECASE,
    )
    for match in duration_pattern.finditer(raw_text):
        claimed_years = int(match.group(1))
        tech_name = match.group(2).lower()

        if tech_name in TECH_RELEASE_YEARS:
            max_possible_years = current_year - TECH_RELEASE_YEARS[tech_name]
            if claimed_years > max_possible_years:
                flags.append({
                    "category": "Anachronistic Tech Claim",
                    "severity": "CRITICAL",
                    "title": f"Impossible Tech Tenure ({tech_name.title()})",
                    "description": (
                        f"Claims {claimed_years} years of experience with {tech_name.title()}, "
                        f"but the technology has only existed for {max_possible_years} years (released in {TECH_RELEASE_YEARS[tech_name]})."
                    ),
                    "technology": tech_name.title(),
                    "claimed_years": claimed_years,
                    "max_possible_years": max_possible_years,
                })

    return flags


def check_synthetic_ai_artifacts(raw_text: str) -> List[Dict[str, Any]]:
    """
    Identifies AI chatbot prompt leakage, generic placeholders, and LLM artifacts.
    """
    flags = []

    for item in SYNTHETIC_AI_MARKERS:
        pattern = item[0]
        title = item[1]
        severity = item[2] if len(item) > 2 else "HIGH"

        matches = list(re.finditer(pattern, raw_text, re.IGNORECASE))
        for m in matches:
            flags.append({
                "category": "Synthetic AI Artifact",
                "severity": severity,
                "title": title,
                "description": f"Found synthetic AI assistant artifact: '{m.group(0)}'.",
                "matched_text": m.group(0),
                "start": m.start(),
                "end": m.end(),
            })

    return flags


def analyze_credentials(parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Credential & Authenticity Verification.
    Combines diploma mill detection, anachronistic tech timeline checks,
    and synthetic AI generation detection.
    """
    raw_text = parsed_resume.get("raw_text", "")
    education = parsed_resume.get("education", [])
    experiences = parsed_resume.get("experience", [])

    diploma_flags = check_diploma_mills(education, raw_text)
    anachronistic_flags = check_anachronistic_tech_claims(experiences, raw_text)
    ai_flags = check_synthetic_ai_artifacts(raw_text)

    all_flags = diploma_flags + anachronistic_flags + ai_flags

    # Penalty score calculation (0 - 100)
    penalty = 0
    for f in all_flags:
        if f["severity"] == "CRITICAL":
            penalty += 40
        elif f["severity"] == "HIGH":
            penalty += 25
        elif f["severity"] == "MEDIUM":
            penalty += 15
    penalty = min(100, penalty)

    return {
        "credential_flag_count": len(all_flags),
        "credential_penalty": penalty,
        "flags": all_flags,
        "diploma_mill_detected": len(diploma_flags) > 0,
        "anachronistic_claims_detected": len(anachronistic_flags) > 0,
        "ai_generation_detected": len(ai_flags) > 0,
    }
