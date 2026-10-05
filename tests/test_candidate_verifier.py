"""
Automated unit tests for Candidate Reference & Footprint Verifier (Day 2 - Module 4).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.candidate.verifier import (
    verify_candidate_profiles,
    verify_references,
    verify_digital_footprint,
)


def test_disposable_reference_email():
    parsed = {
        "contact": {"primary_email": "candidate@gmail.com"},
        "references": [
            {
                "name": "HR Manager - Tech Corp",
                "email": "hr.manager@mailinator.com",
            }
        ],
    }

    res = verify_candidate_profiles(parsed)
    assert res["reference_issues"] >= 1
    assert any("Disposable" in f["title"] for f in res["flags"])
    assert res["flags"][0]["severity"] == "CRITICAL"
    print(f"  [PASS] Disposable burner reference email caught: {res['flags'][0]['title']}")


def test_consumer_webmail_for_corporate_referee():
    parsed = {
        "contact": {"primary_email": "candidate@gmail.com"},
        "references": [
            {
                "name": "VP of Engineering at Google",
                "email": "vp.google.referrals@gmail.com",
            }
        ],
    }

    res = verify_candidate_profiles(parsed)
    assert res["reference_issues"] >= 1
    assert any("Consumer Webmail" in f["title"] for f in res["flags"])
    print(f"  [PASS] Free webmail for corporate referee flagged: {res['flags'][0]['title']}")


def test_placeholder_profile_urls():
    parsed = {
        "contact": {
            "primary_email": "real@example.com",
            "linkedin_handle": "your-profile",
            "github_handle": "username",
        },
        "references": [],
    }

    res = verify_candidate_profiles(parsed)
    assert res["footprint_issues"] >= 2
    assert any("LinkedIn" in f["title"] for f in res["flags"])
    assert any("GitHub" in f["title"] for f in res["flags"])
    print(f"  [PASS] Placeholder social profiles flagged: {len(res['flags'])} flags.")


def test_clean_corporate_reference():
    parsed = {
        "contact": {
            "primary_email": "john.doe@gmail.com",
            "linkedin_handle": "johndoe-cloud",
            "github_handle": "johndoe-dev",
        },
        "references": [
            {
                "name": "Vikram Seth, Director at Flipkart",
                "email": "vikram.seth@flipkart.com",
            }
        ],
    }

    res = verify_candidate_profiles(parsed)
    assert res["footprint_flag_count"] == 0
    assert res["footprint_penalty"] == 0
    print("  [PASS] Clean corporate reference and profile handles: 0 flags.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING DAY 2 MODULE 4 TESTS (Reference & Footprint Verifier)")
    print("=" * 60)
    test_disposable_reference_email()
    test_consumer_webmail_for_corporate_referee()
    test_placeholder_profile_urls()
    test_clean_corporate_reference()
    print("=" * 60)
    print("ALL DAY 2 MODULE 4 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
