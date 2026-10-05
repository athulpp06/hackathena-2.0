"""
Automated unit tests for Candidate Profile & Resume Parser (Module 1).
"""

import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.candidate.parser import (
    parse_resume,
    extract_contact_info,
    extract_education,
    extract_work_experience,
    extract_skills,
    extract_certifications,
    extract_references,
)

SAMPLE_RESUME_TEXT = """
Rahul Sharma
Email: rahul.sharma@example.com | Phone: +91 9876543210
LinkedIn: https://linkedin.com/in/rahulsharma-dev | GitHub: https://github.com/rahul-codes

PROFESSIONAL SUMMARY
Senior Software Engineer with 6+ years of experience in distributed backend architectures,
cloud computing, and microservices design.

EDUCATION
B.Tech in Computer Science and Engineering
Indian Institute of Technology Delhi
2016 - 2020 | CGPA: 8.9 / 10

Senior Secondary School (CBSE XII)
Delhi Public School
2014 - 2016 | Percentage: 94.2%

WORK EXPERIENCE
Senior Software Engineer - Stripe Payments
Jan 2022 - Present
- Designed high-throughput payment settlement microservices handling 25,000 req/sec.
- Built real-time transaction monitoring pipeline using Kafka, Python, Go, and Redis.

Software Engineer - Flipkart Internet Pvt Ltd
Jun 2020 - Dec 2021
- Developed order checkout services using Java, Spring Boot, and PostgreSQL.
- Reduced database p99 latency by 35% through query optimization and caching.

Software Engineering Intern - Microsoft India
May 2019 - Jul 2019
- Built internal developer telemetry dashboard using React and Azure cloud functions.

TECHNICAL SKILLS
Languages & Frameworks: Python, Java, Go, JavaScript, TypeScript, React, Spring Boot, FastAPI, Django
Databases & Cloud: PostgreSQL, Redis, Kafka, MongoDB, AWS, Docker, Kubernetes, Linux, Git

CERTIFICATIONS
- AWS Certified Solutions Architect Associate (2022)
- Certified Kubernetes Administrator (CKA)

REFERENCES
Aravind Kumar, Engineering Director at Flipkart
Email: aravind.kumar@flipkart.com | Phone: +91 9123456780
"""


def test_contact_extraction():
    contact = extract_contact_info(SAMPLE_RESUME_TEXT)
    assert "rahul.sharma@example.com" in contact["emails"]
    assert contact["primary_phone"] is not None
    assert contact["linkedin_handle"] == "rahulsharma-dev"
    assert contact["github_handle"] == "rahul-codes"
    print("  [PASS] Contact info extracted successfully.")


def test_education_extraction():
    education = extract_education(SAMPLE_RESUME_TEXT)
    assert len(education) >= 2
    degrees = [e["degree"] for e in education]
    assert "B.Tech" in degrees
    assert "High School / 12th" in degrees

    btech = next(e for e in education if e["degree"] == "B.Tech")
    assert btech["start_year"] == 2016
    assert btech["end_year"] == 2020
    assert "8.9" in str(btech["cgpa"])
    print(f"  [PASS] Education parsed successfully: {degrees}")


def test_work_experience_extraction():
    exp = extract_work_experience(SAMPLE_RESUME_TEXT)
    assert len(exp) >= 3
    titles = [e["title"] for e in exp]
    assert any("Senior Software Engineer" in t for t in titles)
    assert any("Software Engineer" in t for t in titles)
    assert any("Intern" in t for t in titles)

    stripe_exp = next(e for e in exp if "Senior" in e["title"])
    assert stripe_exp["start_year"] == 2022
    assert stripe_exp["is_current"] is True
    print(f"  [PASS] Work experience parsed successfully: {len(exp)} roles detected.")


def test_skills_and_certs():
    skills = extract_skills(SAMPLE_RESUME_TEXT)
    assert "Python" in skills
    assert "Go" in skills
    assert "Docker" in skills
    assert "Kubernetes" in skills

    certs = extract_certifications(SAMPLE_RESUME_TEXT)
    assert len(certs) >= 2
    cert_names = [c["name"] for c in certs]
    assert any("AWS" in c for c in cert_names)
    assert any("Kubernetes" in c for c in cert_names)
    print(f"  [PASS] Skills & Certifications parsed: {len(skills)} skills, {len(certs)} certs.")


def test_references_extraction():
    refs = extract_references(SAMPLE_RESUME_TEXT)
    assert len(refs) >= 1
    assert "aravind.kumar@flipkart.com" in refs[0]["email"]
    print(f"  [PASS] References parsed: {refs[0]['name']} ({refs[0]['email']})")


def test_full_pipeline_parse():
    parsed = parse_resume(text=SAMPLE_RESUME_TEXT)
    assert parsed["source_type"] == "text"
    assert parsed["char_count"] > 500
    assert parsed["total_experience_years"] > 3.0
    print(f"  [PASS] Full resume parse pipeline: {parsed['total_experience_years']} yrs total experience.")


def test_pdf_ingestion():
    import pypdf
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=300, height=300)
    pdf_buffer = io.BytesIO()
    writer.write(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()

    parsed = parse_resume(file_bytes=pdf_bytes, filename="candidate_cv.pdf")
    assert parsed["source_type"] == "pdf"
    print("  [PASS] PDF file bytes ingestion parsed successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING DAY 2 MODULE 1 TESTS (Resume Parser)")
    print("=" * 60)
    test_contact_extraction()
    test_education_extraction()
    test_work_experience_extraction()
    test_skills_and_certs()
    test_references_extraction()
    test_full_pipeline_parse()
    test_pdf_ingestion()
    print("=" * 60)
    print("ALL DAY 2 MODULE 1 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

