"""
Automated unit tests for Candidate Credential Inflation & Diploma Mill Engine (Day 2 - Module 3).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.candidate.credentials import (
    analyze_credentials,
    check_diploma_mills,
    check_anachronistic_tech_claims,
    check_synthetic_ai_artifacts,
)


def test_diploma_mill_detection():
    parsed = {
        "raw_text": (
            "EDUCATION\n"
            "Bachelor of Science in Computer Science\n"
            "Almeda University (Life Experience Degree)\n"
            "2018\n"
        ),
        "education": [
            {
                "degree": "B.Sc",
                "institution": "Almeda University",
                "raw_context": "Bachelor of Science in Computer Science Almeda University (Life Experience Degree)",
            }
        ],
        "experience": [],
    }

    res = analyze_credentials(parsed)
    assert res["diploma_mill_detected"] is True
    assert res["credential_penalty"] >= 40
    print(f"  [PASS] Diploma mill detected: {res['flags'][0]['title']}")


def test_anachronistic_tech_claims():
    parsed = {
        "raw_text": (
            "SUMMARY\n"
            "Software engineer with 14 years of experience in Flutter and mobile architecture.\n"
            "WORK EXPERIENCE\n"
            "Senior Systems Engineer - Tech Systems (2008 - 2012)\n"
            "Managed production Kubernetes clusters and Docker containers for enterprise banking.\n"
        ),
        "education": [],
        "experience": [
            {
                "title": "Senior Systems Engineer",
                "company": "Tech Systems",
                "start_year": 2008,
                "end_year": 2012,
                "raw_context": "Managed production Kubernetes clusters and Docker containers for enterprise banking.",
            }
        ],
    }

    res = analyze_credentials(parsed)
    assert res["anachronistic_claims_detected"] is True
    assert any("Kubernetes" in f["title"] or "Flutter" in f["title"] for f in res["flags"])
    print(f"  [PASS] Anachronistic tech claims detected: {len(res['flags'])} flags raised.")


def test_synthetic_ai_artifacts():
    parsed = {
        "raw_text": (
            "Certainly, here is an optimized professional summary for your resume:\n"
            "As an AI language model, I recommend highlighting your cloud experience.\n"
            "Software Engineer at [Insert Company Name] from 2021 to 2023.\n"
            "Achieved X% increase in throughput.\n"
        ),
        "education": [],
        "experience": [],
    }

    res = analyze_credentials(parsed)
    assert res["ai_generation_detected"] is True
    assert any("ChatGPT" in f["title"] or "Placeholder" in f["title"] for f in res["flags"])
    print(f"  [PASS] Synthetic AI artifacts detected: {len(res['flags'])} flags caught.")


def test_clean_authentic_credentials():
    parsed = {
        "raw_text": (
            "EDUCATION\n"
            "B.Tech in Computer Science - IIT Bombay (2018 - 2022)\n"
            "WORK EXPERIENCE\n"
            "Backend Engineer - Razorpay (Jul 2022 - Present)\n"
            "Built distributed payment webhook dispatchers using Go and Kafka.\n"
        ),
        "education": [
            {"degree": "B.Tech", "institution": "IIT Bombay", "start_year": 2018, "end_year": 2022}
        ],
        "experience": [
            {
                "title": "Backend Engineer",
                "company": "Razorpay",
                "start_year": 2022,
                "start_month": 7,
                "end_year": 2026,
                "end_month": 10,
                "raw_context": "Built distributed payment webhook dispatchers using Go and Kafka.",
            }
        ],
    }

    res = analyze_credentials(parsed)
    assert res["credential_flag_count"] == 0
    assert res["credential_penalty"] == 0
    assert res["diploma_mill_detected"] is False
    assert res["anachronistic_claims_detected"] is False
    assert res["ai_generation_detected"] is False
    print("  [PASS] Clean authentic credentials: 0 flags, 0 penalty.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING DAY 2 MODULE 3 TESTS (Credential & Diploma Mill Engine)")
    print("=" * 60)
    test_diploma_mill_detection()
    test_anachronistic_tech_claims()
    test_synthetic_ai_artifacts()
    test_clean_authentic_credentials()
    print("=" * 60)
    print("ALL DAY 2 MODULE 3 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
