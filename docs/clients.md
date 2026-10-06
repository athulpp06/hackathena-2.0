# LeakedIn — Client Integration & API Specification

**Last Updated**: 2026-10-06  
**Backend Target**: `http://localhost:8000` (FastAPI v2.0)  

---

## 📡 1. Real API Schema for `POST /api/analyze/text`

The schema below is extracted directly from the production backend in [`backend/app/api/routes.py`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/backend/app/api/routes.py) and [`backend/app/detector/aggregator.py`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/backend/app/detector/aggregator.py).

### Request Payload (`JobAnalysisRequest`)
* **Endpoint**: `POST /api/analyze/text`
* **Content-Type**: `application/json`

```json
{
  "text": "Job posting content string (min_length=10, max_length=50000, required)",
  "company_name": "Claimed company name (optional, string, max_length=200, default='')",
  "contact_email": "Recruiter contact email (optional, string, max_length=200, default='')",
  "gemini_api_key": "Optional Gemini Key (optional, string, max_length=200, default='')"
}
```

#### Request Validation Constraints:
- `text`: Minimum 10 characters, maximum 50,000 characters. Input outside this range triggers HTTP `422 Unprocessable Entity`.
- Rate Limit: `30/minute` per client IP. Exceeding triggers HTTP `429 Too Many Requests`.

---

### Response Payload: Genuine Job Posting / Scam Analysis (`is_job_posting: true`)

```json
{
  "is_job_posting": true,
  "content_type": "job_posting",
  "language": "en",
  "risk_score": 87,
  "risk_level": "High Risk",
  "verdict": "Critical Scam Indicators Detected (Critical scam indicators). Do not engage or send money.",
  "ml_probability": 0.9145,
  "ml_fraud_probability": 0.9145,
  "ml_score_pct": 91,
  "ml_verdict": "High probability of recruitment fraud",
  "ml_confidence": "HIGH",
  "rule_penalty": 100,
  "rule_flag_count": 6,
  "red_flags": [
    {
      "category": "Financial Demand",
      "severity": "CRITICAL",
      "penalty": 40,
      "title": "Mandatory Equipment or Software Purchase",
      "explanation": "Scammers often claim you must buy specific software, hardware, or home office kits from their 'approved vendor'.",
      "message": "Scammers often claim you must buy specific software, hardware, or home office kits from their 'approved vendor'.",
      "matched_text": "training kit fee",
      "start": 27,
      "end": 43
    }
  ],
  "domain_penalty": 5,
  "domain_flag_count": 1,
  "domain_flags": [
    {
      "type": "NO_CONTACT_INFO",
      "severity": "LOW",
      "title": "No Verifiable Contact Email Found",
      "detail": "No email address was provided. Legitimate postings include official contact channels."
    }
  ],
  "company_name": "Not Specified",
  "company_mismatch": false,
  "has_free_email": false,
  "has_disposable_email": false,
  "typosquat_detected": false,
  "recommendations": [
    "Verify the employer on their official corporate portal and LinkedIn before applying.",
    "Never pay money to secure a job or internship — legitimate employers never demand fees."
  ],
  "advice": [
    "Do NOT send money or share bank/identity details with this recruiter."
  ],
  "emergency_steps": [
    "If money was already paid: Dial the National Cyber Crime Helpline '1930' immediately."
  ],
  "helpline": {
    "number": 1930,
    "name": "Indian National Cyber Crime Reporting Helpline",
    "portal": "https://cybercrime.gov.in"
  },
  "processing_ms": 15
}
```

---

### Response Payload: Gatekeeper Rejection (`is_job_posting: false`)

When a user submits non-recruitment text (recipe, casual chat, invoice, programming code, or candidate CV):

```json
{
  "is_job_posting": false,
  "content_type": "non_recruitment_text",
  "gatekeeper_reasoning": "Text lacks standard employment markers such as job title, hiring criteria, compensation, or application instructions.",
  "gatekeeper_confidence": 0.82,
  "gatekeeper_provider": "offline_gatekeeper",
  "risk_score": null,
  "risk_level": "Invalid Content",
  "verdict": "The submitted content appears to be a non recruitment text rather than a job vacancy or employment offer. Fraud analysis withheld.",
  "red_flags": [],
  "domain_flags": [],
  "highlighted_spans": [],
  "recommendations": [
    "The submitted text or document appears to be a non recruitment text rather than a recruitment advertisement or offer.",
    "Please submit a genuine job posting, internship offer, or recruiter chat to perform fraud analysis."
  ]
}
```

---

## 🧩 2. Browser Extension (Manifest V3)

The extension lives in [`extension/`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/extension/) and allows job seekers to inspect job descriptions on **LinkedIn**, **Indeed**, and **Naukri** without leaving the page.

### Architecture & Security Policies:
1. **Background Service Worker Architecture**: All HTTP `fetch` requests are made strictly inside [`extension/background.js`](file:///d:/My%20Files/GEC/Hackathon/20261005%20Hackathena%202.0/extension/background.js). The content script and popup communicate via message passing (`chrome.runtime.sendMessage`).
2. **User-Initiated Scans Only**: Scans execute **only** when the user clicks the floating "Check this job" button, clicks "Scan Job Posting" in the popup, or uses the context menu. Zero background page scraping.
3. **Strict XSS Defense**: All API outputs and text spans are injected using `textContent` and native DOM nodes. Zero `innerHTML` or `eval()`.
4. **Zero Persistent Storage of Scanned Content**: Raw text is never stored in `chrome.storage`. Only the last result metadata is kept in service-worker memory for popup inspection.
5. **Score & Color Thresholds**:
   - `0 – 25`: Safe (Green `#10b981`)
   - `26 – 50`: Low Risk (Yellow `#f59e0b`)
   - `51 – 75`: Suspicious (Orange `#f97316`)
   - `76 – 100`: High Risk (Red `#ef4444`)
   *(Identical to `backend/app/detector/aggregator.py`)*

---

### Installation Guide (Chromium Browsers)

1. Open your browser (Google Chrome, Brave, Microsoft Edge, Opera).
2. Enter `chrome://extensions/` in the URL bar.
3. Toggle on **"Developer mode"** in the top-right corner.
4. Click the **"Load unpacked"** button in the top-left toolbar.
5. Select the `extension/` directory in this repository:
   ```text
   d:\My Files\GEC\Hackathon\20261005 Hackathena 2.0\extension
   ```
6. The **LeakedIn — AI Job Scam Detector** icon will now appear in your browser toolbar.

---

### Configuration & Settings

- **Default API Base URL**: `http://localhost:8000` (stored in `chrome.storage.sync`).
- **How to Edit**:
  1. Click the LeakedIn toolbar icon to open the popup.
  2. Click the gear icon (**⚙️**) at the top right.
  3. Enter your custom or hosted API endpoint (e.g., `https://your-deployment.domain.com` or `http://localhost:8000`).
  4. Click **"Save"**.

---

### Manual Test Checklist

| Test Scenario | Steps to Execute | Expected Result |
| :--- | :--- | :--- |
| **1. Scam Text via Context Menu** | Highlight text: *"Urgent hiring! Pay Rs 1,500 registration fee via UPI."* $\rightarrow$ Right-click $\rightarrow$ Select **"🛡️ Scan selection with LeakedIn"**. | Toolbar badge turns red (`71` or `87`). In-page modal pops up displaying **High Risk**, red flag for *Registration Fee*, and 1930 Cybercrime warning. |
| **2. Genuine Text via Context Menu** | Highlight genuine text from TCS/Google careers portal $\rightarrow$ Right-click $\rightarrow$ **"🛡️ Scan selection with LeakedIn"**. | Toolbar badge turns green (`0` or `1`). In-page modal displays **Safe**, zero red flags. |
| **3. Non-Job Content (Gatekeeper)** | Highlight recipe or casual text: *"Mix 2 cups of sugar with butter..."* $\rightarrow$ Scan via context menu. | Badge displays `NON` (gray). Modal shows: *"⚠️ This doesn't look like a job posting"* with gatekeeper reasoning. |
| **4. Empty / Too Short Selection** | Highlight 3 letters (e.g., *"Job"*) $\rightarrow$ Scan via context menu. | Displays clear error: *"Selected text is too short (minimum 10 characters)."* |
| **5. Floating Button on Job Site** | Open a job description on LinkedIn, Indeed, or Naukri. Click **"🛡️ Check this job"** at the bottom-right. | Button updates to *"⏳ Checking..."*, reads job container via smart selectors, and displays the in-page score card. |
| **6. Floating Button on Non-Job Page** | Click the floating button on a page without job description markup (e.g., feed). | Alert/modal instructs user: *"Could not locate job description. Please highlight the text and use the right-click menu."* |
| **7. Backend Offline** | Stop the backend server $\rightarrow$ Click Scan in popup or page. | Clear error: *"Backend is offline or unreachable at http://localhost:8000. Please start your LeakedIn server."* |
| **8. Wrong API Base URL** | In popup settings, change URL to `http://localhost:9999` $\rightarrow$ Click Scan. | Clear error: *"Backend is offline or unreachable at http://localhost:9999."* |
| **9. Text Exceeds Limit** | Paste >50,000 characters into popup. | Automatically truncates to 50,000 characters with notification: *"Text truncated to 50,000 characters."* |
