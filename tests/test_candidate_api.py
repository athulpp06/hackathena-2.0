"""
Test Suite for Day 2 Candidate API Routes.
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.api.routes import (
    analyse_resume_endpoint,
    ResumeAnalysisRequest,
)

SAMPLE_RESUME = """
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

TECHNICAL SKILLS
Languages: Python, Go, JavaScript, TypeScript
Frameworks & Databases: FastAPI, React, PostgreSQL, Redis, Kafka, Docker, Kubernetes

REFERENCES
Manoj Nair, Engineering Manager at Swiggy
Email: manoj.nair@swiggy.in
"""

FRAUD_RESUME = """
Vikram Malhotra
Email: vikram.malhotra@mailinator.com
LinkedIn: https://linkedin.com/in/your-profile

SUMMARY
Chief Technology Officer with 16 years of Flutter experience.

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

REFERENCES
HR Director at Microsoft
Email: hr.microsoft.reference@gmail.com
"""


async def test_analyse_resume_api():
    req = ResumeAnalysisRequest(text=SAMPLE_RESUME)
    res = await analyse_resume_endpoint(req)
    assert res["risk_score"] <= 25
    assert res["risk_level"] in ("Safe / Authentic", "Low Risk")
    assert "parsed_entities" in res
    print(f"  [PASS] test_analyse_resume_api (Authentic) -> Risk Score: {res['risk_score']}/100, Level: {res['risk_level']}")


async def test_analyse_fraud_resume_api():
    req = ResumeAnalysisRequest(text=FRAUD_RESUME)
    res = await analyse_resume_endpoint(req)
    assert res["risk_score"] >= 80
    assert res["risk_level"] == "High Risk"
    assert res["has_critical_flags"] is True
    print(f"  [PASS] test_analyse_fraud_resume_api (Fraud) -> Risk Score: {res['risk_score']}/100, Flags: {res['total_anomalies']}")


def main():
    print("=" * 60)
    print("RUNNING DAY 2 CANDIDATE API ROUTE TESTS")
    print("=" * 60)
    asyncio.run(test_analyse_resume_api())
    asyncio.run(test_analyse_fraud_resume_api())
    print("=" * 60)
    print("ALL DAY 2 CANDIDATE API TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
