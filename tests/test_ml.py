import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.detector.ml import predict, is_model_ready

print(f"Model ready: {is_model_ready()}\n")

sample_scam = """
URGENT HIRING: Data entry operator at TCS!
Earn Rs 45000 per week working from home 2 hours a day. No experience required.
Direct selection without interview! 
Only 3 seats left - offer expires within 24 hours.
To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit.
Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com.
"""

sample_legit = """
We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.
Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.
Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.
Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off.
To apply, submit your resume on our careers portal at https://stripe.com/jobs.
"""

print("--- SCAM JOB ---")
result = predict(sample_scam)
for k, v in result.items():
    print(f"  {k}: {v}")

print("\n--- LEGIT JOB ---")
result2 = predict(sample_legit)
for k, v in result2.items():
    print(f"  {k}: {v}")
