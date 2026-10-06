# 🛡️ LeakedIn — AI-Powered Recruitment Security & Scam Shield

> **Hackathena 2.0 Project**  
> A production-grade multi-layer recruitment fraud detection shield designed to protect job seekers from predatory employment scams, fake offer letters, WhatsApp recruitment traps, corporate identity theft, and advance-fee fraud.

[![Tests](https://img.shields.io/badge/pytest-101%2F101%20passing-success.svg)](#-test-suites--validation)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v2.0-009688.svg)](https://fastapi.tiangolo.com/)
[![ROC-AUC](https://img.shields.io/badge/ROC--AUC-0.9901-brightgreen.svg)](#-calibrated-machine-learning--xai)

---

## 📌 Flagship Highlights

1. **4 Unified Input Modes**:
   - 📝 **Paste Text**: Analyze job postings, WhatsApp messages, or recruiter emails.
   - 🔗 **Job URL**: Scrape and scan posting URLs with private IP & SSRF blocklists.
   - 📸 **Screenshot (OCR)**: Drag & drop, file upload, or direct clipboard (<kbd>Ctrl+V</kbd>) paste with local OCR (runs offline by default; Gemini vision optional).
   - 📄 **Offer Letter Forensics (PDF/DOCX)**: Inspect appointment letters for fake MCA CIN/GST numbers, suspicious signatories, and template anomalies.
2. **Multilingual Localization & Rules**:
   - Full UI & heuristic support for **English**, **हिन्दी (Hindi)**, and **മലയാളം (Malayalam)** with 42 YAML-compiled regional scam patterns.
3. **AI Gatekeeper & Vision Rejection**:
   - Zero-config offline heuristic filter + Google Gemini 1.5 Flash multimodal vision layer to intercept recipes, candidate CVs, invoices, and casual chats before fraud scoring.
4. **Explainable AI (XAI)**:
   - Linear-time n-gram feature attribution displaying visual trigger chips with score weights.
5. **Community Threat Blacklist (`reputation.db`)**:
   - Salted SHA-256 HMAC lookups for scam phone numbers, UPI IDs, and domain lookalikes.
6. **1930 Cybercrime Helpline & One-Click Police Complaint Draft**:
   - Immediate guidance for Indian cybercrime recovery and pre-filled legal complaint drafts ready for [cybercrime.gov.in](https://cybercrime.gov.in).
7. **Shareable Verification Card**:
   - Generates high-resolution branded PNG cards using HTML5 Canvas for instant sharing.

---

## 🏗️ 5-Tier Hybrid Architecture

```
                            ┌──────────────────────────────────────────────┐
                            │               USER INPUT                     │
                            │ (Text / URL / Screenshot / PDF Offer Letter) │
                            └──────────────────────┬───────────────────────┘
                                                   │
                ┌──────────────────────────────────▼──────────────────────────────────┐
                │   LAYER 0: AI Gatekeeper & Relevance Filter                         │
                │   • Google Gemini 1.5 Flash Vision / Zero-Config Offline Fallback   │
                │   • Rejects recipes, CVs, invoices, and casual chats                │
                └──────────────────────────────────┬──────────────────────────────────┘
                                                   │ (Recruitment Text Verified)
        ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
        │                                          │                                          │
┌───────▼───────────────────────────┐ ┌────────────▼─────────────────────────┐ ┌──────────────▼─────────────────────────┐
│ LAYER 1: Calibrated ML & XAI      │ │ LAYER 2: Multilingual Rules Engine   │ │ LAYER 3: Forensics & Threat DB         │
│ • Isotonic regression (CV=5)      │ │ • 42 YAML rules (en/hi/ml)           │ │ • PDF/DOCX offer letter forensics      │
│ • ROC-AUC: 0.9901, Prec: 95.7%    │ │ • Normalizes leetspeak & homoglyphs  │ │ • Indian CIN / GST validation          │
│ • Linear-time XAI signal chips    │ │ • Exact offset phrase highlighting   │ │ • Salted SHA-256 reputation.db hits    │
└───────┬───────────────────────────┘ └────────────┬─────────────────────────┘ └──────────────┬─────────────────────────┘
        │                                          │                                          │
        └──────────────────────────────────────────┼──────────────────────────────────────────┘
                                                   │
                ┌──────────────────────────────────▼──────────────────────────────────┐
                │   UNIFIED RISK AGGREGATOR                                           │
                │   • Language-aware weighting (lowers ML weight on Indic text)       │
                │   • Combination bonus logic + Critical risk floor (>= 51)           │
                │   • 1930 Cybercrime Guidance & Police Complaint Draft               │
                └──────────────────────────────────┬──────────────────────────────────┘
                                                   │
                ┌──────────────────────────────────▼──────────────────────────────────┐
                │   MODERN GLASSMORPHISM FRONTEND                                     │
                │   • Animated SVG circular risk gauge (0 - 100)                      │
                │   • Interactive hover tooltips on highlighted phrases               │
                │   • Canvas-rendered shareable verification card (PNG download)      │
                └─────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Deep-Dive: Core Modules

### 1. AI Gatekeeper (`backend/app/detector/gatekeeper.py`)
- **Semantic Noise Rejection**: Eliminates false positives by determining whether an input represents genuine employment recruitment before calculating fraud scores.
- **Dual-Engine Execution**: Operates offline by default using built-in linguistic heuristics. If `GEMINI_API_KEY` is configured in the environment, Google Gemini Cloud Multimodal Vision (configurable via `GEMINI_MODEL`, defaulting to `gemini-2.5-flash`) can optionally be used (transmitting text/screenshots to Google).

### 2. Calibrated Machine Learning & XAI (`backend/app/detector/ml.py`)
- **Training Pipeline**: Trained on EMSCAD (17,880 postings) augmented with real-world Indian recruitment scams, calibrated via `CalibratedClassifierCV(method='isotonic', cv=5)`.
- **Explainable Feature Attribution**: Calculates linear-time feature contributions for top fraud triggers and top legitimacy indicators.
- **Model Metrics**:
  - **ROC-AUC**: `0.9901`
  - **Scam Precision**: `95.71%`
  - **Scam Recall**: `77.46%`
  - **Scam F1-Score**: `85.62%`

### 3. Multilingual Heuristics & Normalizer (`backend/app/detector/rules.py`)
- **Unicode & Leetspeak Normalizer**: Strips zero-width characters, Cyrillic homoglyphs, and converts obfuscated numbers (`ph0ne`, `₹5,OOO`) while mapping exact character offsets back to the raw string.
- **42 Multilingual Rules (`backend/app/detector/patterns/rules.yaml`)**:
  - Upfront kit/registration charges, security deposits, cheque fraud.
  - Student internship exploitation, "pocket money" bait, unrealistic stipends.
  - WhatsApp/Telegram-only recruiters, disposable contact forms.
  - Work-from-home YouTube liking and data-entry task scams.

### 4. Offer Letter Forensics (`backend/app/detector/document_checks.py`)
- **MCA CIN / GST Validation**: Extracts and cross-references Corporate Identification Numbers (CIN) and GSTIN formats against ministry standards.
- **Template Plagiarism**: Flags common placeholders (`[Insert Employee Name]`, `[Company Logo Here]`) and suspect PDF generator metadata (`Canva`, `ilovepdf`).

### 5. Community Threat Blacklist (`backend/app/db/analytics.py` & `reputation.py`)
- **Privacy-Preserving Lookups**: Entity identifiers (phone numbers, UPI IDs, domain names) are hashed using salted SHA-256 HMAC before checking against `reputation.db`.
- **Victim Community Reporting**: Users can report scam contacts via `POST /api/report`, incrementing report counts without storing user message text.

---

## 🔒 Privacy & Optional Cloud Features

LeakedIn is architected to be **offline-by-default and privacy-respecting**:
- **Offline by Default**: All machine learning scoring, 42 multilingual rule heuristics (English, Hindi, Malayalam), OCR text extraction, and offer letter forensics execute entirely on the local system without outbound network calls.
- **Zero Permanent Retention**: User job descriptions, URLs, screenshots, and offer letters are processed in-memory and are never stored to disk or database tables.
- **Optional Google Gemini Cloud**: The AI Gatekeeper only connects to Google Gemini if `GEMINI_API_KEY` is explicitly configured in your environment. The model is configurable via `GEMINI_MODEL` (defaults to `gemini-2.5-flash`). When enabled, job text or screenshots are sent to Google's API for multimodal relevance evaluation. With no key set, the system runs completely offline using local heuristic classifiers.
- **Privacy-Preserving Threat Intelligence**: Contact identifiers (phones, UPI IDs, domains) submitted to the community database are hashed with a salted SHA-256 HMAC before storage, ensuring no raw personal messages or identifiers are stored.

---

## 🧪 Test Suites & Validation

All **113 tests** pass with 100% success across the consolidated test suite in `tests/`:

```powershell
# Run the complete test suite
.\.venv\Scripts\pytest
```

Output:
```text
======================= 113 passed, 1 warning in 7.66s =======================
tests/test_aggregator.py ................. [PASS]
tests/test_api.py ........................ [PASS]
tests/test_api_integration.py ............ [PASS]
tests/test_evaluation_integrity.py ....... [PASS]
tests/test_gatekeeper.py ................. [PASS]
tests/test_ml.py ......................... [PASS]
tests/test_phase3.py ..................... [PASS]
tests/test_phase4.py ..................... [PASS]
tests/test_phase5.py ..................... [PASS]
tests/test_phase6.py ..................... [PASS]
tests/test_phase8.py ..................... [PASS]
tests/test_phase9_coverage.py ............ [PASS]
tests/test_robustness_cases.py ........... [PASS]
tests/test_rules.py ...................... [PASS]
tests/test_verifier.py ................... [PASS]
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Windows PowerShell, macOS Terminal, or Linux Bash

### 2. Local Installation

```bash
# 1. Clone repository
git clone https://github.com/athulpp06/hackathena-2.0.git
cd hackathena-2.0
```

#### Windows (PowerShell):
```powershell
# 2. Setup Virtual Environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Environment Configuration (Optional)
copy .env.example .env

# 4. Install Dependencies
pip install -r requirements.txt
```

#### Linux / macOS (Bash / Zsh):
```bash
# 2. Setup Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Environment Configuration (Optional)
cp .env.example .env

# 4. Install Dependencies
pip install -r requirements.txt
```

### 3. Start the Server

```bash
# Start backend API and frontend static server
uvicorn backend.app.main:app --reload --port 8000
```

- **Web Application UI**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 4. Running via Docker

```bash
# Build and run backend + Nginx frontend
docker-compose up --build
```

- **Frontend Web UI**: [http://localhost:5500/](http://localhost:5500/) (served via Nginx)
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 API Specification

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/analyze/text` | `POST` | Primary job posting scanner (accepts text, optional company & recruiter email) |
| `/api/analyze/url` | `POST` | SSRF-safe career page scraper and analyzer |
| `/api/analyze/image` | `POST` | Multipart upload for screenshot OCR inspection |
| `/api/analyze/document`| `POST` | Multipart upload for PDF / DOCX offer letter forensics |
| `/api/report` | `POST` | Report a scammer phone, UPI ID, or domain to the threat database |
| `/api/reputation/lookup`| `GET` | Cryptographic salted lookup for blacklisted entities |
| `/api/stats` | `GET` | Live community intelligence and blacklisted entity counts |
| `/api/feedback` | `POST` | Record accuracy feedback (correct, false positive, false negative) |
| `/gatekeeper-status` | `GET` | Gatekeeper engine status (Offline Heuristic vs Google Gemini Cloud) |
| `/health` | `GET` | Operational health check with model metrics and OCR readiness |

---

## 📂 Project Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py             # Canonical & legacy API endpoints
│   │   ├── db/
│   │   │   ├── analytics.py          # SQLite analytics & blacklist helper
│   │   │   └── reputation.db         # SQLite threat DB (auto-created on first run, gitignored)
│   │   ├── detector/
│   │   │   ├── advice.py             # 1930 Cybercrime guidance & police drafting
│   │   │   ├── aggregator.py         # Multi-signal risk fusion & guardrails
│   │   │   ├── document_checks.py    # CIN/GST & offer letter forensics
│   │   │   ├── entities.py           # Phone, UPI, email entity extractor
│   │   │   ├── gatekeeper.py         # Gemini multimodal AI gatekeeper
│   │   │   ├── ml.py                 # Isotonic calibrated ML inference & XAI
│   │   │   ├── patterns/rules.yaml   # 42 Multilingual heuristic rules
│   │   │   ├── rules.py              # Heuristics engine & span highlighter
│   │   │   ├── typosquat.py          # Damerau-Levenshtein domain lookalikes
│   │   │   └── verifier.py           # Domain verification & FlagItem wrapper
│   │   ├── utils/
│   │   │   ├── document_extractor.py # PDF (pdfplumber) & DOCX text extractor
│   │   │   ├── normalizer.py         # Homoglyphs, leetspeak, zero-width stripper
│   │   │   ├── ocr.py                # Local EasyOCR & Windows Native fallback
│   │   │   └── scraper.py            # SSRF-protected webpage scraper
│   │   ├── config.py                 # System configuration & weights
│   │   ├── limiter.py                # SlowAPI rate limiting configuration
│   │   └── main.py                   # FastAPI application entrypoint
│   ├── models/
│   │   ├── job_detector_model.joblib # Trained calibrated pipeline
│   │   └── metadata.json             # Calibration metrics & version info
│   ├── scripts/
│   │   ├── train_pipeline.py         # Calibrated classifier training pipeline
│   │   └── run_benchmark_evaluation.py # Ground-truth benchmark evaluation
│   └── tests/                        # 87 Automated phase & robustness tests
├── bots/
│   └── telegram_bot.py               # Interactive Telegram scanner bot
├── docker/
│   └── nginx.conf                    # Nginx reverse proxy config
├── docs/                             # Architecture decisions & audit reports
├── extension/                        # Browser extension (manifest v3)
├── frontend/                         # Luxury glassmorphism web interface
│   ├── index.html                    # Unified UI layout with 4 tabs & modals
│   ├── styles.css                    # Luxury dark-mode CSS design system
│   └── app.js                        # Client logic, i18n, and Canvas PNG exporter
├── tests/                            # 14 Root module tests
├── .env.example                      # Environment variables template
├── .gitignore                        # Git exclusion rules (2.0/ excluded)
├── Dockerfile                        # Production container build
├── docker-compose.yml                # Multi-container service definition
├── LICENSE                           # MIT License
├── pyproject.toml                    # Build tool configuration
├── pytest.ini                        # Pytest configuration
├── requirements.txt                  # Python dependencies
├── run.bat                           # Windows launch script
└── README.md                         # Project documentation
```

---

## 📄 License
Distributed under the [MIT License](LICENSE). Built for **Hackathena 2.0**.
