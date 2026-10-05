import requests
import sys

def run_live_tests():
    print("Testing live server endpoints...")
    try:
        r_health = requests.get("http://127.0.0.1:8000/health", timeout=10)
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
    assert res_legit["is_job_posting"] is True
    assert res_legit["risk_score"] <= 25
    print(f"  [PASS] POST /api/v1/analyse-job (Legit) -> Risk Score: {res_legit['risk_score']}/100, Level: {res_legit['risk_level']}")

    # 5. Gatekeeper Status Check
    r_gk_status = requests.get("http://127.0.0.1:8000/api/v1/gatekeeper-status")
    assert r_gk_status.status_code == 200
    gk_data = r_gk_status.json()
    assert "gatekeeper_active" in gk_data
    print(f"  [PASS] GET /api/v1/gatekeeper-status -> active={gk_data['gatekeeper_active']}, gemini={gk_data['gemini_configured']}")

    # 6. Non-Job Content Scan (Recipe prompt)
    recipe_payload = {
        "text": (
            "Delicious Homemade Chocolate Brownies Recipe: "
            "Melt 200g dark chocolate with 150g butter. Whisk 3 eggs and 200g sugar until fluffy. "
            "Fold in 100g flour and 30g cocoa powder. Bake at 180C for 25 minutes. Serve warm with ice cream!"
        )
    }
    r_recipe = requests.post("http://127.0.0.1:8000/api/v1/analyse-job", json=recipe_payload)
    assert r_recipe.status_code == 200
    res_recipe = r_recipe.json()
    assert res_recipe["is_job_posting"] is False
    assert res_recipe["risk_score"] is None
    assert res_recipe["risk_level"] == "Invalid Content"
    print(f"  [PASS] POST /api/v1/analyse-job (Non-Job Recipe) -> is_job_posting={res_recipe['is_job_posting']}, verdict={res_recipe['verdict']}")

    # 7. Student Internship Scam (User case)
    intern_scam_payload = {
        "text": (
            "We are happy to offer you an opportunity to work as a Marketing intern for pursuing students (part-time job) "
            "where you can earn more than your Pocket money. Immediate Hiring, just pay 5000 initially. "
            "Work from home, good stipend (2500-21000), marketing intern certificate, free internship opportunity. "
            "TO APPLY FILL: NAME, COLLEGE, BRANCH&YEAR, PH, EMAIL."
        )
    }
    r_intern = requests.post("http://127.0.0.1:8000/api/v1/analyse-job", json=intern_scam_payload)
    assert r_intern.status_code == 200
    res_intern = r_intern.json()
    assert res_intern["is_job_posting"] is True
    assert res_intern["risk_score"] >= 85
    assert res_intern["risk_level"] == "High Risk"
    print(f"  [PASS] POST /api/v1/analyse-job (Intern Scam) -> Risk Score: {res_intern['risk_score']}/100, Level: {res_intern['risk_level']}")
    print("\nAll live server endpoint tests passed successfully!")

if __name__ == "__main__":
    run_live_tests()
