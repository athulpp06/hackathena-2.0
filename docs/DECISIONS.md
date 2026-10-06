# Architecture & Design Decisions

This document tracks technical decisions made during the evolution of LeakedIn.

## Phase 1: Credibility and Calibration
- **Decision:** Use `CalibratedClassifierCV(method='isotonic')` over standard Logistic Regression output.
- **Reason:** `class_weight='balanced'` severely skews predicted probabilities (shifting the mean prediction much higher than the actual base rate of fraud). Isotonic regression recalibrates these outputs into true confidence scores, making the Unified Risk Score much more reliable.
- **Aggregator Weights:** Moved to `backend/app/config.py`. ML weight capped at 60%, rules at 40%, domain mismatches +10% penalty. This balance ensures that obvious rule violations (like asking for an upfront fee) heavily penalize a posting even if the ML model is unsure due to domain shift (e.g., WhatsApp vs. EMSCAD).

## Phase 2: Text Normalization and Indian Multilingual Coverage
- **Decision:** Keep exact character index mapping (`normalizer.py`) between normalized text and raw input.
- **Reason:** Regex matching on normalized strings (stripped zero-width characters, collapsed spaces, leetspeak, homoglyphs) must map back to original character offsets so that the UI can highlight the exact original text snippet without distortion.
- **YAML-driven rules:** Rule patterns are compiled dynamically from `backend/app/detector/patterns/*.yaml` with multi-language tags (en, hi, ml, hinglish).

## Phase 3: Advanced Domain & Reputation Intelligence
- **Decision:** Use salted SHA-256 hashing for the community reputation database (`reputation.db`).
- **Reason:** To protect user privacy and avoid storing raw personally identifiable information (PII), all phone numbers, emails, UPI IDs, and domains are stored strictly as salted hashes.

## Phase 4: Document Analysis
- **Decision:** Support both native PDF extraction (pdfplumber) with OCR fallback and DOCX parsing (python-docx).
- **Reason:** Fake offer letters are distributed both as native vector PDFs and scanned image PDFs. An automatic fallback to EasyOCR ensures all documents are parsed reliably.

## Phase 5: Explainable ML (XAI)
- **Decision:** Extract logistic regression coefficients multiplied by TF-IDF sparse vector representations.
- **Reason:** Provides linear-time explainability (`top_fraud_ngrams` vs. `top_legit_ngrams`) without introducing heavy SHAP/LIME dependencies, keeping CPU inference under 50ms.

## Phase 6: Backend Hardening
- **Decision:** SSRF protection with IP resolution filtering and slowapi rate limiting.
- **Reason:** Scraping external job links creates a major server-side request forgery (SSRF) vector. We resolve domains before requesting and explicitly ban loopback, private RFC-1918, link-local, and cloud metadata (169.254.169.254) addresses.

## Phase 7: Frontend Polish & Experience
- **Decision:** Vanilla HTML5/CSS3/JS with canvas-based PNG export and zero external frontend dependencies.
- **Reason:** Keeps the application 100% self-contained, light, and demo-ready without npm, node_modules, or build pipelines. The shareable result card uses HTML5 `<canvas>` to render verified badge graphics with strict exclusion of candidate PII or message text.
- **i18n Translation:** Client-side dictionary for English, Hindi, and Malayalam covers all labels, buttons, tooltips, and sample descriptions.

## Phase 8: Distribution Channels (Chrome / Edge Browser Extension)
- **Decision:** Chrome/Edge Extension built strictly on Manifest V3 with minimal declarative permissions (`contextMenus`, `storage`, `activeTab`).
- **Reason:** Satisfies modern Chrome Web Store security guidelines. Content scripts only activate on verified job portals (LinkedIn, Indeed, Naukri), with context-menu actions handling arbitrary text on any website.
- **Telegram Bot:** Scrapped / retired to streamline codebase focus onto web and browser extension distribution.
- **WhatsApp Cloud API Architecture:** Designed as an in-memory stateless webhook validating Meta HMAC signatures (`X-Hub-Signature-256`) to ensure zero chat retention.

## Phase 9: Testing & DevOps
- **Decision:** Target ≥85% coverage across `detector/` and `utils/`; enforce via `--cov-fail-under=85` in CI rather than arbitrary 100% target.
- **Reason:** Marginal coverage above 85% yields diminishing returns for a hackathon project. The gap consists mainly of exception-handling branches that require brittle internal mocking. The 85% threshold is enforced automatically in GitHub Actions, preventing regressions.
- **`_is_private_ip` behaviour:** DNS-unresolvable hostnames return `True` (blocked) rather than `False`. Fail-closed is the safe default for SSRF protection — if we can't confirm an address is public, we don't fetch it.
- **Dockerfile:** Multi-stage build (builder → runtime) reduces final image size by ~40% by excluding build tools. Runs as non-root user (`leakedin`, UID 1000) to satisfy container security policies on Render and Railway.
- **CI matrix:** Tests run on both Python 3.10 and 3.11. Ruff and Mypy run as separate jobs so lint failures are immediately identifiable without waiting for the test matrix.

## Phase 10: Documentation
- **Decision:** Keep `docs/evaluation/model_comparison.md` as a living document generated by `backend/scripts/evaluate.py` rather than hardcoded numbers.
- **Reason:** Model metrics should be regeneratable — any change to training data or hyperparameters should produce an updated report without manual editing.
- **README structure:** Uses shield badges (no external trackers), a text-art architecture diagram (no external image hosting needed), and an honest metrics table prominently above the feature list. This signals credibility to hackathon judges who often check whether teams self-report limitations.

