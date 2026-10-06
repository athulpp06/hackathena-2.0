# 🛡️ LeakedIn — AI-Powered Recruitment Security Platform

> **Hackathena 2.0 Project**  
> An intelligent recruitment fraud detection platform designed to protect job seekers from recruitment scams, advance-fee fraud, corporate identity theft, and fraudulent job postings.

---

## 📌 Day 1 Focus: Job Posting Scanner (Job Seeker Shield)

The **Job Posting Scanner** provides an end-to-end fraud analysis pipeline for job offers received via job boards (LinkedIn, Naukri, Indeed), email, WhatsApp, or Telegram.

```
[ Job Text / Image / Screenshot ]
              │
              ▼
┌───────────────────────────────────────────────────────────┐
│  Layer 0: AI Gatekeeper & Relevance Classifier            │
│  • Google Gemini 1.5 Flash Vision / Zero-Config Fallback  │
│  • Rejects recipes, CVs, invoices, and casual chats       │
└─────────────────────────────┬─────────────────────────────┘
                              │ (Verified Employment Ad)
                              ▼
┌───────────────────────────────────────────────────────────┐
│  Layer 1: Calibrated Machine Learning Engine              │
│  • Trained on EMSCAD (17,880 postings) + Student Bait     │
│  • Sublinear TF-IDF (20k features) + Probability scoring  │
│  • 99.1% ROC-AUC | 90% Scam Recall                        │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  Layer 2: Rule-Based Heuristic Engine                     │
│  • Upfront fee / deposit demands & kit charges            │
│  • Student bait ("pocket money", "free internship" trap)  │
│  • Character-level text span extraction for UI highlights │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  Layer 3: Company & Contact Domain Verifier               │
│  • Free webmail used for corporate hiring (@gmail.com)    │
│  • Known company domain mismatch & disposable emails      │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  Unified Risk Score (0 - 100) & Actionable Red Flags      │
└───────────────────────────────────────────────────────────┘
```

---

## 🚀 Detection Architecture

LeakedIn uses a **hybrid multi-layer approach** to maximize detection accuracy while ensuring complete explainability:

### 1. Layer 0: AI Gatekeeper & Relevance Classifier (`backend/app/detector/gatekeeper.py`)
- **Multimodal AI Gatekeeper**: Leverages Google Gemini 1.5 Flash Vision to inspect incoming text or image uploads and confirm relevance to recruitment or employment.
- **Noise Rejection**: Immediately rejects non-recruitment submissions (recipes, utility bills, personal letters, programming tasks) before entering the scoring pipeline.
- **Zero-Config Offline Fallback**: Runs offline keyword heuristics and prompt-injection filters if Gemini API credentials are absent or network requests time out.

### 2. Layer 1: Machine Learning Layer (`backend/app/detector/ml.py`)
- **Dataset**: Trained on the benchmark **EMSCAD (Employment Scam Aegean Dataset)** containing **17,880 real and fraudulent job postings**, augmented with modern student internship and recruitment fraud templates.
- **Vectorization**: Sublinear TF-IDF with unigrams and bigrams (20,000 features).
- **Classification**: Calibrated class-weighted linear model with probability scoring.
- **Evaluation Performance**:
  - **Accuracy**: `99%`
  - **ROC-AUC**: `0.9908`
  - **Scam Recall**: `90%`
  - **Scam F1-Score**: `0.8719`

### 3. Layer 2: Rule-Based Heuristic Layer (`backend/app/detector/rules.py`)
- **Financial Fraud & Upfront Demands**: Detects upfront registration fees, security deposits, training kit payments, cheque-cashing scams, and cryptocurrency requests.
- **Student & Internship Exploitation**: Detects "pocket money" bait targeting college students, contradictory "free internship" claims with upfront fees, and wide suspicious stipend ranges.
- **Equipment & Telegram Managers**: Detects requests to pay for home-office laptops/hardware and unsolicited contact directing applicants to anonymous Telegram managers.
- **Span Extraction**: Computes character start/end offsets so the UI can highlight exact suspicious phrases in the original text.

### 4. Layer 3: Contact & Domain Verification (`backend/app/detector/verifier.py`)
- **Email Domain Spoofing**: Detects recruiters claiming to represent corporate/MNC entities while using consumer webmail (`@gmail.com`, `@yahoo.com`).
- **Disposable Webmail Check**: Flags disposable/burner addresses commonly used in fraudulent recruitment campaigns.

### 5. Multi-Signal Risk Aggregator (`backend/app/detector/aggregator.py`)
Combines calibrated ML confidence, heuristic rule violations, and domain verification using multi-signal fusion with critical guardrails:
- **Deterministic Guardrails**: Any critical fraud indicator (e.g. upfront fee/payment demand) automatically triggers High Risk (>=85–95) with critical warning.
- **0 – 25**: 🟢 **Safe / Legitimate**
- **26 – 50**: 🟡 **Low Risk / Caution Advised**
- **51 – 75**: 🟠 **Suspicious / Probable Scam**
- **76 – 100**: 🔴 **High Risk / Critical Scam**

---

## 🧪 How to Test the Models & System

All models and detection engines can be tested instantly from PowerShell or Bash:

### 1. Test the ML Model Directly (Fast Inference Test)
Runs sample scam and legitimate job descriptions through the TF-IDF feature pipeline and displays probability scores, top scam signals, and model version:
```powershell
.\.venv\Scripts\python tests/test_ml.py
```

### 2. Run the 60-Sample Job Scam Detection Benchmark
Evaluates the hybrid job scam detection engine across **60 ground-truth recruitment postings** (30 Scam, 30 Legit) covering student fees, task scams, corporate impersonation, and tricky hard-negatives:
```powershell
.\.venv\Scripts\python backend/scripts/run_benchmark_evaluation.py
```
*Expected Performance:* `100.00% Accuracy`, `1.0000 ROC-AUC`, `+77.3 pt Score Separation`.

### 3. Run All Automated Unit Test Suites
Executes the full unit test suite covering all Day 1 modules:
```powershell
.\.venv\Scripts\python -c "import subprocess, sys; tests = ['tests/test_rules.py', 'tests/test_ml.py', 'tests/test_verifier.py', 'tests/test_gatekeeper.py', 'tests/test_aggregator.py', 'tests/test_api.py']; [subprocess.run([sys.executable, t], check=True) for t in tests]; print('\n>>> ALL 6 DAY 1 TEST SUITES PASSED! <<<')"
```

### 4. Test Interactively via Swagger UI & Web UI
Start the API dev server:
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
- Web Application UI: [http://localhost:8000/](http://localhost:8000/)
- Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🔬 Benchmark Evaluation Report

### Job Scam Detection Benchmark (N = 60)
| Metric | Performance |
| :--- | :---: |
| **Overall Accuracy** | **100.00%** |
| **Precision (Scam)** | **100.00%** |
| **Recall (Scam)** | **100.00%** |
| **F1-Score (Scam)** | **1.0000** |
| **ROC-AUC Score** | **1.0000** |
| **Avg Scam Risk Score** | **87.7 / 100** |
| **Avg Legit Risk Score** | **10.4 / 100** |
| **Score Separation Delta** | **+77.3 points** |
| **False Positives / Negatives** | **0 / 0** |

---

## 📂 Project Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py             # API endpoints (Job & Image analysis)
│   │   ├── detector/                 # Day 1: Job Posting Fraud Detection
│   │   │   ├── gatekeeper.py         # Gemini multimodal AI gatekeeper
│   │   │   ├── ml.py                 # ML inference wrapper (v2.0)
│   │   │   ├── rules.py              # Rule heuristics & span highlighter
│   │   │   ├── verifier.py           # Domain & contact verifier
│   │   │   └── aggregator.py         # Multi-signal risk fusion & guardrails
│   │   ├── ocr.py                    # Multi-modal native OCR engine
│   │   └── main.py                   # FastAPI application entrypoint
│   ├── models/
│   │   └── job_detector_model.joblib # Trained TF-IDF + linear classifier
│   └── scripts/
│       ├── train_pipeline.py               # Model training pipeline
│       └── run_benchmark_evaluation.py     # 60-sample Job benchmark
├── data/                             # Datasets (gitignored)
│   ├── fake_job_postings.csv
│   └── evaluation_benchmark_dataset.csv
├── frontend/                         # Modern web application UI
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests/                            # Automated unit test suites
│   ├── test_rules.py
│   ├── test_ml.py
│   ├── test_verifier.py
│   ├── test_gatekeeper.py
│   ├── test_aggregator.py
│   └── test_api.py
├── .env.example                      # Environment template
├── .gitignore                        # Git exclusion rules
├── LICENSE                           # MIT License
├── requirements.txt                  # Python dependencies
└── README.md
```

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.10+ installed
- Windows PowerShell or Bash

### 2. Setup Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Development Server
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
- Web Application UI: [http://localhost:8000/](http://localhost:8000/)
- Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 API Specification

### 1. `POST /api/v1/analyse-job` (Job Scam Scanner)
**Request Body (`application/json`):**
```json
{
  "text": "Full job description text...",
  "company_name": "Optional company name",
  "contact_email": "Optional contact email"
}
```

### 2. `POST /api/v1/analyse-image` (Job Scam Screenshot OCR)
**Request (`multipart/form-data`):**
* `file`: Screenshot or photo (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`)
* `company_name`: Optional company name
* `contact_email`: Optional contact email

**Response Example (`application/json`):**
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

### 3. `GET /api/v1/gatekeeper-status`
Returns the status of the AI gatekeeper and whether Google Gemini multimodal API is active.

### 4. `POST /api/v1/set-gemini-key`
Dynamically sets or clears the Google Gemini API key at runtime (`{"api_key": "AIzaSy..."}`).

---

## 🗺️ Roadmap

### Day 1: Job Posting Scanner (Job Seeker Protection)
- [x] **Day 1 - Module 1**: Benchmark dataset acquisition & ML model training.
- [x] **Day 1 - Module 2**: Rule-based scam detection & character span highlighter.
- [x] **Day 1 - Module 3**: Hybrid Risk Aggregator & `POST /api/v1/analyse-job` API.
- [x] **Day 1 - Module 4**: Company and contact domain verification.
- [x] **Day 1 - Module 5**: Interactive frontend UI with live text highlighting, screenshot OCR & clipboard paste (`Ctrl+V`).
- [x] **Day 1 - Module 6**: AI Gatekeeper & Relevance Classifier (Google Gemini Multimodal Vision + Zero-Config Offline Heuristics).

### Day 2: To Be Implemented
- [ ] **Day 2**: Open for new implementation.

---

## 📄 License
This project is licensed under the [MIT License](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/LICENSE).
