"""
Candidate Risk Aggregation Engine (Day 2 - Module 5).
Combines timeline anomalies, credential inflation, diploma mill blacklists,
and reference verifications into a single calibrated Candidate Integrity Risk Score (0-100).
"""

from typing import Dict, Any, List, Optional
from backend.app.candidate import parser, timeline, credentials, verifier


def _risk_level(score: int) -> str:
    if score >= 76:
        return "High Risk"
    elif score >= 51:
        return "Suspicious"
    elif score >= 26:
        return "Low Risk"
    else:
        return "Safe / Authentic"


def _candidate_verdict(score: int, has_critical: bool, total_flags: int) -> str:
    if score >= 76 or has_critical:
        return "Critical candidate credential fabrication or timeline contradiction detected. Detailed audit required."
    elif score >= 51:
        return "Multiple suspicious anomalies detected in career timeline or credentials. Comprehensive background check recommended."
    elif score >= 26:
        return "Minor discrepancies or unverified references detected. Standard due diligence advised."
    else:
        return "Candidate profile exhibits authentic career chronology, accredited credentials, and consistent digital footprint."


def _generate_recruiter_recommendations(
    timeline_res: Dict[str, Any],
    cred_res: Dict[str, Any],
    verif_res: Dict[str, Any],
) -> List[str]:
    recs = []

    if timeline_res.get("overlapping_roles"):
        recs.append("Request EPFO / Provident Fund service history or Form 16 to audit overlapping corporate tenures.")

    if cred_res.get("diploma_mill_detected"):
        recs.append("Candidate claims credentials from an unaccredited diploma mill. Reject degree credits and report counterfeit claims.")

    if cred_res.get("anachronistic_claims_detected"):
        recs.append("Conduct a technical screen on claimed technologies to evaluate actual depth vs exaggerated tenure.")

    if cred_res.get("ai_generation_detected"):
        recs.append("Resume contains AI generator leakage or template placeholders. Require customized in-person or live interview assessment.")

    if verif_res.get("reference_issues", 0) > 0:
        recs.append("References use consumer webmail or disposable addresses. Request verified corporate email addresses or HR contacts.")

    if not recs:
        recs.append("Profile verified. Proceed with standard technical and culture-fit interviews.")

    return recs


def _compute_candidate_risk_score(
    timeline_penalty: int,
    credential_penalty: int,
    footprint_penalty: int,
    has_critical: bool,
) -> int:
    """
    Calibrates candidate risk score (0-100).
    Critical guardrails ensure fraudulent fabrication (diploma mill, overlapping jobs, fake references)
    cannot be averaged away into an acceptable score.
    """
    weighted = (timeline_penalty * 0.45) + (credential_penalty * 0.40) + (footprint_penalty * 0.30)
    max_single = max(timeline_penalty, credential_penalty, footprint_penalty)
    raw_score = max(max_single, weighted)
    score = min(100, int(round(raw_score)))

    if has_critical:
        score = max(score, 82)

    return score


def analyse_candidate_resume(
    text: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete candidate resume screening pipeline.
    Parses resume, runs timeline, credential, and reference checks,
    and returns a structured integrity report.
    """
    # 1. Parse entities
    parsed = parser.parse_resume(text=text, file_bytes=file_bytes, filename=filename)

    if not parsed.get("raw_text") or len(parsed["raw_text"].strip()) < 20:
        return {
            "error": "Insufficient text extracted from resume.",
            "risk_score": 0,
            "risk_level": "Unknown",
            "verdict": "Unable to extract readable text from candidate submission.",
        }

    # 2. Analyze timeline
    timeline_res = timeline.analyze_timeline(parsed)

    # 3. Analyze credentials & diploma mills
    cred_res = credentials.analyze_credentials(parsed)

    # 4. Verify references & digital footprint
    verif_res = verifier.verify_candidate_profiles(parsed)

    # Combine all detected red flags
    all_flags = (
        timeline_res.get("anomalies", []) +
        cred_res.get("flags", []) +
        verif_res.get("flags", [])
    )

    has_critical = any(f.get("severity") == "CRITICAL" for f in all_flags)
    risk_score = _compute_candidate_risk_score(
        timeline_penalty=timeline_res["timeline_penalty"],
        credential_penalty=cred_res["credential_penalty"],
        footprint_penalty=verif_res["footprint_penalty"],
        has_critical=has_critical,
    )
    risk_level = _risk_level(risk_score)
    verdict = _candidate_verdict(risk_score, has_critical, len(all_flags))
    recommendations = _generate_recruiter_recommendations(timeline_res, cred_res, verif_res)

    return {
        "candidate_name": parsed["contact"].get("linkedin_handle") or "Applicant",
        "risk_score": risk_score,
        "risk_level": risk_level,
        "verdict": verdict,
        "has_critical_flags": has_critical,
        "total_anomalies": len(all_flags),
        "red_flags": all_flags,
        "recommendations": recommendations,
        "parsed_entities": {
            "contact": parsed["contact"],
            "education": parsed["education"],
            "experience": parsed["experience"],
            "total_experience_years": parsed["total_experience_years"],
            "skills": parsed["skills"],
            "certifications": parsed["certifications"],
            "references": parsed["references"],
        },
        "timeline_analysis": {
            "timeline_penalty": timeline_res["timeline_penalty"],
            "overlapping_roles": timeline_res["overlapping_roles"],
            "visual_timeline": timeline_res["visual_timeline"],
        },
        "credential_analysis": {
            "credential_penalty": cred_res["credential_penalty"],
            "diploma_mill_detected": cred_res["diploma_mill_detected"],
            "anachronistic_claims_detected": cred_res["anachronistic_claims_detected"],
            "ai_generation_detected": cred_res["ai_generation_detected"],
        },
        "footprint_analysis": {
            "footprint_penalty": verif_res["footprint_penalty"],
            "reference_issues": verif_res["reference_issues"],
        },
    }
