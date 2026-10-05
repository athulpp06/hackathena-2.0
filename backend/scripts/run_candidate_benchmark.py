"""
Candidate Resume Integrity Benchmark Evaluation Suite (Day 2 - Module 6).
Evaluates the candidate fraud detection engine across 30 realistic resumes
(15 Authentic, 15 Fabricated / Timeline Anomaly cases).
Computes Accuracy, Precision, Recall, F1, ROC-AUC, and Risk Score Separation.
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.candidate.aggregator import analyse_candidate_resume


def build_candidate_benchmark_dataset():
    samples = [
        # ── 15 AUTHENTIC CANDIDATE RESUMES ──────────────────────────────────
        {
            "id": "AUTH_01",
            "category": "Authentic Entry Level",
            "title": "Junior Backend Developer - NIT Graduate",
            "ground_truth": 0,
            "text": (
                "Pooja Hegde\n"
                "Email: pooja.hegde@gmail.com | Phone: +91 9876543201\n"
                "LinkedIn: https://linkedin.com/in/pooja-hegde-dev | GitHub: https://github.com/pooja-h\n\n"
                "EDUCATION\n"
                "B.Tech in Computer Science\n"
                "National Institute of Technology Surathkal\n"
                "2018 - 2022 | CGPA: 8.4\n\n"
                "WORK EXPERIENCE\n"
                "Software Engineer - Infosys Limited\n"
                "Aug 2022 - Present\n"
                "- Developed enterprise Java REST APIs using Spring Boot and PostgreSQL.\n\n"
                "Software Intern - Infosys Limited\n"
                "Jan 2022 - Jun 2022\n"
                "- Built data ingestion pipelines using Python and Docker.\n\n"
                "SKILLS\n"
                "Java, Spring Boot, Python, PostgreSQL, Docker, Git\n\n"
                "REFERENCES\n"
                "Suresh Rao, Delivery Manager at Infosys\n"
                "Email: suresh_rao@infosys.com\n"
            ),
        },
        {
            "id": "AUTH_02",
            "category": "Authentic Experienced",
            "title": "Senior Frontend Engineer - IIT Graduate",
            "ground_truth": 0,
            "text": (
                "Kunal Joshi\n"
                "Email: kunal.joshi@gmail.com | Phone: +91 9811223344\n"
                "LinkedIn: https://linkedin.com/in/kunal-joshi-ui\n\n"
                "EDUCATION\n"
                "B.Tech in Electrical Engineering\n"
                "IIT Roorkee\n"
                "2015 - 2019 | CGPA: 7.9\n\n"
                "WORK EXPERIENCE\n"
                "Senior Frontend Engineer - Razorpay\n"
                "Jan 2022 - Present\n"
                "- Engineered merchant dashboard components using React and TypeScript.\n\n"
                "Frontend Engineer - Swiggy\n"
                "Jul 2019 - Dec 2021\n"
                "- Built real-time order tracking UI using React and Redux.\n\n"
                "SKILLS\n"
                "JavaScript, TypeScript, React, Next.js, HTML, CSS, Git\n\n"
                "REFERENCES\n"
                "Ankit Singhal, Engineering Manager at Swiggy\n"
                "Email: ankit.singhal@swiggy.in\n"
            ),
        },
        {
            "id": "AUTH_03",
            "category": "Authentic Full Stack",
            "title": "Full Stack Engineer - BITS Pilani",
            "ground_truth": 0,
            "text": (
                "Rohan Deshmukh\n"
                "Email: rohan.deshmukh@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/rohan-deshmukh-bits\n\n"
                "EDUCATION\n"
                "B.E. in Computer Science\n"
                "BITS Pilani\n"
                "2016 - 2020 | CGPA: 8.8\n\n"
                "WORK EXPERIENCE\n"
                "Software Engineer - Stripe\n"
                "Jan 2022 - Present\n"
                "- Built transaction routing microservices in Go and Kafka.\n\n"
                "Associate Engineer - Flipkart\n"
                "Jun 2020 - Dec 2021\n"
                "- Built payment gateway integrations using Java and MySQL.\n\n"
                "SKILLS\n"
                "Go, Java, Python, Kafka, Redis, PostgreSQL, Docker\n"
            ),
        },
        {
            "id": "AUTH_04",
            "category": "Authentic Cloud Architect",
            "title": "Cloud Architect with AWS & Azure Certs",
            "ground_truth": 0,
            "text": (
                "Amitabh Saxena\n"
                "Email: amitabh.saxena@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/amitabh-saxena-cloud\n\n"
                "EDUCATION\n"
                "B.Tech in Computer Engineering\n"
                "Delhi Technological University (DTU)\n"
                "2012 - 2016 | CGPA: 8.2\n\n"
                "WORK EXPERIENCE\n"
                "Cloud Architect - Wipro Technologies\n"
                "Mar 2020 - Present\n"
                "- Migrated on-premise infrastructure to AWS cloud.\n\n"
                "Senior DevOps Engineer - Cognizant\n"
                "Jul 2016 - Feb 2020\n"
                "- Deployed Kubernetes clusters and Terraform modules.\n\n"
                "CERTIFICATIONS\n"
                "- AWS Certified Solutions Architect Associate\n"
                "- Certified Kubernetes Administrator (CKA)\n"
            ),
        },
        {
            "id": "AUTH_05",
            "category": "Authentic Mobile Developer",
            "title": "Mobile App Developer - Flutter & Kotlin",
            "ground_truth": 0,
            "text": (
                "Sneha Nair\n"
                "Email: sneha.nair@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/sneha-nair-mobile\n\n"
                "EDUCATION\n"
                "BCA in Computer Applications\n"
                "Christ University Bangalore\n"
                "2017 - 2020 | CGPA: 8.6\n\n"
                "WORK EXPERIENCE\n"
                "Mobile Developer - Zomato\n"
                "Jan 2021 - Present\n"
                "- Developed delivery partner app using Flutter and Kotlin.\n\n"
                "SKILLS\n"
                "Flutter, Kotlin, Swift, Android, iOS, Firebase\n"
            ),
        },
        {
            "id": "AUTH_06",
            "category": "Authentic Data Scientist",
            "title": "Machine Learning Engineer - IIIT Hyderabad",
            "ground_truth": 0,
            "text": (
                "Aditya Roy\n"
                "Email: aditya.roy@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/aditya-roy-ml\n\n"
                "EDUCATION\n"
                "M.Tech in Artificial Intelligence\n"
                "IIIT Hyderabad\n"
                "2019 - 2021 | CGPA: 9.1\n\n"
                "B.Tech in Computer Science\n"
                "Osmania University\n"
                "2015 - 2019 | CGPA: 8.5\n\n"
                "WORK EXPERIENCE\n"
                "Machine Learning Engineer - Fractal Analytics\n"
                "Jul 2021 - Present\n"
                "- Trained predictive churn models using PyTorch, Scikit-Learn, and Python.\n"
            ),
        },
        {
            "id": "AUTH_07",
            "category": "Authentic QA Engineer",
            "title": "QA Automation Engineer - Pune University",
            "ground_truth": 0,
            "text": (
                "Deepak Patel\n"
                "Email: deepak.patel@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/deepak-patel-qa\n\n"
                "EDUCATION\n"
                "B.E. in Information Technology\n"
                "Pune University\n"
                "2016 - 2020\n\n"
                "WORK EXPERIENCE\n"
                "QA Engineer - Barclays\n"
                "Aug 2020 - Present\n"
                "- Implemented end-to-end automation test suites in Selenium and Python.\n"
            ),
        },
        {
            "id": "AUTH_08",
            "category": "Authentic Systems Engineer",
            "title": "Linux Systems Engineer - Mumbai University",
            "ground_truth": 0,
            "text": (
                "Kavita Sen\n"
                "Email: kavita.sen@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/kavita-sen-sys\n\n"
                "EDUCATION\n"
                "B.Sc in Computer Science\n"
                "Mumbai University\n"
                "2017 - 2020\n\n"
                "WORK EXPERIENCE\n"
                "Systems Analyst - Tata Consultancy Services (TCS)\n"
                "Nov 2020 - Present\n"
                "- Managed Linux server clusters, bash automation scripts, and monitoring.\n"
            ),
        },
        {
            "id": "AUTH_09",
            "category": "Authentic Intern / Fresh Graduate",
            "title": "Recent Graduate Intern - IIT Madras",
            "ground_truth": 0,
            "text": (
                "Varun Pillai\n"
                "Email: varun.pillai@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/varun-pillai-iitm\n\n"
                "EDUCATION\n"
                "B.Tech in Computer Science\n"
                "IIT Madras\n"
                "2020 - 2024 | CGPA: 9.0\n\n"
                "WORK EXPERIENCE\n"
                "Software Engineering Intern - Google India\n"
                "May 2023 - Jul 2023\n"
                "- Developed telemetry parsing pipeline using C++ and Go.\n"
            ),
        },
        {
            "id": "AUTH_10",
            "category": "Authentic Product Manager",
            "title": "Technical Product Manager - IIM Bangalore",
            "ground_truth": 0,
            "text": (
                "Meera Chawla\n"
                "Email: meera.chawla@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/meera-chawla-pm\n\n"
                "EDUCATION\n"
                "MBA in Technology Management\n"
                "IIM Bangalore\n"
                "2018 - 2020\n\n"
                "B.Tech in Computer Science\n"
                "Punjab Engineering College\n"
                "2013 - 2017\n\n"
                "WORK EXPERIENCE\n"
                "Product Manager - PhonePe\n"
                "Jul 2020 - Present\n"
                "- Spearheaded UPI merchant checkout features handling 15M daily transactions.\n"
            ),
        },
        {
            "id": "AUTH_11",
            "category": "Authentic Cybersecurity Analyst",
            "title": "Security Analyst with CEH",
            "ground_truth": 0,
            "text": (
                "Naveen Gupta\n"
                "Email: naveen.gupta@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/naveen-gupta-sec\n\n"
                "EDUCATION\n"
                "B.Tech in Information Technology\n"
                "Anna University\n"
                "2016 - 2020\n\n"
                "WORK EXPERIENCE\n"
                "Security Analyst - HCL Technologies\n"
                "Jan 2021 - Present\n"
                "- Performed vulnerability assessments and SOC incident triaging.\n\n"
                "CERTIFICATIONS\n"
                "- CEH Ethical Hacker\n"
            ),
        },
        {
            "id": "AUTH_12",
            "category": "Authentic Frontend Lead",
            "title": "Lead UI Developer - 8 Years Experience",
            "ground_truth": 0,
            "text": (
                "Ritu Bansal\n"
                "Email: ritu.bansal@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/ritu-bansal-ui\n\n"
                "EDUCATION\n"
                "B.Tech in Computer Science\n"
                "Thapar Institute of Engineering\n"
                "2012 - 2016\n\n"
                "WORK EXPERIENCE\n"
                "Technical Lead - MakeMyTrip\n"
                "Apr 2021 - Present\n"
                "- Leading frontend engineering team for international flight bookings.\n\n"
                "Software Engineer - Adobe India\n"
                "Jun 2016 - Mar 2021\n"
                "- Developed Creative Cloud web components in React.\n"
            ),
        },
        {
            "id": "AUTH_13",
            "category": "Authentic DevOps Engineer",
            "title": "DevOps Engineer - NIT Warangal",
            "ground_truth": 0,
            "text": (
                "Gaurav Yadav\n"
                "Email: gaurav.yadav@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/gaurav-yadav-devops\n\n"
                "EDUCATION\n"
                "B.Tech in Electronics\n"
                "NIT Warangal\n"
                "2017 - 2021\n\n"
                "WORK EXPERIENCE\n"
                "DevOps Engineer - Delhivery\n"
                "Aug 2021 - Present\n"
                "- Implemented GitOps automated deployments using ArgoCD and Kubernetes.\n"
            ),
        },
        {
            "id": "AUTH_14",
            "category": "Authentic Database Administrator",
            "title": "Database Engineer - PostgreSQL & Oracle",
            "ground_truth": 0,
            "text": (
                "Sunita Menon\n"
                "Email: sunita.menon@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/sunita-menon-db\n\n"
                "EDUCATION\n"
                "MCA in Computer Applications\n"
                "Calicut University\n"
                "2015 - 2018\n\n"
                "WORK EXPERIENCE\n"
                "Database Administrator - Reliance Jio\n"
                "Sep 2018 - Present\n"
                "- Optimized high-volume PostgreSQL and Oracle database instances.\n"
            ),
        },
        {
            "id": "AUTH_15",
            "category": "Authentic Senior Consultant",
            "title": "ERP & Cloud Consultant - Deloitte",
            "ground_truth": 0,
            "text": (
                "Tarun Khanna\n"
                "Email: tarun.khanna@gmail.com\n"
                "LinkedIn: https://linkedin.com/in/tarun-khanna-consult\n\n"
                "EDUCATION\n"
                "B.Tech in Computer Science\n"
                "Manipal Institute of Technology\n"
                "2014 - 2018\n\n"
                "WORK EXPERIENCE\n"
                "Senior Consultant - Deloitte India\n"
                "Jul 2018 - Present\n"
                "- Delivered digital enterprise transformations for banking clients.\n"
            ),
        },

        # ── 15 FABRICATED / FRAUDULENT RESUMES ──────────────────────────────
        {
            "id": "FRAUD_01",
            "category": "Concurrent Full-Time Roles",
            "title": "Dual Full-Time Software Engineer at Amazon & Microsoft",
            "ground_truth": 1,
            "text": (
                "Ramesh Kumar\n"
                "Email: ramesh.kumar@gmail.com\n"
                "EDUCATION\n"
                "B.Tech in Computer Science (2016 - 2020)\n\n"
                "WORK EXPERIENCE\n"
                "Software Engineer - Amazon AWS\n"
                "Jun 2020 - Dec 2023\n"
                "- Built DynamoDB microservices full time.\n\n"
                "Senior Backend Developer - Microsoft Azure\n"
                "Jan 2022 - Aug 2023\n"
                "- Developed Azure microservices full time.\n"
            ),
        },
        {
            "id": "FRAUD_02",
            "category": "Diploma Mill Degree",
            "title": "Counterfeit B.Sc from Almeda University Mill",
            "ground_truth": 1,
            "text": (
                "Suresh Sharma\n"
                "Email: suresh.sharma@yahoo.com\n"
                "EDUCATION\n"
                "Bachelor of Science in Computer Science\n"
                "Almeda University (Life Experience Degree)\n"
                "2019\n\n"
                "WORK EXPERIENCE\n"
                "Lead Architect - Zenith Global\n"
                "Jan 2020 - Present\n"
            ),
        },
        {
            "id": "FRAUD_03",
            "category": "Diploma Mill Degree",
            "title": "Counterfeit MBA from Rochville University Mill",
            "ground_truth": 1,
            "text": (
                "Anita Verma\n"
                "Email: anita.verma@gmail.com\n"
                "EDUCATION\n"
                "MBA in Management\n"
                "Rochville University\n"
                "2018\n\n"
                "WORK EXPERIENCE\n"
                "VP of Engineering - Apex Technologies\n"
                "Mar 2019 - Present\n"
            ),
        },
        {
            "id": "FRAUD_04",
            "category": "Anachronistic Tech Claim",
            "title": "Claiming Kubernetes and Docker in 2008",
            "ground_truth": 1,
            "text": (
                "Vikas Mehra\n"
                "Email: vikas.mehra@gmail.com\n"
                "EDUCATION\n"
                "B.Tech in Computer Science (2004 - 2008)\n\n"
                "WORK EXPERIENCE\n"
                "Senior Systems Engineer - Tech Solutions\n"
                "Jan 2008 - Dec 2012\n"
                "- Managed enterprise Kubernetes clusters and Docker containers.\n"
            ),
        },
        {
            "id": "FRAUD_05",
            "category": "Anachronistic Tech Claim",
            "title": "Claiming 15 Years of Flutter Experience",
            "ground_truth": 1,
            "text": (
                "Pradeep Singh\n"
                "Email: pradeep.singh@gmail.com\n"
                "SUMMARY\n"
                "Mobile Architect with 15 years experience in Flutter application architecture.\n"
                "WORK EXPERIENCE\n"
                "Mobile Lead - Mobile Soft\n"
                "Jan 2019 - Present\n"
            ),
        },
        {
            "id": "FRAUD_06",
            "category": "AI Synthetic CV / Prompt Leakage",
            "title": "ChatGPT Assistant Leakage ('As an AI language model')",
            "ground_truth": 1,
            "text": (
                "Certainly! Here is an optimized professional summary for your resume:\n"
                "As an AI language model, I recommend highlighting your distributed cloud experience.\n"
                "Software Engineer at [Insert Company Name] from 2021 to 2023.\n"
                "Feel free to customize the metrics to suit your target job.\n"
            ),
        },
        {
            "id": "FRAUD_07",
            "category": "Disposable Reference Email",
            "title": "Reference Email on GuerrillaMail Burner Domain",
            "ground_truth": 1,
            "text": (
                "Sunil Narang\n"
                "Email: sunil.narang@gmail.com\n"
                "WORK EXPERIENCE\n"
                "Software Developer - Alpha Systems (2020 - 2023)\n\n"
                "REFERENCES\n"
                "Kunal Sen, HR Director at Tata Consultancy Services\n"
                "Email: hr.tcs.kunal@guerrillamail.com\n"
            ),
        },
        {
            "id": "FRAUD_08",
            "category": "Disposable Candidate Email",
            "title": "Candidate Primary Contact on Mailinator Burner Domain",
            "ground_truth": 1,
            "text": (
                "Manish Tyagi\n"
                "Email: manish.tyagi@mailinator.com\n"
                "LinkedIn: https://linkedin.com/in/your-profile\n"
                "EDUCATION\n"
                "B.Tech (2017 - 2021)\n\n"
                "WORK EXPERIENCE\n"
                "Software Developer - Global Corp (2021 - Present)\n"
            ),
        },
        {
            "id": "FRAUD_09",
            "category": "Timeline Paradox",
            "title": "Senior Architect Role Starting Before High School Completion",
            "ground_truth": 1,
            "text": (
                "Harish Chandra\n"
                "Email: harish.chandra@gmail.com\n"
                "EDUCATION\n"
                "Senior Secondary School (12th Grade) - 2018 - 2020\n"
                "B.Tech in Computer Science - 2020 - 2024\n\n"
                "WORK EXPERIENCE\n"
                "Senior Solutions Architect - Oracle India\n"
                "Jan 2017 - May 2021\n"
                "- Led enterprise architecture across Asia-Pacific.\n"
            ),
        },
        {
            "id": "FRAUD_10",
            "category": "Unfeasible Career Velocity",
            "title": "Sudden Leap from Intern to Chief Technology Officer in 2 Months",
            "ground_truth": 1,
            "text": (
                "Aakash Aggarwal\n"
                "Email: aakash.aggarwal@gmail.com\n"
                "EDUCATION\n"
                "B.Tech (2018 - 2022)\n\n"
                "WORK EXPERIENCE\n"
                "Chief Technology Officer - Mega Tech Holdings\n"
                "Aug 2022 - Present\n"
                "- Directing 200 engineers worldwide.\n\n"
                "Summer Intern - Startup Hub\n"
                "May 2022 - Jul 2022\n"
                "- Tested login forms.\n"
            ),
        },
        {
            "id": "FRAUD_11",
            "category": "Education Chronology Paradox",
            "title": "High School Completion Listed After University Graduation",
            "ground_truth": 1,
            "text": (
                "Pawan Khera\n"
                "Email: pawan.khera@gmail.com\n"
                "EDUCATION\n"
                "B.Tech in Information Technology - 2014 - 2018\n"
                "High School / 12th Grade - 2019 - 2021\n\n"
                "WORK EXPERIENCE\n"
                "Software Engineer - Tech Cloud (2018 - Present)\n"
            ),
        },
        {
            "id": "FRAUD_12",
            "category": "Counterfeit Accreditation Mill",
            "title": "Belford University with Universal Accreditation",
            "ground_truth": 1,
            "text": (
                "Gautam Gambhir\n"
                "Email: gautam.gambhir@yahoo.com\n"
                "EDUCATION\n"
                "Bachelor of Technology in Software\n"
                "Belford University\n"
                "Universal Accreditation Commission Certified\n"
                "2018\n\n"
                "WORK EXPERIENCE\n"
                "Software Lead - Omega Solutions (2019 - Present)\n"
            ),
        },
        {
            "id": "FRAUD_13",
            "category": "Triple Concurrent Roles",
            "title": "3 Concurrent Full-Time Jobs Across Capgemini, HCL & Wipro",
            "ground_truth": 1,
            "text": (
                "Rohit Sethi\n"
                "Email: rohit.sethi@gmail.com\n"
                "EDUCATION\n"
                "B.Tech (2015 - 2019)\n\n"
                "WORK EXPERIENCE\n"
                "Senior Developer - Capgemini\n"
                "Jan 2020 - Dec 2023\n\n"
                "Senior Software Engineer - HCL Tech\n"
                "Feb 2020 - Nov 2023\n\n"
                "Full Stack Engineer - Wipro\n"
                "Mar 2020 - Oct 2023\n"
            ),
        },
        {
            "id": "FRAUD_14",
            "category": "Future Dated Experience",
            "title": "Post-Dated Career Dates in 2032",
            "ground_truth": 1,
            "text": (
                "Simran Kaur\n"
                "Email: simran.kaur@gmail.com\n"
                "EDUCATION\n"
                "B.Tech (2020 - 2024)\n\n"
                "WORK EXPERIENCE\n"
                "Principal Architect - Quantum Cloud\n"
                "Jan 2030 - Dec 2034\n"
                "- Built quantum computing infrastructure.\n"
            ),
        },
        {
            "id": "FRAUD_15",
            "category": "Template Placeholders & Unverified Referees",
            "title": "Unfilled Template with [Insert Company] & Fake References",
            "ground_truth": 1,
            "text": (
                "John Doe\n"
                "Email: john.doe@tempmail.com\n"
                "LinkedIn: https://linkedin.com/in/username\n"
                "GitHub: https://github.com/your-username\n\n"
                "SUMMARY\n"
                "Software Developer with experience at [Insert Company Name].\n\n"
                "WORK EXPERIENCE\n"
                "Software Engineer - [Insert Company Name]\n"
                "Jan 2021 - Dec 2023\n\n"
                "REFERENCES\n"
                "Engineering VP at Google\n"
                "Email: vp.google.referrals@gmail.com\n"
            ),
        },
    ]
    return samples


def run_candidate_benchmark():
    print("=" * 70)
    print("[+] GENERATING CANDIDATE BENCHMARK EVALUATION DATASET")
    print("=" * 70)
    samples = build_candidate_benchmark_dataset()
    df = pd.DataFrame(samples)
    print(f"Total benchmark candidate resumes: {len(df)} (Authentic: {(df['ground_truth'] == 0).sum()}, Fraudulent: {(df['ground_truth'] == 1).sum()})")

    print("\n" + "=" * 70)
    print("[*] RUNNING CANDIDATE EVALUATION SUITE")
    print("=" * 70)

    results = []
    start_time = time.time()

    for idx, row in df.iterrows():
        analysis = analyse_candidate_resume(text=row["text"])
        score = analysis.get("risk_score", 0)
        level = analysis.get("risk_level", "Unknown")
        total_flags = analysis.get("total_anomalies", 0)
        has_critical = analysis.get("has_critical_flags", False)

        # Decision threshold: Fraud if risk_score >= 51 (Suspicious / High Risk)
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
            "total_flags": total_flags,
            "has_critical": has_critical,
        })

    elapsed = time.time() - start_time
    print(f"\nCompleted analysis of {len(df)} candidate resumes in {elapsed:.2f}s.\n")

    res_df = pd.DataFrame(results)

    # Compute Metrics
    y_true = res_df["ground_truth"].values
    y_pred = res_df["pred_label"].values
    scores = res_df["risk_score"].values

    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    roc_auc = roc_auc_score(y_true, scores)
    cm = confusion_matrix(y_true, y_pred)

    tn, fp, fn, tp = cm.ravel()

    fraud_scores = res_df[res_df["ground_truth"] == 1]["risk_score"]
    auth_scores = res_df[res_df["ground_truth"] == 0]["risk_score"]

    print("=" * 70)
    print("[+] CANDIDATE INTEGRITY BENCHMARK PERFORMANCE REPORT")
    print("=" * 70)
    print(f"  * Overall Accuracy : {acc * 100:.2f}%")
    print(f"  * Precision (Fraud): {prec * 100:.2f}%")
    print(f"  * Recall (Fraud)   : {rec * 100:.2f}%")
    print(f"  * F1-Score (Fraud) : {f1:.4f}")
    print(f"  * ROC-AUC Score    : {roc_auc:.4f}")
    print()
    print("  * Confusion Matrix :")
    print(f"      True Negatives (Authentic recognized as Safe/Low Risk): {tn} / {len(auth_scores)}")
    print(f"      False Positives (Authentic wrongly flagged as Fraud)  : {fp} / {len(auth_scores)}")
    print(f"      False Negatives (Fraudulent resumes missed)           : {fn} / {len(fraud_scores)}")
    print(f"      True Positives (Fraudulent resumes caught)            : {tp} / {len(fraud_scores)}")
    print()
    print("-" * 70)
    print("[*] CANDIDATE RISK SCORE SEPARATION")
    print("-" * 70)
    print(f"  * Fraudulent Resumes Average Score : {fraud_scores.mean():.1f} / 100 (Min: {fraud_scores.min()}, Max: {fraud_scores.max()})")
    print(f"  * Authentic Resumes Average Score  : {auth_scores.mean():.1f} / 100 (Min: {auth_scores.min()}, Max: {auth_scores.max()})")
    print(f"  * Score Separation Delta           : +{fraud_scores.mean() - auth_scores.mean():.1f} points")
    print()
    print("-" * 70)
    print("[*] BREAKDOWN BY CATEGORY")
    print("-" * 70)
    for cat, group in res_df.groupby("category"):
        cat_type = "FRAUD" if group["ground_truth"].iloc[0] == 1 else "AUTH "
        cat_acc = (group["ground_truth"] == group["pred_label"]).mean() * 100
        avg_s = group["risk_score"].mean()
        print(f"  [{cat_type}] {cat:<40} | N={len(group):>2} | Avg Score: {avg_s:>5.1f} | Accuracy: {cat_acc:>5.1f}%")

    assert acc == 1.0, f"Benchmark accuracy expected 1.0, got {acc}"
    print("\n[SUCCESS] Candidate Benchmark passed with 100% accuracy!")


if __name__ == "__main__":
    run_candidate_benchmark()
