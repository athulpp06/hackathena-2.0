import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.detector.aggregator import analyse
import json

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
To apply, submit your resume on our careers portal at https://stripe.com/jobs or contact recruiting@stripe.com.
"""

print("=" * 60)
print("SCAM JOB ANALYSIS")
print("=" * 60)
scam_result = analyse(sample_scam, declared_company="TCS")
print(f"  Risk Score : {scam_result['risk_score']}/100")
print(f"  Risk Level : {scam_result['risk_level']}")
print(f"  Verdict    : {scam_result['verdict']}")
print(f"  ML Score   : {scam_result['ml_score_pct']}%")
print(f"  Rule Flags : {scam_result['rule_flag_count']} flags (penalty: {scam_result['rule_penalty']})")
print(f"  Domain Flags: {scam_result['domain_flag_count']} flags")
print(f"  Company Mismatch: {scam_result['company_mismatch']}")
print(f"  Red Flags:")
for f in scam_result["red_flags"]:
    print(f"    [{f['severity']}] {f['title']}: '{f['matched_text']}'")
print(f"  Domain Issues:")
for f in scam_result["domain_flags"]:
    print(f"    [{f['severity']}] {f['title']}")
print(f"  Recommendations:")
for r in scam_result["recommendations"]:
    print(f"    - {r}")

print()
print("=" * 60)
print("LEGIT JOB ANALYSIS")
print("=" * 60)
legit_result = analyse(sample_legit)
print(f"  Risk Score  : {legit_result['risk_score']}/100")
print(f"  Risk Level  : {legit_result['risk_level']}")
print(f"  Verdict     : {legit_result['verdict']}")
print(f"  ML Score    : {legit_result['ml_score_pct']}%")
print(f"  Rule Flags  : {legit_result['rule_flag_count']}")
print(f"  Domain Flags: {legit_result['domain_flag_count']}")
assert legit_result["risk_score"] <= 25, f"Legit job score too high: {legit_result['risk_score']}"
assert legit_result["risk_level"] == "Safe"

print()
print("=" * 60)
print("STUDENT INTERNSHIP SCAM ANALYSIS (USER CASE)")
print("=" * 60)
sample_intern_scam = """
We are happy to offer you an opportunity to work as a Marketing intern for pursuing students (part-time job) where you can earn more than your Pocket money. Immediate Hiring, just pay 5000 initially

Your opportunity involves

* Work from home
* Branding/Promotion
* Good Stipend (2500-21000)
* Marketing Intern certificate 
* Free internship opportunity
* Letter of recommendation 

TO APPLY FILL

NAME:
COLLEGE:
BRANCH&YEAR:
PH:
EMAIL:
COMFORTABLE LANGUAGE:
STATE YOU BELONG TO:
"""
intern_result = analyse(sample_intern_scam)
print(f"  Risk Score  : {intern_result['risk_score']}/100")
print(f"  Risk Level  : {intern_result['risk_level']}")
print(f"  Verdict     : {intern_result['verdict']}")
print(f"  ML Score    : {intern_result['ml_score_pct']}%")
print(f"  Rule Flags  : {intern_result['rule_flag_count']} flags (penalty: {intern_result['rule_penalty']})")
print(f"  Top Signals : {intern_result['ml_top_signals']}")

assert intern_result["risk_score"] >= 85, f"Intern scam score too low: {intern_result['risk_score']}"
assert intern_result["risk_level"] == "High Risk"
assert "Critical scam indicators" in intern_result["verdict"]
assert intern_result["rule_penalty"] >= 80

print("\nAll aggregator test assertions passed successfully!")
