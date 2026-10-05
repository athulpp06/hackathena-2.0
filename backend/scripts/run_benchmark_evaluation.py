"""
Benchmark Dataset Generator & Model Evaluation Suite.
Generates an independent, diverse evaluation dataset of modern recruitment scams
and legitimate job/internship postings, executes the detection pipeline,
and computes comprehensive performance metrics.
"""

import os
import sys
import json
import time

# Ensure clean UTF-8 console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.detector import aggregator

BENCHMARK_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "evaluation_benchmark_dataset.csv"
)
BENCHMARK_CSV_PATH = os.path.normpath(BENCHMARK_CSV_PATH)


def build_benchmark_samples():
    """
    Creates a diverse, realistic benchmark suite of 60 test postings:
    30 Scam Postings across various modern fraud archetypes
    30 Legitimate Postings across corporate, startups, internships, and tricky edge-cases.
    """
    samples = [
        # =====================================================================
        # SCAM POSTINGS (ground_truth = 1)
        # =====================================================================
        # 1. Student / Internship Upfront Fee Scams
        {
            "id": "SCAM_01",
            "category": "Student Internship Fee",
            "title": "Marketing Intern (Work From Home)",
            "declared_company": "",
            "contact_email": "",
            "ground_truth": 1,
            "text": """We are happy to offer you an opportunity to work as a Marketing intern for pursuing students (part-time job) where you can earn more than your Pocket money. Immediate Hiring, just pay 5000 initially.
Your opportunity involves: Work from home, Branding/Promotion, Good Stipend (2500-21000), Marketing Intern certificate, Free internship opportunity, Letter of recommendation.
TO APPLY FILL
NAME:
COLLEGE:
BRANCH&YEAR:
PH:
EMAIL:
COMFORTABLE LANGUAGE:
STATE YOU BELONG TO:"""
        },
        {
            "id": "SCAM_02",
            "category": "Student Internship Fee",
            "title": "HR Recruiter Intern - College Students",
            "declared_company": "Apex HR Solutions",
            "contact_email": "apex.internship.desk@gmail.com",
            "ground_truth": 1,
            "text": """Part time HR Internship for pursuing college students. Earn daily pocket money working 1-2 hours from home.
Guaranteed monthly stipend of Rs 15000 + performance bonus. Marketing and screening candidates.
Immediate joining! Direct selection without interview.
To issue your verified appointment letter and ID card kit, pay initial registration charge of Rs 999 (refundable after 30 days).
Send CV and screenshot of payment on WhatsApp: +91 9123456780."""
        },
        {
            "id": "SCAM_03",
            "category": "Student Internship Fee",
            "title": "Graphic Design Intern - Remote",
            "declared_company": "Creative Minds Studio",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Looking for student graphic design interns. Work from anywhere, flexible hours.
Stipend: Rs 12000 per month. Certificate of completion and LOR provided.
All pursuing diploma and degree students eligible. No prior design portfolio needed.
Candidates must pay a nominal software license and kit fee of Rs 1,499 initially before onboarding.
Apply now - only 5 slots available. Offer valid for 24 hours only!"""
        },
        {
            "id": "SCAM_04",
            "category": "Student Internship Fee",
            "title": "Content Writing Intern (Part-Time)",
            "declared_company": "Veritas Media",
            "contact_email": "content.veritas@yahoo.com",
            "ground_truth": 1,
            "text": """Free internship opportunity for students and freshers! Earn pocket money writing short articles from mobile.
Stipend: Rs 18,000 per month. Instant offer letter provided upon registration.
Just deposit a refundable caution fee of 2000 initially for writer portal login credentials.
FILL DETAILS TO APPLY:
Name:
College:
Mobile:
City:"""
        },
        {
            "id": "SCAM_05",
            "category": "Student Internship Fee",
            "title": "Web Development Intern - WFH",
            "declared_company": "CodeNext Technologies",
            "contact_email": "codenext.careers@gmail.com",
            "ground_truth": 1,
            "text": """Summer web development internship for college students. Work from home with stipend Rs 25000.
Learn HTML, CSS, React on live client projects. Direct selection without technical interview!
A mandatory training and cloud server setup charge of Rs 3,500 must be paid upfront before starting.
Certificate and placement guarantee provided upon fee payment."""
        },

        # 2. Task & Social Media Rating / Review Scams
        {
            "id": "SCAM_06",
            "category": "Task & Review Scam",
            "title": "YouTube Video Like & Subscribe Assistant",
            "declared_company": "",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Earn Rs 2000 to Rs 5000 daily by simply watching and liking YouTube videos!
Part time online work from home for students, housewives, and job seekers.
100% genuine daily income transferred directly to UPI / Google Pay.
Contact HR manager immediately on Telegram: https://t.me/hr_priya_tasks.
Initial security deposit of Rs 1000 required to activate your task dispatcher dashboard."""
        },
        {
            "id": "SCAM_07",
            "category": "Task & Review Scam",
            "title": "Google Maps Hotel Reviewer",
            "declared_company": "Global Hospitality Media",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Urgent hiring: 5-Star Hotel Rating Assistant. Give positive reviews and ratings on Google Maps.
Payout: Rs 200 per review, earn up to Rs 6,000 daily.
No experience required. Work on WhatsApp and Telegram.
To unlock VIP merchant level tasks, recharge your account with Rs 3,000 initially.
Payout guaranteed within 10 minutes of task completion."""
        },
        {
            "id": "SCAM_08",
            "category": "Task & Review Scam",
            "title": "E-Commerce Product Rating Agent",
            "declared_company": "Shopee Merchant Services",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Work from home part time. Help merchants boost product ratings and order volume.
Guaranteed daily income of Rs 3500 working only 1 hour per day.
Selected without interview. Instant joining bonus of Rs 500.
Send message to our Telegram supervisor @shopee_merchant_task to get your registration link.
Initial deposit required to begin product order cycle."""
        },

        # 3. Data Entry / Typing / SMS Work-From-Home Scams
        {
            "id": "SCAM_09",
            "category": "Data Entry Bait",
            "title": "Data Entry Operator at TCS",
            "declared_company": "TCS",
            "contact_email": "hr.tcs.recruiter@gmail.com",
            "ground_truth": 1,
            "text": """URGENT HIRING: Data entry operator at TCS!
Earn Rs 45000 per week working from home 2 hours a day. No experience required.
Direct selection without interview! Only 3 seats left - offer expires within 24 hours.
To confirm your slot, a refundable security deposit of Rs 1500 is required for training kit.
Send your CV on WhatsApp: +91 9876543210 or email hr.tcs.recruiter@gmail.com."""
        },
        {
            "id": "SCAM_10",
            "category": "Data Entry Bait",
            "title": "Offline Form Filling Work From Home",
            "declared_company": "Apex Data Corp",
            "contact_email": "apex.data.filling@yahoo.com",
            "ground_truth": 1,
            "text": """Earn Rs 30,000 to Rs 60,000 per month doing simple English form filling work at home.
No internet needed during typing. 100% accuracy not compulsory.
Direct appointment without test or interview.
Courier dispatch charge for data CD and legal agreement is Rs 2,200 to be paid upfront via PhonePe."""
        },
        {
            "id": "SCAM_11",
            "category": "Data Entry Bait",
            "title": "SMS Sending Part-Time Job",
            "declared_company": "",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Send 100 SMS daily from your mobile phone and earn Rs 1500 daily.
Work anytime from anywhere. Pursuing students and freshers welcome.
Guaranteed weekly salary of Rs 10,500.
Pay initial registration fee of Rs 750 to receive customer phone numbers list.
Contact on WhatsApp: +91 9988776655."""
        },
        {
            "id": "SCAM_12",
            "category": "Data Entry Bait",
            "title": "Handwriting & Notebook Typing Job",
            "declared_company": "National Education Press",
            "contact_email": "press.notebooks@hotmail.com",
            "ground_truth": 1,
            "text": """Convert handwritten books into MS Word documents. Simple copy-paste and typing.
Payment: Rs 50 per page. Earn Rs 40,000 monthly.
Immediate hiring, spot selection.
Refundable security deposit of Rs 1800 required before books are sent to your home address."""
        },

        # 4. Corporate Impersonation & Free Webmail Scams
        {
            "id": "SCAM_13",
            "category": "Corporate Impersonation",
            "title": "Customer Support Executive - Amazon India",
            "declared_company": "Amazon",
            "contact_email": "amazon.recruitment.india@gmail.com",
            "ground_truth": 1,
            "text": """Amazon India is urgently hiring 200 remote customer care representatives.
Salary: Rs 55,000 per month + laptop provided by Amazon.
Immediate joining! Direct selection based on resume.
A processing charge of Rs 2,500 is required for background verification and courier delivery of your company laptop.
Contact HR manager directly at amazon.recruitment.india@gmail.com or WhatsApp +91 8877665544."""
        },
        {
            "id": "SCAM_14",
            "category": "Corporate Impersonation",
            "title": "Software Engineer Trainee - Infosys",
            "declared_company": "Infosys",
            "contact_email": "hr.infosys.onboarding@yahoo.com",
            "ground_truth": 1,
            "text": """Congratulations! Your profile has been shortlisted for Software Engineer Trainee at Infosys Mysore.
Package: 8.5 LPA. No further rounds of interview needed.
Offer letter valid for 48 hours only.
To confirm acceptance, candidates must pay a document verification fee of Rs 4,999 to our authorized recruitment partner account."""
        },
        {
            "id": "SCAM_15",
            "category": "Corporate Impersonation",
            "title": "Cloud Operations Associate - Google India",
            "declared_company": "Google",
            "contact_email": "google.hr.talent@gmail.com",
            "ground_truth": 1,
            "text": """Google India remote hiring drive. Cloud Operations Associate openings in Bangalore and Hyderabad.
Competitive compensation of 14 LPA with work from home allowance.
Direct selection for 2024, 2025, and 2026 graduates.
Pay Rs 3500 for candidate assessment kit and training portal credentials before interview schedule."""
        },
        {
            "id": "SCAM_16",
            "category": "Corporate Impersonation",
            "title": "Business Analyst - Deloitte",
            "declared_company": "Deloitte",
            "contact_email": "deloitte.careers.desk@outlook.com",
            "ground_truth": 1,
            "text": """Deloitte India invites applications for remote Business Analyst positions.
Salary: Rs 85,000 per month.
Shortlisted candidates must deposit Rs 5,000 as refundable interview gate pass fee.
Send payment receipt to deloitte.careers.desk@outlook.com."""
        },

        # 5. Overpayment / Cheque Cashing / Equipment Advance Scams
        {
            "id": "SCAM_17",
            "category": "Cheque Overpayment Scheme",
            "title": "Executive Personal Assistant (Remote)",
            "declared_company": "Global Ventures LLC",
            "contact_email": "hr@throwam.com",
            "ground_truth": 1,
            "text": """We are seeking a trustworthy Virtual Assistant to handle scheduling and office procurement.
Salary: $4,500 per month.
We will mail you a company cashier's check of $6,000. Deposit the check into your bank account, purchase home office equipment from our approved vendor, and wire the remainder back to us via Western Union or MoneyGram."""
        },
        {
            "id": "SCAM_18",
            "category": "Cheque Overpayment Scheme",
            "title": "Remote Administrative Clerk",
            "declared_company": "Horizon Holdings",
            "contact_email": "admin@mailinator.com",
            "ground_truth": 1,
            "text": """Immediate hiring for Remote Administrative Clerk.
Generous pay of $35 per hour.
A company check will be issued to your name to buy your home office kit. Cash our check, keep your first week advance salary, and transfer the remaining balance to our vendor via Bitcoin or USDT."""
        },

        # 6. Premature Identity / Banking Theft Scams
        {
            "id": "SCAM_19",
            "category": "Identity Harvesting",
            "title": "Immediate Spot Hiring - Office Coordinator",
            "declared_company": "Sunlight Logistics",
            "contact_email": "recruitment@sunlight-logistics.xyz",
            "ground_truth": 1,
            "text": """Immediate hiring without interview! You have been selected as Office Coordinator.
Salary: Rs 35,000 per month.
To release your appointment letter today, send your Aadhaar card copy, PAN card, bank account number with IFSC, and cancelled cheque immediately on WhatsApp."""
        },
        {
            "id": "SCAM_20",
            "category": "Identity Harvesting",
            "title": "Banking Document Verification Specialist",
            "declared_company": "Reliable Finance Desk",
            "contact_email": "careers@reliable-loans.biz",
            "ground_truth": 1,
            "text": """Urgent opening for document processing assistants.
To verify your employment eligibility, share your net banking login mobile number and submit the verification OTP received on your phone.
Failure to share OTP within 15 minutes will cancel your job offer."""
        },

        # 7. Crypto / Forex / Arbitrage Work Scams
        {
            "id": "SCAM_21",
            "category": "Crypto / Investment Scheme",
            "title": "Crypto Trading Assistant (Work From Home)",
            "declared_company": "Binance Global Partners",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Earn 100 USDT to 500 USDT daily from home assisting our crypto trading desk.
No financial experience needed. 100% guaranteed daily return.
Must connect your crypto wallet and make an initial deposit of $200 USDT to activate trade signals.
Reach our investment manager on Telegram: t.me/crypto_earning_signals."""
        },
        {
            "id": "SCAM_22",
            "category": "Crypto / Investment Scheme",
            "title": "Foreign Exchange Arbitrage Operator",
            "declared_company": "Apex Forex Exchange",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Part time forex data operator. Work 30 minutes daily on your phone.
Earn 15% commission on all currency swaps.
Transfer funds via Binance or Western Union to initiate demo account trading privileges."""
        },

        # 8. Artificial Urgency / Pressure Tactics Scams
        {
            "id": "SCAM_23",
            "category": "High Pressure Scam",
            "title": "Urgent Opening: Airport Ground Staff",
            "declared_company": "SkyHigh Aviation",
            "contact_email": "skyhigh.aviation.hr@gmail.com",
            "ground_truth": 1,
            "text": """Urgent hiring for Airport Ground Staff and Baggage Handlers.
Salary: Rs 42,000 per month + uniform.
Direct selection without interview! Only 2 seats left in your city. Offer expires in 6 hours! Act fast!
Pay uniform and gate security pass charge of Rs 2,800 to confirm your seat immediately."""
        },
        {
            "id": "SCAM_24",
            "category": "High Pressure Scam",
            "title": "Railway Ticket Booking Clerk (Contract)",
            "declared_company": "Railways",
            "contact_email": "indian.railway.desk@yahoo.com",
            "ground_truth": 1,
            "text": """Indian Railways contractual hiring for Ticket Booking Operator.
Salary: Rs 38,000 per month. No exam or written test required. Direct joining today!
Medical fitness fee of Rs 2,100 must be deposited within 3 hours to secure your joining date."""
        },

        # 9. Campus Ambassador / Pyramid Student Scams
        {
            "id": "SCAM_25",
            "category": "Student Pyramid Scheme",
            "title": "Campus Ambassador & Student Leader",
            "declared_company": "Youth Connect Foundation",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Be your college Campus Ambassador! Earn up to Rs 50,000 per month pocket money.
Work involves branding, promotion, and onboarding other pursuing students.
To become an official verified ambassador, pay a one-time enrollment fee of Rs 1,500 for your ambassador kit and t-shirt."""
        },
        {
            "id": "SCAM_26",
            "category": "Student Pyramid Scheme",
            "title": "Student Marketing Partner (WFH)",
            "declared_company": "InnoBrand Network",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Make more than your pocket money working online.
Part-time marketing opportunity for college students. Good stipend (3000-25000).
Marketing intern certificate and letter of recommendation guaranteed.
Pay initial deposit of 3000 to start your promotional tasks."""
        },

        # 10. Overseas / Visa Scam
        {
            "id": "SCAM_27",
            "category": "Visa & Immigration Scam",
            "title": "Hotel Staff - Canada / Dubai Placement",
            "declared_company": "Global Overseas Recruiters",
            "contact_email": "canada.visaprocess@gmail.com",
            "ground_truth": 1,
            "text": """Immediate hiring for Hotel Receptionists and Waiters in Canada and Dubai.
Salary: $3,800 CAD per month with free accommodation and food.
No IELTS required. Selected without interview.
Send registration charge and visa processing fee of Rs 15,000 to initiate work permit paperwork."""
        },
        {
            "id": "SCAM_28",
            "category": "Visa & Immigration Scam",
            "title": "Warehouse Worker - Singapore / Malaysia",
            "declared_company": "AsiaPacific Placements",
            "contact_email": "singapore.jobs.agency@yahoo.com",
            "ground_truth": 1,
            "text": """Singapore port warehouse workers urgently required.
Earn Rs 1,20,000 per month. Free air ticket and work pass.
Pay nominal screening fee of Rs 7,500 initially before document submission. Contact on WhatsApp."""
        },

        # 11. Work From Home Packaging Scam
        {
            "id": "SCAM_29",
            "category": "Packaging Scam",
            "title": "Pen & Candle Packaging Home Work",
            "declared_company": "Domestic Craft India",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Simple work from home pen assembly and packaging job.
Earn Rs 800 daily, Rs 24000 monthly.
Raw materials will be delivered to your doorstep free of cost.
Pay refundable security deposit of Rs 1200 for material safety before dispatch."""
        },

        # 12. Captcha Solving Scam
        {
            "id": "SCAM_30",
            "category": "Captcha Scam",
            "title": "Online Captcha Entry Operator",
            "declared_company": "FastType Services",
            "contact_email": "",
            "ground_truth": 1,
            "text": """Solve simple 4-letter captchas and earn Rs 15,000 to Rs 35,000 per month.
No skills or qualification needed. Instant payout.
Pay software activation fee of Rs 999 to start solving captchas on our portal."""
        },

        # =====================================================================
        # LEGITIMATE POSTINGS (ground_truth = 0)
        # =====================================================================
        # 1. Tech & Engineering Roles
        {
            "id": "LEGIT_01",
            "category": "Corporate Tech",
            "title": "Senior Backend Engineer",
            "declared_company": "Stripe",
            "contact_email": "recruiting@stripe.com",
            "ground_truth": 0,
            "text": """We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.
Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.
Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.
Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance, and 25 days paid time off.
To apply, submit your resume on our careers portal at https://stripe.com/jobs or contact recruiting@stripe.com."""
        },
        {
            "id": "LEGIT_02",
            "category": "Corporate Tech",
            "title": "Software Development Engineer II",
            "declared_company": "Amazon",
            "contact_email": "aws-careers@amazon.com",
            "ground_truth": 0,
            "text": """Amazon Web Services (AWS) is looking for an SDE II to build scalable cloud storage infrastructure in Seattle, WA.
Key Responsibilities: Architect distributed microservices, write clean Java/C++ code, and mentor junior developers.
Basic Qualifications: Bachelor's degree in Computer Science, 3+ years professional software development experience.
Compensation includes competitive base salary, Amazon restricted stock units (RSUs), and comprehensive health benefits.
Apply online at https://amazon.jobs."""
        },
        {
            "id": "LEGIT_03",
            "category": "Corporate Tech",
            "title": "Site Reliability Engineer",
            "declared_company": "Google",
            "contact_email": "google-recruiting@google.com",
            "ground_truth": 0,
            "text": """Google Site Reliability Engineering (SRE) team in Sunnyvale, CA is hiring.
Role: Manage the performance, uptime, and latency of Google Cloud infrastructure.
Requirements: Experience in Linux system internals, networking protocols, and scripting in Python or Go.
Interview process: Initial recruiter screen, technical phone interview, followed by 4 virtual on-site rounds.
Apply directly via https://careers.google.com."""
        },
        {
            "id": "LEGIT_04",
            "category": "Corporate Tech",
            "title": "Frontend Engineer (React / TypeScript)",
            "declared_company": "Razorpay",
            "contact_email": "talent@razorpay.com",
            "ground_truth": 0,
            "text": """Razorpay is hiring Frontend Engineers in Bangalore (Hybrid).
You will build intuitive payment dashboards used by millions of merchants.
Requirements: 2-5 years experience with React, TypeScript, state management (Redux/Zustand), and web accessibility standards.
Benefits: Group medical insurance, wellness allowance, flexible leave policy.
To apply, visit https://razorpay.com/jobs."""
        },
        {
            "id": "LEGIT_05",
            "category": "Corporate Tech",
            "title": "DevOps / Infrastructure Engineer",
            "declared_company": "Microsoft",
            "contact_email": "jobs@microsoft.com",
            "ground_truth": 0,
            "text": """Join the Azure Core Infrastructure team at Microsoft Hyderabad.
Responsibilities: Design CI/CD pipelines using GitHub Actions and Terraform, monitor Kubernetes clusters.
Qualifications: B.Tech in CS/IT, 3+ years experience with Docker, Kubernetes, and Azure cloud infrastructure.
Apply through Microsoft Careers: https://careers.microsoft.com."""
        },

        # 2. Legitimate Student Internships & Campus Roles
        {
            "id": "LEGIT_06",
            "category": "Student Internship (Legit)",
            "title": "Software Engineering Intern - Summer 2026",
            "declared_company": "Google",
            "contact_email": "university-recruiting@google.com",
            "ground_truth": 0,
            "text": """Software Engineering Intern - Summer 2026.
Company: Google (google.com). Locations: Bangalore or Hyderabad.
Requirements: Currently pursuing a BS or MS degree in Computer Science or related technical field.
Experience with Python, Java, or C++. Strong problem solving and data structures skills.
Benefits: Monthly stipend of INR 85,000, free meals, mentorship from senior engineers, and certificate upon completion.
To apply, submit your resume on our official careers portal: https://careers.google.com/jobs or contact university-recruiting@google.com."""
        },
        {
            "id": "LEGIT_07",
            "category": "Student Internship (Legit)",
            "title": "Marketing Intern - Summer Program",
            "declared_company": "Zomato",
            "contact_email": "campus-hiring@zomato.com",
            "ground_truth": 0,
            "text": """Marketing Intern at Zomato.
We are looking for enthusiastic college students for a 3-month summer internship in Gurgaon.
Responsibilities: Help execute brand campaigns, manage campus activations, and conduct market research.
Requirements: Currently enrolled in an undergraduate or postgraduate degree. Strong written communication skills.
Benefits: Fixed monthly stipend of INR 25,000, certificate of completion, and letter of recommendation based on performance.
To apply, send your resume and portfolio through our official careers page at https://zomato.com/careers."""
        },
        {
            "id": "LEGIT_08",
            "category": "Student Internship (Legit)",
            "title": "Data Science Intern",
            "declared_company": "Swiggy",
            "contact_email": "university@swiggy.in",
            "ground_truth": 0,
            "text": """Swiggy is hiring Data Science Interns for our Bangalore headquarters.
Duration: 6 months full-time.
Work with our machine learning team on delivery routing algorithms, demand forecasting, and recommendation systems.
Qualifications: Pursuing degree in Computer Science, Statistics, or Data Science. Proficiency in Python and SQL.
Monthly stipend: INR 40,000. Apply at https://careers.swiggy.com."""
        },
        {
            "id": "LEGIT_09",
            "category": "Student Internship (Legit)",
            "title": "Product Design Intern",
            "declared_company": "Flipkart",
            "contact_email": "design-interns@flipkart.com",
            "ground_truth": 0,
            "text": """Flipkart Design Studio is seeking Product Design Interns for summer 2026.
Focus on user journey mapping, wireframing, and Figma prototyping for e-commerce shopping workflows.
Eligibility: Enrolled in Bachelor's or Master's in Design (B.Des / M.Des / HCI).
Stipend: INR 45,000 per month.
Submit your portfolio link via the Flipkart careers portal at https://flipkartcareers.com."""
        },
        {
            "id": "LEGIT_10",
            "category": "Student Internship (Legit)",
            "title": "Graduate Trainee Engineer - Campus Drive",
            "declared_company": "Tata Consultancy Services",
            "contact_email": "campus.talent@tcs.com",
            "ground_truth": 0,
            "text": """TCS National Qualifier Test (NQT) for 2026 Batch Graduates.
Role: Graduate Trainee Engineer across Digital and Prime tracks.
Eligibility: B.E. / B.Tech / M.E. / M.Tech / MCA students.
Selection process: Online cognitive test, technical coding interview, and HR round.
Official communications are conducted solely through the TCS NextStep portal (https://nextstep.tcs.com).
TCS never asks for any money or deposit from candidates at any stage of recruitment."""
        },

        # 3. Non-Tech Corporate & Professional Roles
        {
            "id": "LEGIT_11",
            "category": "Corporate Non-Tech",
            "title": "Human Resources Specialist",
            "declared_company": "Deloitte",
            "contact_email": "talentacquisition@deloitte.com",
            "ground_truth": 0,
            "text": """Deloitte India is seeking an HR Talent Acquisition Specialist in Hyderabad.
Responsibilities: End-to-end recruitment lifecycle, stakeholder management, and diversity hiring initiatives.
Qualifications: MBA in HR with 2-4 years of corporate recruiting experience.
Comprehensive healthcare coverage, parental leave, and competitive base salary.
Apply directly at https://deloitte.com/careers."""
        },
        {
            "id": "LEGIT_12",
            "category": "Corporate Non-Tech",
            "title": "Financial Analyst - FP&A",
            "declared_company": "HDFC Bank",
            "contact_email": "careers@hdfcbank.com",
            "ground_truth": 0,
            "text": """HDFC Bank is hiring a Financial Analyst for its Mumbai corporate office.
Responsibilities: Variance analysis, quarterly financial forecasting, and management reporting.
Requirements: CA / CFA or MBA in Finance with 1-3 years of analytical experience in banking.
Official application portal: https://www.hdfcbank.com/careers."""
        },
        {
            "id": "LEGIT_13",
            "category": "Corporate Non-Tech",
            "title": "Senior Content Strategist",
            "declared_company": "Canva",
            "contact_email": "jobs@canva.com",
            "ground_truth": 0,
            "text": """Canva is looking for a Senior Content Strategist to shape our brand voice in India.
Responsibilities: Develop content frameworks, lead editorial planning, and collaborate with product marketing teams.
Requirements: 5+ years of content marketing experience at high-growth consumer or SaaS brands.
Flexible hybrid work policy, competitive equity grants, and generous learning budget.
Apply via Canva Careers: https://canva.com/careers."""
        },
        {
            "id": "LEGIT_14",
            "category": "Corporate Non-Tech",
            "title": "Supply Chain Operations Lead",
            "declared_company": "Unilever",
            "contact_email": "careers.india@unilever.com",
            "ground_truth": 0,
            "text": """Hindustan Unilever Limited (HUL) is hiring a Supply Chain Lead in Mumbai.
Overview: Optimize warehouse fulfillment, reduce inventory transit times, and manage 3PL partners.
Qualifications: Engineering graduate with MBA in Supply Chain or Operations. 3-5 years relevant experience.
Apply through Unilever Global Portal: https://unilever.com/careers."""
        },
        {
            "id": "LEGIT_15",
            "category": "Corporate Non-Tech",
            "title": "Corporate Legal Counsel",
            "declared_company": "Infosys",
            "contact_email": "legal-hiring@infosys.com",
            "ground_truth": 0,
            "text": """Infosys Legal Department is hiring an Associate Legal Counsel in Bangalore.
Scope: Drafting and negotiating international software licensing agreements, vendor contracts, and IP protection.
Requirements: LL.B. with 4+ years experience in corporate or commercial law.
Submit application via https://infosys.com/careers."""
        },

        # 4. Tricky / Hard Negatives (Contains words like 'fee', 'immediate', 'pocket', etc.)
        {
            "id": "LEGIT_16",
            "category": "Tricky Hard-Negative",
            "title": "FinTech Product Manager - Zero Fee Trading",
            "declared_company": "Groww",
            "contact_email": "careers@groww.in",
            "ground_truth": 0,
            "text": """Groww is hiring a Senior Product Manager to lead our Zero Fee Mutual Funds and Stock Broking platform.
You will build seamless investor onboarding experiences and optimize payment gateway routing.
Requirements: 4+ years of product management in fintech or banking. Strong analytical capabilities.
Competitive compensation with significant ESOPs. Apply on https://groww.in/careers."""
        },
        {
            "id": "LEGIT_17",
            "category": "Tricky Hard-Negative",
            "title": "Healthcare App Developer - Out-of-Pocket Expense Tracker",
            "declared_company": "Practo",
            "contact_email": "engineering@practo.com",
            "ground_truth": 0,
            "text": """Practo is developing tools to help patients track out-of-pocket medical expenses and insurance copays.
We need a Senior iOS Developer (Swift) in Bangalore.
Role: Implement secure biometric storage, offline SQLite sync, and interactive spending charts.
Qualifications: 3+ years native iOS development. Apply via https://practo.com/careers."""
        },
        {
            "id": "LEGIT_18",
            "category": "Tricky Hard-Negative",
            "title": "Immediate Joining: Incident Response Specialist",
            "declared_company": "Wipro",
            "contact_email": "cybersecurity@wipro.com",
            "ground_truth": 0,
            "text": """Wipro Cybersecurity Practice has immediate openings for SOC Incident Response Analysts due to customer expansion.
Roles require formal background verification and a multi-round technical assessment on SIEM tools (Splunk / QRadar).
Salary: INR 12 LPA. Notice period of 15 days or immediate availability preferred.
Apply through Wipro Careers: https://careers.wipro.com."""
        },
        {
            "id": "LEGIT_19",
            "category": "Tricky Hard-Negative",
            "title": "Research Assistant - Computational Biology",
            "declared_company": "Indian Institute of Science",
            "contact_email": "bio-admissions@iisc.ac.in",
            "ground_truth": 0,
            "text": """IISc Bangalore invites applications for a Research Assistant position in Molecular Biophysics.
Eligibility: Post-graduate degree in Bioinformatics, Biotechnology, or allied sciences with valid GATE/NET score.
Monthly fellowship: INR 31,000 + HRA as per central government norms.
No application fee is charged by the Institute. Official notification available at https://iisc.ac.in."""
        },
        {
            "id": "LEGIT_20",
            "category": "Tricky Hard-Negative",
            "title": "Customer Success Manager - Payment Gateway Fees Desk",
            "declared_company": "Cashfree Payments",
            "contact_email": "recruiting@cashfree.com",
            "ground_truth": 0,
            "text": """Cashfree Payments is seeking a Customer Success Manager to advise enterprise clients on interchange fee optimization and settlement reconciliation.
Requirements: 3 years experience in B2B fintech or SaaS account management.
Location: Bangalore (Hybrid).
Apply on https://cashfree.com/careers."""
        },

        # 5. Remote & Freelance Legitimate Postings
        {
            "id": "LEGIT_21",
            "category": "Remote Legitimate",
            "title": "Technical Writer - Open Source Documentation",
            "declared_company": "Red Hat",
            "contact_email": "careers@redhat.com",
            "ground_truth": 0,
            "text": """Red Hat is looking for a Remote Technical Writer to document Kubernetes and OpenShift features.
Responsibilities: Create developer tutorials, API documentation, and configuration guides using Markdown and Git.
Requirements: 2+ years writing software documentation. Familiarity with cloud-native technologies.
Benefits: 100% remote flexibility, competitive salary, comprehensive healthcare.
Apply at https://redhat.com/jobs."""
        },
        {
            "id": "LEGIT_22",
            "category": "Remote Legitimate",
            "title": "Online English Tutor",
            "declared_company": "Cambly",
            "contact_email": "support@cambly.com",
            "ground_truth": 0,
            "text": """Cambly connects English language learners worldwide with native and fluent speakers.
Work whenever you want with flexible scheduling.
Pay rate: $10.20 to $12.00 per hour delivered weekly via PayPal.
Requirements: Strong communication skills, quiet environment, webcam, and stable internet. No fees or equipment purchase required to start tutoring.
Sign up at https://cambly.com/tutors."""
        },
        {
            "id": "LEGIT_23",
            "category": "Remote Legitimate",
            "title": "Curriculum Developer - Computer Science",
            "declared_company": "Khan Academy",
            "contact_email": "jobs@khanacademy.org",
            "ground_truth": 0,
            "text": """Khan Academy is hiring a Remote Curriculum Specialist in Computer Science.
Collaborate with educators to design introductory programming lessons, exercises, and teacher guides.
Qualifications: Experience teaching high school or undergraduate computer science.
Non-profit salary structure with full medical benefits and generous retirement match.
Apply at https://khanacademy.org/careers."""
        },
        {
            "id": "LEGIT_24",
            "category": "Remote Legitimate",
            "title": "Remote Data Annotator - NLP & LLM Training",
            "declared_company": "Cohere",
            "contact_email": "annotators@cohere.com",
            "ground_truth": 0,
            "text": """Cohere is hiring native language specialists to review and evaluate Large Language Model outputs for safety, fluency, and accuracy.
Flexible part-time hourly contract (15-20 hours/week).
Pay: $22 per hour.
Requires passing an initial language assessment test. No upfront software or registration charges.
Apply through our official careers portal at https://cohere.com/careers."""
        },
        {
            "id": "LEGIT_25",
            "category": "Remote Legitimate",
            "title": "Product Support Specialist - India Shift",
            "declared_company": "Notion",
            "contact_email": "careers@makenotion.com",
            "ground_truth": 0,
            "text": """Notion is seeking a remote Product Support Specialist based in India.
Help users troubleshoot workspace permissions, formulas, and API integrations via Zendesk and in-app chat.
Requirements: 1-3 years in technical SaaS support, exceptional empathy, and clear written English.
Compensation includes competitive base salary and equity.
Apply on https://notion.so/careers."""
        },

        # 6. Public Sector / Institutional Postings
        {
            "id": "LEGIT_26",
            "category": "Institutional / PSU",
            "title": "Junior Research Fellow - Renewable Energy",
            "declared_company": "IIT Madras",
            "contact_email": "recruitment@iitm.ac.in",
            "ground_truth": 0,
            "text": """IIT Madras Project Recruitment for Junior Research Fellow in Solar Energy Storage.
Eligibility: First-class M.Tech in Chemical or Mechanical Engineering with valid GATE score.
Stipend: INR 37,000 per month + 24% HRA.
Official application form available at https://iitm.ac.in. Candidates should not send money to any unauthorized third party."""
        },
        {
            "id": "LEGIT_27",
            "category": "Institutional / PSU",
            "title": "Management Trainee - Finance & Accounts",
            "declared_company": "State Bank of India",
            "contact_email": "careers@sbi.co.in",
            "ground_truth": 0,
            "text": """State Bank of India (SBI) Central Recruitment & Promotion Department.
Recruitment of Probationary Officers (PO).
Selection through preliminary online examination, main examination, psychometric test, and interview.
Applications accepted exclusively through official bank portal at https://sbi.co.in/careers."""
        },
        {
            "id": "LEGIT_28",
            "category": "Institutional / PSU",
            "title": "Scientific Officer / Engineer",
            "declared_company": "BARC",
            "contact_email": "rect@barc.gov.in",
            "ground_truth": 0,
            "text": """Bhabha Atomic Research Centre (BARC) invites applications for Orientation Course for Engineering Graduates and Science Postgraduates.
Selection through OCES/DGFS exam.
Stipend during training: INR 55,000 per month.
Notification published on employment news and https://barc.gov.in."""
        },
        {
            "id": "LEGIT_29",
            "category": "Institutional / PSU",
            "title": "System Analyst - Digital Governance",
            "declared_company": "National Informatics Centre",
            "contact_email": "support@nic.in",
            "ground_truth": 0,
            "text": """National Informatics Centre (NIC) recruitment for Scientific and Technical staff.
Positions: Scientist B and Scientific/Technical Assistant A.
Examination conducted through National Institute of Electronics and Information Technology (NIELIT).
Apply on official portal: https://calicut.nielit.in."""
        },
        {
            "id": "LEGIT_30",
            "category": "Institutional / PSU",
            "title": "Medical Officer - Occupational Health",
            "declared_company": "Tata Motors",
            "contact_email": "careers@tatamotors.com",
            "ground_truth": 0,
            "text": """Tata Motors is hiring a Factory Medical Officer for its Pune manufacturing plant.
Requirements: MBBS with Associate Fellow of Industrial Health (AFIH) certificate and 2+ years clinical experience.
Manage plant health center, periodic employee wellness screenings, and first-aid protocols.
Apply via https://tatamotors.com/careers."""
        },
    ]
    return samples


def run_benchmark():
    print("=" * 70)
    print("[+] GENERATING BENCHMARK EVALUATION DATASET")
    print("=" * 70)

    samples = build_benchmark_samples()
    df = pd.DataFrame(samples)
    os.makedirs(os.path.dirname(BENCHMARK_CSV_PATH), exist_ok=True)
    df.to_csv(BENCHMARK_CSV_PATH, index=False)
    print(f"Dataset successfully created at: {BENCHMARK_CSV_PATH}")
    print(f"Total benchmark samples: {len(df)} (Scam: {(df['ground_truth'] == 1).sum()}, Legit: {(df['ground_truth'] == 0).sum()})")

    print("\n" + "=" * 70)
    print("[*] RUNNING EVALUATION SUITE ACROSS ALL BENCHMARK SAMPLES")
    print("=" * 70)

    results = []
    start_time = time.time()

    for idx, row in df.iterrows():
        analysis = aggregator.analyse(
            text=row["text"],
            declared_company=row["declared_company"],
            contact_email=row["contact_email"]
        )

        score = analysis["risk_score"]
        level = analysis["risk_level"]
        ml_prob = analysis["ml_fraud_probability"]
        rule_penalty = analysis["rule_penalty"]
        rule_flags_cnt = analysis["rule_flag_count"]
        domain_flags_cnt = analysis["domain_flag_count"]
        verdict = analysis["verdict"]

        # Classification decision based on risk score:
        # Scam if risk_score >= 51 (Suspicious / High Risk); Legitimate if risk_score <= 50 (Safe / Low Risk)
        # For strict High Risk evaluation: risk_score >= 76
        pred_label = 1 if score >= 51 else 0
        pred_high_risk = 1 if score >= 76 else 0

        results.append({
            "id": row["id"],
            "category": row["category"],
            "title": row["title"],
            "ground_truth": row["ground_truth"],
            "risk_score": score,
            "risk_level": level,
            "pred_label": pred_label,
            "pred_high_risk": pred_high_risk,
            "ml_fraud_prob": ml_prob,
            "rule_penalty": rule_penalty,
            "rule_flags_cnt": rule_flags_cnt,
            "domain_flags_cnt": domain_flags_cnt,
            "verdict": verdict,
            "top_signals": analysis.get("ml_top_signals", []),
            "red_flags": [f["title"] for f in analysis.get("red_flags", [])],
        })

    elapsed = round(time.time() - start_time, 2)
    res_df = pd.DataFrame(results)

    # ── Evaluation Metrics ──────────────────────────────────────────────────
    y_true = res_df["ground_truth"]
    y_pred = res_df["pred_label"]
    y_scores = res_df["risk_score"] / 100.0

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    auc = roc_auc_score(y_true, y_scores)

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    # Score statistics
    scam_scores = res_df[res_df["ground_truth"] == 1]["risk_score"]
    legit_scores = res_df[res_df["ground_truth"] == 0]["risk_score"]

    print(f"\nCompleted analysis of {len(res_df)} postings in {elapsed}s.")

    print("\n" + "=" * 70)
    print("[+] BENCHMARK PERFORMANCE REPORT")
    print("=" * 70)
    print(f"  * Overall Accuracy : {acc:.2%}")
    print(f"  * Precision (Scam) : {prec:.2%}")
    print(f"  * Recall (Scam)    : {rec:.2%}")
    print(f"  * F1-Score (Scam)  : {f1:.4f}")
    print(f"  * ROC-AUC Score    : {auc:.4f}")
    print(f"\n  * Confusion Matrix :")
    print(f"      True Negatives (Legit identified as Safe/Low Risk) : {tn} / 30")
    print(f"      False Positives (Legit wrongly flagged as Scam)   : {fp} / 30")
    print(f"      False Negatives (Scams missed)                    : {fn} / 30")
    print(f"      True Positives (Scams correctly caught)           : {tp} / 30")

    print("\n" + "-" * 70)
    print("[*] RISK SCORE SEPARATION")
    print("-" * 70)
    print(f"  * Scam Postings Average Score : {scam_scores.mean():.1f} / 100 (Min: {scam_scores.min()}, Max: {scam_scores.max()})")
    print(f"  * Legit Postings Average Score: {legit_scores.mean():.1f} / 100 (Min: {legit_scores.min()}, Max: {legit_scores.max()})")
    print(f"  * Score Separation Delta      : +{scam_scores.mean() - legit_scores.mean():.1f} points")

    print("\n" + "-" * 70)
    print("[*] BREAKDOWN BY CATEGORY")
    print("-" * 70)
    cat_summary = res_df.groupby(["category", "ground_truth"]).agg(
        Count=("risk_score", "count"),
        AvgScore=("risk_score", "mean"),
        MinScore=("risk_score", "min"),
        MaxScore=("risk_score", "max"),
        Correct=("pred_label", lambda p: (p == res_df.loc[p.index, "ground_truth"]).sum())
    ).reset_index()

    for _, row in cat_summary.iterrows():
        label_str = "SCAM" if row["ground_truth"] == 1 else "LEGIT"
        accuracy_pct = (row["Correct"] / row["Count"]) * 100
        print(f"  [{label_str:5}] {row['category']:32} | N={row['Count']:2} | Avg Score: {row['AvgScore']:5.1f} | Accuracy: {accuracy_pct:5.1f}%")

    # High Risk classification rate on scams
    high_risk_scams = res_df[(res_df["ground_truth"] == 1) & (res_df["risk_level"] == "High Risk")]
    print(f"\n  • High Risk Detection Rate on Scams: {len(high_risk_scams)}/{len(scam_scores)} ({len(high_risk_scams)/len(scam_scores):.1%})")

    # Save detailed evaluation output
    out_json_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "benchmark_evaluation_results.json"
    )
    out_json_path = os.path.normpath(out_json_path)
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "total_samples": len(res_df),
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(auc, 4),
                "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
                "scam_avg_score": round(float(scam_scores.mean()), 1),
                "legit_avg_score": round(float(legit_scores.mean()), 1),
                "score_separation": round(float(scam_scores.mean() - legit_scores.mean()), 1),
            },
            "detailed_results": results
        }, f, indent=2)

    print(f"\nDetailed evaluation results saved to: {out_json_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
