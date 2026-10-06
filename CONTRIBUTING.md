# Contributing to LeakedIn

Thank you for your interest in contributing to **LeakedIn**! We welcome community contributions, scam report dataset additions, multilingual rule improvements, and forensic feature suggestions.

---

## 📜 Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [athulpp2006@gmail.com](mailto:athulpp2006@gmail.com).

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Git
- (Optional) Docker & Docker Compose

### 2. Fork & Clone
```bash
git clone https://github.com/athulpp06/hackathena-2.0.git
cd hackathena-2.0
```

### 3. Setup Virtual Environment

#### Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
copy .env.example .env
pip install -r requirements.txt
```

#### Linux / macOS (Bash / Zsh):
```bash
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
```

### 4. Running the Complete Test Suite
Ensure all 113 automated tests pass before proposing changes:
```bash
pytest -v
```

---

## 🛠️ Development Guidelines

1. **Privacy & Offline First**:
   - The platform is **offline by default**. All ML scoring, heuristics, OCR, and forensics run locally without outbound network calls.
   - Cloud capabilities (like Google Gemini Vision) are strictly opt-in via environment variables (`GEMINI_API_KEY`).
   - User inputs (resumes, screenshots, job text) must never be permanently stored or logged in plain text.

2. **Multilingual Rules**:
   - Heuristics are defined in `backend/app/detector/patterns/rules.yaml`.
   - When adding regex rules for Indic languages (Hindi, Malayalam, Hinglish), include corresponding positive and negative test cases under `tests/test_rules.py`.

3. **Threat Database & Hashing**:
   - Contact identifiers stored in `reputation.db` must always be salted and hashed via HMAC-SHA256. Never store raw PII (emails, phone numbers, UPI IDs).

4. **Code Style & Formatting**:
   - Follow PEP 8 style standards with type annotations (`typing`).
   - Avoid external CDN dependencies in the frontend — keep fonts and assets self-hosted.

---

## 📬 Submitting a Pull Request

1. Create a feature branch: `git checkout -b feat/your-feature-name`
2. Commit changes with descriptive messages following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(...)`: New feature or capability
   - `fix(...)`: Bug fix or patch
   - `docs(...)`: Documentation updates
   - `test(...)`: Adding or updating test cases
   - `refactor(...)`: Code restructuring without functional changes
3. Verify all 113 test cases pass (`pytest`).
4. Push to your branch and open a Pull Request targeting `main`.
