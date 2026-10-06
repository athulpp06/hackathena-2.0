"""
test_phase9_coverage.py - Comprehensive coverage tests for Phase 9.
Targets scraper, OCR, document_extractor, document_checks, and verifier.
"""

from unittest.mock import MagicMock, patch

import pytest

from backend.app.detector.document_checks import check_document
from backend.app.detector.verification.typosquat import check_company_claim, check_domain
from backend.app.detector.verifier import _company_is_known_large, _is_free_provider, verify
from backend.app.utils.document_extractor import (
    extract_text_from_docx,
    extract_text_from_pdf,
    validate_file,
)
from backend.app.utils.ocr import extract_text_from_image
from backend.app.utils.scraper import _is_private_ip, _validate_url, scrape_job_url

# ---------------------------------------------------------------------------
# Scraper & SSRF Tests
# ---------------------------------------------------------------------------

def test_is_private_ip():
    assert _is_private_ip("127.0.0.1") is True
    assert _is_private_ip("10.0.0.1") is True
    assert _is_private_ip("192.168.1.1") is True
    assert _is_private_ip("169.254.169.254") is True
    assert _is_private_ip("8.8.8.8") is False
    assert _is_private_ip("invalid_ip") is True  # DNS failure treated as blocked


def test_validate_url_success():
    url = _validate_url("https://example.com/jobs")
    assert url == "https://example.com/jobs"

    with pytest.raises(ValueError):
        _validate_url("ftp://example.com")


def test_scrape_job_url_blocked_schemes():
    from backend.app.utils.scraper import BlockedURLError
    with pytest.raises(BlockedURLError):
        scrape_job_url("ftp://example.com")
    with pytest.raises(BlockedURLError):
        scrape_job_url("file:///etc/passwd")


def test_scrape_job_url_private_ip():
    from backend.app.utils.scraper import BlockedURLError
    with pytest.raises(BlockedURLError):
        scrape_job_url("http://127.0.0.1:8000/secret")
    with pytest.raises(BlockedURLError):
        scrape_job_url("http://169.254.169.254/latest/meta-data")


@patch("requests.Session.get")
def test_scrape_job_url_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.url = "https://example.com/careers/job1"
    mock_resp.iter_content = lambda chunk_size: [b"<html><body><h1>Software Engineer</h1><p>Join our team</p></body></html>"]
    mock_get.return_value = mock_resp

    with patch("backend.app.utils.scraper._is_private_ip", return_value=False):
        text = scrape_job_url("https://example.com/careers/job1")
        assert "Software Engineer" in text
        assert "Join our team" in text


# ---------------------------------------------------------------------------
# OCR Tests
# ---------------------------------------------------------------------------

def test_ocr_empty_text():
    with patch("backend.app.utils.ocr.get_reader") as mock_get_r:
        mock_r = MagicMock()
        mock_r.readtext.return_value = []
        mock_get_r.return_value = mock_r

        res = extract_text_from_image(b"fake_image_bytes")
        assert "No text could be extracted" in res


def test_ocr_exception_handling():
    with patch("backend.app.utils.ocr.get_reader") as mock_get_r:
        mock_r = MagicMock()
        mock_r.readtext.side_effect = RuntimeError("GPU memory error")
        mock_get_r.return_value = mock_r

        with pytest.raises(ValueError) as exc:
            extract_text_from_image(b"fake_image_bytes")
        assert "Failed to extract text using EasyOCR" in str(exc.value)


# ---------------------------------------------------------------------------
# Document Extractor Tests
# ---------------------------------------------------------------------------

def test_validate_file():
    # PDF magic bytes
    pdf_bytes = b"%PDF-1.4 sample content"
    detected = validate_file("offer.pdf", "application/pdf", pdf_bytes)
    assert detected == "pdf"

    # DOCX magic bytes
    docx_bytes = b"PK\x03\x04sample content"
    detected_docx = validate_file("contract.docx", "application/vnd.openxmlformats", docx_bytes)
    assert detected_docx == "docx"

    # Invalid header
    with pytest.raises(ValueError):
        validate_file("fake.pdf", "application/pdf", b"NOT_A_PDF")


def test_extract_pdf_mocked():
    with patch("pdfplumber.open") as mock_pdfplumber:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Offer letter for John Doe at Tech Corp."
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {"Producer": "Microsoft Word"}
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        text, meta = extract_text_from_pdf(b"%PDF-fake")
        assert "Offer letter" in text
        assert meta["Producer"] == "Microsoft Word"


def test_extract_docx_mocked():
    with patch("docx.Document") as mock_docx:
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "Employment Agreement and Contract"
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []
        mock_doc.core_properties = MagicMock()
        mock_doc.core_properties.author = "HR Director"
        mock_doc.core_properties.created = None
        mock_doc.core_properties.modified = None
        mock_doc.core_properties.last_modified_by = None
        mock_docx.return_value = mock_doc

        text, meta = extract_text_from_docx(b"PK\x03\x04fake_docx")
        assert "Employment Agreement" in text
        assert meta["author"] == "HR Director"


# ---------------------------------------------------------------------------
# Document Forensics Checks
# ---------------------------------------------------------------------------

def test_document_forensics_checks():
    text = (
        "Dear [Candidate Name], You are hired for [Job Role] at [Company Name]. "
        "Please pay immediately to confirm your registration before joining. "
        "Contact hr@gmail.com."
    )
    meta = {"Creator": "smallpdf", "CreationDate": "D:20261005120000"}
    res = check_document(text, meta)

    assert len(res["document_flags"]) > 0
    assert any("free email" in f.lower() for f in res["document_flags"])
    assert any("placeholder" in f.lower() for f in res["document_flags"])
    assert any("urgent payment" in f.lower() for f in res["document_flags"])
    assert res["has_registration"] is False


def test_document_forensics_clean_letter():
    text = (
        "Offer of Employment from Tata Consultancy Services. "
        "CIN: U74140MH1995PLC085000 GSTIN: 27AAAAA0000A1Z5 "
        "Sincerely, Authorized Signatory, TCS HR."
    )
    meta = {"Creator": "Adobe InDesign"}
    res = check_document(text, meta)
    assert res["has_registration"] is True
    assert res["has_signatory"] is True



# ---------------------------------------------------------------------------
# Verifier & Typosquat Tests
# ---------------------------------------------------------------------------

def test_verifier_free_email():
    res = verify(
        text="Send resume to hr-google@gmail.com",
        company_name="Google India",
        contact_email="hr-google@gmail.com"
    )
    assert res["domain_mismatch"] is True
    assert any("free" in f.lower() for f in res["flags"])


def test_verifier_helpers():
    assert _is_free_provider("test@gmail.com") is True
    assert _is_free_provider("test@google.com") is False
    assert _company_is_known_large("Google India") is True
    assert _company_is_known_large("Local Bakery LLC") is False


def test_typosquat_and_domain_checks():
    res = check_domain("g00gle-careers.com")
    assert res["is_typosquat"] is True
    assert res["matched_company"] == "Google"

    # Suspicious TLD
    res_tld = check_domain("tcs-jobs.xyz")
    assert any(".xyz" in f for f in res_tld["domain_flags"])

    # Shortener
    res_short = check_domain("bit.ly")
    assert any("shortener" in f for f in res_short["domain_flags"])

    # Raw IP
    res_ip = check_domain("192.168.1.1")
    assert any("IP address" in f for f in res_ip["domain_flags"])


def test_company_claim_verification():
    flags = check_company_claim("Amazon", ["recruiter@gmail.com"])
    assert len(flags) > 0
    assert any("Official domain" in f for f in flags)
