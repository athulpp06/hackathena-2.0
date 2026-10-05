"""
Automated unit tests for Candidate Timeline Anomaly Detection (Day 2 - Module 2).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.candidate.timeline import (
    analyze_timeline,
    detect_overlapping_roles,
    detect_education_timeline_paradoxes,
    detect_career_velocity_anomalies,
)

def test_overlapping_full_time_roles():
    # Candidate claiming two concurrent full-time jobs for 18 months
    parsed = {
        "education": [{"degree": "B.Tech", "start_year": 2016, "end_year": 2020}],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Amazon AWS",
                "start_year": 2020,
                "start_month": 6,
                "end_year": 2023,
                "end_month": 12,
                "is_current": False,
                "duration_months": 42,
            },
            {
                "title": "Senior Backend Developer",
                "company": "Microsoft Azure",
                "start_year": 2022,
                "start_month": 1,
                "end_year": 2023,
                "end_month": 8,
                "is_current": False,
                "duration_months": 20,
            },
        ],
    }

    res = analyze_timeline(parsed)
    assert res["timeline_anomaly_count"] >= 1
    assert any("Concurrent Employment" in a["category"] for a in res["anomalies"])
    overlap = res["overlapping_roles"][0]
    assert overlap["overlap_months"] >= 12
    print(f"  [PASS] Overlapping full-time roles detected: {overlap['description']}")


def test_education_timeline_paradox():
    # Senior Architect claimed before high school completion
    parsed = {
        "education": [
            {"degree": "High School / 12th", "start_year": 2018, "end_year": 2020},
            {"degree": "B.Tech", "start_year": 2020, "end_year": 2024},
        ],
        "experience": [
            {
                "title": "Senior Solutions Architect",
                "company": "Oracle Systems",
                "start_year": 2017,
                "start_month": 1,
                "end_year": 2021,
                "end_month": 5,
                "is_current": False,
                "duration_months": 52,
            }
        ],
    }

    res = analyze_timeline(parsed)
    assert res["timeline_anomaly_count"] >= 1
    assert any("Paradox" in a["category"] for a in res["anomalies"])
    print(f"  [PASS] Education vs Experience paradox caught: {res['anomalies'][0]['title']}")


def test_unfeasible_career_velocity():
    # Intern leaping to CTO in 3 months
    parsed = {
        "education": [{"degree": "B.Tech", "start_year": 2018, "end_year": 2022}],
        "experience": [
            {
                "title": "Summer Intern",
                "company": "Tech Corp",
                "start_year": 2022,
                "start_month": 5,
                "end_year": 2022,
                "end_month": 8,
                "is_current": False,
                "duration_months": 3,
            },
            {
                "title": "Chief Technology Officer (CTO)",
                "company": "Enterprise Global",
                "start_year": 2022,
                "start_month": 9,
                "end_year": 2024,
                "end_month": 1,
                "is_current": False,
                "duration_months": 16,
            },
        ],
    }

    res = analyze_timeline(parsed)
    assert any("Velocity" in a["category"] for a in res["anomalies"])
    print(f"  [PASS] Unfeasible career velocity leap flagged: {res['anomalies'][0]['title']}")


def test_clean_legitimate_timeline():
    # Completely legitimate progression: Intern during college -> Junior Dev -> Senior Dev
    parsed = {
        "education": [
            {"degree": "High School / 12th", "start_year": 2014, "end_year": 2016},
            {"degree": "B.Tech", "start_year": 2016, "end_year": 2020},
        ],
        "experience": [
            {
                "title": "Software Engineering Intern",
                "company": "Microsoft India",
                "start_year": 2019,
                "start_month": 5,
                "end_year": 2019,
                "end_month": 7,
                "is_current": False,
                "duration_months": 2,
            },
            {
                "title": "Software Engineer",
                "company": "Flipkart",
                "start_year": 2020,
                "start_month": 6,
                "end_year": 2021,
                "end_month": 12,
                "is_current": False,
                "duration_months": 18,
            },
            {
                "title": "Senior Software Engineer",
                "company": "Stripe",
                "start_year": 2022,
                "start_month": 1,
                "end_year": 2026,
                "end_month": 10,
                "is_current": True,
                "duration_months": 57,
            },
        ],
    }

    res = analyze_timeline(parsed)
    assert res["timeline_anomaly_count"] == 0
    assert res["timeline_penalty"] == 0
    assert len(res["overlapping_roles"]) == 0
    assert len(res["visual_timeline"]) == 5
    print("  [PASS] Clean legitimate timeline: 0 anomalies, 0 penalty, perfectly sequential.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING DAY 2 MODULE 2 TESTS (Timeline Anomaly Engine)")
    print("=" * 60)
    test_overlapping_full_time_roles()
    test_education_timeline_paradox()
    test_unfeasible_career_velocity()
    test_clean_legitimate_timeline()
    print("=" * 60)
    print("ALL DAY 2 MODULE 2 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
