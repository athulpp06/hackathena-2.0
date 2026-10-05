"""
Automated unit tests for Candidate Risk Aggregator (Day 2 - Module 5).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.candidate.aggregator import analyse_candidate_resume

AUTHENTIC_RESUME = """
Ananya Verma
Email: ananya.verma@gmail.com | Phone: +91 9876543210
LinkedIn: https://linkedin.com/in/ananyaverma-tech | GitHub: https://github.com/ananya-v

SUMMARY
Full Stack Engineer with 4 years of experience building scalable web applications.

EDUCATION
B.Tech in Information Technology
National Institute of Technology Karnataka (NITK)
2017 - 2021 | CGPA: 8.7

WORK EXPERIENCE
Software Engineer - Swiggy
Aug 2021 - Present
- Built food delivery logistics tracking microservices using Go, Kafka, and Redis.
- Implemented real-time order status webhooks with 99.99% uptime.

Software Engineering Intern - Cisco Systems
Jan 2021 - Jun 2021
- Developed network packet analysis tools using Python and Docker.

TECHNICAL SKILLS
Languages: Python, Go, JavaScript, TypeScript
Frameworks & Databases: FastAPI, React, PostgreSQL, Redis, Kafka, Docker, Kubernetes

REFERENCES
Manoj Nair, Engineering Manager at Swiggy
Email: manoj.nair@swiggy.in | Phone: +91 9988776655
"""

FRAUDULENT_RESUME = """
Vikram Malhotra
Email: vikram.malhotra@mailinator.com
LinkedIn: https://linkedin.com/in/your-profile

SUMMARY
Chief Technology Officer with 16 years of Flutter and Kubernetes experience.

EDUCATION
Bachelor of Science in Computer Science
Almeda University (Life Experience Degree)
2019

WORK EXPERIENCE
Chief Technology Officer - Global Alpha Tech
Jan 2021 - Present
- Directing entire cloud engineering infrastructure.

Senior Backend Engineer - Beta Systems
Mar 2021 - Dec 2023
- Built core banking APIs full-time.

Intern - Gamma Corp
Sep 2020 - Dec 2020
- Supported QA team.

REFERENCES
HR Director at Microsoft
Email: hr.microsoft.reference@gmail.com
"""


def test_authentic_candidate_analysis():
    res = analyse_candidate_resume(text=AUTHENTIC_RESUME)
    assert res["risk_score"] <= 25, f"Expected low risk for authentic resume, got {res['risk_score']}"
    assert res["risk_level"] in ("Safe / Authentic", "Low Risk")
    assert res["has_critical_flags"] is False
    assert len(res["red_flags"]) == 0
    print(f"  [PASS] Authentic Resume -> Risk Score: {res['risk_score']}/100, Level: {res['risk_level']}")


def test_fraudulent_candidate_analysis():
    res = analyse_candidate_resume(text=FRAUDULENT_RESUME)
    assert res["risk_score"] >= 80, f"Expected high risk for fraudulent resume, got {res['risk_score']}"
    assert res["risk_level"] == "High Risk"
    assert res["has_critical_flags"] is True
    assert res["total_anomalies"] >= 3

    categories = [f["category"] for f in res["red_flags"]]
    assert any("Diploma Mill" in c for c in categories)
    assert any("Concurrent Employment" in c for c in categories)
    print(f"  [PASS] Fraudulent Resume -> Risk Score: {res['risk_score']}/100, Level: {res['risk_level']}")
    print(f"         Total Anomalies Caught: {res['total_anomalies']}")
    for f in res["red_flags"]:
        print(f"         [{f['severity']}] {f['title']}")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING DAY 2 MODULE 5 TESTS (Candidate Risk Aggregator)")
    print("=" * 60)
    test_authentic_candidate_analysis()
    test_fraudulent_candidate_analysis()
    print("=" * 60)
    print("ALL DAY 2 MODULE 5 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
