"""Tests for Phase 3: entity extraction, typosquat, reputation."""

from backend.app.detector.verification.entities import extract_entities
from backend.app.detector.verification.reputation import init_db, lookup, report
from backend.app.detector.verification.typosquat import (
    check_company_claim,
    check_domain,
)

# ---- Entity Extraction ----

def test_email_extraction():
    text = "Contact us at recruiter@gmail.com or hr@tcs.com"
    entities = extract_entities(text)
    assert "recruiter@gmail.com" in entities["emails"]
    assert "hr@tcs.com" in entities["emails"]


def test_phone_extraction():
    text = "Call 9876543210 or WhatsApp +91 9876543211"
    entities = extract_entities(text)
    assert "9876543210" in entities["phones"]


def test_upi_extraction():
    text = "Send fees to fraudster@okaxis via UPI"
    entities = extract_entities(text)
    assert "fraudster@okaxis" in entities["upi_ids"]


def test_url_extraction():
    text = "Apply at http://amazon-careers-hr.xyz/jobs"
    entities = extract_entities(text)
    assert any("amazon-careers-hr.xyz" in url for url in entities["urls"])


# ---- Typosquat Detection ----

def test_typosquat_detected():
    result = check_domain("amazon-careers-hr.xyz")
    # Should flag keyword stuffing with amazon
    assert result["is_typosquat"] is True
    assert any("amazon" in f.lower() for f in result["domain_flags"])


def test_legitimate_domain_safe():
    result = check_domain("amazon.com")
    assert result["is_typosquat"] is False


def test_company_claim_free_email():
    flags = check_company_claim("Google", ["recruiter@gmail.com"])
    assert len(flags) > 0
    assert "Google" in flags[0]


def test_company_claim_official_email():
    flags = check_company_claim("Google", ["recruiter@google.com"])
    assert len(flags) == 0


# ---- Reputation DB ----

def test_reputation_report_and_lookup():
    init_db()
    report("test_scammer_unique@evil.com", "email")
    result = lookup("test_scammer_unique@evil.com")
    assert result is not None
    assert result["report_count"] >= 1


def test_reputation_unknown():
    init_db()
    result = lookup("definitely_not_a_scammer_xyz123@legit.com")
    assert result is None
