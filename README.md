# 🛡️ LeakedIn — AI-Powered Recruitment Security Platform

> **Hackathena 2.0 Project**  
> An intelligent recruitment fraud detection platform designed to protect job seekers and organizations from recruitment scams, identity theft, and fraudulent job postings.

---

## 📌 Day 1 Focus: Job Posting Scanner

The **Job Posting Scanner** provides an end-to-end fraud analysis pipeline for job offers received via job boards (LinkedIn, Naukri, Indeed), email, WhatsApp, or Telegram.

```
[ Paste Job Posting ]
          │
          ▼
┌──────────────────────────────────────────────┐
│          HYBRID DETECTION ENGINE             │
├──────────────────────┬───────────────────────┤
│  🤖 Machine Learning │  📐 Rule Heuristics   │
│  • TF-IDF N-grams    │  • Upfront Fee Scams  │
│  • Balanced Model    │  • WhatsApp/Telegram  │
│  • 98.9% ROC-AUC     │  • Personal Emails    │
│  • 91% Scam Recall   │  • Urgency & Pressure │
└──────────────────────┴───────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────┐
│  🌐 Contact & Domain Verification            │
│  • Free email vs Corporate identity mismatch │
│  • Disposable or suspicious contact channels │
└──────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────┐
│  📊 Unified Risk Score (0 - 100) & Verdict   │
│  🔍 Explainable Red Flags with Text Spans    │
└──────────────────────────────────────────────┘
```

---

## 🚀 Detection Architecture

LeakedIn uses a **hybrid multi-layer approach** to maximize detection accuracy while ensuring complete explainability:

### 1. Machine Learning Layer (`backend/app/detector/ml.py`)
- **Dataset**: Trained on the benchmark **EMSCAD (Employment Scam Aegean Dataset)** containing **17,880 real and fraudulent job postings**.
- **Vectorization**: Sublinear TF-IDF with unigrams and bigrams (15,000 features).
- **Classification**: Calibrated class-weighted linear model with probability scoring.
- **Evaluation Performance**:
  - **Accuracy**: `98%`
  - **ROC-AUC**: `0.9894`
  - **Scam Recall**: `91%`
  - **Scam F1-Score**: `0.8418`

### 2. Rule-Based Heuristic Layer (`backend/app/detector/rules.py`)
- **Financial Fraud**: Detects upfront registration fees, security deposits, training kit payments, cheque-cashing scams, and cryptocurrency requests.
- **Channel Hijacking**: Detects recruiters refusing corporate communication in favor of personal WhatsApp/Telegram accounts.
- **Email Domain Spoofing**: Detects recruiters claiming to represent Fortune 500 / tech firms while communicating from free webmail (`@gmail.com`, `@yahoo.com`, `@hotmail.com`).
- **Urgency & Coercion**: Detects pressure tactics (*"offer expires in 2 hours"*, *"no interview required"*, *"send Aadhaar/PAN immediately"*).
- **Span Extraction**: Computes character start/end offsets so the UI can highlight exact suspicious phrases in the original text.

### 3. Unified Risk Scoring (`backend/app/detector/aggregator.py`)
Combines ML confidence, severity-weighted rule infractions, and domain checks into a calibrated score:
- **0 – 25**: 🟢 **Safe / Legitimate**
- **26 – 50**: 🟡 **Low Risk / Caution Advised**
- **51 – 75**: 🟠 **Suspicious / Probable Scam**
- **76 – 100**: 🔴 **High Risk / Critical Scam**

---

## 📂 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py         # POST /analyse-job endpoint
│   │   ├── detector/
│   │   │   ├── ml.py             # ML inference wrapper
│   │   │   ├── rules.py          # Heuristics & text span highlighter
│   │   │   ├── verifier.py       # Domain & contact validation
│   │   │   └── aggregator.py     # Unified risk score engine
│   │   └── main.py               # FastAPI application entrypoint
│   ├── models/
│   │   └── job_detector_model.joblib  # Serialized trained model (~750 KB)
│   └── scripts/
│       └── train_pipeline.py     # Dataset download & model training pipeline
├── data/                         # Benchmark dataset (gitignored)
│   └── fake_job_postings.csv
├── frontend/                     # Modern demo-ready web interface
├── requirements.txt              # Project dependencies
└── README.md
```

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.10+ installed
- PowerShell / Bash

### 2. Setup Virtual Environment & Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Train or Retrain the Model (Optional)
The pre-trained model is already saved in `backend/models/`. To retrain from scratch:
```powershell
python backend/scripts/train_pipeline.py
```

### 4. Run the API Server
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

---

## 📡 API Specification

### 1. `POST /api/v1/analyse-job` (Raw Text Input)

**Request Body (`application/json`):**
```json
{
  "text": "Full job description text...",
  "company_name": "Optional declared company name",
  "contact_email": "Optional contact email"
}
```

### 2. `POST /api/v1/analyse-image` (Image / Screenshot OCR Input)

**Request (`multipart/form-data`):**
* `file`: Image or screenshot (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`)
* `company_name`: Optional declared company name (`Form` field)
* `contact_email`: Optional contact email (`Form` field)

**Response (`application/json`):**
```json
{
  "risk_score": 88,
  "risk_level": "High Risk",
  "verdict": "Critical scam indicators detected. Do NOT respond or pay anything.",
  "ml_score_pct": 92,
  "ocr_extracted_text": "Extracted text from screenshot...",
  "ocr_engine": "Windows Native OCR",
  "ocr_char_count": 422,
  "red_flags": [
    {
      "category": "Financial Demand",
      "severity": "CRITICAL",
      "title": "Upfront Fee / Registration Charge",
      "matched_text": "security deposit of Rs 1500",
      "start": 124,
      "end": 148
    }
  ],
  "domain_flags": [
    {
      "type": "FREE_WEBMAIL",
      "severity": "HIGH",
      "title": "Free Webmail Used for Corporate Contact"
    }
  ],
  "recommendations": [
    "Never pay any upfront registration fee or security deposit for a job.",
    "Verify the recruiter via the company's official careers portal."
  ]
}
```

---

## 🗺️ Roadmap
- [x] **Day 1 - Module 1**: Benchmark dataset acquisition & ML model training.
- [x] **Day 1 - Module 2**: Rule-based scam detection & character span highlighter.
- [x] **Day 1 - Module 3**: Hybrid Risk Aggregator & `POST /api/v1/analyse-job` API.
- [x] **Day 1 - Module 4**: Company and contact domain verification.
- [x] **Day 1 - Module 5**: Interactive frontend UI with live text highlighting, screenshot OCR & clipboard paste (`Ctrl+V`).
- [ ] **Day 2**: Candidate profile verification & resume scanner module.

