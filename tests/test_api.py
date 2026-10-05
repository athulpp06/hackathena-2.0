"""
Test Suite for Module 5: FastAPI Routes & API Logic
"""

import sys, os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app, health
from backend.app.api.routes import analyse_job, ocr_status, JobAnalysisRequest

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

async def main():
    print("=" * 60)
    print("RUNNING MODULE 5 API ROUTE TESTS")
    print("=" * 60)
    await test_health_endpoint()
    await test_ocr_status_endpoint()
    await test_analyse_job_endpoint()
    print("=" * 60)
    print("ALL MODULE 5 API ROUTE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
