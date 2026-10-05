"""
Chronological Timeline & Anomaly Detection Engine (Day 2 - Module 2).
Analyzes candidate career and education progression to detect:
1. Overlapping full-time roles (parallel employment / moonlighting / fabrication).
2. Education vs. work experience timeline paradoxes (e.g. senior corporate roles prior to high school).
3. Impossible title velocities (e.g. Intern directly to CTO in under 6 months).
4. Future dates or invalid temporal claims.
5. Generates structured timeline visualization objects for the frontend UI.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


def _is_internship_or_part_time(role: Dict[str, Any]) -> bool:
    """Checks whether an experience entry is an internship, trainee, or part-time position based on its job title."""
    title = (role.get("title") or "").lower()
    return any(w in title for w in ["intern", "internship", "trainee", "part-time", "part time", "fellow", "volunteer"])


def detect_overlapping_roles(experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identifies overlapping full-time employment tenures.
    Permits legitimate internships or part-time projects overlapping with education/work.
    """
    overlaps = []
    n = len(experiences)
    if n < 2:
        return overlaps

    for i in range(n):
        exp_a = experiences[i]
        if _is_internship_or_part_time(exp_a):
            continue

        a_start = exp_a["start_year"] * 12 + exp_a["start_month"]
        a_end = exp_a["end_year"] * 12 + exp_a["end_month"]

        for j in range(i + 1, n):
            exp_b = experiences[j]
            if _is_internship_or_part_time(exp_b):
                continue

            b_start = exp_b["start_year"] * 12 + exp_b["start_month"]
            b_end = exp_b["end_year"] * 12 + exp_b["end_month"]

            # Check overlap between [a_start, a_end] and [b_start, b_end]
            overlap_start = max(a_start, b_start)
            overlap_end = min(a_end, b_end)

            if overlap_end > overlap_start:
                overlap_months = overlap_end - overlap_start
                # Tolerate small transitions <= 1 month (resignation / notice overlap)
                if overlap_months >= 2:
                    severity = "CRITICAL" if overlap_months >= 6 else "HIGH"
                    overlaps.append({
                        "category": "Concurrent Employment",
                        "severity": severity,
                        "title": "Simultaneous Full-Time Roles Detected",
                        "description": (
                            f"Concurrent full-time tenures detected between '{exp_a['company']}' ({exp_a['title']}) "
                            f"and '{exp_b['company']}' ({exp_b['title']}) spanning {overlap_months} overlapping months."
                        ),
                        "role_a": exp_a["title"],
                        "company_a": exp_a["company"],
                        "role_b": exp_b["title"],
                        "company_b": exp_b["company"],
                        "overlap_months": overlap_months,
                    })

    return overlaps


def detect_education_timeline_paradoxes(
    education: List[Dict[str, Any]],
    experiences: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detects chronological contradictions between education dates and career history:
    - Claiming senior corporate roles before completing 10th/12th grade or starting college.
    - Post-graduate degree dates preceding bachelor degree completion.
    """
    anomalies = []

    # 1. Degree order paradox (e.g. Master's before Bachelor's)
    bachelor_end_year = None
    masters_start_year = None
    high_school_year = None

    for edu in education:
        deg = edu.get("degree", "").lower()
        if "b.tech" in deg or "b.e" in deg or "bachelor" in deg or "bca" in deg or "b.sc" in deg:
            bachelor_end_year = edu.get("end_year") or edu.get("start_year")
        elif "m.tech" in deg or "m.s" in deg or "mba" in deg or "master" in deg:
            masters_start_year = edu.get("start_year") or edu.get("end_year")
        elif "high school" in deg or "12th" in deg or "secondary" in deg:
            high_school_year = edu.get("end_year") or edu.get("start_year")

    if bachelor_end_year and masters_start_year and masters_start_year < (bachelor_end_year - 1):
        anomalies.append({
            "category": "Education Chronology Paradox",
            "severity": "HIGH",
            "title": "Master's Degree Precedes Bachelor's Completion",
            "description": (
                f"Master's degree listed as starting in {masters_start_year}, prior to "
                f"Bachelor's degree completion in {bachelor_end_year}."
            ),
        })

    if high_school_year and bachelor_end_year and high_school_year > bachelor_end_year:
        anomalies.append({
            "category": "Education Chronology Paradox",
            "severity": "CRITICAL",
            "title": "High School Completion Listed After University Graduation",
            "description": (
                f"High school completion ({high_school_year}) is listed after university "
                f"graduation ({bachelor_end_year}), which is chronologically impossible."
            ),
        })

    # 2. Senior / Full-time role prior to high school or early college
    for exp in experiences:
        role_start = exp.get("start_year")
        title = exp.get("title", "")
        is_senior = any(w in title.lower() for w in ["senior", "lead", "principal", "manager", "director", "architect", "head", "vp", "chief"])

        if high_school_year and role_start and role_start <= high_school_year:
            if not _is_internship_or_part_time(exp):
                anomalies.append({
                    "category": "Experience vs Education Paradox",
                    "severity": "CRITICAL",
                    "title": "Full-Time Corporate Employment Precedes High School",
                    "description": (
                        f"Candidate claims full-time role '{title}' at '{exp.get('company')}' starting in {role_start}, "
                        f"before completing high school in {high_school_year}."
                    ),
                    "role": title,
                    "company": exp.get("company"),
                })
        elif bachelor_end_year and is_senior and role_start and role_start < (bachelor_end_year - 2):
            anomalies.append({
                "category": "Experience vs Education Paradox",
                "severity": "HIGH",
                "title": "Senior Corporate Title Claimed During Early Undergrad",
                "description": (
                    f"Senior level title '{title}' at '{exp.get('company')}' claimed in {role_start}, "
                    f"years prior to university graduation in {bachelor_end_year}."
                ),
                "role": title,
                "company": exp.get("company"),
            })

    return anomalies


def detect_career_velocity_anomalies(experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detects unfeasible rapid title jumps (e.g. Intern -> CTO/VP in < 6 months).
    """
    anomalies = []
    executive_keywords = ["chief technology officer", "cto", "chief executive", "ceo", "vp of engineering", "vice president", "director of engineering"]

    for i in range(len(experiences) - 1):
        role_a = experiences[i]
        role_b = experiences[i + 1]

        title_a = role_a.get("title", "").lower()
        title_b = role_b.get("title", "").lower()

        # Check if transitioned from Intern to Executive
        is_a_intern = "intern" in title_a or "trainee" in title_a
        is_b_exec = any(exec_w in title_b for exec_w in executive_keywords)

        if is_a_intern and is_b_exec:
            # Check elapsed time between start of role A and start of role B
            a_months = role_a["start_year"] * 12 + role_a["start_month"]
            b_months = role_b["start_year"] * 12 + role_b["start_month"]
            diff_months = b_months - a_months

            if diff_months < 12:
                severity = "CRITICAL" if diff_months <= 6 else "HIGH"
                anomalies.append({
                    "category": "Unfeasible Career Velocity",
                    "severity": severity,
                    "title": "Sudden Leap from Intern to Executive Leadership",
                    "description": (
                        f"Candidate transitioned from '{role_a['title']}' to executive role '{role_b['title']}' "
                        f"in only {max(0, diff_months)} months without intermediate software engineering tenure."
                    ),
                    "role_a": role_a["title"],
                    "role_b": role_b["title"],
                    "elapsed_months": diff_months,
                })

    return anomalies


def detect_future_dates(
    education: List[Dict[str, Any]],
    experiences: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detects past work experiences listed with dates in the future beyond reasonable graduation year.
    """
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_total = current_year * 12 + current_month

    anomalies = []

    for exp in experiences:
        start_total = exp["start_year"] * 12 + exp["start_month"]
        if start_total > current_total + 1:
            anomalies.append({
                "category": "Invalid Date",
                "severity": "CRITICAL",
                "title": "Post-Dated Work Experience",
                "description": (
                    f"Role '{exp.get('title')}' at '{exp.get('company')}' has a start date in the future "
                    f"({exp['start_year']}), which is physically impossible."
                ),
            })

    return anomalies


def build_timeline_visual_data(
    education: List[Dict[str, Any]],
    experiences: List[Dict[str, Any]],
    anomalies: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Assembles a chronological timeline payload for the frontend UI visualizer.
    """
    timeline_items = []

    for edu in education:
        s_year = edu.get("start_year") or edu.get("end_year") or 2018
        e_year = edu.get("end_year") or s_year
        timeline_items.append({
            "type": "education",
            "title": edu.get("degree", "Degree"),
            "organization": edu.get("institution", "Institution"),
            "start_year": s_year,
            "end_year": e_year,
            "cgpa": edu.get("cgpa"),
            "has_conflict": any(edu.get("degree", "").lower() in a.get("description", "").lower() for a in anomalies),
        })

    for exp in experiences:
        has_conflict = any(
            exp.get("title", "").lower() in a.get("description", "").lower() or
            exp.get("company", "").lower() in a.get("description", "").lower()
            for a in anomalies
        )
        timeline_items.append({
            "type": "experience",
            "title": exp.get("title", "Role"),
            "organization": exp.get("company", "Company"),
            "start_year": exp["start_year"],
            "start_month": exp["start_month"],
            "end_year": exp["end_year"],
            "end_month": exp["end_month"],
            "is_current": exp.get("is_current", False),
            "duration_months": exp.get("duration_months", 1),
            "has_conflict": has_conflict,
        })

    timeline_items.sort(key=lambda x: (x.get("start_year", 2000), x.get("start_month", 1)))
    return timeline_items


def analyze_timeline(parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Chronological Timeline & Anomaly Analysis.
    Combines overlap detection, education paradoxes, velocity checks, and future dates.
    """
    experiences = parsed_resume.get("experience", [])
    education = parsed_resume.get("education", [])

    overlaps = detect_overlapping_roles(experiences)
    edu_paradoxes = detect_education_timeline_paradoxes(education, experiences)
    velocity_anomalies = detect_career_velocity_anomalies(experiences)
    future_date_anomalies = detect_future_dates(education, experiences)

    all_anomalies = overlaps + edu_paradoxes + velocity_anomalies + future_date_anomalies

    # Compute timeline penalty score (0 - 100)
    penalty = 0
    for anomaly in all_anomalies:
        if anomaly["severity"] == "CRITICAL":
            penalty += 45
        elif anomaly["severity"] == "HIGH":
            penalty += 25
        elif anomaly["severity"] == "MEDIUM":
            penalty += 15
    penalty = min(100, penalty)

    visual_timeline = build_timeline_visual_data(education, experiences, all_anomalies)

    return {
        "timeline_anomaly_count": len(all_anomalies),
        "timeline_penalty": penalty,
        "anomalies": all_anomalies,
        "overlapping_roles": overlaps,
        "visual_timeline": visual_timeline,
    }
