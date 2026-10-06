import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.detector.rules import RuleEngine

engine = RuleEngine()

sample_scam = """
URGENT HIRING: Data entry operator at TCS!
Earn Rs 45000 per week working from home 2 hours a day. No experience required.
Direct selection without interview! 
Only 3 seats left - offer expires within 24 hours.
To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit.
Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com.
"""

result = engine.analyze(sample_scam)

print("--- Detected Flags ---")
for flag in result["red_flags"]:
    print(f"[{flag['severity']}] {flag['title']}: '{flag['matched_text']}' (chars {flag['start']}..{flag['end']})")

print(f"\nTotal Flag Count: {result['flag_count']}")
print(f"Total Penalty: {result['total_penalty']}/100")
print(f"\nMerged UI Highlight Spans ({len(result['highlighted_spans'])} spans):")
for s in result["highlighted_spans"]:
    print(f"  [{s['severity']}] chars {s['start']}..{s['end']} -> '{sample_scam[s['start']:s['end']].strip()}'")

print("\n--- Legit Job Test ---")
sample_legit = """
We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.
Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.
Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.
Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off.
To apply, submit your resume on our careers portal at https://stripe.com/jobs.
"""
legit_result = engine.analyze(sample_legit)
print(f"Legit job flags detected: {legit_result['flag_count']} (Penalty: {legit_result['total_penalty']}/100)")
assert legit_result["flag_count"] == 0

print("\n--- Malayalam Scam Rule Test ---")
malayalam_sample = "വർക്ക് ഫ്രം ഹോം ജോലി. രജിസ്ട്രേഷൻ ഫീസ് 1500 രൂപ അടക്കണം. ആധാർ അയക്കൂ."
ml_result = engine.analyze(malayalam_sample)
assert ml_result["flag_count"] >= 2
assert any("Malayalam" in f["title"] for f in ml_result["red_flags"])
assert any("Aadhaar" in f["title"] for f in ml_result["red_flags"])
print(f"  [PASS] Malayalam Scam detected: {ml_result['flag_count']} flags (Penalty: {ml_result['total_penalty']})")

print("\n--- Hindi Scam Rule Test ---")
hindi_sample = "घर बैठे जॉब। रजिस्ट्रेशन फीस 2000 रुपये जमा करें और पैन कार्ड शेयर करें।"
hi_result = engine.analyze(hindi_sample)
assert hi_result["flag_count"] >= 2
assert any("Fee Demand" in f["title"] for f in hi_result["red_flags"])
print(f"  [PASS] Hindi Scam detected: {hi_result['flag_count']} flags (Penalty: {hi_result['total_penalty']})")
