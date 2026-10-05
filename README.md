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
│  • Balanced Model    │  • Student Bait Scams │
│  • 99.1% ROC-AUC     │  • WhatsApp/Telegram  │
│  • 90% Scam Recall   │  • Urgency & Pressure │
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
- **Dataset**: Trained on the benchmark **EMSCAD (Employment Scam Aegean Dataset)** containing **17,880 real and fraudulent job postings**, augmented with modern student internship and recruitment fraud templates.
- **Vectorization**: Sublinear TF-IDF with unigrams and bigrams (20,000 features).
- **Classification**: Calibrated class-weighted linear model with probability scoring.
- **Evaluation Performance**:
  - **Accuracy**: `99%`
  - **ROC-AUC**: `0.9908`
  - **Scam Recall**: `90%`
  - **Scam F1-Score**: `0.8719`

### 2. Rule-Based Heuristic Layer (`backend/app/detector/rules.py`)
- **Financial Fraud & Upfront Demands**: Detects upfront registration fees, security deposits, training kit payments, cheque-cashing scams, and cryptocurrency requests.
- **Student & Internship Exploitation**: Detects "pocket money" bait targeting college students, contradictory "free internship" claims with upfront fees, and wide suspicious stipend ranges.
- **Suspicious Application Forms**: Detects informal fill-in chat questionnaires (Name, College, Branch, Phone) distributed on messaging platforms.
- **Channel Hijacking**: Detects recruiters refusing corporate communication in favor of personal WhatsApp/Telegram accounts.
- **Email Domain Spoofing**: Detects recruiters claiming to represent corporate/MNC entities while using consumer webmail (`@gmail.com`, `@yahoo.com`).
- **Urgency & Coercion**: Detects pressure tactics (*"offer expires in 24 hours"*, *"direct selection without interview"*, *"immediate hiring"*).
- **Span Extraction**: Computes character start/end offsets so the UI can highlight exact suspicious phrases in the original text.

### 3. Unified Risk Scoring (`backend/app/detector/aggregator.py`)
Combines calibrated ML confidence, heuristic rule violations, and domain verification using multi-signal fusion with critical guardrails:
- **Deterministic Guardrails**: Any critical fraud indicator (e.g. upfront fee/payment demand) automatically triggers High Risk (>=85-95) with critical warning.
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
│   │   │   └── routes.py         # POST /analyse-job & /analyse-image endpoints
│   │   ├── detector/
│   │   │   ├── ml.py             # ML inference wrapper (v2.0)
│   │   │   ├── rules.py          # Heuristics & text span highlighter
│   │   │   ├── verifier.py       # Domain & contact validation
│   │   │   └── aggregator.py     # Multi-signal risk fusion & guardrails
│   │   ├── ocr.py                # Multi-modal native OCR engine
│   │   └── main.py               # FastAPI application entrypoint
│   ├── models/
│   │   └── job_detector_model.joblib  # Serialized trained model
│   └── scripts/
│       ├── train_pipeline.py           # Model training pipeline
│       └── run_benchmark_evaluation.py # 60-sample evaluation suite
├── data/                         # Datasets (gitignored)
│   ├── fake_job_postings.csv
│   └── evaluation_benchmark_dataset.csv
├── frontend/                     # Modern web application UI
├── tests/                        # Automated test suites
├── requirements.txt              # Project dependencies
└── README.md
```

---

## 🔬 Benchmark Evaluation Suite

LeakedIn includes an independent evaluation suite of **60 realistic recruitment postings** (30 Scam, 30 Legit) covering modern student internship fee schemes, task review traps, corporate impersonation, tricky hard-negatives, and public sector positions.

### Performance on Benchmark (N = 60)
- **Overall Accuracy**: `100.00%`
- **Precision (Scam)**: `100.00%`
- **Recall (Scam)**: `100.00%`
- **F1-Score (Scam)**: `1.0000`
- **ROC-AUC Score**: `1.0000`
- **Average Scam Risk Score**: `87.7 / 100` (90% categorized as **High Risk**)
- **Average Legit Risk Score**: `10.4 / 100` (All categorized as **Safe / Low Risk**)
- **Risk Score Separation Delta**: `+77.3 points`
- **Hard-Negative Robustness**: Legitimate jobs containing context words like *"zero fee"*, *"immediate opening"*, or *"out-of-pocket expenses"* averaged only `6.8 / 100` with **zero false positives**.

To run the benchmark suite:
```powershell
python backend/scripts/run_benchmark_evaluation.py
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
The pre-trained model is already saved in `backend/models/`. To retrain:
```powershell
python backend/scripts/train_pipeline.py
```

### 4. Run Automated Tests
```powershell
python tests/test_aggregator.py
python tests/test_rules.py
python tests/test_ml.py
python tests/test_api.py
python tests/test_verifier.py
```

### 5. Run the API Server & Web UI
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
- Web Application UI: [http://localhost:8000/](http://localhost:8000/)
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

