import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.detector import aggregator, gatekeeper
from backend.app import ocr

router = APIRouter()

# Supported image MIME types
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png",
    "image/webp", "image/bmp", "image/tiff",
}


class JobAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Job posting text, recruitment message, or prompt to analyze")
    company_name: Optional[str] = Field(default="", description="Declared company name (optional)")
    contact_email: Optional[str] = Field(default="", description="Contact email extracted from posting (optional)")
    gemini_api_key: Optional[str] = Field(default="", description="Optional Gemini API key provided by client")


class GeminiKeyRequest(BaseModel):
    api_key: str = Field(..., description="Google Gemini API key")


@router.post("/analyse-job", summary="Analyse a job posting for fraud signals")
async def analyse_job(request: JobAnalysisRequest):
    """
    Performs full hybrid fraud analysis on a job posting with AI gatekeeper:
    - **Gatekeeper Layer**: Uses Gemini Multimodal / offline classifier to verify if input is a genuine recruitment offer
    - **ML Layer**: TF-IDF + Logistic Regression trained on 17,880+ job postings
    - **Rules Layer**: High-precision heuristics for fees, student exploitation, fake urgency, and spoofing
    - **Domain Layer**: Contact email domain verification and company identity mismatch detection

    Returns a unified risk score (0-100), risk level, red flags with exact text spans, and actionable recommendations.
    """
    try:
        if request.gemini_api_key and request.gemini_api_key.strip():
            os.environ["GEMINI_API_KEY"] = request.gemini_api_key.strip()

        result = aggregator.analyse(
            text=request.text,
            declared_company=request.company_name or "",
            contact_email=request.contact_email or "",
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyse-image", summary="Analyse a job posting image or screenshot for fraud signals")
async def analyse_image(
    file: UploadFile = File(..., description="Job posting image or screenshot (JPEG, PNG, WebP, BMP, TIFF)"),
    company_name: Optional[str] = Form(default="", description="Declared company name (optional)"),
    contact_email: Optional[str] = Form(default="", description="Contact email (optional)"),
    gemini_api_key: Optional[str] = Form(default="", description="Optional Gemini API key"),
):
    """
    Accepts an image upload (screenshot, photo, scanned job posting).
    - Runs **AI Gatekeeper & Gemini Multimodal Vision** to check if the image is a recruitment offer vs general photo/meme/receipt.
    - Runs **OCR** to extract text from the image.
    - Passes extracted content through the full fraud detection pipeline.

    Supports: JPEG, PNG, WebP, BMP, TIFF formats.
    """
    if gemini_api_key and gemini_api_key.strip():
        os.environ["GEMINI_API_KEY"] = gemini_api_key.strip()

    # Validate file type
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_IMAGE_TYPES:
        name = (file.filename or "").lower()
        if not any(name.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"]):
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type '{content_type}'. Please upload a JPEG, PNG, WebP, BMP, or TIFF image."
            )

    # Read image bytes
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(image_bytes) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=413, detail="Image too large. Maximum size is 20 MB.")

    # Check OCR availability
    extracted_text = ""
    ocr_confidence = 0.0
    ocr_engine = "None"

    if ocr.is_ocr_available():
        try:
            extracted_text, ocr_confidence = await ocr.extract_text_from_image_bytes(image_bytes, file.filename or "upload")
            ocr_engine = ocr.get_ocr_engine() or "OCR"
        except Exception:
            extracted_text = ""

    # If OCR extracted minimal text (e.g. photo of food, scenery, receipt, meme):
    # Check with Gatekeeper / Gemini vision directly before throwing a blind error!
    gate_check = gatekeeper.classify_job_relevance(
        text=extracted_text,
        image_bytes=image_bytes,
        mime_type=content_type or "image/png"
    )

    if not gate_check.get("is_job_posting", True):
        detected_type = gate_check.get("content_type", "non_recruitment_photo").replace("_", " ").title()
        return {
            "is_job_posting": False,
            "content_type": gate_check.get("content_type", "non_recruitment_photo"),
            "gatekeeper_reasoning": gate_check.get("reasoning", "Uploaded image does not appear to be a job posting."),
            "gatekeeper_provider": gate_check.get("provider", "offline_gatekeeper"),
            "risk_score": None,
            "risk_level": "Invalid Content",
            "verdict": f"The uploaded image was classified as {detected_type}, not a recruitment or internship offer.",
            "recommendations": [
                "Please upload a screenshot of a job posting, recruitment email, employment flyer, or offer letter.",
                f"Current image was identified as: {detected_type}."
            ],
            "red_flags": [],
            "rule_flag_count": 0,
            "rule_penalty": 0,
            "highlighted_spans": [],
            "domain_flags": [],
            "domain_flag_count": 0,
            "emails_found": [],
            "company_mismatch": False,
            "ml_fraud_probability": 0.0,
            "ml_score_pct": 0,
            "ml_verdict": "Analysis Skipped (Not a job posting)",
            "ocr_extracted_text": extracted_text,
            "ocr_confidence": ocr_confidence,
            "ocr_char_count": len(extracted_text),
            "ocr_engine": ocr_engine,
            "source": "image_ocr",
            "gemini_scam_assessment": gate_check.get("gemini_scam_assessment"),
        }

    # If it is considered a job posting but OCR failed to extract text:
    if not extracted_text or len(extracted_text.strip()) < 15:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract legible recruitment text from this image. "
                "Please try uploading a clearer, higher-resolution screenshot or paste the job description text."
            )
        )

    # Run full hybrid analysis on extracted text
    try:
        result = aggregator.analyse(
            text=extracted_text,
            declared_company=company_name or "",
            contact_email=contact_email or "",
            image_bytes=image_bytes,
            mime_type=content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Enrich result with OCR metadata
    result["ocr_extracted_text"] = extracted_text
    result["ocr_confidence"] = ocr_confidence
    result["ocr_char_count"] = len(extracted_text)
    result["ocr_engine"] = ocr_engine
    result["source"] = "image_ocr"

    return result


@router.get("/gatekeeper-status", summary="Check AI Gatekeeper & Gemini status")
async def gatekeeper_status(x_gemini_key: Optional[str] = Header(None)):
    """Returns AI Gatekeeper availability and whether Google Gemini is configured."""
    # Check if header provided key
    header_key = (x_gemini_key or "").strip()
    if header_key and len(header_key) > 10:
        has_gemini = True
        key_source = "header"
    else:
        has_gemini = gatekeeper.is_gemini_available()
        key_source = "env" if has_gemini else "none"

    return {
        "gatekeeper_active": True,
        "gatekeeper_ready": True,
        "gemini_available": has_gemini,
        "gemini_configured": has_gemini,
        "key_source": key_source,
        "active_provider": "Google Gemini (gemini-1.5-flash)" if has_gemini else "Built-in Heuristic Gatekeeper",
        "description": "Scans and differentiates non-job images/prompts from real recruitment postings."
    }


@router.post("/set-gemini-key", summary="Configure Gemini API Key")
async def set_gemini_key(request: GeminiKeyRequest):
    """Sets or clears the Gemini API key in server runtime environment."""
    key = request.api_key.strip()
    if not key:
        os.environ.pop("GEMINI_API_KEY", None)
        return {
            "status": "cleared",
            "gemini_available": False,
            "gemini_configured": False,
            "active_provider": "Built-in Heuristic Gatekeeper",
            "message": "Gemini API key cleared. Operating with zero-config offline gatekeeper."
        }
    if len(key) < 15:
        raise HTTPException(status_code=400, detail="Invalid Gemini API key format.")
    os.environ["GEMINI_API_KEY"] = key
    return {
        "status": "success",
        "gemini_available": True,
        "gemini_configured": True,
        "active_provider": "Google Gemini (gemini-1.5-flash)",
        "message": "Gemini API key configured successfully! Multimodal vision gatekeeper is active."
    }


@router.get("/ocr-status", summary="Check if OCR is available")
async def ocr_status():
    """Returns whether OCR is available on the server and which engine is active."""
    available = ocr.is_ocr_available()
    engine = ocr.get_ocr_engine()
    return {
        "ocr_available": available,
        "engine": engine,
        "message": f"OCR is ready using {engine}." if available else "No OCR engine is available. Image upload is disabled.",
    }

