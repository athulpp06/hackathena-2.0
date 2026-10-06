"""Tests for Phase 4: document extraction and document-specific checks."""
import pytest

from backend.app.detector.document_checks import check_document
from backend.app.utils.document_extractor import MAX_SIZE_BYTES, validate_file

# ---- File Validation ----

def test_valid_pdf_magic():
    fake_pdf = b"%PDF-1.4 fake content"
    result = validate_file("offer.pdf", "application/pdf", fake_pdf)
    assert result == "pdf"


def test_valid_docx_magic():
    # DOCX is a ZIP; starts with PK\x03\x04
    fake_docx = b"PK\x03\x04fake content"
    result = validate_file("offer.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", fake_docx)
    assert result == "docx"


def test_invalid_magic_raises():
    bad_data = b"This is definitely not a PDF or DOCX"
    with pytest.raises(ValueError, match="magic bytes"):
        validate_file("evil.pdf", "application/pdf", bad_data)


def test_file_too_large_raises():
    oversized = b"A" * (MAX_SIZE_BYTES + 1)
    with pytest.raises(ValueError, match="too large"):
        validate_file("big.pdf", "application/pdf", oversized)


def test_unsupported_type_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        validate_file("virus.exe", "application/octet-stream", b"MZ...")


# ---- Document Checks ----

def test_placeholder_detection():
    text = "Dear [Candidate Name], You are hired at [Company Name]. Pay [Amount] immediately."
    result = check_document(text, {})
    assert len(result["placeholders_found"]) > 0
    assert any("placeholder" in f.lower() for f in result["document_flags"])


def test_free_email_flagged():
    text = "Contact your HR at recruiter@gmail.com for further steps."
    result = check_document(text, {})
    assert any("gmail" in f for f in result["document_flags"])


def test_urgent_payment_flagged():
    text = "The security deposit must be paid within 24 hours to confirm your offer."
    result = check_document(text, {})
    assert any("urgent payment" in f.lower() or "payment" in f.lower() for f in result["document_flags"])


def test_missing_registration_flagged():
    text = "Welcome to Acme Corp. Your salary is 50,000/month."
    result = check_document(text, {})
    assert not result["has_registration"]
    assert any("CIN" in f or "GST" in f for f in result["document_flags"])


def test_cin_detected():
    # Valid CIN format
    text = "Company Registration: L17110MH1973PLC019786. Best regards, HR."
    result = check_document(text, {})
    assert result["has_registration"] is True


def test_has_signatory_detected():
    text = "Congratulations! Sincerely, HR Manager."
    result = check_document(text, {})
    assert result["has_signatory"] is True
