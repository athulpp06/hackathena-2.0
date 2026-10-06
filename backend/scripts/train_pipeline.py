import datetime
import hashlib
import json
import os
import urllib.request

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DATA_PATH = os.path.join(DATA_DIR, "fake_job_postings.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_PATH = os.path.join(MODELS_DIR, "job_detector_model.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "metadata.json")
DATASET_URL = "https://raw.githubusercontent.com/Cindyalifia/bangkit-project-1/master/fake_job_postings.csv"


def download_dataset():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_PATH) or os.path.getsize(DATA_PATH) < 1000000:
        print(f"Downloading dataset from {DATASET_URL}...")
        urllib.request.urlretrieve(DATASET_URL, DATA_PATH)
        print(f"Downloaded dataset to {DATA_PATH} ({os.path.getsize(DATA_PATH)} bytes)")
    else:
        print(f"Dataset already exists at {DATA_PATH}")


def _dataset_hash(path: str) -> str:
    """Compute MD5 hash of dataset for provenance tracking."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_and_preprocess():
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"Dataset shape: {df.shape}")

    text_cols = ['title', 'company_profile', 'description', 'requirements', 'benefits']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('')
        else:
            df[col] = ''

    df['combined_text'] = (
        df['title'] + " " +
        df['company_profile'] + " " +
        df['description'] + " " +
        df['requirements'] + " " +
        df['benefits']
    ).str.lower()

    y = df['fraudulent'].astype(int)
    X = df['combined_text']

    print(f"Class distribution: {y.value_counts().to_dict()} (0: Real, 1: Scam)")
    return X, y


def load_real_world_seeds() -> tuple[pd.Series, pd.Series]:
    """Load synthetic training seeds for augmentation (strictly train_seeds)."""
    train_seeds_dir = os.path.join(DATA_DIR, "real_world", "train_seeds")
    dfs = []
    if os.path.exists(train_seeds_dir):
        for f in os.listdir(train_seeds_dir):
            if f.endswith(".csv"):
                dfs.append(pd.read_csv(os.path.join(train_seeds_dir, f)))
    if not dfs:
        return pd.Series([], dtype=str), pd.Series([], dtype=int)
    combined = pd.concat(dfs).dropna(subset=["text", "label"])
    return combined["text"].str.lower(), combined["label"].astype(int)


def train():
    download_dataset()
    X_emscad, y_emscad = load_and_preprocess()

    print("Splitting dataset (80% train, 20% test, stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_emscad, y_emscad, test_size=0.2, random_state=42, stratify=y_emscad
    )

    # Augment training set with real-world seeds (never touches EMSCAD test split)
    X_rw, y_rw = load_real_world_seeds()
    if len(X_rw) > 0:
        print(f"Augmenting training data with {len(X_rw)} real-world seed samples...")
        X_train = pd.concat([X_train, X_rw], ignore_index=True)
        y_train = pd.concat([y_train, y_rw], ignore_index=True)

    print("Building and training TF-IDF + Calibrated LogisticRegression pipeline...")
    base_lr = LogisticRegression(
        class_weight='balanced',
        C=2.0,
        max_iter=1000,
        random_state=42
    )

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=15000,
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True
        )),
        ('clf', CalibratedClassifierCV(estimator=base_lr, method='isotonic', cv=5))
    ])

    pipeline.fit(X_train, y_train)

    print("Evaluating model performance on EMSCAD hold-out test set...")
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    classification_report(y_test, y_pred, target_names=["Legitimate", "Scam"], output_dict=True)
    roc = roc_auc_score(y_test, y_proba)
    f1 = f1_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)

    print("\n--- Model Performance Report ---")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Scam"]))
    print(f"ROC-AUC Score: {roc:.4f}")
    print(f"Scam Precision: {prec:.4f}  |  Recall: {rec:.4f}  |  F1: {f1:.4f}")

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    # Save training metadata for model versioning
    metadata = {
        "version": "2.0.0",
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dataset": "EMSCAD + real-world seeds",
        "dataset_hash_md5": _dataset_hash(DATA_PATH),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "real_world_seeds": len(X_rw),
        "model_type": "TF-IDF(15k, 1-2gram, sublinear) + CalibratedClassifierCV(LR, isotonic, cv=5)",
        "metrics": {
            "roc_auc": round(roc, 4),
            "fraud_precision": round(prec, 4),
            "fraud_recall": round(rec, 4),
            "fraud_f1": round(f1, 4),
        },
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {METADATA_PATH}")

    # Sanity test
    sample_scam = "Work from home! Earn Rs 5000 per day. Data entry assistant. No experience required. Registration fee required. Contact on WhatsApp."
    sample_real = "Senior Software Engineer. Requirements: 5+ years experience in Python, AWS, Docker. Strong algorithmic skills. Full benefits including health insurance."

    p_scam = pipeline.predict_proba([sample_scam])[0, 1]
    p_real = pipeline.predict_proba([sample_real])[0, 1]

    print("\n--- Sanity Test ---")
    print(f"Sample Scam Job  -> Fraud Probability: {p_scam:.2%}")
    print(f"Sample Real Job  -> Fraud Probability: {p_real:.2%}")


if __name__ == '__main__':
    train()
