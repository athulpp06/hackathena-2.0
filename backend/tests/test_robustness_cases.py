"""
test_robustness_cases.py — 20 regression cases from the AUDIT_REPORT.md Section 6.

All 20 cases must pass:
- 10 scam cases: score must be >= 51 (Suspicious or High Risk)
- 10 legit cases: score must be <= 50 (Safe or Low Risk), no false alarms

Key cases this file explicitly guards against regressions for:
  Case #3 (Scam): "transfer registration fee of Rs 3500 immediately" — previously scored 30 (FAIL)
  Case #4 (Scam): Native Malayalam script scam — previously scored 12 with zero flags (FAIL)
"""

import pytest

from backend.app.detector.aggregator import aggregate
from backend.app.detector.rules import detect_rules
from backend.app.detector.verifier import verify


def _score(text: str, company_name: str = "", contact_email: str = "") -> dict:
    """Run the detection pipeline without ML (rules + verifier + aggregator) and return result."""
    flags = detect_rules(text)
    verifier = verify(text, company_name=company_name, contact_email=contact_email)
    return aggregate(0.0, flags, verifier, text=text)  # ml_score=0 so we test rule+aggregator only


# ─────────────────────────────────────────────────────────────────
# SCAM CASES — must score >= 51
# ─────────────────────────────────────────────────────────────────

class TestScamCases:
    """10 scam cases — all must score >= 51 (Suspicious or High Risk)."""

    def test_case1_hinglish_registration_fee(self):
        """Audit case #1: Hinglish data-entry scam with Rs 2000 registration fee."""
        text = (
            "Dear bhai, aapka profile select hua hai. Data entry kaam ghar se kar sakte ho. "
            "Rs 2000 registration fee bhejo aur kaam shuru karo. Jaldi karo limited seats hain."
        )
        result = _score(text)
        assert result["risk_score"] >= 51, (
            f"Case #1 (Hinglish registration fee) scored {result['risk_score']} — expected >= 51. "
            f"Flags: {[f['category'] for f in detect_rules(text)]}"
        )

    def test_case2_telegram_task_scam(self):
        """Audit case #2: Telegram task scam — like YouTube videos."""
        text = (
            "Join our Telegram group @earnmoney2024. Like YouTube videos and earn Rs 500 per task. "
            "No experience required. Work from home. Limited seats, apply immediately."
        )
        result = _score(text)
        assert result["risk_score"] >= 51, (
            f"Case #2 (Telegram task scam) scored {result['risk_score']} — expected >= 51"
        )

    def test_case3_offer_letter_with_transfer_fee_immediately(self):
        """Audit case #3: PREVIOUSLY FAILING. Offer letter asking to 'transfer registration fee immediately'."""
        text = (
            "Dear [Candidate Name], You are hired at our company. "
            "Please transfer registration fee of Rs 3500 immediately to confirm your slot. "
            "Offer letter will be sent on WhatsApp once payment is done."
        )
        result = _score(text)
        assert result["risk_score"] >= 51, (
            f"Case #3 (transfer fee immediately) scored {result['risk_score']} — expected >= 51. "
            f"This is the regression for the 'transfer...immediately' intermediate-word bug. "
            f"Flags: {[f['category'] for f in detect_rules(text)]}"
        )

    def test_case4_native_malayalam_script_scam(self):
        """Audit case #4: PREVIOUSLY FAILING. Pure Malayalam-script scam — no English words."""
        text = "ഹോം ജോബ് ഉണ്ട്! ദിവസം 3000 രൂപ സമ്പാദിക്കാം. ആധാർ കൊണ്ടുവരൂ. 1500 രൂപ അഡ്വാൻസ് ആദ്യം അടക്കണം."
        result = _score(text)
        assert result["risk_score"] >= 51, (
            f"Case #4 (Malayalam script) scored {result['risk_score']} — expected >= 51. "
            f"This is the regression for zero Malayalam heuristic rules. "
            f"Flags: {[f['category'] for f in detect_rules(text)]}"
        )

    def test_case5_amazon_impersonation_aadhaar(self):
        """Audit case #5: Amazon impersonation with Aadhaar + free email."""
        text = (
            "Congratulations! Selected by Amazon India for WFH role. "
            "Send Aadhaar and bank details to hr-amazon@gmail.com"
        )
        result = _score(text, company_name="Amazon India", contact_email="hr-amazon@gmail.com")
        assert result["risk_score"] >= 51, (
            f"Case #5 (Amazon impersonation) scored {result['risk_score']} — expected >= 51"
        )

    def test_case6_bitcoin_wfh_no_interview(self):
        """Audit case #6: Bitcoin payment + WFH + guaranteed income."""
        text = (
            "Work from home. Earn Rs 10000 per day. Send Bitcoin worth $200. "
            "No interview. 100% guaranteed income."
        )
        result = _score(text)
        assert result["risk_score"] >= 51, (
            f"Case #6 (Bitcoin + WFH) scored {result['risk_score']} — expected >= 51"
        )

    def test_case7_google_upi_fee(self):
        """Audit case #7: Google India recruiter asking UPI registration fee."""
        text = (
            "Google India recruiter: Upload Aadhaar and PAN card. "
            "Registration fee Rs 2500 via UPI in 2 hours. Limited time offer."
        )
        result = _score(text)
        assert result["risk_score"] >= 51, (
            f"Case #7 (Google UPI fee) scored {result['risk_score']} — expected >= 51"
        )

    def test_case8_leetspeak_obfuscated_scam(self):
        """Audit case #8: Leetspeak-obfuscated job scam (J0b, W0rk, r3g1str4t10n)."""
        text = "J0b 0pp0rtun1ty! W0rk fr0m h0me. 50000 per m0nth. Pay 1000 r3g1str4t10n f33 to start."
        result = _score(text)
        assert result["risk_score"] >= 51, (
            f"Case #8 (leetspeak) scored {result['risk_score']} — expected >= 51. "
            f"Flags: {[f['category'] for f in detect_rules(text)]}"
        )

    def test_case9_tcs_yahoo_fee(self):
        """Audit case #9: TCS impersonation with Yahoo email and processing fee."""
        text = "TCS job alert: Selected candidates must pay Rs 4000 processing fee to hr-tcs@yahoo.com"
        result = _score(text, company_name="TCS", contact_email="hr-tcs@yahoo.com")
        assert result["risk_score"] >= 51, (
            f"Case #9 (TCS Yahoo fee) scored {result['risk_score']} — expected >= 51"
        )

    def test_case10_infosys_crypto_bank_details(self):
        """Audit case #10: Infosys + crypto + bank details."""
        text = (
            "Fake Infosys offer: Join crypto team. Earn 1 BTC per month. "
            "Send bank details and Rs 2000 joining fee."
        )
        result = _score(text)
        assert result["risk_score"] >= 51, (
            f"Case #10 (Infosys crypto) scored {result['risk_score']} — expected >= 51"
        )


# ─────────────────────────────────────────────────────────────────
# LEGIT CASES — must score <= 50, no false alarms
# ─────────────────────────────────────────────────────────────────

class TestLegitCases:
    """10 legit cases — all must score <= 50 (Safe or Low Risk)."""

    def test_case11_genuine_wipro_recruiter(self):
        """Audit case #11: Genuine Wipro recruiter LinkedIn outreach."""
        text = (
            "Hi, I am a recruiter from Wipro. Saw your profile on LinkedIn. "
            "We have a suitable opening. Would you like to schedule a technical interview? "
            "There are no fees. Apply at careers.wipro.com."
        )
        result = _score(text, company_name="Wipro")
        assert result["risk_score"] <= 50, (
            f"Case #11 (Wipro legitimate) scored {result['risk_score']} — false alarm, expected <= 50"
        )

    def test_case12_interview_whatsapp_video(self):
        """Audit case #12: Legitimate interview via WhatsApp video — WhatsApp mentioned but not a scam."""
        text = (
            "Dear Candidate, your interview is scheduled for Monday at 11 AM via WhatsApp video call. "
            "Please bring your government-issued ID for document verification. No fees required."
        )
        result = _score(text)
        assert result["risk_score"] <= 50, (
            f"Case #12 (WhatsApp video interview) scored {result['risk_score']} — false alarm, expected <= 50. "
            f"Flags triggered: {[f['category'] for f in detect_rules(text)]}"
        )

    def test_case13_data_analyst_hiring(self):
        """Audit case #13: Genuine data analyst job posting."""
        text = (
            "Hiring Data Analyst. Salary: 8-12 LPA. Requirements: Python, SQL, 3 years experience. "
            "Apply at our official portal. No fees required. Background check conducted by company."
        )
        result = _score(text)
        assert result["risk_score"] <= 50, (
            f"Case #13 (Data analyst hiring) scored {result['risk_score']} — false alarm, expected <= 50"
        )

    def test_case14_joining_aadhaar_for_payroll(self):
        """Audit case #14: HR asking Aadhaar on joining day for company ID — LEGITIMATE context."""
        text = (
            "Congratulations! Completed round 2. Please bring your salary slips, bank statement, "
            "and Aadhaar for joining formalities and payroll setup. Joining date is October 15."
        )
        result = _score(text)
        assert result["risk_score"] <= 50, (
            f"Case #14 (Aadhaar for payroll joining) scored {result['risk_score']} — false alarm, expected <= 50. "
            f"Flags triggered: {[f['category'] for f in detect_rules(text)]}"
        )

    def test_case15_hcl_software_engineer(self):
        """Audit case #15: HCL software engineer job posting with official domain."""
        text = (
            "Software Engineer at HCL Technologies. CTC: 12 LPA. "
            "Health insurance, PF, and gratuity. Apply at hcltech.com/careers."
        )
        result = _score(text, company_name="HCL Technologies")
        assert result["risk_score"] <= 50, (
            f"Case #15 (HCL software engineer) scored {result['risk_score']} — false alarm, expected <= 50"
        )

    def test_case16_razorpay_developer(self):
        """Audit case #16: Razorpay senior developer role with official email."""
        text = (
            "Senior Developer at Razorpay. Required skills: Node.js, AWS, PostgreSQL. "
            "3-5 years experience. Contact: jobs@razorpay.com"
        )
        result = _score(text, company_name="Razorpay", contact_email="jobs@razorpay.com")
        assert result["risk_score"] <= 50, (
            f"Case #16 (Razorpay developer) scored {result['risk_score']} — false alarm, expected <= 50"
        )

    def test_case17_infosys_onboarding_portal(self):
        """Audit case #17: Infosys joining-date notification with official onboarding email."""
        text = (
            "Notice: Your joining date is 15 October. Please complete pre-joining formalities "
            "on the HR portal. Contact onboarding@infosys.com for queries."
        )
        result = _score(text, company_name="Infosys", contact_email="onboarding@infosys.com")
        assert result["risk_score"] <= 50, (
            f"Case #17 (Infosys onboarding) scored {result['risk_score']} — false alarm, expected <= 50"
        )

    def test_case18_swiggy_immediate_opening(self):
        """Audit case #18: Swiggy 'immediate opening' — immediate is not inherently scam."""
        text = (
            "Immediate opening at Swiggy: Operations Manager. Salary 15-20 LPA. "
            "3+ years experience in logistics. Apply at careers.swiggy.in"
        )
        result = _score(text, company_name="Swiggy")
        assert result["risk_score"] <= 50, (
            f"Case #18 (Swiggy immediate opening) scored {result['risk_score']} — false alarm, expected <= 50"
        )

    def test_case19_zoom_interview_reminder(self):
        """Audit case #19: Simple Zoom interview reminder."""
        text = (
            "Interview reminder: Technical interview with the engineering team at 2 PM today on Zoom. "
            "Please be prepared with your code editor."
        )
        result = _score(text)
        assert result["risk_score"] <= 50, (
            f"Case #19 (Zoom interview reminder) scored {result['risk_score']} — false alarm, expected <= 50"
        )

    def test_case20_rejection_email(self):
        """Audit case #20: Rejection email — must not be flagged as scam."""
        text = (
            "We regret to inform you that after careful consideration, "
            "we cannot move forward with your application at this time. "
            "We appreciate your interest in joining our company."
        )
        result = _score(text)
        assert result["risk_score"] <= 50, (
            f"Case #20 (Rejection email) scored {result['risk_score']} — false alarm, expected <= 50"
        )


# ─────────────────────────────────────────────────────────────────
# Aggregate pass-rate summary helper (for CI output readability)
# ─────────────────────────────────────────────────────────────────

def test_robustness_summary_scam_recall():
    """Meta-test: ALL 10 scam cases must score >= 51."""
    scam_cases = [
        "Dear bhai, aapka profile select hua hai. Rs 2000 registration fee bhejo. Jaldi karo limited seats.",
        "Join our Telegram group @earnmoney2024. Like YouTube videos and earn Rs 500 per task. No experience required. Work from home. Limited seats, apply immediately.",
        "transfer registration fee of Rs 3500 immediately to confirm your slot.",
        "ഹോം ജോബ് ഉണ്ട്! ദിവസം 3000 രൂപ സമ്പാദിക്കാം. ആധാർ കൊണ്ടുവരൂ. 1500 രൂപ അഡ്വാൻസ് ആദ്യം അടക്കണം.",
        "Selected by Amazon India. Send Aadhaar and bank details to hr-amazon@gmail.com",
        "Work from home. Earn Rs 10000 per day. Send Bitcoin worth $200. No interview. 100% guaranteed.",
        "Google India recruiter: Upload Aadhaar and PAN. Registration fee Rs 2500 via UPI in 2 hours.",
        "J0b 0pp0rtun1ty! W0rk fr0m h0me. Pay 1000 r3g1str4t10n f33 to start.",
        "TCS job alert: pay Rs 4000 processing fee to hr-tcs@yahoo.com",
        "Join crypto team. Earn 1 BTC per month. Send bank details and Rs 2000 joining fee.",
    ]
    failures = []
    for i, text in enumerate(scam_cases, start=1):
        flags = detect_rules(text)
        verifier = verify(text)
        result = aggregate(0.0, flags, verifier, text=text)
        if result["risk_score"] < 51:
            failures.append(f"Scam case #{i}: score={result['risk_score']}, flags={[f['category'] for f in flags]}")
    assert not failures, f"Scam recall failures ({len(failures)}/10):\n" + "\n".join(failures)


def test_robustness_summary_legit_specificity():
    """Meta-test: ALL 10 legit cases must score <= 50 (zero false alarms)."""
    legit_cases = [
        "Hi, I am a recruiter from Wipro. Saw your profile on LinkedIn. We have a suitable opening. No fees. Apply at careers.wipro.com.",
        "Dear Candidate, interview scheduled via WhatsApp video call. Bring government-issued ID for verification. No fees required.",
        "Hiring Data Analyst. Salary: 8-12 LPA. Requirements: Python, SQL. No fees required.",
        "Bring salary slips, bank statement, and Aadhaar for joining formalities on October 15.",
        "Software Engineer at HCL Technologies. CTC: 12 LPA. Apply at hcltech.com/careers.",
        "Senior Developer at Razorpay. Skills: Node.js, AWS. Contact: jobs@razorpay.com",
        "Your joining date is 15 October. Complete pre-joining formalities. Contact onboarding@infosys.com.",
        "Immediate opening at Swiggy: Operations Manager. Salary 15-20 LPA. Apply at careers.swiggy.in",
        "Interview reminder: Technical interview with engineering team at 2 PM on Zoom.",
        "We regret to inform you we cannot move forward with your application at this time.",
    ]
    failures = []
    for i, text in enumerate(legit_cases, start=1):
        flags = detect_rules(text)
        verifier = verify(text)
        result = aggregate(0.0, flags, verifier, text=text)
        if result["risk_score"] > 50:
            failures.append(f"Legit case #{i}: score={result['risk_score']}, flags={[f['category'] for f in flags]}")
    assert not failures, f"False alarm failures ({len(failures)}/10):\n" + "\n".join(failures)
