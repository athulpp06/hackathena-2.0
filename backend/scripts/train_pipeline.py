import os
import sys
import urllib.request
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score, f1_score
import joblib

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DATA_PATH = os.path.join(DATA_DIR, "fake_job_postings.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_PATH = os.path.join(MODELS_DIR, "job_detector_model.joblib")
DATASET_URL = "https://raw.githubusercontent.com/Cindyalifia/bangkit-project-1/master/fake_job_postings.csv"

def download_dataset():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_PATH) or os.path.getsize(DATA_PATH) < 1000000:
        print(f"Downloading dataset from {DATASET_URL}...")
        urllib.request.urlretrieve(DATASET_URL, DATA_PATH)
        print(f"Downloaded dataset to {DATA_PATH} ({os.path.getsize(DATA_PATH)} bytes)")
    else:
        print(f"Dataset already exists at {DATA_PATH}")

def load_and_preprocess():
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"Dataset shape: {df.shape}")

    # Text columns that give signals
    text_cols = ['title', 'company_profile', 'description', 'requirements', 'benefits']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('')
        else:
            df[col] = ''

    # Combine text fields into a single comprehensive feature text
    df['combined_text'] = (
        df['title'] + " " +
        df['company_profile'] + " " +
        df['description'] + " " +
        df['requirements'] + " " +
        df['benefits']
    ).str.lower()

    # Target: 'fraudulent' is 1 for fake/scam, 0 for legitimate
    y = df['fraudulent'].astype(int)
    X = df['combined_text']

    # Augment with modern scam archetypes (student internships, upfront fees, pocket money, task scams)
    # and legitimate internship postings so contemporary fraud patterns are recognized by ML.
    modern_scams = [
        "marketing intern for pursuing students part-time job earn more than your pocket money immediate hiring just pay 5000 initially work from home branding promotion good stipend 2500-21000 marketing intern certificate free internship opportunity letter of recommendation to apply fill name college branch phone email state language",
        "student internship opportunity work from home earn pocket money initial payment required 3000 registration fee deposit stipend 5000 15000 marketing intern branding promotion to apply send details on whatsapp",
        "immediate hiring part time job for college students earn pocket money just pay 2000 upfront registration fee for training kit marketing and promotion intern daily stipend direct selection no interview",
        "pursuing students work from home marketing intern earn pocket money pay 5000 initially for registration certificate and letter of recommendation free internship stipend 20000",
        "hiring interns work from home earn 10000 to 30000 monthly registration charge 1500 refundable security deposit direct selection fill name branch college phone to apply",
        "part time online job for students earn daily pocket money typing form filling just pay 1000 initially for software activation key immediate selection work from home",
        "summer internship 2026 for pursuing students earn pocket money marketing branding promotion deposit 2500 for training kit guaranteed certificate and stipend 15000",
        "urgent hiring marketing intern students can earn pocket money just pay 4000 initially for registration security fee work from home stipend 20000 to apply fill name college phone",
        "online task job part time earn 2000 5000 daily watch videos like products initial deposit required 3000 on upi telegram recruiter immediate hiring",
        "data entry job work from home earn 25000 weekly no experience direct selection pay 1500 registration fee refundable within 48 hours send cv on whatsapp",
        "student work from home internship marketing assistant earn more than pocket money pay 5000 initially joining kit certificate guaranteed stipend",
        "hr intern required for pursuing students work from home earn stipend 12000 pay 1500 initially for offer letter registration charges direct selection",
        "graphic designer intern part time job for students just pay 2500 upfront for design software license and certification immediate hiring no interview",
        "campus ambassador internship earn 50000 per month just pay 1000 enrollment fee upfront to join marketing student community",
        "freelance content writer part time for college students earn daily income pay nominal fee of 500 to start tasks telegram hr",
        "work from home copy paste data entry job earn 30000 monthly initial training deposit 2000 refundable after 15 days",
        "hotel review task job earn 2500 per day telegram work from home recharge wallet with 2000 to unlock vip commission tasks",
        "youtube video like and subscribe job earn 150 to 500 per task initial security deposit required 2000 via google pay",
        "urgent opening for students work from home daily payout direct selection without interview just pay 3500 initially",
        "social media marketing intern earn 2500-20000 stipend free certificate pay 1999 initially for registration portal access",
        "business development intern pursuing students pocket money pay 5000 initially branding promotion stipend 21000 to apply fill name college",
        "digital marketing intern spot offer no test needed initial payment 3000 for training materials work from home 2 hours daily",
        "part time customer service remote job pay 2500 initially for id card and appointment letter dispatch",
        "earn more than your pocket money part time marketing internship immediate hiring just pay upfront 5000 free certificate and lor",
        "student job alert earn 1000 daily simple typing work pay registration fee 750 on phonepe direct joining letter",
    ]

    modern_legit = [
        "software engineering intern summer 2026 google bangalore pursuing bs or ms degree in computer science python java c++ data structures competitive monthly stipend 85000 inr free meals mentorship apply on careers portal",
        "marketing intern zomato gurgaon full time internship for college students brand campaigns social media market research monthly stipend 25000 inr certificate of completion apply on careers page",
        "data science intern swiggy bangalore machine learning python sql exploratory data analysis monthly stipend 35000 inr apply on official portal",
        "backend developer intern stripe remote api microservices python go databases competitive stipend health coverage apply via careers portal",
        "business analyst intern tata consultancy services campus recruitment aptitude test technical interview hr interview formal offer letter official domain email",
        "product design intern flipkart bangalore ui ux design figma user research stipend 40000 inr per month apply with portfolio at careers.flipkart.com",
        "human resources intern infosys mysore campus hiring student talent acquisition employee engagement official application via careers portal",
        "summer research intern iit bombay undergraduate students fellowship grant laboratory experiments academic mentorship no application fee",
        "finance intern deloitte hyderabad financial modeling accounting excel analytics competitive stipend health benefits formal interview process",
        "content marketing intern fintech startup remote blog posts copywriting seo 20000 inr monthly stipend submit samples via linkedin",
        "frontend engineer intern razorpay react typescript web development bangalore hybrid 45000 inr monthly stipend",
        "operations intern uber india supply operations driver support analytics excel sql competitive compensation official careers portal",
    ]

    aug_scam_s = pd.Series([s.lower() for s in modern_scams])
    aug_scam_y = pd.Series([1] * len(modern_scams))

    aug_legit_s = pd.Series([s.lower() for s in modern_legit])
    aug_legit_y = pd.Series([0] * len(modern_legit))

    X = pd.concat([X, aug_scam_s, aug_legit_s], ignore_index=True)
    y = pd.concat([y, aug_scam_y, aug_legit_y], ignore_index=True)

    print(f"Class distribution (with modern augmentations): {y.value_counts().to_dict()} (0: Real, 1: Scam)")
    return X, y

def train():
    download_dataset()
    X, y = load_and_preprocess()

    print("Splitting dataset (80% train, 20% test, stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Building and training TF-IDF + LogisticRegression pipeline...")
    # Using TF-IDF with unigrams + bigrams and class-weighted Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=20000,
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True
        )),
        ('clf', LogisticRegression(
            class_weight='balanced',
            C=2.5,
            max_iter=1000,
            random_state=42
        ))
    ])

    pipeline.fit(X_train, y_train)

    print("Evaluating model performance on test set...")
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print("\n--- Model Performance Report ---")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Scam"]))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    print(f"Scam F1-Score: {f1_score(y_test, y_pred):.4f}")

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nModel saved successfully to {MODEL_PATH}")

    # Quick test
    sample_scam = "Work from home! Earn $5000 per week. Data entry assistant. No experience required. Registration fee required to start. Contact on WhatsApp."
    sample_real = "Senior Software Engineer. Requirements: 5+ years experience in Python, AWS, Docker. Strong algorithmic skills. Full benefits package including 401k and health insurance."

    p_scam = pipeline.predict_proba([sample_scam])[0, 1]
    p_real = pipeline.predict_proba([sample_real])[0, 1]

    print("\n--- Sanity Test ---")
    print(f"Sample Scam Job -> Fraud Probability: {p_scam:.2%}")
    print(f"Sample Real Job -> Fraud Probability: {p_real:.2%}")

if __name__ == '__main__':
    train()
