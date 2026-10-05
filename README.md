# 🛡️ LeakedIn — AI-Powered Dual-Sided Recruitment Security Platform

> **Hackathena 2.0 Project**  
> An intelligent recruitment fraud detection platform designed to protect both **Job Seekers** and **Employers/Recruiters** from recruitment scams, credential fabrication, identity theft, and fraudulent job postings.

---

## 📌 Executive Summary

Recruitment security is a two-sided ecosystem challenge. LeakedIn addresses both vectors:
1. **Day 1: Job Seeker Shield (Job Posting & Offer Scanner)**  
   Protects candidates from fake recruiters, upfront registration fees, training kit scams, Telegram traps, and corporate impersonation.
2. **Day 2: Recruiter Shield (Candidate Integrity & Resume Scanner)**  
   Protects organizations from candidate fraud, moonlighting (overlapping full-time jobs), counterfeit diploma mill degrees, anachronistic tech stack claims, AI synthetic CV prompt leakage, and burner reference contacts.

```
┌────────────────────────────────────────────────────────────────────────┐
│               LEAKEDIN RECRUITMENT SECURITY PLATFORM                   │
├────────────────────────────────────┬───────────────────────────────────┤
│  🔍 JOB SEEKER SHIELD (Day 1)      │  👔 RECRUITER SHIELD (Day 2)      │
│  • Upfront Fee & Deposit Scams     │  • Concurrent Full-Time Jobs      │
│  • WhatsApp / Telegram Hijacking   │  • Unaccredited Diploma Mills     │
│  • Free Webmail Impersonation      │  • Timeline & Chronology Paradox  │
│  • Calibrated ML Fraud Classifier  │  • Anachronistic Tech Claims      │
│  • Gemini Multimodal Vision GK     │  • ChatGPT Prompt Leakage Markers │
│  • Character Span Highlighter      │  • Disposable Reference Contacts  │
└────────────────────────────────────┴───────────────────────────────────┘
```

---

## 🚀 Detection Architecture

### 🛡️ Side 1: Job Posting Scanner (Job Seeker Protection)

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

### 👔 Side 2: Candidate Integrity & Resume Scanner (Recruiter Protection)

```
[ Candidate Resume: PDF / Image OCR / Text ]
                      │
                      ▼
┌───────────────────────────────────────────────────────────┐
│  Module 1: Structured Entity Parsing Engine               │
│  • Contact Details, Social Handles (LinkedIn, GitHub)     │
│  • Education History (degrees, institutions, CGPA, years) │
│  • Work Timeline (companies, roles, date ranges, months)  │
│  • Technical Skills, Certifications & Referees            │
└─────────────────────────────┬─────────────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         ▼                                         ▼
┌─────────────────────────────────┐ ┌───────────────────────────────────┐
│  Module 2: Chronological        │ │  Module 3: Credential Inflation & │
│            Timeline Anomalies   │ │            Diploma Mill Engine    │
│  • Overlapping full-time roles  │ │  • Blacklisted counterfeit mills  │
│    (parallel moonlighting)      │ │    (Almeda, Rochville, Belford)   │
│  • Education vs experience      │ │  • Anachronistic tech stacks (e.g.│
│    paradoxes (roles < 12th)     │ │    Kubernetes in 2008, 15yr Flut) │
│  • Intern-to-CTO leaps < 6 mo   │ │  • ChatGPT prompt leakage markers │
│  • Future post-dated tenures    │ │  • Unfilled template placeholders │
└────────────────┬────────────────┘ └─────────────────┬─────────────────┘
                 │                                    │
                 └────────────────────┬───────────────┘
                                      ▼
┌───────────────────────────────────────────────────────────┐
│  Module 4: Reference & Digital Footprint Verifier         │
│  • Disposable burner emails for managerial references     │
│  • Corporate referees using generic consumer webmail      │
│  • Placeholder LinkedIn and GitHub profile handles        │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  Module 5: Candidate Risk Aggregator                      │
│  • Integrity Risk Score (0 - 100) & Level                 │
│  • Visual Career Timeline with conflict collision flags   │
│  • Actionable HR Due-Diligence Audit Recommendations      │
└───────────────────────────────────────────────────────────┘
```

---

## 🧪 How to Test the Models & System

All models and detection engines can be tested instantly from PowerShell or Bash:

### 1. Test the ML Model Directly (Fast Inference Test)
Runs sample scam and legitimate job descriptions through the TF-IDF feature pipeline and displays probability scores, top scam signals, and model version:
```powershell
.\.venv\Scripts\python tests/test_ml.py
```

### 2. Run the 60-Sample Job Scam Detection Benchmark (Day 1)
Evaluates the hybrid job scam detection engine across **60 ground-truth recruitment postings** (30 Scam, 30 Legit) covering student fees, task scams, corporate impersonation, and tricky hard-negatives:
```powershell
.\.venv\Scripts\python backend/scripts/run_benchmark_evaluation.py
```
*Expected Performance:* `100.00% Accuracy`, `1.0000 ROC-AUC`, `+77.3 pt Score Separation`.

### 3. Run the 30-Sample Candidate Resume Integrity Benchmark (Day 2)
Evaluates the candidate fraud detection engine across **30 realistic resumes** (15 Authentic, 15 Fabricated / Anomaly cases):
```powershell
.\.venv\Scripts\python backend/scripts/run_candidate_benchmark.py
```
*Expected Performance:* `100.00% Accuracy`, `1.0000 ROC-AUC`, `+81.1 pt Score Separation`.

### 4. Run All 12 Automated Unit Test Suites in One Command
Executes the full test suite covering all modules across both Day 1 and Day 2:
```powershell
.\.venv\Scripts\python -c "import subprocess, sys; tests = ['tests/test_rules.py', 'tests/test_ml.py', 'tests/test_verifier.py', 'tests/test_gatekeeper.py', 'tests/test_aggregator.py', 'tests/test_api.py', 'tests/test_candidate_parser.py', 'tests/test_timeline.py', 'tests/test_credentials.py', 'tests/test_candidate_verifier.py', 'tests/test_candidate_aggregator.py', 'tests/test_candidate_api.py']; [subprocess.run([sys.executable, t], check=True) for t in tests]; print('\n>>> ALL 12 TEST SUITES PASSED! <<<')"
```

### 5. Test Interactively via Swagger UI
Start the API dev server:
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
Open **[http://localhost:8000/docs](http://localhost:8000/docs)** to test:
- `POST /api/v1/analyse-job` (Raw text job scam analysis)
- `POST /api/v1/analyse-image` (Image / screenshot OCR scam analysis)
- `POST /api/v1/analyse-resume` (Raw candidate CV text analysis)
- `POST /api/v1/analyse-resume-file` (PDF / Image candidate resume upload)

---

## 🔬 Benchmark Evaluation Reports

### Benchmark 1: Job Scam Detection (N = 60)
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

### Benchmark 2: Candidate Resume Integrity (N = 30)
| Metric | Performance |
| :--- | :---: |
| **Overall Accuracy** | **100.00%** |
| **Precision (Fraud)** | **100.00%** |
| **Recall (Fraud)** | **100.00%** |
| **F1-Score (Fraud)** | **1.0000** |
| **ROC-AUC Score** | **1.0000** |
| **Avg Fraud Risk Score** | **84.4 / 100** |
| **Avg Authentic Risk Score** | **3.3 / 100** |
| **Score Separation Delta** | **+81.1 points** |
| **False Positives / Negatives** | **0 / 0** |

---

## 📂 Project Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py             # API endpoints (Job & Resume analysis)
│   │   ├── candidate/                # Day 2: Candidate Fraud Verification
│   │   │   ├── parser.py             # Ingestion & structured entity parser
│   │   │   ├── timeline.py           # Chronology & overlap anomaly engine
│   │   │   ├── credentials.py        # Diploma mills & anachronistic tech engine
│   │   │   ├── verifier.py           # Reference & digital footprint verifier
│   │   │   └── aggregator.py         # Candidate risk aggregator
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
│       ├── run_benchmark_evaluation.py     # 60-sample Job benchmark
│       └── run_candidate_benchmark.py      # 30-sample Candidate benchmark
├── data/                             # Datasets (gitignored)
│   ├── fake_job_postings.csv
│   └── evaluation_benchmark_dataset.csv
├── frontend/                         # Modern web application UI
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests/                            # 12 automated unit test suites
│   ├── test_rules.py
│   ├── test_ml.py
│   ├── test_verifier.py
│   ├── test_gatekeeper.py
│   ├── test_aggregator.py
│   ├── test_api.py
│   ├── test_candidate_parser.py
│   ├── test_timeline.py
│   ├── test_credentials.py
│   ├── test_candidate_verifier.py
│   ├── test_candidate_aggregator.py
│   └── test_candidate_api.py
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

### 3. `POST /api/v1/analyse-resume` (Candidate Resume Text Scanner)
**Request Body (`application/json`):**
```json
{
  "text": "Full candidate resume text..."
}
```

### 4. `POST /api/v1/analyse-resume-file` (Candidate Resume Document Upload)
**Request (`multipart/form-data`):**
* `file`: Candidate resume document (`.pdf`, `.png`, `.jpg`, `.jpeg`)

**Response Example (`application/json`):**
```json
{
  "candidate_name": "Applicant",
  "risk_score": 84,
  "risk_level": "High Risk",
  "verdict": "Critical candidate credential fabrication or timeline contradiction detected. Detailed audit required.",
  "has_critical_flags": true,
  "total_anomalies": 3,
  "red_flags": [
    {
      "category": "Concurrent Employment",
      "severity": "CRITICAL",
      "title": "Simultaneous Full-Time Roles Detected",
      "description": "Concurrent full-time tenures detected between 'Amazon AWS' and 'Microsoft Azure' spanning 18 months."
    },
    {
      "category": "Bogus Degree / Diploma Mill",
      "severity": "CRITICAL",
      "title": "Degree from Blacklisted Diploma Mill (Almeda University)",
      "description": "Institution 'Almeda University' is a globally blacklisted unaccredited diploma mill."
    }
  ],
  "recommendations": [
    "Request EPFO / Provident Fund service history or Form 16 to audit overlapping corporate tenures.",
    "Candidate claims credentials from an unaccredited diploma mill. Reject degree credits."
  ],
  "timeline_analysis": {
    "visual_timeline": [...]
  }
}
```

---

## 🗺️ Roadmap

### Day 1: Job Posting Scanner (Job Seeker Protection)
- [x] **Day 1 - Module 1**: Benchmark dataset acquisition & ML model training.
- [x] **Day 1 - Module 2**: Rule-based scam detection & character span highlighter.
- [x] **Day 1 - Module 3**: Hybrid Risk Aggregator & `POST /api/v1/analyse-job` API.
- [x] **Day 1 - Module 4**: Company and contact domain verification.
- [x] **Day 1 - Module 5**: Interactive frontend UI with live text highlighting, screenshot OCR & clipboard paste (`Ctrl+V`).
- [x] **Day 1 - Module 6**: AI Gatekeeper & Relevance Classifier (Google Gemini Multimodal Vision + Zero-Config Offline Heuristics).

### Day 2: Candidate Integrity & Resume Scanner (Recruiter Protection)
- [x] **Day 2 - Module 1**: Resume Ingestion & Structured Entity Parsing Engine ([`parser.py`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/backend/app/candidate/parser.py)).
- [x] **Day 2 - Module 2**: Chronological Timeline & Anomaly Detection Engine ([`timeline.py`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/backend/app/candidate/timeline.py)).
- [x] **Day 2 - Module 3**: Credential Inflation & Diploma Mill Engine ([`credentials.py`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/backend/app/candidate/credentials.py)).
- [x] **Day 2 - Module 4**: Reference & Digital Footprint Verifier ([`verifier.py`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/backend/app/candidate/verifier.py)).
- [x] **Day 2 - Module 5**: Candidate Risk Aggregator & API Pipeline ([`aggregator.py`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/backend/app/candidate/aggregator.py)).
- [x] **Day 2 - Module 6 (Evaluation)**: Candidate Benchmark Suite ([`run_candidate_benchmark.py`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/backend/scripts/run_candidate_benchmark.py)) (100% Accuracy, 0 False Positives, 0 False Negatives).
- [ ] **Day 2 - Module 6 (UI Integration)**: Dual-Persona Frontend UI/UX Integration (Persona Switcher: Job Seeker ⇄ Recruiter).

---

## 📄 License
This project is licensed under the [MIT License](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/LICENSE).
