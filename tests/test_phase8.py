"""
test_phase8.py - Unit tests for Phase 8 distribution channels.
Validates Telegram bot report formatting, pipeline integration, and extension structure.
"""

from pathlib import Path

from backend.app.api.routes import _run_pipeline
from bots.telegram_bot import format_telegram_report


def test_telegram_report_formatting():
    """Verify format_telegram_report handles scam results with red flags and advice."""
    sample_text = (
        "Dear candidate, pay Rs 2000 registration fee via UPI to hr@okaxis. "
        "Send Aadhaar to +91-9876543210 on WhatsApp."
    )
    result = _run_pipeline(sample_text)
    report = format_telegram_report(result)

    assert "LEAKEDIN SCAM AUDIT REPORT" in report
    assert "Threat Score:" in report
    assert "1930" in report
    assert "cybercrime.gov.in" in report
    assert "Aadhaar" in report or "Financial Demand" in report


def test_telegram_report_safe_posting():
    """Verify format_telegram_report formats legitimate postings cleanly."""
    sample_text = (
        "We are looking for a Senior Software Engineer with 5 years experience in Python and AWS. "
        "Apply through our official careers page at careers.google.com."
    )
    result = _run_pipeline(sample_text)
    report = format_telegram_report(result)

    assert "LEAKEDIN SCAM AUDIT REPORT" in report
    assert result["risk_score"] <= 50
    assert "1930" in report


def test_chrome_extension_manifest():
    """Verify Manifest V3 file exists and contains valid JSON with required permissions."""
    manifest_path = Path("extension/manifest.json")
    assert manifest_path.exists()

    import json
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["manifest_version"] == 3
    assert "contextMenus" in data["permissions"]
    assert "storage" in data["permissions"]
    assert "background" in data
    assert "service_worker" in data["background"]
    assert Path("extension/background.js").exists()
    assert Path("extension/content.js").exists()
    assert Path("extension/popup.html").exists()
    assert Path("extension/icons/icon128.png").exists()
