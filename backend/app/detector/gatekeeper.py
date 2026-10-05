"""
AI Gatekeeper & Relevance Classifier for LeakedIn.
Detects whether an uploaded image or text is actually a recruitment / job / internship posting
before running fraud detection.

Supports:
1. Google Gemini Multimodal API (gemini-1.5-flash) for vision and semantic reasoning.
2. Offline heuristic gatekeeper fallback (zero-config, works without API key or when offline).
"""

import os
import io
import json
import re
import logging
from typing import Dict, Any, Optional
from PIL import Image

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Check for Gemini API key
def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""


def is_gemini_available() -> bool:
    key = get_gemini_api_key()
    return bool(key and len(key.strip()) > 10)


# ── Offline Heuristic Gatekeeper ─────────────────────────────────────────────

RECRUITMENT_ROLE_KEYWORDS = {
    "intern", "internship", "engineer", "developer", "manager", "executive",
    "assistant", "operator", "specialist", "consultant", "analyst", "designer",
    "writer", "coordinator", "representative", "clerk", "associate", "trainee",
    "officer", "salesperson", "recruiter", "lead", "architect", "data entry",
}

RECRUITMENT_ACTION_KEYWORDS = {
    "hiring", "apply", "opening", "vacancy", "vacancies", "job offer", "stipend",
    "salary", "compensation", "per month", "per week", "per day", "daily income",
    "part-time", "full-time", "work from home", "wfh", "remote work", "direct selection",
    "requirements", "qualifications", "eligibility", "send cv", "submit resume",
    "careers", "to apply", "job description", "immediate joining", "spot offer",
    "pocket money", "branding promotion", "training kit", "registration fee",
}

RESUME_MARKERS = [
    r"\bcurriculum\s+vitae\b", r"\bresume\b", r"\bcareer\s+objective\b",
    r"\beducation\s*:\s*(?:b\.?tech|m\.?tech|bca|mca|bba|mba|high\s+school|cgpa|percentage)\b",
    r"\bacademic\s+projects?\b", r"\btechnical\s+skills?\s*:", r"\bdeclaration\s*:\s*i\s+hereby\b",
    r"\bpersonal\s+details?\s*:\s*(?:father|dob|gender|marital)\b",
]

RECEIPT_MARKERS = [
    r"\btax\s+invoice\b", r"\bbill\s+to\b", r"\border\s+(?:number|id|total)\b",
    r"\bsubtotal\b", r"\bamount\s+due\b", r"\bpayment\s+received\b", r"\bshipping\s+address\b",
]

CONVERSATION_OR_PROMPT_MARKERS = [
    r"^(?:write|generate|explain|code|summarize|translate|solve|create)\s+(?:a|an|the|me)?\b",
    r"\b(?:what\s+is|how\s+to|tell\s+me\s+about|can\s+you\s+help\s+with)\b",
    r"\b(?:recipe|ingredients|tablespoon|teaspoon|preheat\s+oven|simmer|boil)\b",
    r"\b(?:hey\s+(?:bro|dude|there)|how\s+are\s+you|call\s+me|see\s+you\s+tomorrow|what\'s\s+up)\b",
]


def _offline_classify_text(text: str) -> Dict[str, Any]:
    """
    Evaluates text structure using lexical and semantic recruitment heuristics.
    Distinguishes legitimate/fraudulent job postings from resumes, receipts, code, and chat.
    """
    cleaned = text.strip().lower()

    if len(cleaned) < 25:
        return {
            "is_job_posting": False,
            "content_type": "insufficient_text",
            "confidence": 0.95,
            "reasoning": "The provided text is too brief to constitute a job posting or employment offer.",
            "provider": "offline_gatekeeper",
            "gemini_scam_assessment": None,
        }

    # 1. Check for candidate resumes (applying candidate vs hiring employer)
    resume_matches = sum(1 for p in RESUME_MARKERS if re.search(p, cleaned))
    if resume_matches >= 2:
        return {
            "is_job_posting": False,
            "content_type": "resume_cv",
            "confidence": 0.90,
            "reasoning": "The text appears to be a candidate's resume or curriculum vitae, rather than a recruiter's job vacancy.",
            "provider": "offline_gatekeeper",
            "gemini_scam_assessment": None,
        }

    # 2. Check for invoices / receipts
    receipt_matches = sum(1 for p in RECEIPT_MARKERS if re.search(p, cleaned))
    if receipt_matches >= 2:
        return {
            "is_job_posting": False,
            "content_type": "receipt_or_invoice",
            "confidence": 0.92,
            "reasoning": "The text appears to be a financial receipt, bill, or invoice.",
            "provider": "offline_gatekeeper",
            "gemini_scam_assessment": None,
        }

    # 3. Check for general conversational prompts or recipes
    for p in CONVERSATION_OR_PROMPT_MARKERS:
        if re.search(p, cleaned):
            return {
                "is_job_posting": False,
                "content_type": "general_prompt_or_chat",
                "confidence": 0.88,
                "reasoning": "The text appears to be a conversational message, AI prompt, or general query rather than a recruitment offer.",
                "provider": "offline_gatekeeper",
                "gemini_scam_assessment": None,
            }

    # 4. Count recruitment indicators
    tokens = set(re.findall(r"\b[a-z]{3,}\b", cleaned))
    role_count = len(tokens.intersection(RECRUITMENT_ROLE_KEYWORDS))
    action_count = sum(1 for w in RECRUITMENT_ACTION_KEYWORDS if w in cleaned)

    # Specific job patterns
    has_apply_pattern = bool(re.search(r"\b(?:to\s*apply|how\s+to\s+apply|send\s+(?:cv|resume)|apply\s+at|visit\s+http)\b", cleaned))
    has_compensation = bool(re.search(r"\b(?:stipend|salary|lpa|ctc|per\s*(?:month|week|day|hr|hour)|\d+k\s*\/\s*month)\b", cleaned))
    has_intern_pattern = bool(re.search(r"\b(?:intern(?:ship)?|pursuing\s+students?|marketing\s+intern|wfh\s+intern)\b", cleaned))

    score = 0
    if role_count >= 1:
        score += 2
    if role_count >= 2:
        score += 1
    if action_count >= 1:
        score += 2
    if action_count >= 3:
        score += 2
    if has_apply_pattern:
        score += 2
    if has_compensation:
        score += 2
    if has_intern_pattern:
        score += 2

    # Threshold evaluation
    if score >= 4:
        return {
            "is_job_posting": True,
            "content_type": "job_posting",
            "confidence": min(0.95, 0.65 + (score * 0.05)),
            "reasoning": "Recruitment structure, role description, and employment terms verified.",
            "provider": "offline_gatekeeper",
            "gemini_scam_assessment": None,
        }
    else:
        return {
            "is_job_posting": False,
            "content_type": "non_recruitment_text",
            "confidence": 0.82,
            "reasoning": "Text lacks standard employment markers such as job title, hiring criteria, compensation, or application instructions.",
            "provider": "offline_gatekeeper",
            "gemini_scam_assessment": None,
        }


# ── Gemini Multimodal Gatekeeper ─────────────────────────────────────────────

def _classify_with_gemini(
    text: str,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png"
) -> Optional[Dict[str, Any]]:
    """
    Executes multimodal content relevance scan via Google Gemini API.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Use fast, cost-efficient gemini-1.5-flash
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            }
        )

        prompt = (
            "You are an AI gatekeeper for a Recruitment Fraud Detection tool. "
            "Your job is to determine whether the provided input (image or text) is an actual job vacancy, "
            "recruitment offer, employment advertisement, or internship posting.\n\n"
            "Respond strictly in JSON matching this schema:\n"
            "{\n"
            '  "is_job_posting": boolean,\n'
            '  "content_type": string (one of: "job_posting", "resume", "receipt_or_invoice", "personal_photo", "social_meme", "chat_conversation", "general_text", "code_snippet", "other"),\n'
            '  "confidence": number (between 0.0 and 1.0),\n'
            '  "reasoning": string (concise 1-2 sentence explanation of what this input represents and whether it is a job/internship offer),\n'
            '  "extracted_role": string or null,\n'
            '  "extracted_company": string or null,\n'
            '  "gemini_fraud_notes": string or null (if it is a job posting, note any glaring fraud cues like upfront fees or telegram chat; null otherwise)\n'
            "}"
        )

        content_parts = [prompt]

        if image_bytes:
            # Multimodal Vision: Load image directly from bytes
            img = Image.open(io.BytesIO(image_bytes))
            content_parts.append(img)
            content_parts.append(f"Additional extracted text from OCR: {text[:1500]}" if text else "Examine the image carefully.")
        else:
            content_parts.append(f"Input text to evaluate:\n'''\n{text[:3000]}\n'''")

        response = model.generate_content(content_parts)
        if response and response.text:
            data = json.loads(response.text)
            return {
                "is_job_posting": bool(data.get("is_job_posting", False)),
                "content_type": data.get("content_type", "unknown"),
                "confidence": float(data.get("confidence", 0.90)),
                "reasoning": data.get("reasoning", "Classified via Gemini AI."),
                "provider": "gemini-1.5-flash",
                "extracted_role": data.get("extracted_role"),
                "extracted_company": data.get("extracted_company"),
                "gemini_scam_assessment": data.get("gemini_fraud_notes"),
            }

    except Exception as e:
        logger.warning(f"Gemini gatekeeper call failed, falling back to offline classifier: {e}")
        return None

    return None


def classify_job_relevance(
    text: str,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png"
) -> Dict[str, Any]:
    """
    Main entrypoint:
    1. Tries Gemini Multimodal API if configured.
    2. Falls back to offline heuristic gatekeeper seamlessly.
    """
    if is_gemini_available():
        res = _classify_with_gemini(text, image_bytes, mime_type)
        if res is not None:
            return res

    # Offline gatekeeper fallback
    return _offline_classify_text(text)
