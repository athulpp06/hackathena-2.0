"""
Test Suite for Module 5: FastAPI Routes & API Logic
"""

import sys, os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app, health
from backend.app.api.routes import analyse_job, ocr_status, gatekeeper_status, JobAnalysisRequest
from starlette.testclient import TestClient

async def test_health_endpoint():
    res = await health()
    assert res["status"] in ("ok", "degraded")
    assert res["service"] == "LeakedIn Job Posting Scanner"
    assert "ml_model_loaded" in res
    print("  [PASS] test_health_endpoint ->", res)

async def test_ocr_status_endpoint():
    res = await ocr_status()
    assert "ocr_available" in res
    print("  [PASS] test_ocr_status_endpoint ->", res)

async def test_analyse_job_endpoint():
    req = JobAnalysisRequest(
        text=(
            "URGENT HIRING: Data entry operator at TCS! "
            "Earn Rs 45000 per week working from home 2 hours a day. No experience required. "
            "Direct selection without interview! Only 3 seats left - offer expires within 24 hours. "
            "To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit. "
            "Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com."
        ),
        company_name="TCS",
        contact_email="hr.tcs.recruiter@gmail.com"
    )
    result = await analyse_job(req)
    assert result["risk_score"] > 70
    assert result["risk_level"] in ("High Risk", "Suspicious")
    assert result["rule_flag_count"] > 0
    assert result["company_mismatch"] is True
    print(f"  [PASS] test_analyse_job_endpoint -> Risk Score: {result['risk_score']}/100, Level: {result['risk_level']}")

async def test_gatekeeper_non_job_api():
    req = JobAnalysisRequest(
        text="Chocolate Chip Cookies: Cream 1 cup softened butter with 1 cup brown sugar and 1 tsp vanilla extract. Stir in 2 cups chocolate chips and bake at 350F for 10 minutes."
    )
    result = await analyse_job(req)
    assert result["is_job_posting"] is False
    assert result["risk_score"] is None
    assert result["risk_level"] == "Invalid Content"
    print(f"  [PASS] test_gatekeeper_non_job_api -> is_job_posting={result['is_job_posting']}, verdict={result['verdict']}")

async def test_analyse_url_ssrf_blocked():
    from backend.app.api.routes import analyse_url, URLAnalysisRequest
    from fastapi import HTTPException
    req = URLAnalysisRequest(url="http://127.0.0.1:8000/internal-admin")
    try:
        await analyse_url(req)
        assert False, "Should have blocked internal SSRF IP"
    except HTTPException as e:
        assert e.status_code == 400
        assert "blocked" in e.detail.lower() or "internal" in e.detail.lower()
        print("  [PASS] test_analyse_url_ssrf_blocked -> Successfully blocked internal IP:", e.detail)


async def test_gatekeeper_status_safe():
    res = await gatekeeper_status()
    assert "gemini_active" in res
    assert "mode" in res
    assert "model" in res
    assert "vision_supported" in res
    # Ensure zero key leakage
    res_str = str(res).lower()
    assert "api_key" not in res_str
    assert "aiza" not in res_str
    print("  [PASS] test_gatekeeper_status_safe -> Gatekeeper status contains no key credentials:", res)


def test_set_gemini_key_endpoint_removed():
    client = TestClient(app)
    # /set-gemini-key must return 404 since it has been removed
    resp = client.post("/set-gemini-key", json={"api_key": "dummy_key_123456789"})
    assert resp.status_code in (404, 405)
    print("  [PASS] test_set_gemini_key_endpoint_removed -> /set-gemini-key is successfully removed")


async def main():
    print("=" * 60)
    print("RUNNING MODULE 5 API ROUTE TESTS")
    print("=" * 60)
    await test_health_endpoint()
    await test_ocr_status_endpoint()
    await test_analyse_job_endpoint()
    await test_gatekeeper_non_job_api()
    await test_analyse_url_ssrf_blocked()
    await test_gatekeeper_status_safe()
    test_set_gemini_key_endpoint_removed()
    print("=" * 60)
    print("ALL MODULE 5 API ROUTE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

