"""
FastAPI routes for the LeakedIn Job Posting Scanner API.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.detector import aggregator
from backend.app import ocr

router = APIRouter()

# Supported image MIME types
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png",
    "image/webp", "image/bmp", "image/tiff",
}


class JobAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=30, description="Full job posting text to analyze")
    company_name: Optional[str] = Field(default="", description="Declared company name (optional)")
    contact_email: Optional[str] = Field(default="", description="Contact email extracted from posting (optional)")


@router.post("/analyse-job", summary="Analyse a job posting for fraud signals")
async def analyse_job(request: JobAnalysisRequest):
    """
    Performs a full hybrid fraud analysis on a job posting:
    - **ML Layer**: TF-IDF + Logistic Regression trained on 17,880 job postings
    - **Rules Layer**: 15+ regex-based heuristics covering payment demands, suspicious channels, urgency tactics
    - **Domain Layer**: Contact email domain verification and company identity mismatch detection

    Returns a unified risk score (0-100), risk level, red flags with exact text spans, and actionable recommendations.
    """
    try:
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
):
    """
    Accepts an image upload (screenshot, photo, scanned job posting).
    - Runs **Tesseract OCR** to extract text from the image.
    - Passes extracted text through the full hybrid fraud analysis pipeline.

    Supports: JPEG, PNG, WebP, BMP, TIFF formats.
    """
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_IMAGE_TYPES:
        # Try to infer from filename extension
        name = (file.filename or "").lower()
        if not any(name.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"]):
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type '{content_type}'. Please upload a JPEG, PNG, WebP, BMP, or TIFF image."
            )

    # Check OCR availability
    if not ocr.is_ocr_available():
        raise HTTPException(
            status_code=503,
            detail="No OCR engine is available on this server. Please paste text manually."
        )

    # Read image bytes
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(image_bytes) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=413, detail="Image too large. Maximum size is 20 MB.")

    # Extract text via OCR
    try:
        extracted_text, ocr_confidence = await ocr.extract_text_from_image_bytes(image_bytes, file.filename or "upload")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not extracted_text or len(extracted_text.strip()) < 20:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract enough readable text from this image. "
                f"OCR confidence: {ocr_confidence:.0%}. "
                "Please try a clearer image or paste the text manually."
            )
        )

    # Run full analysis on extracted text
    try:
        result = aggregator.analyse(
            text=extracted_text,
            declared_company=company_name or "",
            contact_email=contact_email or "",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Enrich result with OCR metadata
    result["ocr_extracted_text"] = extracted_text
    result["ocr_confidence"] = ocr_confidence
    result["ocr_char_count"] = len(extracted_text)
    result["ocr_engine"] = ocr.get_ocr_engine()
    result["source"] = "image_ocr"

    return result


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
