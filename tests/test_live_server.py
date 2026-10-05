import requests
import sys

def run_live_tests():
    print("Testing live server endpoints...")
    try:
        r_health = requests.get("http://127.0.0.1:8000/health", timeout=2)
    except Exception as e:
        print(f"  [SKIP] Live server is not running on http://127.0.0.1:8000 ({e}).")
        print("  Start the server with: uvicorn backend.app.main:app --port 8000")
        return

    # 1. Root / Frontend
    r_root = requests.get("http://127.0.0.1:8000/")
    assert r_root.status_code == 200, f"Root failed: {r_root.status_code}"
    assert "LeakedIn" in r_root.text
    print("  [PASS] http://127.0.0.1:8000/ (Frontend UI served successfully)")

    # 2. Health check
    assert r_health.status_code == 200
    print(f"  [PASS] http://127.0.0.1:8000/health -> {r_health.json()}")

    # 3. Analyze Job (Scam)
    scam_payload = {
        "text": (
            "URGENT HIRING: Data entry operator at TCS! "
            "Earn Rs 45000 per week working from home 2 hours a day. No experience required. "
            "Direct selection without interview! Only 3 seats left - offer expires within 24 hours. "
            "To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit. "
            "Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com."
        ),
        "company_name": "TCS",
        "contact_email": "hr.tcs.recruiter@gmail.com"
    }
    r_analyse = requests.post("http://127.0.0.1:8000/api/v1/analyse-job", json=scam_payload)
    assert r_analyse.status_code == 200
    res = r_analyse.json()
    print(f"  [PASS] POST /api/v1/analyse-job -> Risk Score: {res['risk_score']}/100, Verdict: {res['verdict']}")
    print(f"         Flags: {len(res['red_flags'])} red flags, {len(res['domain_flags'])} domain flags")

    # 4. Analyze Job (Legit)
    legit_payload = {
        "text": (
            "We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe. "
            "Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices. "
            "Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems. "
            "Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off. "
            "To apply, submit your resume on our careers portal at https://stripe.com/jobs or contact recruiting@stripe.com."
        )
    }
    r_legit = requests.post("http://127.0.0.1:8000/api/v1/analyse-job", json=legit_payload)
    assert r_legit.status_code == 200
    res_legit = r_legit.json()
    print(f"  [PASS] POST /api/v1/analyse-job (Legit) -> Risk Score: {res_legit['risk_score']}/100, Level: {res_legit['risk_level']}")

if __name__ == "__main__":
    run_live_tests()
