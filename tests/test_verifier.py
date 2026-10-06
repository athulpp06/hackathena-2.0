"""
Test Suite for Module 4: Domain & Contact Verifier
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.detector.verifier import verify

def test_verifier_free_webmail_impersonation():
    text = "Join TCS as a software engineer! Apply at hr.tcs.hiring@gmail.com"
    result = verify(text, declared_company="TCS")
    assert result["has_free_email"] is True
    assert result["company_mismatch"] is True
    assert result["flag_count"] >= 2
    assert any(f["type"] == "FREE_WEBMAIL" for f in result["flags"])
    assert any(f["type"] == "DOMAIN_MISMATCH" for f in result["flags"])
    print("  [PASS] test_verifier_free_webmail_impersonation")

def test_verifier_disposable_email():
    text = "Quick part time job. Send your resume to hiring@mailinator.com"
    result = verify(text)
    assert result["has_disposable_email"] is True
    assert any(f["type"] == "DISPOSABLE_EMAIL" for f in result["flags"])
    print("  [PASS] test_verifier_disposable_email")

def test_verifier_legitimate_corporate():
    text = "We are hiring engineers at Google. Submit your application to jobs@google.com"
    result = verify(text, declared_company="Google")
    assert result["has_free_email"] is False
    assert result["company_mismatch"] is False
    assert result["has_disposable_email"] is False
    assert result["penalty"] == 0
    print("  [PASS] test_verifier_legitimate_corporate")

def test_verifier_no_email():
    text = "Direct call only. Contact 9876543210 for immediate joining bonus."
    result = verify(text)
    assert len(result["emails_found"]) == 0
    assert any(f["type"] == "NO_CONTACT_INFO" for f in result["flags"])
    print("  [PASS] test_verifier_no_email")

def test_verifier_typosquat_lookalike():
    text = "Apply for Google Cloud intern! Send CV to recruiter@g00gle.com or visit https://google-careers-portal.xyz"
    result = verify(text, declared_company="Google")
    assert result["typosquat_detected"] is True
    assert any(f["type"] == "TYPOSQUAT_DOMAIN" for f in result["flags"])
    print("  [PASS] test_verifier_typosquat_lookalike")

def test_verifier_upi_entities():
    text = "Send your registration charges to jobs@okaxis or call +919876543210 on WhatsApp"
    result = verify(text)
    assert any(f["type"] == "UPI_ID_DETECTED" for f in result["flags"])
    assert "jobs@okaxis" in result["entities"]["upi_ids"]
    assert len(result["entities"]["phones"]) >= 1
    print("  [PASS] test_verifier_upi_entities")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING MODULE 4 TESTS (Domain & Contact Verifier)")
    print("=" * 60)
    test_verifier_free_webmail_impersonation()
    test_verifier_disposable_email()
    test_verifier_legitimate_corporate()
    test_verifier_no_email()
    test_verifier_typosquat_lookalike()
    test_verifier_upi_entities()
    print("=" * 60)
    print("ALL MODULE 4 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
