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

    print(f"Class distribution: {y.value_counts().to_dict()} (0: Real, 1: Scam)")
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
            max_features=15000,
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True
        )),
        ('clf', LogisticRegression(
            class_weight='balanced',
            C=2.0,
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
