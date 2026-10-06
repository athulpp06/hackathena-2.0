# LeakedIn — Evaluation 1 Experimental Results & Pipeline Audit

**Date of Execution**: 2026-10-06  
**Execution Environment**: Python 3.12.6, Windows PowerShell, virtualenv `.venv`  
**Evaluation Scope**: Job Posting Scam Analyser Pipeline Validation  

---

## 🛠️ Commands Executed

The results recorded in this document were generated using the following commands:

```powershell
# Step 1: Execute 4 evaluation texts through the live API / pipeline
.\.venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from backend.app.main import app; ..."

# Step 2: Run the full evaluation benchmark suite
.\.venv\Scripts\python.exe backend/scripts/run_benchmark_evaluation.py

# Step 3: Inspect model training metadata
Get-Content backend/models/metadata.json

# Step 4: Run evaluation integrity validation tests
.\.venv\Scripts\pytest.exe tests/test_evaluation_integrity.py -v
```

---

## 🔬 Section 1: Per-Text Evaluation Results

Each text below was evaluated using the exact pipeline logic powering the `/api/analyze/text` endpoint (`backend.app.detector.aggregator.analyse` and `backend.app.detector.ml.predict`).

---

### Text A — Obvious Advance-Fee Scam

| Metric / Layer | Output Value |
| :--- | :--- |
| **Declared Company** | `Google India` |
| **Contact Email** | `hr.google.careers@gmail.com` |
| **Input Text** | `"Congratulations! You are selected for Work From Home Data Entry at Google India. Salary Rs 45,000/month, no interview needed. Pay Rs 1,500 refundable registration fee via UPI to confirm your seat. Offer expires in 24 hours. Contact us on WhatsApp only."` |
| **Gatekeeper Decision** | `is_job_posting: True` (Confidence: `0.95`, Type: `job_posting`) |
| **Gatekeeper Reasoning** | `"Recruitment structure, role description, and employment terms verified."` |
| **ML-Only Fraud Probability** | **`0.9222`** (92.22%) |
| **XAI Top Fraud n-grams** | `rs` (+1.7809), `data entry` (+0.7493), `fee` (+0.5131), `work home` (+0.4752), `entry` (+0.3969) |
| **XAI Top Legit n-grams** | `india` (+0.1672), `interview` (+0.1541), `google` (+0.1416), `hours` (+0.1079), `45` (+0.0630) |
| **Rules Engine Penalty** | `77` (5 flags triggered) |
| **Rules Triggered** | 1. **No Interview or Instant Selection** (`Urgency / Pressure`, `HIGH`, Matched: `"no interview needed"`, Offsets: `[105, 124]`)<br>2. **Requires candidate to pay a registration or joining fee** (`Financial Demand`, `CRITICAL`, Matched: `"registration fee"`, Offsets: `[150, 166]`)<br>3. **Artificial scarcity — limited seats, time-limited offer** (`Urgency / Pressure`, `HIGH`, Matched: `"Offer expires in 2"`, Offsets: `[197, 215]`)<br>4. **Claims job offer is given without any interview** (`Too Good To Be True`, `MEDIUM`, Matched: `"no interview needed"`, Offsets: `[105, 124]`)<br>5. **Unsolicited offer letter claiming to be from a known company** (`Brand Impersonation`, `MEDIUM`, Matched: `"Congratulations! You are selected for Work From Home Data Entry at Google"`, Offsets: `[0, 73]`) |
| **Domain / Verifier Flags** | 1. **Free Webmail Used for Corporate Contact** (`FREE_WEBMAIL`, `HIGH`): Recruiter uses `hr.google.careers@gmail.com` instead of corporate domain.<br>2. **Company Identity Mismatch** (`DOMAIN_MISMATCH`, `CRITICAL`): Claims to be 'Google India', but email does not use expected official domain(s) `google.com` or `alphabet.com`. |
| **Domain Penalty** | `50` |
| **Final Risk Score** | **`100 / 100`** |
| **Risk Level** | **`High Risk`** |
| **Pipeline Verdict** | `"Critical Scam Indicators Detected (Critical scam indicators). Do not engage or send money."` |

---

### Text B — Genuine Corporate Job Posting

| Metric / Layer | Output Value |
| :--- | :--- |
| **Declared Company** | `Tata Consultancy Services` |
| **Contact Email** | `careers@tcs.com` |
| **Input Text** | `"TCS is hiring Associate Software Engineers for 2026. Eligibility: B.E./B.Tech with 60% or above. Apply only through the official careers portal. The process includes an online test and two interviews. TCS never charges any fee at any stage of recruitment."` |
| **Gatekeeper Decision** | `is_job_posting: True` (Confidence: `0.95`, Type: `job_posting`) |
| **Gatekeeper Reasoning** | `"Recruitment structure, role description, and employment terms verified."` |
| **ML-Only Fraud Probability** | **`0.0197`** (1.97%) |
| **XAI Top Fraud n-grams** | `fee` (+0.6466), `apply` (+0.2127), `hiring` (+0.1454), `online` (+0.1091), `test` (+0.0961) |
| **XAI Top Legit n-grams** | `recruitment` (+0.5111), `software` (+0.3258), `associate` (+0.3050), `interviews` (+0.3022), `tech` (+0.2296) |
| **Rules Engine Penalty** | `0` (0 flags triggered) |
| **Rules Triggered** | *None* |
| **Domain / Verifier Flags** | *None* (Verified official domain `tcs.com` matches Tata Consultancy Services) |
| **Domain Penalty** | `0` |
| **Final Risk Score** | **`1 / 100`** |
| **Risk Level** | **`Safe`** |
| **Pipeline Verdict** | `"This job posting appears legitimate. No significant fraud signals detected."` |

---

### Text C — Obfuscated Scam with Leetspeak & Spacing

| Metric / Layer | Output Value |
| :--- | :--- |
| **Declared Company** | *(none provided)* |
| **Contact Email** | *(none provided)* |
| **Input Text** | `"Urgent hiring!! Pay ₹5,OOO training kit fee to get ph0ne verified job. Send money on WhatsApp 98xxxxxx10 today, limited seats."` |
| **Gatekeeper Decision** | `is_job_posting: True` (Confidence: `0.85`, Type: `job_posting`) |
| **Gatekeeper Reasoning** | `"Recruitment structure, role description, and employment terms verified."` |
| **ML-Only Fraud Probability** | **`0.9145`** (91.45%) |
| **XAI Top Fraud n-grams** | `fee` (+0.7359), `money` (+0.7175), `send` (+0.6391), `urgent` (+0.4562), `pay` (+0.3856) |
| **XAI Top Legit n-grams** | `kit` (+0.0976), `send money` (+0.0626), `today` (+0.0444), `job` (+0.0335) |
| **Rules Engine Penalty** | `100` (6 flags triggered) |
| **Rules Triggered** | 1. **Mandatory Equipment or Software Purchase** (`Financial Demand`, `CRITICAL`, Matched: `"training kit fee"`, Offsets: `[27, 43]`)<br>2. **No Interview or Instant Selection** (`Urgency / Pressure`, `HIGH`, Matched: `"Urgent hiring"`, Offsets: `[0, 13]`)<br>3. **Requires candidate to pay for training or a security deposit** (`Financial Demand`, `CRITICAL`, Matched: `"kit fee"`, Offsets: `[36, 43]`)<br>4. **Requests money via wire transfer, Western Union, MoneyGram, or hawala** (`Financial Demand`, `CRITICAL`, Matched: `"Send money "`, Offsets: `[71, 82]`)<br>5. **Artificial scarcity — limited seats, time-limited offer** (`Urgency / Pressure`, `HIGH`, Matched: `"limited seats"`, Offsets: `[112, 125]`)<br>6. **Mild urgency that could be legitimate — context-dependent** (`Urgency / Pressure`, `LOW`, Matched: `"Urgent hiring"`, Offsets: `[0, 13]`) |
| **Domain / Verifier Flags** | **No Verifiable Contact Email Found** (`NO_CONTACT_INFO`, `LOW`): No official email provided. |
| **Domain Penalty** | `5` |
| **Final Risk Score** | **`87 / 100`** |
| **Risk Level** | **`High Risk`** |
| **Pipeline Verdict** | `"Critical Scam Indicators Detected (Critical scam indicators). Do not engage or send money."` |

#### Normalizer Analysis for Text C

```text
Original String  : Urgent hiring!! Pay ₹5,OOO training kit fee to get ph0ne verified job. Send money on WhatsApp 98xxxxxx10 today, limited seats.
Normalized String: urgent hiring!! pay ₹s,ooo training kit fee to get phone verified job. send money on whatsapp 98xxxxxxio today, limited seats.
```

**Modifications made by `backend.app.utils.normalizer`**:
1. **Homoglyph & Case Normalization**: `Urgent`, `Pay`, and `WhatsApp` lowercased to `urgent`, `pay`, and `whatsapp`.
2. **Leetspeak Homoglyph Substitution (`ph0ne` -> `phone`)**: Leetspeak digit `'0'` was mapped to `'o'` within the mixed-alphanumeric token `ph0ne`, enabling keyword rules and entity extractors to detect `phone`.
3. **Number/Letter Obfuscation (`5,OOO` -> `s,ooo`)**: The uppercase letter 'O's used to disguise numeric zeros were lowercased (`ooo`), and leetspeak substitution normalized mixed tokens.
4. **Offset Preservation**: `normalize_with_mapping` preserved the exact 1-to-1 character index mapping so that spans detected in the normalized text map directly back to character indices `[27, 43]` (`"training kit fee"`) and `[71, 82]` (`"Send money "`) in the user's raw input.

---

### Text D — Benchmark Sample SCAM_14 (Corporate Impersonation)

| Metric / Layer | Output Value |
| :--- | :--- |
| **Benchmark ID** | `SCAM_14` |
| **Declared Company** | `Infosys` |
| **Contact Email** | `hr.infosys.onboarding@yahoo.com` |
| **Input Text** | `"Congratulations! Your profile has been shortlisted for Software Engineer Trainee at Infosys Mysore.\nPackage: 8.5 LPA. No further rounds of interview needed.\nOffer letter valid for 48 hours only.\nTo confirm acceptance, candidates must pay a document verification fee of Rs 4,999 to our authorized recruitment partner account."` |
| **Gatekeeper Decision** | `is_job_posting: True` (Confidence: `0.95`, Type: `job_posting`) |
| **Gatekeeper Reasoning** | `"Recruitment structure, role description, and employment terms verified."` |
| **ML-Only Fraud Probability** | **`0.4910`** (49.10% — **Below 0.50 cutoff, Missed by ML**) |
| **Why ML Missed It** | Professional corporate phrasing (`"recruitment"` +0.4613, `"software"` +0.2941, `"trainee"` +0.2667, `"software engineer"` +0.2666, `"interview"` +0.1753) balanced out fraud tokens (`"rs"` +1.1963, `"fee"` +0.5836, `"pay"` +0.3058), bringing probability just below 0.50. |
| **XAI Top Fraud n-grams** | `rs` (+1.1963), `fee` (+0.5836), `pay` (+0.3058), `package` (+0.1667), `needed` (+0.1438) |
| **XAI Top Legit n-grams** | `recruitment` (+0.4613), `software` (+0.2941), `trainee` (+0.2667), `software engineer` (+0.2666), `interview` (+0.1753) |
| **Rules Engine Penalty** | `74` (3 flags triggered) |
| **Rules Triggered** | 1. **Upfront Fee / Registration Charge** (`Financial Demand`, `CRITICAL`, Matched: `"verification fee of Rs 4"`, Offsets: `[249, 273]`)<br>2. **Processing, application, or courier fee demand** (`Financial Demand`, `CRITICAL`, Matched: `"verification fee of Rs"`, Offsets: `[249, 271]`)<br>3. **Unsolicited offer letter claiming to be from a known company** (`Brand Impersonation`, `MEDIUM`, Matched: `"Congratulations! Your profile has been shortlisted for Software Engineer Trainee at Infosys"`, Offsets: `[0, 91]`) |
| **Domain / Verifier Flags** | 1. **Free Webmail Used for Corporate Contact** (`FREE_WEBMAIL`, `HIGH`): Recruiter uses `hr.infosys.onboarding@yahoo.com`.<br>2. **Company Identity Mismatch** (`DOMAIN_MISMATCH`, `CRITICAL`): Declared company 'Infosys' mismatch against `yahoo.com` (expected `infosys.com`). |
| **Domain Penalty** | `50` |
| **Final Risk Score** | **`79 / 100`** |
| **Risk Level** | **`High Risk`** |
| **Pipeline Verdict** | `"Critical Scam Indicators Detected (Critical scam indicators). Do not engage or send money."` |
| **Rescue Outcome** | **Rules & Domain Verification Layer rescued the false negative**, elevating an ambiguous 49.1% ML probability to a decisive **79/100 High Risk** score. |

---

## 📊 Section 2: Benchmark Evaluation Unedited Terminal Output

Command executed:
```powershell
.\.venv\Scripts\python.exe backend/scripts/run_benchmark_evaluation.py
```

Unedited output:
```text
REPUTATION_SALT not set in environment! Generated ephemeral random salt for this session. Set REPUTATION_SALT in .env for persistent hash lookups across restarts.
======================================================================
[+] GENERATING BENCHMARK EVALUATION DATASET
======================================================================
Dataset successfully created at: D:\My Files\GEC\Hackathon\20261005 Hackathena 2.0\data\evaluation_benchmark_dataset.csv
Total benchmark samples: 60 (Scam: 30, Legit: 30)

======================================================================
[*] RUNNING EVALUATION SUITE ACROSS ALL BENCHMARK SAMPLES
======================================================================

Completed analysis of 60 postings in 1.21s.

======================================================================
[+] COMPARATIVE BENCHMARK PERFORMANCE REPORT
======================================================================
Metric                 ML-Only (Isolated)     Full Pipeline (Hybrid)
----------------------------------------------------------------------
Scam Recall            96.67% (29/30)            100.00% (30/30)
Scam Precision         100.00%                 93.75%
Scam F1-Score           0.9831                  0.9677
Overall Accuracy       98.33%                 96.67%
ROC-AUC Score           1.0000                  1.0000
----------------------------------------------------------------------
Confusion Matrix (TN, FP, FN, TP):
  * ML-Only       : TN=30, FP=0, FN=1, TP=29
  * Full Pipeline : TN=28, FP=2, FN=0, TP=30

----------------------------------------------------------------------
[*] ML FALSE NEGATIVE RESCUE ANALYSIS (1 sample(s) missed by ML)
----------------------------------------------------------------------
  [RESCUED & CAUGHT] SCAM_14: Software Engineer Trainee - Infosys (Corporate Impersonation)
      - ML Probability    : 0.4910 (Below 0.50 threshold)
      - Full Pipeline Score: 79/100 (High Risk)
      - Rules Triggered   : ['Upfront Fee / Registration Charge', 'Processing, application, or courier fee demand', 'Unsolicited offer letter claiming to be from a known company']

----------------------------------------------------------------------
[*] RISK SCORE SEPARATION
----------------------------------------------------------------------
  * Scam Postings Average Score : 87.3 / 100 (Min: 52, Max: 100)
  * Legit Postings Average Score: 9.0 / 100 (Min: 0, Max: 51)
  * Score Separation Delta      : +78.3 points

----------------------------------------------------------------------
[*] BREAKDOWN BY CATEGORY
----------------------------------------------------------------------
  [SCAM ] Captcha Scam                     | N= 1 | Avg Score:  52.0 | Accuracy: 100.0%
  [SCAM ] Cheque Overpayment Scheme        | N= 2 | Avg Score:  98.0 | Accuracy: 100.0%
  [SCAM ] Corporate Impersonation          | N= 4 | Avg Score:  74.0 | Accuracy: 100.0%
  [LEGIT] Corporate Non-Tech               | N= 5 | Avg Score:   3.4 | Accuracy: 100.0%
  [LEGIT] Corporate Tech                   | N= 5 | Avg Score:   4.4 | Accuracy: 100.0%
  [SCAM ] Crypto / Investment Scheme       | N= 2 | Avg Score:  96.0 | Accuracy: 100.0%
  [SCAM ] Data Entry Bait                  | N= 4 | Avg Score:  92.5 | Accuracy: 100.0%
  [SCAM ] High Pressure Scam               | N= 2 | Avg Score:  79.0 | Accuracy: 100.0%
  [SCAM ] Identity Harvesting              | N= 2 | Avg Score:  86.5 | Accuracy: 100.0%
  [LEGIT] Institutional / PSU              | N= 5 | Avg Score:  14.8 | Accuracy:  80.0%
  [SCAM ] Packaging Scam                   | N= 1 | Avg Score: 100.0 | Accuracy: 100.0%
  [LEGIT] Remote Legitimate                | N= 5 | Avg Score:   8.0 | Accuracy: 100.0%
  [LEGIT] Student Internship (Legit)       | N= 5 | Avg Score:   7.0 | Accuracy: 100.0%
  [SCAM ] Student Internship Fee           | N= 5 | Avg Score:  92.2 | Accuracy: 100.0%
  [SCAM ] Student Pyramid Scheme           | N= 2 | Avg Score:  67.5 | Accuracy: 100.0%
  [SCAM ] Task & Review Scam               | N= 3 | Avg Score:  95.7 | Accuracy: 100.0%
  [LEGIT] Tricky Hard-Negative             | N= 5 | Avg Score:  16.6 | Accuracy:  80.0%
  [SCAM ] Visa & Immigration Scam          | N= 2 | Avg Score: 100.0 | Accuracy: 100.0%

  • High Risk Detection Rate on Scams: 24/30 (80.0%)

Detailed evaluation results saved to: D:\My Files\GEC\Hackathon\20261005 Hackathena 2.0\data\benchmark_evaluation_results.json
======================================================================
```

---

## 📦 Section 3: Model Metadata Values (`backend/models/metadata.json`)

Exact values extracted from `backend/models/metadata.json`:

```json
{
  "version": "2.0.0",
  "trained_at": "2026-10-06T02:10:08.507245+00:00",
  "dataset": "EMSCAD + real-world seeds",
  "dataset_hash_md5": "6cf8dba3fc88712d8d1181741874c041",
  "train_samples": 14464,
  "test_samples": 3576,
  "real_world_seeds": 160,
  "model_type": "TF-IDF(15k, 1-2gram, sublinear) + CalibratedClassifierCV(LR, isotonic, cv=5)",
  "metrics": {
    "roc_auc": 0.9901,
    "fraud_precision": 0.9571,
    "fraud_recall": 0.7746,
    "fraud_f1": 0.8562
  }
}
```

### Metadata Fields Summary
- **ROC-AUC**: `0.9901`
- **Precision (Fraud)**: `0.9571` (95.71%)
- **Recall (Fraud)**: `0.7746` (77.46%)
- **F1-Score (Fraud)**: `0.8562`
- **Holdout Test Size (`test_samples`)**: `3,576`
- **Training Samples (`train_samples`)**: `14,464`
- **Real-World Seed Augmentations**: `160`
- **Feature Count**: `15,000` (15k unigrams & bigrams via sublinear TF-IDF)
- **Calibration Method**: `CalibratedClassifierCV(estimator=LogisticRegression, method='isotonic', cv=5)`
- **Training Timestamp**: `2026-10-06T02:10:08.507245+00:00`
- **Dataset Hash (MD5)**: `6cf8dba3fc88712d8d1181741874c041`
- **Pipeline Version**: `2.0.0`

---

## 🛡️ Section 4: Evaluation Integrity Test Output

Command executed:
```powershell
.\.venv\Scripts\pytest.exe tests/test_evaluation_integrity.py -v
```

Unedited output:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.6.0 -- D:\My Files\GEC\Hackathon\20261005 Hackathena 2.0\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\My Files\GEC\Hackathon\20261005 Hackathena 2.0
configfile: pytest.ini
plugins: anyio-4.15.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 2 items

tests/test_evaluation_integrity.py::test_no_exact_or_near_duplicate_overlap PASSED
tests/test_evaluation_integrity.py::test_train_pipeline_does_not_load_holdout PASSED

============================== 2 passed in 0.10s ==============================
```

**Integrity Verification Notes**:
- `test_no_exact_or_near_duplicate_overlap`: Confirms zero training/benchmark data leakage or duplicate text contamination.
- `test_train_pipeline_does_not_load_holdout`: Asserts training pipeline does not consume holdout benchmark evaluation data.

---

## 🔍 Section 5: Comparison Against `README.md` Claims

| Metric / Parameter | Value Claimed in README | Real Reproducible Output | Status |
| :--- | :---: | :---: | :---: |
| **Model Isolated ROC-AUC** | `0.9901` | `0.9901` | **Exact Match** |
| **Model Isolated Scam Precision** | `95.71%` | `95.71%` | **Exact Match** |
| **Model Isolated Scam Recall** | `77.46%` | `77.46%` | **Exact Match** |
| **Model Isolated F1-Score** | `85.62%` | `85.62%` | **Exact Match** |
| **Benchmark ML-Only Recall** | `96.67%` (29/30) | `96.67%` (29/30) | **Exact Match** |
| **Benchmark Full Pipeline Recall** | `100.00%` (30/30) | `100.00%` (30/30) | **Exact Match** |
| **Benchmark Full Pipeline Precision** | `93.75%` | `93.75%` | **Exact Match** |
| **Benchmark Full Pipeline Accuracy** | `96.67%` | `96.67%` | **Exact Match** |
| **Benchmark Full Pipeline ROC-AUC** | `1.0000` | `1.0000` | **Exact Match** |
| **Scam Avg Score on Benchmark** | `87.3 / 100` | `87.3 / 100` | **Exact Match** |
| **Legit Avg Score on Benchmark** | `9.0 / 100` | `9.0 / 100` | **Exact Match** |
| **Score Separation Delta** | `+78.3 points` | `+78.3 points` | **Exact Match** |
| **SCAM_14 ML Probability** | `~0.4910` | `0.4910` | **Exact Match** |
| **SCAM_14 Full Pipeline Score** | `79 / 100` (High Risk) | `79 / 100` (High Risk) | **Exact Match** |

**Differences Found**: **Zero discrepancies.** Every number claimed in `README.md` matches the real command outputs identically.
