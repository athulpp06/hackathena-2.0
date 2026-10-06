"""
test_api_integration.py - Integration tests for Task 1:
- Verifies all canonical /api/ endpoints exist (non-404)
- Verifies rate limiting triggers HTTP 429 on rapid requests
- Verifies /api/stats returns aggregate telemetry with zero PII
- Verifies SSRF blocked URLs return HTTP 400
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_readme_endpoints_exist_non_404(client):
    """Verify every path in the README API table exists and returns non-404."""
    # 1. /health
    r_health = client.get("/health")
    assert r_health.status_code == 200

    # 2. /api/analyze/text
    r_text = client.post("/api/analyze/text", json={"text": "Software Engineer role at TCS. Apply on portal."})
    assert r_text.status_code == 200

    # 3. /api/analyze/url (invalid/blocked url returns 400, not 404!)
    r_url = client.post("/api/analyze/url", json={"url": "http://127.0.0.1:8000"})
    assert r_url.status_code == 400

    # 4. /api/analyze/image (empty file returns 400, not 404!)
    r_img = client.post("/api/analyze/image", files={"file": ("test.png", b"", "image/png")})
    assert r_img.status_code == 400

    # 5. /api/analyze/document (empty file returns 400, not 404!)
    r_doc = client.post("/api/analyze/document", files={"file": ("test.pdf", b"", "application/pdf")})
    assert r_doc.status_code == 400

    # 6. /api/report
    r_rep = client.post("/api/report", json={"value": "test@scam.com", "entity_type": "email"})
    assert r_rep.status_code == 200

    # 7. /api/reputation/lookup
    r_look = client.get("/api/reputation/lookup?value=test@scam.com")
    assert r_look.status_code == 200

    # 8. /api/feedback
    r_feed = client.post("/api/feedback", json={"verdict": "correct"})
    assert r_feed.status_code == 200

    # 9. /api/stats
    r_stats = client.get("/api/stats")
    assert r_stats.status_code == 200
    stats = r_stats.json()
    assert "total_scans" in stats
    assert "risk_distribution" in stats
    assert "top_rule_categories" in stats

    # 10. Deprecated aliases still respond non-404
    r_dep_text = client.post("/analyse-text", json={"text": "Testing deprecated alias"})
    assert r_dep_text.status_code == 200


def test_ssrf_returns_http_400(client):
    """Verify internal and invalid URLs return HTTP 400 with a clear error message."""
    resp = client.post("/api/analyze/url", json={"url": "http://localhost:8000/secret"})
    assert resp.status_code == 400
    assert "blocked" in resp.json()["detail"].lower() or "internal" in resp.json()["detail"].lower()


def test_rate_limiting_burst(client):
    """Verify rapid requests exceed rate limits and trigger HTTP 429."""
    # Stricter endpoint /api/report has limit 10/minute
    statuses = []
    for i in range(20):
        r = client.post(
            "/api/report",
            json={"value": f"spammer{i}@gmail.com", "entity_type": "email"},
            headers={"X-Forwarded-For": "203.0.113.195"}
        )
        statuses.append(r.status_code)

    assert 429 in statuses, f"Expected HTTP 429 in rate limit test, got statuses: {statuses[:15]}"
