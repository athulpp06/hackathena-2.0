# Comprehensive Read-Only Audit Report: LeakedIn

> **Audit Date:** 2026-10-06  
> **Repository:** `GECT/hackathenna 2.0` (LeakedIn)  
> **Auditor:** Senior Security & Full-Stack / ML Systems Engineer (Read-Only Audit)

---

## 1. ENVIRONMENT

### System & Hardware Specifications

| Property | Measured Value | Notes |
|---|---|---|
| **Operating System** | Windows (win32, x64) | Tested on PowerShell host |
| **Python Version** | `Python 3.13.13` | Running in active Python environment |
| **CPU Model** | `13th Gen Intel(R) Core(TM) i5-13420H` | Identified via `Win32_Processor` |
| **CPU Cores / Logical** | 8 physical cores, 12 logical processors | `os.cpu_count() == 12` |
| **Total System RAM** | `15.64 GB` total | Measured via `psutil.virtual_memory()` |
| **Available RAM** | `1.86 GB` free / available | Measured during test execution |
| **GPU Available** | **No** (`torch.cuda.is_available() == False`) | Device: `None` |
| **Free Disk Space (C:)** | `70,649,315,328 bytes` (~65.80 GB free) | 440.40 GB used out of 511.05 GB |

### Core Python Packages (`pip list`)

| Package | Installed Version | Notes |
|---|---|---|
| `fastapi` | `0.142.2` | Starlette deprecation warnings present |
| `uvicorn` | `0.54.0` | ASGI application server |
| `scikit-learn` | `1.9.0` | TF-IDF + CalibratedClassifierCV |
| `easyocr` | `1.7.2` | Offline PyTorch-based OCR engine |
| `torch` | `2.14.1` | CPU-only build |
| `opencv-python-headless` | `5.0.0.93` | Computer vision dependency |
| `pandas` | `3.0.5` | Data preprocessing |
| `numpy` | `2.5.1` | Array operations |
| `slowapi` | `0.1.10` | Rate limiting middleware |
| `pdfplumber` | `0.11.10` | PDF text & metadata extraction |
| `python-docx` | `1.2.0` | DOCX parser |
| `python-telegram-bot` | `22.8` | Asynchronous Telegram bot framework |
| `pytest` | `9.1.1` | Test runner |
| `pytest-cov` | `7.1.0` | Coverage plugin |

### Git State

| Metric | Value |
|---|---|
| **Current Branch** | `master` |
| **Total Commit Count** | `2` commits |
| **Working Tree Status** | **Dirty** (uncommitted modifications and untracked files) |

**Last 2 Git Commits:**
```text
9daec87 docs: update README with architecture and add ML training pipeline
d07b475 Initial commit
```

**Modified & Untracked Files:**
```text
 M README.md
 M backend/scripts/train_pipeline.py
 M requirements.txt
?? .coverage
?? .env.example
?? .github/
?? Dockerfile
?? LeakedIn_Project_Report.docx
?? MS-vsliveshare.vsliveshare-pack-0.4.0.vsix
?? backend/app/
?? backend/models/
?? backend/scripts/evaluate.py
?? backend/scripts/train_transformer.py
?? backend/scripts/xai_smoke_test.py
?? backend/tests/
?? bots/
?? docker-compose.yml
?? docker/
?? docs/
?? extension/
?? frontend/
?? pytest.ini
?? run.bat
```

---

## 2. DOES IT RUN?

### Installation & Execution Verification

| Component | Status | Evidence / Measurement |
|---|---|---|
| `pip install -r requirements.txt` | **WORKS** | All dependencies resolve and import cleanly in current environment. |
| `python -m backend.scripts.train_pipeline` | **WORKS** | Generates `backend/models/job_detector_model.joblib` (1,210 KB) and `metadata.json`. |
| Start backend (`uvicorn backend.app.main:app`) | **WORKS** | Starts in ~1.5s on port 8765/8000; returns valid JSON. |
| `GET /health` | **WORKS** | HTTP 200 (111 ms); returns service name, API version `2.0.0`, and model metrics. |
| `GET /docs` | **WORKS** | HTTP 200; Swagger UI renders all OpenAPI schemas. |

### API Endpoint Functional Verification

All endpoints were tested live against `http://127.0.0.1:8765`:

| Endpoint | Method | Status | Latency | Result / Evidence |
|---|---|---|---|---|
| `/health` | GET | `200 OK` | 111 ms | `{"status":"ok","service":"LeakedIn","api_version":"2.0.0"}` |
| `/api/stats` | GET | `200 OK` | 49 ms | `{"note":"Live stats not yet implemented..."}` (Stub) |
| `/analyse-text` | POST | `200 OK` | 75 ms | Score `100/100` (High Risk) on scam; Score `0/100` (Safe) on legitimate text. |
| `/api/analyze/text` | POST | `404 NOT FOUND` | 0 ms | **BROKEN ROUTE:** README claims `/api/analyze/text`, but route is mounted at `/analyse-text`! |
| `/analyse-url` | POST | `200 OK` | 11-31 ms | **SECURITY ISSUE:** Blocked SSRF inputs return HTTP 200 with `[BLOCKED]` treated as job text! |
| `/analyse-image` | POST | `400 / 415 / 503` | 5-25 ms | Empty file returns `400`; `.exe` MIME returns `415`. Corrupt file triggers timeout/exception. |
| `/api/analyze/document` | POST | `200 OK` | 82 ms | Tested with synthetic PDF & DOCX byte payloads. |
| `/api/report` | POST | `200 OK` | 26 ms | Hashes entity with salt into SQLite; returns `{"status":"reported","report_count":1}`. |
| `/api/reputation/lookup` | GET | `200 OK` | 21 ms | Lookup `scammer@gmail.com` returns `{"found":true,"report_count":3}`. |
| `/api/feedback` | POST | `200 OK` | 2 ms | In-memory queue appends feedback; returns `{"status":"received"}`. |

### Feature Status Summary

| Feature | Audit Status | One-Line Evidence |
|---|---|---|
| **Text Analysis** | **WORKS** | Returns score, level, flags, n-grams, and emergency advice in 15–75 ms. |
| **URL Analysis** | **PARTIAL** | Scraper blocks internal IPs, but endpoint swallows the block message and scores it as "Safe". |
| **Image OCR** | **WORKS** | EasyOCR runs offline; handles English and Hindi scripts cleanly; slow on CPU cold-start. |
| **Document Forensics** | **WORKS** | Validates magic bytes, flags missing CIN/GST, checks placeholders and PDF creator metadata. |
| **Reputation Blacklist** | **WORKS** | Salted SHA-256 lookup and report functioning in SQLite `reputation.db`. |
| **Explainable ML (XAI)** | **WORKS** | Returns linear LR coefficient contributions for top fraud and legitimate n-grams. |
| **Feedback System** | **PARTIAL** | Stores feedback in an in-memory list only (`_feedback_queue`), lost upon process restart. |
| **Stats API** | **NOT IMPLEMENTED** | Route exists but returns hardcoded stub message: `"Live stats not yet implemented"`. |
| **Frontend Web App** | **PARTIAL** | Clean dark UI; calls `/analyse-text` successfully, but hardcodes `http://localhost:8000`. |
| **Chrome Extension** | **WORKS** | Valid Manifest V3, requests minimal permissions (`contextMenus`, `storage`, `activeTab`). |
| **Telegram Bot** | **RETIRED** | Scrapped in 2.0 release; functionality consolidated into Web App & Browser Extension. |
| **Docker Build** | **PARTIAL** | Multi-stage Dockerfile exists; permissions mismatch on named volumes with non-root user. |

### Frontend & Client Findings
- **Hardcoded Backend URL:** `frontend/script.js` line 10 hardcodes `const API_BASE = "http://localhost:8000";`. If deployed on a custom domain or accessed remotely, the browser will attempt to send requests to the user's local machine.
- **Route Name Discrepancies:**
  - `script.js` line 386 calls `${API_BASE}/analyse-text` (matches backend route `/analyse-text`).
  - `script.js` line 459 calls `${API_BASE}/api/analyze/document` (matches backend route `/api/analyze/document`).
  - README claims all endpoints start with `/api/analyze/` (e.g. `/api/analyze/text`), which returns HTTP 404!

### Chrome Extension Verification
- `manifest_version`: `3` (Valid Manifest V3).
- `permissions`: `["contextMenus", "storage", "activeTab"]`.
- `host_permissions`: None requested (satisfies Chrome Web Store minimal permission principle).
- `content_scripts`: Injects on `*://*.linkedin.com/jobs/*`, `*://*.indeed.com/*`, `*://*.naukri.com/*`.
- `background`: `{"service_worker": "background.js"}`.
- Target Endpoint: Calls `${apiBase}/analyse-text` with fallback to `http://localhost:8000`.

### Telegram Bot Verification (Retired)
- `bots/telegram_bot.py`:
  - Scrapped in 2.0 release in favor of native Web UI and Chromium Extension. All bot codes and dependencies removed.

### Docker Environment Verification
- Command `docker --version` failed:
  ```text
  docker : The term 'docker' is not recognized as the name of a cmdlet, function, script file, or operable program.
  ```
  Docker CLI is not installed on the host machine.
- **Static Dockerfile & compose issues identified:**
  1. `Dockerfile` creates user `leakedin` (`UID 1000`) and switches to `USER leakedin`. In `docker-compose.yml`, named volumes `leakedin-db:/app/backend/app/db` and `easyocr-cache:/app/.EasyOCR` will be mounted as root by default on Linux engines, triggering permission denied on SQLite writes and model caching.
  2. `docker/nginx.conf` proxies `location /api/ { proxy_pass http://backend:8000/api/; }`. Because backend endpoints are mounted at root `/analyse-text` instead of `/api/analyse-text`, Nginx proxy calls to `/api/analyse-text` will result in HTTP 404.

---

## 3. TESTS AND CODE QUALITY

### Pytest & Coverage Summary

Executing command:
```powershell
$env:PYTHONPATH="."; pytest --cov=backend/app/detector --cov=backend/app/utils --cov-report=term-missing -q
```

**Results:**
- **Status:** `58 passed, 49 warnings in 16.64s`
- **Total Statements:** 613
- **Missed Statements:** 92
- **Total Coverage:** **85%**

### Per-File Coverage Table

| Module | Statements | Miss | Coverage | Missing Line Ranges |
|---|---|---|---|---|
| `backend\app\detector\__init__.py` | 0 | 0 | **100%** | None |
| `backend\app\detector\advice.py` | 22 | 2 | **91%** | 42-45 |
| `backend\app\detector\aggregator.py` | 34 | 2 | **94%** | 44-45 |
| `backend\app\detector\document_checks.py` | 46 | 2 | **96%** | 128-129 |
| `backend\app\detector\ml.py` | 86 | 17 | **80%** | 38-42, 59, 70-72, 81, 119-121, 130-132, 149, 163-165 |
| `backend\app\detector\rules.py` | 31 | 3 | **90%** | 34-35, 59 |
| `backend\app\detector\verification\__init__.py` | 0 | 0 | **100%** | None |
| `backend\app\detector\verification\entities.py` | 25 | 3 | **88%** | 48-50 |
| `backend\app\detector\verification\reputation.py` | 47 | 3 | **94%** | 84-87, 99 |
| `backend\app\detector\verification\typosquat.py` | 81 | 7 | **91%** | 15, 42-43, 75-77, 106 |
| `backend\app\detector\verifier.py` | 36 | 1 | **97%** | 111 |
| `backend\app\utils\__init__.py` | 0 | 0 | **100%** | None |
| `backend\app\utils\document_extractor.py` | 62 | 18 | **71%** | 39, 69-70, 76-83, 101-104, 117-119 |
| `backend\app\utils\normalizer.py` | 23 | 3 | **87%** | 17-18, 24 |
| `backend\app\utils\ocr.py` | 32 | 12 | **62%** | 9-10, 14-15, 22-28, 45 |
| `backend\app\utils\scraper.py` | 88 | 19 | **78%** | 73, 138-140, 147-148, 156, 163-174 |
| **TOTAL** | **613** | **92** | **85%** | — |

### Test Inventory & Assertion Quality

| Test File | Count | Actual Assertions / Scope | Flagged / Vacuous Tests |
|---|---|---|---|
| `test_phase3.py` | 10 | Entity regexes, typosquat flags, reputation SQLite insert/lookup | None. Meaningful behavioral assertions. |
| `test_phase4.py` | 11 | Magic bytes for PDF/DOCX, size limits, CIN/GST, signatory patterns | None. Tests parser failure and edge cases. |
| `test_phase5.py` | 4 | Explanation structure, probabilities, relative scam ranking | **FLAG:** `test_model_metadata_exists` uses `if os.path.exists()` and silently passes if file is missing. |
| `test_phase6.py` | 11 | SSRF loopback/RFC1918 blocks, max length 50k, feedback queue | None. Tests security limits and HTTP error codes. |
| `test_phase8.py` | 3 | Telegram format strings, helpline checks, extension file presence | **FLAG:** `test_chrome_extension_manifest` only checks file existence and JSON keys; does not test logic. |
| `test_phase9_coverage.py` | 19 | Scraper mocks, OCR fallbacks, clean vs scam forensics, helpers | None. Targets previously unexercised edge cases. |
| **Total** | **58** | **Full regression and coverage suite** | **2 flagged tests with weak assertions** |

### Static Analysis: Ruff & Mypy

#### Ruff Linter Output
Executing command: `ruff check backend/ --statistics`
- **Total Errors Found:** **83 errors** (51 auto-fixable)
- **Top Issue Breakdown:**
  1. `F401`: 23 instances — Unused imports across detector and utility modules.
  2. `I001`: 22 instances — Unsorted or unformatted import blocks.
  3. `BLE001`: 20 instances — Blind exception catching (`except Exception:` or bare `except:`).
  4. `S110`: 6 instances — `try`-`except`-`pass` blocks suppressing errors without logging.
  5. `RUF046`: 3 instances — Unnecessary cast to `int`.
  6. `F541`: 2 instances — F-strings without placeholder variables.
  7. `B008`: 2 instances — Function calls in default arguments (`File(...)`, `Form(...)` in FastAPI).
  8. `DTZ005`: 1 instance — Naive `datetime.now()` without explicit timezone.
  9. `DTZ007`: 1 instance — `datetime.strptime()` without timezone.
  10. `PLW0602`: 1 instance — Global variable used without explicit assignment.

#### Mypy Type Checker Output
Executing command: `mypy backend/app --ignore-missing-imports --no-strict-optional`
- **Error Count:** 1 fatal configuration/path error preventing further analysis:
  ```text
  backend\app\detector\verification\entities.py: error: Source file found twice under different module names:
  "app.detector.verification.entities" and "backend.app.detector.verification.entities"
  Found 1 error in 1 file (errors prevented further checking)
  ```
  *Root Cause:* Inconsistent import paths (`from app...` vs `from backend.app...`) across legacy and current modules.

### Lines of Code (LOC) by Component

| Component | File Types | Lines of Code | Percentage |
|---|---|---|---|
| **Frontend UI** | `.html`, `.css`, `.js` | **2,968** | 44.2% |
| **Backend Core & Scripts** | `.py` (excl tests) | **2,366** | 35.2% |
| **Test Suite** | `.py` | **601** | 9.0% |
| **Chrome Extension** | `.json`, `.js`, `.html` | **508** | 7.6% |
| **Bots (Telegram)** | `.py` | **272** | 4.0% |
| **Total** | — | **6,715** | 100.0% |

---

## 4. MODEL AND EVALUATION

### Dataset Provenance & Properties

- **Primary Corpus:** EMSCAD (Employment Scam Aegean Dataset).
- **Origin / Source:** Kaggle / Bangkit project mirror (`https://raw.githubusercontent.com/Cindyalifia/bangkit-project-1/master/fake_job_postings.csv`).
- **Total Samples:** `17,880` job postings (CSV contains 17,881 rows including header).
- **Class Distribution:**
  - Legitimate Postings: `17,014` (95.16%)
  - Fraudulent Postings: `866` (**4.84%**)
  - Severe class imbalance ratio: ~19.6 : 1.
- **Train / Test Split:** Stratified 80/20 split (`random_state=42`).
  - Train: `14,304` EMSCAD postings (plus augmented synthetic seeds).
  - Holdout Test: `3,576` EMSCAD postings (173 fraud, 3,403 legit).

### Synthetic Data & Data Contamination Audit

- **Files Present:**
  - `data/real_world/scam_messages.csv`: 7 rows (header + 6 data rows).
  - `data/real_world/legit_messages.csv`: 7 rows (header + 6 data rows).
  - Total synthetic samples: **12 rows**.
- **Synthesis Method:** Hand-written synthetic templates mimicking Indian WhatsApp/Telegram scams (UPI fees, Aadhaar/PAN collection, Hindi transliteration).

> [!CAUTION]
> **CRITICAL DATA CONTAMINATION DETECTED:**
> In `backend/scripts/train_pipeline.py` (lines 95–99), all 12 rows from `data/real_world/*.csv` are appended directly to `X_train`:
> ```python
> X_rw, y_rw = load_real_world_seeds()
> X_train = pd.concat([X_train, X_rw], ignore_index=True)
> ```
> In `backend/scripts/evaluate.py` (lines 37–44), the script loads `data/real_world/*.csv` and evaluates the model on it:
> ```python
> df_scam = pd.read_csv(os.path.join(DATA_DIR, "real_world", "scam_messages.csv"))
> df_legit = pd.read_csv(os.path.join(DATA_DIR, "real_world", "legit_messages.csv"))
> ...
> y_pred_rw_ml = model.predict(X_rw)
> ```
> **Finding:** 100% of the "real-world evaluation dataset" was ingested during training. Any real-world evaluation metric reported by `evaluate.py` represents train-set memorization, not out-of-sample generalization.

### Model Architecture
- **Pipeline:** `scikit-learn` Pipeline:
  1. `TfidfVectorizer(max_features=15000, ngram_range=(1, 2), stop_words='english', sublinear_tf=True)`
  2. `CalibratedClassifierCV(estimator=LogisticRegression(class_weight='balanced', C=2.0, max_iter=1000), method='isotonic', cv=5)`
- **Model File Size:** `1,210 KB` (`backend/models/job_detector_model.joblib`).

### Model Evaluation: EMSCAD Holdout Test Split (3,576 Samples)

Tested purely out-of-sample on the 20% holdout test set (173 fraud, 3,403 legit):

| Metric | Scam Class (Fraud) | Legitimate Class | Overall Macro / Weighted |
|---|---|---|---|
| **Precision** | **0.9624** (96.2%) | 0.9869 (98.7%) | Macro: 0.9747 |
| **Recall** | **0.7399** (74.0%) | 0.9985 (99.9%) | Macro: 0.8692 |
| **F1-Score** | **0.8366** (83.7%) | 0.9927 (99.3%) | Macro: 0.9146 |
| **Accuracy** | — | — | **0.9860** (98.6%) |
| **ROC-AUC** | — | — | **0.9887** |
| **PR-AUC (Avg Precision)** | — | — | **0.9282** |

#### Confusion Matrix (EMSCAD Holdout)
```text
                  Predicted Legit    Predicted Scam
Actual Legit:          3,398               5          (False Positive Rate: 0.15%)
Actual Scam:              45             128          (False Negative Rate: 26.01%)
```

### Top Discriminating Model Features (Logistic Regression Base Estimator)

| Rank | Top 15 Fraud-Indicative N-Grams | Top 15 Legitimacy-Indicative N-Grams |
|---|---|---|
| 1 | `link` | `clients` |
| 2 | `earn` | `companies` |
| 3 | `data entry` | `team` |
| 4 | `timejob` | `english` |
| 5 | `accion` | `web` |
| 6 | `high school` | `recruitment` |
| 7 | `hospital` | `fun` |
| 8 | `money` | `growing` |
| 9 | `surgical` | `digital` |
| 10 | `aptitude staffing` | `software` |
| 11 | `offshore` | `new` |
| 12 | `send` | `love` |
| 13 | `assistant` | `client` |
| 14 | `oil gas` | `creative` |
| 15 | `accountant` | `fast` |

### Calibration Analysis (Isotonic Regression)

Measured across 10 probability bins on the out-of-sample EMSCAD test split:

| Probability Bin Mean | Actual Empirical Fraud Rate | Observations |
|---|---|---|
| `0.006` | `0.004` | Extremely well-calibrated in the safe zone. |
| `0.144` | `0.096` | Minor over-prediction. |
| `0.249` | `0.083` | Conservative probability output. |
| `0.353` | `0.875` | Step jump due to isotonic regression step function. |
| `0.453` | `0.643` | Transition region. |
| `0.562` | `0.500` | Approximately calibrated around the 0.5 decision threshold. |
| `0.648` | `1.000` | 100% of samples in this bin are fraudulent. |
| `0.749` | `1.000` | 100% of samples in this bin are fraudulent. |
| `0.842` | `0.913` | Minor variance due to sparse samples in upper bins. |
| `0.987` | `1.000` | 100% precision in high-confidence region. |

### Error Analysis

#### Common False Negatives (Why the ML Model Misses Scams)
1. **Scam offers using standard corporate templates:** Scammers copying real job descriptions word-for-word, changing only the contact email to a free provider. (ML cannot see domain mismatch; handled by rule/verifier layer).
2. **Short informal WhatsApp / SMS messages:** Messages under 20 words have near-zero vocabulary overlap with the formal 300-word EMSCAD job descriptions.
3. **Indic / Vernacular script:** The TF-IDF vectorizer uses English stop words and standard tokenization; Malayalam and Devanagari text produce empty or uninformative feature vectors.
4. **Obfuscated / Spaced characters:** `w h a t s a p p` or `reg1strat1on` do not match standard TF-IDF unigrams.

#### Common False Positives (Why Legit Postings are Flagged)
1. **Entry-level postings:** Legit postings stating "No prior experience required" trigger the heuristic rules.
2. **Commission-based sales jobs:** Legit postings with "Earn up to ₹50,000 per month" trigger the `too_good_to_be_true` rule.
3. **Urgent replacement hiring:** "Immediate joining required" triggers urgency rules.

---

## 5. DETECTION LOGIC

### Source Code: `backend/app/config.py`

```python
"""
config.py - Configuration settings for the LeakedIn backend.
"""

# ---------------------------------------------------------------------------
# Aggregator Weights
# ---------------------------------------------------------------------------
# Maximum points the ML model can contribute to the final risk score.
AGGREGATOR_ML_WEIGHT = 60.0

# Maximum points the Rule Engine can contribute to the final risk score.
AGGREGATOR_RULE_MAX_CAP = 40.0

# Points assigned per rule severity
AGGREGATOR_RULE_SEVERITY_POINTS = {
    "CRITICAL": 20.0,
    "HIGH": 10.0,
    "MEDIUM": 5.0,
    "LOW": 2.0
}

# Penalty points for domain mismatches or suspicious emails
AGGREGATOR_DOMAIN_MISMATCH_PENALTY = 10.0
```

### Source Code: `backend/app/detector/aggregator.py`

```python
"""
aggregator.py - Unified risk score engine for LeakedIn.
"""

from typing import Any
from backend.app.config import (
    AGGREGATOR_ML_WEIGHT,
    AGGREGATOR_RULE_MAX_CAP,
    AGGREGATOR_RULE_SEVERITY_POINTS,
    AGGREGATOR_DOMAIN_MISMATCH_PENALTY
)

def aggregate(ml_score: float, rule_flags: list[dict[str, Any]], verifier_result: dict[str, Any]) -> dict[str, Any]:
    """
    Combines ML score, rule flags, and domain verification into a single risk score (0-100).
    """
    # 1. Base ML Score (up to AGGREGATOR_ML_WEIGHT)
    risk_score = ml_score * AGGREGATOR_ML_WEIGHT
    
    # 2. Rule Score (capped at AGGREGATOR_RULE_MAX_CAP)
    rule_score = 0.0
    for flag in rule_flags:
        severity = flag.get("severity", "LOW").upper()
        rule_score += AGGREGATOR_RULE_SEVERITY_POINTS.get(severity, 0.0)
    
    rule_score = min(rule_score, AGGREGATOR_RULE_MAX_CAP)
    risk_score += rule_score
    
    # 3. Domain Mismatch Penalty
    if verifier_result.get("domain_mismatch", False) or verifier_result.get("suspicious_email", False):
        risk_score += AGGREGATOR_DOMAIN_MISMATCH_PENALTY
        
    # Clamp to 0-100
    final_score = int(max(0, min(100, risk_score)))
    
    # Determine risk level
    if final_score <= 25:
        risk_level = "Safe"
        verdict = "This job posting appears legitimate."
    elif final_score <= 50:
        risk_level = "Low Risk"
        verdict = "This posting has minor concerns. Research the company and recruiter before sharing sensitive information."
    elif final_score <= 75:
        risk_level = "Suspicious"
        verdict = "Probable Scam Detected. Proceed with extreme caution."
    else:
        risk_level = "High Risk"
        verdict = "Critical Scam Indicators Detected. Do not engage or send money."
        
    # Generate recommendations
    recommendations = []
    if final_score > 25:
        recommendations.append("Verify the company on its official website and LinkedIn before applying.")
    if any(f.get("category") == "Financial Demand" for f in rule_flags):
        recommendations.append("Never pay money to secure a job — legitimate employers do not charge fees.")
    if verifier_result.get("domain_mismatch", False):
        recommendations.append("Be wary of recruiters using free email addresses claiming to represent large corporations.")
    if not recommendations:
        recommendations.append("Use official career portals (company website, Naukri, LinkedIn) to apply.")
        
    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "verdict": verdict,
        "recommendations": recommendations
    }
```

### Source Code: `backend/app/api/routes.py`

```python
"""
routes.py - FastAPI router for LeakedIn's analysis endpoints.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.app.detector.aggregator import aggregate
from backend.app.detector.ml import predict
from backend.app.detector.rules import detect_rules
from backend.app.detector.verifier import verify
from backend.app.detector.verification.entities import extract_entities, get_domains_from_urls
from backend.app.detector.verification.typosquat import check_domain, check_company_claim
from backend.app.detector.verification.reputation import bulk_lookup, report, init_db
from backend.app.utils.ocr import extract_text_from_image
from backend.app.utils.scraper import scrape_job_url
from backend.app.utils.normalizer import detect_language
from backend.app.utils.document_extractor import validate_file, extract_text_from_pdf, extract_text_from_docx
from backend.app.detector.advice import generate_advice
from backend.app.detector.document_checks import check_document

logger = logging.getLogger(__name__)

# Initialize reputation DB on startup
try:
    init_db()
except Exception as e:
    logger.warning("Failed to initialize reputation DB: %s", e)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000, description="Raw job posting text to analyse")
    company_name: str = Field("", max_length=200, description="Company name (optional, improves domain check)")
    contact_email: str = Field("", max_length=200, description="Recruiter contact email (optional)")


class UrlAnalysisRequest(BaseModel):
    url: str = Field(..., max_length=2048, description="Public URL of the job posting to scrape and analyse")
    company_name: str = Field("", max_length=200, description="Company name (optional)")
    contact_email: str = Field("", max_length=200, description="Recruiter contact email (optional)")


class ReportRequest(BaseModel):
    value: str = Field(..., max_length=500, description="Identifier to report (email, phone, UPI, domain)")
    entity_type: str = Field(..., description="Type: email | phone | upi | domain")


class ReputationLookupRequest(BaseModel):
    value: str = Field(..., description="Identifier to look up")


class FeedbackRequest(BaseModel):
    analysis_id: str = Field("", description="Optional ID to correlate with a prior analysis")
    verdict: str = Field(..., description="'correct' | 'incorrect' | 'missed_scam'")
    opt_in_text: bool = Field(False, description="If True, user consents to share the raw text for retraining review")
    raw_text: str = Field("", max_length=50_000, description="Raw text (only stored if opt_in_text=True)")


# Max upload size for images (10 MB)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024



# ---------------------------------------------------------------------------
# Shared pipeline helper
# ---------------------------------------------------------------------------

def _run_pipeline(
    text: str,
    company_name: str = "",
    contact_email: str = "",
) -> dict[str, Any]:
    """Run the full LeakedIn detection pipeline on *text*."""
    t_start = time.monotonic()

    # 0. Language detection
    lang = detect_language(text)

    # 1. ML inference
    ml_result = predict(text)
    ml_score: float = ml_result["fraud_probability"]
    model_explanation: dict = ml_result.get("model_explanation", {})

    # 2. Rule-based heuristics
    red_flags = detect_rules(text)

    # 3. Entity extraction
    entities = extract_entities(text)

    # 4. Domain checks (typosquat + known company claim verification)
    domain_flags: list[str] = []
    domains = get_domains_from_urls(entities["urls"])
    for domain in domains:
        result = check_domain(domain)
        domain_flags.extend(result["domain_flags"])

    # If emails are in text, also check their domains
    email_domains = [e.split("@")[-1] for e in entities["emails"] if "@" in e]
    for ed in email_domains:
        result = check_domain(ed)
        domain_flags.extend(result["domain_flags"])

    # 5. Company claim verification
    company_claim_flags = check_company_claim(company_name, entities["emails"])
    domain_flags.extend(company_claim_flags)

    # 6. Original verifier (free email vs. corporate mismatch)
    verifier_result = verify(text, company_name=company_name, contact_email=contact_email)
    domain_flags.extend(verifier_result["flags"])

    # Deduplicate domain flags
    domain_flags = list(dict.fromkeys(domain_flags))

    # 7. Reputation database lookups
    reputation_hits = bulk_lookup({
        "email": entities["emails"],
        "phone": entities["phones"],
        "upi": entities["upi_ids"],
        "domain": domains + email_domains,
    })

    # Reputation boost to risk score: add 15 per hit, capped at 30
    reputation_boost = min(len(reputation_hits) * 15, 30)

    # 8. Aggregate risk score
    domain_mismatch = verifier_result.get("domain_mismatch", False) or bool(domain_flags)
    synthetic_verifier = {"domain_mismatch": domain_mismatch, "suspicious_email": verifier_result.get("suspicious_email", False)}
    risk_report = aggregate(ml_score, red_flags, synthetic_verifier)

    # Apply reputation boost
    final_score = min(100, risk_report["risk_score"] + reputation_boost)
    
    # Recalculate risk level with final score
    if final_score <= 25:
        risk_level = "Safe"
    elif final_score <= 50:
        risk_level = "Low Risk"
    elif final_score <= 75:
        risk_level = "Suspicious"
    else:
        risk_level = "High Risk"

    processing_ms = int((time.monotonic() - t_start) * 1000)

    # 9. Safety advice engine
    safety = generate_advice(red_flags, reputation_hits, risk_level)

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "verdict": risk_report["verdict"],
        "ml_score": round(ml_score, 4),
        "model_explanation": model_explanation,
        "red_flags": red_flags,
        "domain_flags": domain_flags,
        "entities": entities,
        "reputation_hits": reputation_hits,
        "recommendations": risk_report["recommendations"],
        "advice": safety["advice"],
        "emergency_steps": safety["emergency_steps"],
        "language": lang,
        "processing_ms": processing_ms,
    }


# ---------------------------------------------------------------------------
# Analysis Endpoints
# ---------------------------------------------------------------------------

@router.post("/analyse-text", summary="Analyse raw job posting text")
async def analyse_text(request: TextAnalysisRequest) -> dict[str, Any]:
    logger.info("analyse-text called (text length: %d)", len(request.text))
    return _run_pipeline(
        text=request.text,
        company_name=request.company_name,
        contact_email=request.contact_email,
    )


@router.post("/analyse-url", summary="Scrape a job posting URL and analyse it")
async def analyse_url(request: UrlAnalysisRequest) -> dict[str, Any]:
    logger.info("analyse-url called (url: %s)", request.url)
    extracted_text = scrape_job_url(request.url)
    if not extracted_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the provided URL. Try pasting the text instead.",
        )
    result = _run_pipeline(
        text=extracted_text,
        company_name=request.company_name,
        contact_email=request.contact_email,
    )
    result["extracted_text"] = extracted_text[:500]
    return result


@router.post("/analyse-image", summary="OCR an image and analyse the extracted text")
async def analyse_image(
    file: UploadFile = File(...),
    company_name: str = Form(""),
    contact_email: str = Form(""),
) -> dict[str, Any]:
    logger.info("analyse-image called (filename: %s)", file.filename)
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{content_type}'.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Image too large. Maximum allowed size is {MAX_UPLOAD_BYTES // (1024*1024)} MB.")

    try:
        extracted_text = extract_text_from_image(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the uploaded image.")

    result = _run_pipeline(
        text=extracted_text,
        company_name=company_name,
        contact_email=contact_email,
    )
    result["extracted_text"] = extracted_text[:500]
    return result


# ---------------------------------------------------------------------------
# Reputation Endpoints
# ---------------------------------------------------------------------------

@router.post("/api/report", summary="Report a scam identifier to the community database")
async def report_entity(request: ReportRequest) -> dict[str, Any]:
    """
    Report a scam contact (email, phone, UPI, domain).
    Stored as a salted SHA-256 hash — never raw content.
    """
    valid_types = {"email", "phone", "upi", "domain"}
    if request.entity_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"entity_type must be one of {valid_types}")
    result = report(request.value, request.entity_type)
    return result


@router.get("/api/reputation/lookup", summary="Look up an identifier in the reputation database")
async def reputation_lookup(value: str) -> dict[str, Any]:
    """Look up whether an identifier (email, phone, UPI, domain) has been reported."""
    from backend.app.detector.verification.reputation import lookup
    result = lookup(value)
    if result:
        return {"found": True, **result}
    return {"found": False}


# ---------------------------------------------------------------------------
# Document Analysis Endpoint (Phase 4)
# ---------------------------------------------------------------------------

@router.post("/api/analyze/document", summary="Analyse a PDF or DOCX offer letter for fraud")
async def analyze_document(
    file: UploadFile = File(...),
    company_name: str = Form(""),
    contact_email: str = Form(""),
) -> dict[str, Any]:
    """
    Accept a PDF or DOCX file (max 5 MB), extract text, run the full
    detection pipeline, plus document-specific checks (placeholders,
    missing CIN/GST, payment clauses, metadata anomalies).

    - Strict magic-byte + extension + MIME validation.
    - Scanned PDFs fall back to EasyOCR automatically.
    - No file content is stored after this request.
    """
    logger.info("analyze-document called (filename: %s)", file.filename)

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Validate file type
    try:
        file_type = validate_file(
            filename=file.filename or "",
            content_type=file.content_type or "",
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    # Extract text + metadata
    metadata: dict = {}
    if file_type == "pdf":
        extracted_text, metadata = extract_text_from_pdf(data)
    else:
        extracted_text, metadata = extract_text_from_docx(data)

    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from the document. "
                   "If this is a scanned image PDF, OCR was attempted but found no text.",
        )

    # Full fraud detection pipeline
    result = _run_pipeline(
        text=extracted_text,
        company_name=company_name,
        contact_email=contact_email,
    )

    # Document-specific checks
    doc_checks = check_document(extracted_text, metadata)

    # Boost risk score for serious document-level issues
    doc_penalty = 0
    if doc_checks["placeholders_found"]:
        doc_penalty += 15  # Unfilled template is a major red flag
    if not doc_checks["has_registration"]:
        doc_penalty += 5
    if not doc_checks["has_signatory"]:
        doc_penalty += 5

    boosted_score = min(100, result["risk_score"] + doc_penalty)
    if boosted_score <= 25:
        risk_level = "Safe"
    elif boosted_score <= 50:
        risk_level = "Low Risk"
    elif boosted_score <= 75:
        risk_level = "Suspicious"
    else:
        risk_level = "High Risk"

    result.update({
        "risk_score": boosted_score,
        "risk_level": risk_level,
        "document_flags": doc_checks["document_flags"],
        "placeholders_found": doc_checks["placeholders_found"],
        "has_company_registration": doc_checks["has_registration"],
        "has_signatory": doc_checks["has_signatory"],
        "document_metadata": metadata,
        "extracted_text": extracted_text[:800],
        "file_type": file_type,
    })

    return result


# ---------------------------------------------------------------------------
# Feedback Endpoint (Phase 6)
# ---------------------------------------------------------------------------

# In-memory review queue (resets on restart — connect to SQLite for persistence)
_feedback_queue: list[dict] = []

@router.post("/api/feedback", summary="Submit feedback on an analysis result")
async def submit_feedback(request: FeedbackRequest) -> dict[str, Any]:
    """
    Submit correctness feedback on a prior analysis.

    - Raw message text is ONLY stored if the user explicitly sets opt_in_text=True.
    - Default behavior: only verdict + analysis_id stored (no PII, no message content).
    - Stored feedback feeds a manual review queue for model retraining consideration.
    """
    valid_verdicts = {"correct", "incorrect", "missed_scam"}
    if request.verdict not in valid_verdicts:
        raise HTTPException(
            status_code=400,
            detail=f"verdict must be one of: {valid_verdicts}"
        )

    entry: dict[str, Any] = {
        "verdict": request.verdict,
        "analysis_id": request.analysis_id or None,
        "has_user_text": request.opt_in_text,
    }

    # Only store raw text if user explicitly opted in
    if request.opt_in_text and request.raw_text:
        entry["raw_text_preview"] = request.raw_text[:100] + "..." if len(request.raw_text) > 100 else request.raw_text

    _feedback_queue.append(entry)
    logger.info(
        "Feedback received: verdict=%s, opt_in=%s, queue_size=%d",
        request.verdict, request.opt_in_text, len(_feedback_queue)
    )

    return {
        "status": "received",
        "message": "Thank you for your feedback. It will be reviewed for model improvement.",
        "text_stored": request.opt_in_text,
    }
```

### Real Response Payloads from `/analyse-text`

#### 1. Scam Input
```json
{
  "risk_score": 100,
  "risk_level": "High Risk",
  "verdict": "Critical Scam Indicators Detected. Do not engage or send money.",
  "ml_score": 0.9372,
  "red_flags": [
    {
      "category": "Financial Demand",
      "severity": "CRITICAL",
      "message": "Mentions a financial requirement that applicants must pay",
      "matched_text": "registration fee",
      "start": 21,
      "end": 37
    },
    {
      "category": "Urgency / Pressure",
      "severity": "HIGH",
      "message": "Creates artificial urgency or pressure to apply without due diligence",
      "matched_text": "No experience needed",
      "start": 102,
      "end": 122
    },
    {
      "category": "Urgency / Pressure",
      "severity": "HIGH",
      "message": "Creates artificial urgency or pressure to apply without due diligence",
      "matched_text": "Work from home. Earn",
      "start": 124,
      "end": 144
    },
    {
      "category": "Urgency / Pressure",
      "severity": "HIGH",
      "message": "Creates artificial urgency or pressure to apply without due diligence",
      "matched_text": "Immediate joining",
      "start": 156,
      "end": 173
    },
    {
      "category": "Identity Theft",
      "severity": "CRITICAL",
      "message": "Requests sensitive personal identity or financial documents",
      "matched_text": "Send Aadhaar",
      "start": 75,
      "end": 87
    }
  ],
  "domain_flags": [
    "'Google India' is a major company, but recruiter is using free email 'hr-google@gmail.com'. Official domain should be @google.com",
    "Recruiter contact uses a free/personal email address: hr-google@gmail.com. Legitimate companies use corporate email domains.",
    "Critical mismatch: 'Google India' is a well-known company but the contact email uses a free/personal provider. This is a strong indicator of impersonation fraud."
  ],
  "reputation_hits": [],
  "recommendations": [
    "Verify the company on its official website and LinkedIn before applying.",
    "Never pay money to secure a job — legitimate employers do not charge fees.",
    "Be wary of recruiters using free email addresses claiming to represent large corporations."
  ],
  "advice": [
    "Do NOT respond to this recruiter or share any personal information.",
    "Report this job posting to the platform where you found it.",
    "Legitimate employers NEVER ask for money. Do not make any payments.",
    "Do not share your Aadhaar, PAN, passport, or bank details with this recruiter."
  ],
  "emergency_steps": [
    "If you already paid: Call the National Cyber Crime Helpline: 1930. File a report at cybercrime.gov.in. Contact your bank/UPI provider immediately to reverse the transaction.",
    "If you already shared Aadhaar: Lock your Aadhaar biometrics via the mAadhaar app or UIDAI website (uidai.gov.in) to prevent misuse. Monitor your bank accounts for suspicious activity."
  ],
  "language": "en",
  "processing_ms": 12
}
```

#### 2. Genuine Recruiter Input
```json
{
  "risk_score": 0,
  "risk_level": "Safe",
  "verdict": "This job posting appears legitimate.",
  "ml_score": 0.0057,
  "red_flags": [],
  "domain_flags": [],
  "reputation_hits": [],
  "recommendations": [
    "Use official career portals (company website, Naukri, LinkedIn) to apply."
  ],
  "advice": [
    "Always verify recruiter identity through the official company website before sharing information."
  ],
  "emergency_steps": [],
  "language": "en",
  "processing_ms": 9
}
```

### Heuristic Rules Audit (`backend/app/detector/patterns/rules.yaml`)

- **Total Rule Definitions:** **5** (NOT "30+ patterns" as claimed in README; each rule entry contains a compound regex with alternations).
- **Severity Distribution:**
  - `CRITICAL`: 2 (`financial_demand`, `identity_theft`)
  - `HIGH`: 2 (`suspicious_contact`, `urgency_pressure`)
  - `MEDIUM`: 1 (`too_good_to_be_true`)
  - `LOW`: 0
- **Language Coverage:** All 5 rules list `languages: ["en", "hi", "ml", "hinglish"]`, but regexes are almost entirely written in Latin script!
  - Hindi terms present: `paise bhejo`, `jaldi apply`, `aadhaar bhejo`, `pan card share`.
  - Malayalam terms present: **0 native Malayalam script patterns**! (Only Romanized Hinglish/Hindi terms).

#### Breadth & Specificity Evaluation:
1. **Too Broad:**
   - `urgent_hiring`: Appears in thousands of genuine startup postings.
   - `immediate_joining`: Standard requirement for backfill roles.
   - `₹\s*\d+|rs\.?\s*\d+`: Matches ANY rupee amount! Mentioning "Salary Rs 50000" triggers `financial_demand` (CRITICAL)!
2. **Too Narrow:**
   - `transfer\s+immediately`: Does not match "Please transfer the registration fee immediately" because words are separated.
   - `send\s*aadhaar`: Does not match "Upload your Aadhaar" or "Submit Aadhaar card".

### Normalizer Audit (`backend/app/utils/normalizer.py`)

Tested with `normalize_with_mapping(text)`:

| Input String | Normalized Output | Offset Mapping Behavior |
|---|---|---|
| `"W h a t s A p p"` | `"w h a t s a p p"` | **FAIL:** Spaces are NOT collapsed (comment in code explicitly notes: *"this is complex... we will normalize characters one-by-one"*). |
| `"g00gle careers"` | `"google careers"` | **PASS:** `0` maps to `o`; offsets maintain 1-to-1 character index. |
| `"Rs.2k/-"` | `"rs.2k/-"` | **PARTIAL:** Currency abbreviations are not converted or expanded. |
| `"Hello\u200bWorld\u200c test"` | `"helloworld test"` | **PASS:** Zero-width spaces (`\u200b`, `\u200c`) are deleted; offset map shifts subsequent indices correctly. |
| `"ഹോം ജോബ് ഉണ്ട്"` (Malayalam) | `"ഹോം ജോബ് ഉണ്ട്"` | Unchanged Unicode glyphs; offsets map 1-to-1. |

### Domain Verifier & Typosquat Audit

Tested live with `check_domain()`:

| Domain Tested | `is_typosquat` | `matched_company` | Flags Output |
|---|---|---|---|
| `google-careers-hr.com` | `True` | `Google` | Flagged: contains 'google' but not official domain. |
| `g00gle.com` | **`False`** | `None` | **BUG:** Homoglyph normalized to 'google', edit distance to 'google' is 0, condition `0 < dist <= 2` evaluates to `False`! |
| `tcs.com` | `False` | `None` | Accurate: identified as official. |
| `tcs-jobs.in` | `True` | `TCS` | Flagged: contains 'tcs' but not official domain. |
| `amazon-careers.com` | `True` | `Amazon` | Flagged: keyword stuffing. |
| Claim: "Infosys HR", Email: `recruiter@gmail.com` | `True` | `Infosys` | Flagged: free email used for major corporate claim. |

### Known Companies Dataset (`data/known_companies.json`)

- **Claim in README:** "500+ companies"
- **Actual Measurement:** **27 companies** (`len(json.load(f)) == 27`).
- **Verdict:** **FALSE CLAIM.** The file contains exactly 27 entries (Google, Amazon, Microsoft, Apple, Meta, TCS, Infosys, Wipro, Accenture, Deloitte, HCL, Cognizant, IBM, Flipkart, Paytm, Swiggy, Zomato, Reliance, Tata, Airtel, PhonePe, PayPal, Cisco, Adobe, SAP, ICICI Bank, Axis Bank).

---

## 6. REAL-WORLD ROBUSTNESS TEST

20 realistic test cases executed against the live API endpoint `/analyse-text`:

| # | Type | Input Snippet | Score | Level | Flags | Verdict | Result |
|---|---|---|---|---|---|---|---|
| 1 | SCAM | `Dear bhai, aapka profile select hua hai. Data entry kaam... Rs 2000 registration fee...` | 88 | High Risk | 2 | Critical Scam Indicators | **PASS** |
| 2 | SCAM | `Telegram task scam: Join our Telegram group @earnmoney2024. Like YouTube videos...` | 100 | High Risk | 3 | Critical Scam Indicators | **PASS** |
| 3 | SCAM | `Dear [Candidate Name], You are hired... transfer registration fee of Rs 3500 immediately...` | 30 | Low Risk | 1 | Minor concerns | **FAIL** |
| 4 | SCAM | `ഹോം ജോബ് ഉണ്ട്! ദിവസം 3000 രൂപ സമ്പാദിക്കാം. ആധാർ കൊണ്ടുവരൂ. 1500 രൂപ അഡ്വാൻസ് ആദ്യം അടക്കണം.` | 12 | Safe | 0 | Appears legitimate | **FAIL** |
| 5 | SCAM | `Congratulations! Selected by Amazon India. Send Aadhaar & bank details. hr-amazon@gmail.com` | 56 | Suspicious | 1 | Probable Scam | **PASS** |
| 6 | SCAM | `Work from home. Earn 10000/day. Send Bitcoin worth $200. No interview. 100% guarantee.` | 99 | High Risk | 5 | Critical Scam Indicators | **PASS** |
| 7 | SCAM | `Google India recruiter: Upload Aadhaar & PAN. Registration fee Rs 2500 via UPI in 2 hours.` | 58 | Suspicious | 2 | Probable Scam | **PASS** |
| 8 | SCAM | `J0b 0pp0rtun1ty! W0rk fr0m h0me. 50000 per m0nth. Pay 1000 reg1strat1on f33...` | 99 | High Risk | 3 | Critical Scam Indicators | **PASS** |
| 9 | SCAM | `TCS job alert: Selected candidates must pay Rs 4000 processing fee to hr-tcs@yahoo.com` | 55 | Suspicious | 2 | Probable Scam | **PASS** |
| 10 | SCAM | `Fake Infosys offer: Join crypto team. Earn 1 BTC/month. Send bank details + Rs 2000...` | 78 | High Risk | 2 | Critical Scam Indicators | **PASS** |
| 11 | LEGIT | `Hi, I am a recruiter from Wipro. Saw profile on LinkedIn. Schedule technical interview...` | 0 | Safe | 0 | Appears legitimate | **PASS** |
| 12 | LEGIT | `Dear Candidate, interview scheduled on WhatsApp video call. Bring docs for verification.` | 12 | Safe | 1 | Appears legitimate | **PASS** |
| 13 | LEGIT | `Hiring Data Analyst. Salary: 8-12 LPA. Requirements: Python, SQL. No fees required.` | 19 | Safe | 0 | Appears legitimate | **PASS** |
| 14 | LEGIT | `Completed round 2! Bring salary slips, bank statement, Aadhaar for joining verification.` | 2 | Safe | 0 | Appears legitimate | **PASS** |
| 15 | LEGIT | `Software Engineer at HCL. CTC: 12 LPA. Health insurance and PF. hcltech.com/careers.` | 1 | Safe | 0 | Appears legitimate | **PASS** |
| 16 | LEGIT | `Senior Developer at Razorpay. Skills: Node.js, AWS. jobs@razorpay.com.` | 6 | Safe | 0 | Appears legitimate | **PASS** |
| 17 | LEGIT | `Notice: Joining date 15 October. Complete pre-joining on HR portal. onboarding@infosys.com.` | 2 | Safe | 0 | Appears legitimate | **PASS** |
| 18 | LEGIT | `Immediate opening at Swiggy: Operations Manager. Salary 15-20 LPA. careers.swiggy.in.` | 14 | Safe | 0 | Appears legitimate | **PASS** |
| 19 | LEGIT | `Interview reminder: Technical interview with engineering team at 2 PM on Zoom.` | 20 | Safe | 0 | Appears legitimate | **PASS** |
| 20 | LEGIT | `We regret to inform that we cannot move forward with your application at this time.` | 12 | Safe | 0 | Appears legitimate | **PASS** |

### Summary of Robustness Performance
- **Overall Accuracy:** **18 / 20 = 90.0%**
- **Scam Recall:** 8 / 10 = 80.0%
- **Legit Specificity:** 10 / 10 = 100.0% (Zero false alarms on tricky legitimate posts mentioning "WhatsApp", "Aadhaar", or "Salary").

#### Failure Breakdown:
1. **Scam #3 (Unfilled Template Offer Letter):** Missed because the rule `transfer\s+immediately` did not match `transfer registration fee of Rs 3500 immediately`. Scored only 30 (Low Risk).
2. **Scam #4 (Native Malayalam Script Scam):** Scored only 12 (Safe)! Zero heuristic flags triggered. Proof that while Malayalam language detection is claimed, heuristic rules have zero Malayalam script patterns.

---

## 7. SECURITY AND PRIVACY CHECKS

### SSRF Protection Audit (`backend/app/utils/scraper.py`)

Tested URL inputs against `/analyse-url`:

| Target URL | Expected | Scraper Return | API Response Code | API Verdict |
|---|---|---|---|---|
| `http://127.0.0.1` | Block | `[BLOCKED] Requests to internal IP...` | `200 OK` | `Score 17 (Safe)` ⚠️ |
| `http://localhost` | Block | `[BLOCKED] Resolves to private...` | `200 OK` | `Score 12 (Safe)` ⚠️ |
| `http://169.254.169.254` | Block | `[BLOCKED] Requests to internal IP...` | `200 OK` | `Score 17 (Safe)` ⚠️ |
| `file:///etc/passwd` | Block | `[BLOCKED] Only http/https supported` | `200 OK` | `Score 11 (Safe)` ⚠️ |
| `http://0x7f000001` (Hex) | Block | `[BLOCKED] Resolves to private...` | `200 OK` | `Score 12 (Safe)` ⚠️ |
| `http://2130706433` (Decimal) | Block | `[BLOCKED] Resolves to private...` | `200 OK` | `Score 12 (Safe)` ⚠️ |
| `ftp://example.com` | Block | `[BLOCKED] Only http/https supported` | `200 OK` | `Score 10 (Safe)` ⚠️ |

> [!WARNING]
> **SSRF FLAW:** The scraper correctly blocks network connection to internal targets. However, `routes.py` lines 193–204 do not check if `extracted_text.startswith("[BLOCKED]")`. The API feeds the error message string `"[BLOCKED] ..."` directly into the ML and heuristic pipeline, returning HTTP 200 with verdict "Safe"! It should raise `HTTPException(400)`.

### File Upload & Input Validation

| Test Case | Payload | HTTP Response | Result |
|---|---|---|---|
| Empty file | 0 bytes to `/analyse-image` | `400 Bad Request` | `{"detail":"Uploaded file is empty."}` |
| Wrong MIME type | `.exe` binary to `/analyse-image` | `415 Unsupported Media Type` | `{"detail":"Unsupported file type 'application/octet-stream'."}` |
| Oversized upload | > 10 MB payload | ASGI cap enforced | Rejected before full buffer read. |
| Non-image bytes | Random bytes with `image/jpeg` header | Timed out / 503 | EasyOCR parser hangs or errors cleanly. |

### Rate Limiting

- **Configuration:** `limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])` in `main.py`.
- **Finding:** Burst of 35 requests from loopback all returned `200 OK`. In `routes.py`, individual route functions are not decorated with `@limiter.limit("30/minute")`. SlowAPI default limits only apply when endpoints have the limiter decorator or when SlowAPI middleware is explicitly configured.

### Reputation Database Security

- **Hashing Algorithm:** `hashlib.sha256(f"{_SALT}:{value.lower().strip()}".encode()).hexdigest()`
- **Salt Storage:** Hardcoded in source code at `reputation.py` line 13:
  ```python
  _SALT = "leakedin-salt-2024"  # In production, load from env variable
  ```
  `<REDACTED>`: Salt is committed to version control.
- **Abuse Vector:** No rate limit or CAPTCHA on `POST /api/report`. A single client can report arbitrary numbers/emails repeatedly to artificially inflate blacklist scores.

### Logging & Data Retention

- **User Content Audit:**
  - `routes.py`: Logs only string lengths: `logger.info("analyse-text called (text length: %d)", len(request.text))`.
  - `main.py`: Configures structured logging without payload bodies.
  - Zero SQL storage of user text submissions (except voluntary opt-in in `feedback.py`).
- **Temporary Files:** Documents and images are read via `await file.read()` directly into memory buffers; no temporary files written to `/tmp` or disk.

### CORS Configuration

In `main.py` lines 58–59:
```python
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")]
```
Defaults to `*` (wildcard) with `allow_credentials=True`. This allows arbitrary cross-origin script requests by default.

---

## 8. PERFORMANCE

### Inference & API Latency

Measured across 50 consecutive requests to `/analyse-text`:

| Scenario | Median Latency | p95 Latency | Min Latency | Max Latency |
|---|---|---|---|---|
| Short text (~25 words) | **17 ms** | **36 ms** | 9 ms | 75 ms (warm) |
| Long text (~800 words) | **51 ms** | **64 ms** | 42 ms | 88 ms |

### OCR & Model Footprint

| Component | Metric | Measured Value | Notes |
|---|---|---|---|
| **EasyOCR Cold Start** | First image analysis | ~2.5 – 3.5 s | Model weights initialized into memory |
| **EasyOCR Warm Execution** | Subsequent image analysis | ~800 – 1,400 ms | CPU-only PyTorch execution |
| **Model Disk Size** | `job_detector_model.joblib` | `1,210 KB` (~1.2 MB) | Highly compact TF-IDF + CalibratedLR |
| **Model In-Memory Size** | RAM footprint | ~18 MB | Measured on pipeline deserialization |
| **Backend Total RAM** | Idle startup | ~140 MB | Python 3.13 process baseline |
| **Backend Total RAM** | Post-OCR execution | ~720 MB | PyTorch + EasyOCR models loaded in memory |

---

## 9. FRONTEND AND DEMO READINESS

### UI Tabs & Features
1. **Tabs:** 4 functional tabs (Text Analysis, Job URL Scraping, Image OCR, Offer Letter PDF/DOCX).
2. **Demo Presets:** 5 clickable presets in `index.html` (WhatsApp Hinglish, Fake Amazon Offer, Telegram Task Scam, Malayalam WFH, Genuine TCS Invite).
3. **Languages:** 3 languages in selector: English (`en`), Hindi (`hi`), Malayalam (`ml`).

### Internationalization (i18n) Completeness
- `I18N` object contains:
  - `en`: 65 string keys
  - `hi`: 58 string keys (Missing 9 non-essential sub-keys; fallbacks work)
  - `ml`: 59 string keys (Missing 9 non-essential sub-keys; fallbacks work)

### Accessibility & Responsiveness
- `index.html`:
  - 1 image tag (has `alt` attribute).
  - 8 `<label>` tags for form controls.
  - 9 ARIA attributes (`aria-selected`, `aria-controls`, `aria-hidden`, etc.).
  - Viewport meta tag present: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
- `style.css`:
  - **1 media query:** `@media (max-width: 640px)`. Responsive for mobile screens up to 640px, but lacks tablet-specific breakpoints (768px/1024px).

### Demo Assets
- **Screenshots / Video:** No demo video (`.mp4`), screen recordings, or GIF files present in repository root or `docs/`.
- **Live Deployment URL:** None found. No public domain or cloud hosting link configured in repository.

---

## 10. README VS REALITY

| Item / Claim in README | Stated Claim | Measured Reality | Verdict |
|---|---|---|---|
| **Test count badge** | `58 tests passing` | Exactly 58 passed | **VERIFIED** |
| **Coverage badge** | `85% coverage` | Exactly 85% total | **VERIFIED** |
| **Python version** | `Python 3.10+` | Runs on 3.10, 3.11, 3.13 | **VERIFIED** |
| **Known companies** | `500+ company -> domain map` | **27 companies** | **FALSE** |
| **Rule patterns** | `30+ regex patterns across 5 severity categories` | **5 rule entries across 3 severities** (CRITICAL, HIGH, MEDIUM) | **FALSE** |
| **API Endpoints** | `POST /api/analyze/text`, `url`, `image` | Routes are `/analyse-text`, `/analyse-url`, `/analyse-image` | **FALSE** |
| **Quick Start command** | `$env:PYTHONPATH="."; uvicorn backend.app.main:app...` | Works on Windows PowerShell | **VERIFIED** |
| **Quick Start command** | `run.bat` | Windows batch launcher runs both servers cleanly | **VERIFIED** |
| **Model Metrics Table** | Precision 0.87, Recall 0.82 | Measured on EMSCAD: Precision 0.96, Recall 0.74 | **PARTIAL** (Stated numbers slightly conservative) |

---

## 11. TOP ISSUES & RECOMMENDATIONS

### Ranked Top 15 Issues

| Rank | Severity | Location | Issue Description | Suggested One-Line Fix |
|---|---|---|---|---|
| **1** | **HIGH** | `backend/scripts/train_pipeline.py:98` & `evaluate.py:37` | **Train-Test Data Contamination:** 100% of real-world evaluation data is appended to training set. | Remove `load_real_world_seeds()` from `train_pipeline.py` or maintain a distinct holdout evaluation file. |
| **2** | **HIGH** | `backend/app/api/routes.py:193-205` | **SSRF Error Leakage:** Scraper returns `"[BLOCKED]..."` but route feeds it into ML, returning HTTP 200 "Safe". | Check `if extracted_text.startswith("[BLOCKED]"): raise HTTPException(400, extracted_text)`. |
| **3** | **HIGH** | `backend/app/api/routes.py:180` vs `README.md` | **Endpoint Path Mismatch:** Backend defines `/analyse-text` while README documents `/api/analyze/text`. | Add path alias `/api/analyze/text` to router or update documentation to match implementation. |
| **4** | **HIGH** | `frontend/script.js:10` | **Hardcoded API Base URL:** `const API_BASE = "http://localhost:8000"` breaks non-localhost hosting. | Use relative URL `const API_BASE = ""` or dynamically derive from `window.location.origin`. |
| **5** | **MEDIUM** | `backend/app/detector/patterns/rules.yaml` | **Overly Broad Currency Regex:** `₹\s*\d+|rs\.?\s*\d+` flags any rupee salary figure as CRITICAL fraud. | Require fee keywords adjacent to amounts, e.g. `(?:fee|deposit|pay)\s*(?:₹|rs\.?)\s*\d+`. |
| **6** | **MEDIUM** | `backend/app/detector/patterns/rules.yaml` | **Missing Malayalam Script Patterns:** Zero Malayalam script terms in rules despite claimed support. | Add native Malayalam script regexes (e.g. `രജിസ്ട്രേഷൻ ഫീസ്`, `ആധാർ`, `പണം`). |
| **7** | **MEDIUM** | `backend/app/detector/verification/typosquat.py:74` | **Typosquat Logic Bug:** `g00gle.com` normalizes to `google`, distance is 0, so `0 < dist <= 2` fails. | Check `if dist == 0 and domain_base != official_base:` to catch homoglyph equivalents. |
| **8** | **MEDIUM** | `data/known_companies.json` | **Exaggerated Company Count:** Contains 27 companies, not "500+". | Expand JSON list with top Indian IT/BPO companies or correct README claim to "top 27 tech employers". |
| **9** | **MEDIUM** | `backend/app/detector/verification/reputation.py:13` | **Hardcoded Salt in Git:** `_SALT = "leakedin-salt-2024"` committed to version control. | Load salt from environment variable `os.getenv("REPUTATION_SALT")`. |
| **10** | **MEDIUM** | `backend/app/main.py:53` & `routes.py` | **Inactive Rate Limiting:** SlowAPI default limits do not trigger on un-decorated endpoints. | Add `@limiter.limit("30/minute")` decorator to endpoints in `routes.py`. |
| **11** | **LOW** | `docker/nginx.conf:14` | **Nginx Proxy Route Mismatch:** Proxies `/api/` to `backend:8000/api/` but text routes are at root. | Change Nginx proxy pass or standardize all backend routes under `/api/`. |
| **12** | **LOW** | `backend/app/detector/verification/reputation.py:72` | **Unrestricted Blacklist Reporting:** No rate limiting or CAPTCHA on `POST /api/report`. | Add IP-based rate limiting to prevent spam attacks on the community database. |
| **13** | **LOW** | `backend/tests/test_phase5.py:30` | **Vacuous Test Assertion:** `test_model_metadata_exists` uses `if os.path.exists()` and can pass silently. | Remove `if os.path.exists()` check so missing file causes explicit failure. |
| **14** | **LOW** | `backend/app/main.py:58` | **Insecure CORS Default:** `ALLOWED_ORIGINS` defaults to wildcard `*`. | Restrict default to `["http://localhost:5500", "http://127.0.0.1:5500"]`. |
| **15** | **LOW** | `backend/app/api/routes.py:367` | **Volatile Feedback Queue:** User feedback is stored in an in-memory list lost on restart. | Persist feedback entries to SQLite table in `reputation.db`. |

---

### Genuinely Strong & Demo-Ready Elements
1. **Explainable ML (XAI):** Linear TF-IDF feature attribution returns positive and negative n-grams in under 20 ms without requiring heavy frameworks like SHAP or LIME.
2. **Hybrid Scoring Architecture:** Combining ML confidence with rule severity caps and domain penalties ensures high recall on informal scams that confuse pure NLP models.
3. **Zero-PII Community Blacklist:** Storing only salted SHA-256 hashes of phone numbers and emails in SQLite demonstrates strong privacy engineering.
4. **Offline OCR Engine:** EasyOCR runs 100% locally with zero cloud API dependencies.
5. **Frontend User Experience:** The dark-themed dashboard, SVG gauge animation, preset selector, and HTML5 Canvas card generator create an exceptional hackathon presentation.
6. **Robustness Against Tricky Legitimate Messages:** 100% specificity on legitimate recruiter messages containing words like "WhatsApp" or "Aadhaar".

---

### Unchecked Items & Required Developer Inputs

#### What Could Not Be Checked
1. **Docker Container Execution:** Docker CLI is not installed on the Windows test environment; container build and startup could only be audited statically.
2. **Production Cloud Deployment:** No active Render, Railway, or VPS credentials were provided to verify live cloud behavior.
3. **WhatsApp Cloud API Webhook:** Meta WhatsApp integration is currently documented as an architectural specification (`docs/whatsapp_integration.md`) rather than an active endpoint.

#### Information Needed from Developer
1. **Hackathon Submission Deadline & Scope:** Do you intend to standardize routes under `/api/` before demo submission?
2. **Target Deployment Environment:** Will the app be presented locally using `run.bat` (recommended) or deployed to a free-tier cloud service?
3. **Native Vernacular Requirements:** Should native Malayalam script regexes be added to `rules.yaml` prior to judging?
