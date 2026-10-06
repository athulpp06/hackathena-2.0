"""Tests for Phase 6: SSRF protection, request validation, feedback endpoint."""
import pytest
from fastapi.testclient import TestClient

# ---- SSRF protection ----

def test_ssrf_localhost_blocked():
    from backend.app.utils.scraper import _validate_url
    with pytest.raises(ValueError, match="private|internal"):
        _validate_url("http://localhost/admin")


def test_ssrf_loopback_blocked():
    from backend.app.utils.scraper import _validate_url
    with pytest.raises(ValueError, match="private|internal"):
        _validate_url("http://127.0.0.1/secret")


def test_ssrf_internal_ip_blocked():
    from backend.app.utils.scraper import _validate_url
    with pytest.raises(ValueError, match="private|internal|IP"):
        _validate_url("http://192.168.1.1/data")


def test_ssrf_ftp_scheme_blocked():
    from backend.app.utils.scraper import _validate_url
    with pytest.raises(ValueError, match="http"):
        _validate_url("ftp://example.com/file")


def test_ssrf_valid_url_passes():
    from backend.app.utils.scraper import _validate_url
    # Should not raise
    result = _validate_url("https://example.com/jobs")
    assert result == "https://example.com/jobs"


def test_scrape_returns_blocked_message_for_linkedin():
    from backend.app.utils.scraper import ScrapingNotAllowedError, scrape_job_url
    with pytest.raises(ScrapingNotAllowedError):
        scrape_job_url("https://www.linkedin.com/jobs/view/123")


# ---- API request validation & feedback endpoint ----

@pytest.fixture(scope="module")
def client():
    from backend.app.main import app
    return TestClient(app)


def test_text_too_long_rejected(client):
    resp = client.post("/analyse-text", json={"text": "A" * 51000})
    assert resp.status_code == 422


def test_feedback_correct_verdict(client):
    resp = client.post("/api/feedback", json={"verdict": "correct"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "received"
    assert resp.json()["text_stored"] is False


def test_feedback_invalid_verdict(client):
    resp = client.post("/api/feedback", json={"verdict": "wrong_value"})
    assert resp.status_code == 400


def test_feedback_with_opt_in(client):
    resp = client.post("/api/feedback", json={
        "verdict": "missed_scam",
        "opt_in_text": True,
        "raw_text": "This was a scam and LeakedIn missed it"
    })
    assert resp.status_code == 200
    assert resp.json()["text_stored"] is True


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model_version" in data
    assert "privacy_note" in data
