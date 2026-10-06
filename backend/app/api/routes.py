"""
routes.py - Standardized and unified FastAPI router for LeakedIn threat analysis.
Supports Text, URL, Image OCR, Document PDF/DOCX Forensics, Community Threat DB,
Rate Limiting, and backwards-compatible legacy aliases.
"""

import io
import logging
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from backend.app.db.analytics import (
    get_aggregate_stats,
    init_analytics_db,
    record_feedback_entry,
    record_scan_event,
)
from backend.app.detector import aggregator, gatekeeper
from backend.app.detector.document_checks import check_document
from backend.app.detector.verification.reputation import bulk_lookup, init_db, report
from backend.app.limiter import limiter
from backend.app.ocr import extract_text_from_image, is_ocr_available, get_ocr_engine
from backend.app.utils.document_extractor import (
    extract_text_from_docx,
    extract_text_from_pdf,
    validate_file,
)
from backend.app.utils.scraper import (
    BlockedURLError,
    FetchError,
    ScrapeError,
    ScrapingNotAllowedError,
    scrape_job_url,
)

logger = logging.getLogger(__name__)

# Initialize database tables on load
try:
    init_db()
    init_analytics_db()
except Exception as e:
    logger.warning("Database init warning: %s", e)

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024       # 10 MB for images
MAX_DOC_UPLOAD_BYTES = 5 * 1024 * 1024    # 5 MB for PDF/DOCX


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------
class JobAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Job posting content to evaluate")
    company_name: Optional[str] = Field(default="", max_length=200, description="Claimed employer name")
    contact_email: Optional[str] = Field(default="", max_length=200, description="Contact email address")
    gemini_api_key: Optional[str] = Field(default="", max_length=200, description="Optional Google Gemini API Key")


class URLAnalysisRequest(BaseModel):
    url: str = Field(..., max_length=2000, description="URL of the recruitment posting")
    company_name: Optional[str] = Field(default="", max_length=200, description="Claimed company name")
    contact_email: Optional[str] = Field(default="", max_length=200, description="Recruiter contact email")
    gemini_api_key: Optional[str] = Field(default="", max_length=200, description="Optional Google Gemini API Key")


class ReportRequest(BaseModel):
    value: str = Field(..., min_length=3, max_length=300, description="Identifier (email, phone, upi, domain)")
    entity_type: str = Field(..., description="One of: email, phone, upi, domain")
    reporter_id: str = Field(default="anonymous", max_length=100)
    notes: Optional[str] = Field(default="", max_length=500)


class FeedbackRequest(BaseModel):
    verdict: str = Field(..., description="'correct', 'incorrect', or 'missed_scam'")
    analysis_id: Optional[str] = Field(default="")
    opt_in_text: Optional[bool] = Field(default=False)
    raw_text: Optional[str] = Field(default="")


# Aliases for compatibility
TextAnalysisRequest = JobAnalysisRequest
UrlAnalysisRequest = URLAnalysisRequest


# ---------------------------------------------------------------------------
# Core Pipeline Worker (Shared across API Endpoints)
# ---------------------------------------------------------------------------
def _run_pipeline(
    text: str,
    company_name: str = "",
    contact_email: str = "",
    endpoint_name: str = "text",
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png",
    skip_gatekeeper: bool = False,
) -> Dict[str, Any]:
    """Runs full hybrid fraud analysis with AI Gatekeeper & telemetry."""
    t0 = time.monotonic()
    result = aggregator.analyse(
        text=text,
        declared_company=company_name,
        contact_email=contact_email,
        image_bytes=image_bytes,
        mime_type=mime_type,
        skip_gatekeeper=skip_gatekeeper,
    )
    processing_ms = int((time.monotonic() - t0) * 1000)
    result["processing_ms"] = processing_ms

    # Telemetry logging (zero PII)
    if result.get("is_job_posting", True):
        rule_cats = [f.get("category", "") for f in result.get("red_flags", []) if f.get("category")]
        record_scan_event(
            endpoint=endpoint_name,
            risk_level=result.get("risk_level", "Unknown"),
            language=result.get("language", "en"),
            rule_categories=rule_cats,
        )

    return result


# ---------------------------------------------------------------------------
# Canonical Analysis Implementation & Endpoints
# ---------------------------------------------------------------------------
async def _analyze_text_impl(body: JobAnalysisRequest) -> Dict[str, Any]:
    return _run_pipeline(
        text=body.text,
        company_name=body.company_name or "",
        contact_email=body.contact_email or "",
        endpoint_name="text",
    )


@router.post("/api/analyze/text", tags=["Analysis"], summary="Analyze job posting text")
@limiter.limit("30/minute")
async def analyze_text(request: Request, body: JobAnalysisRequest) -> Dict[str, Any]:
    return await _analyze_text_impl(body)


# Compatibility programmatic helper for direct tests
async def analyse_job(request: Any, body: Optional[JobAnalysisRequest] = None) -> Dict[str, Any]:
    target_body = request if isinstance(request, JobAnalysisRequest) else body
    if target_body is None:
        raise HTTPException(status_code=400, detail="Missing request body.")
    return await _analyze_text_impl(target_body)


async def _analyze_url_impl(body: URLAnalysisRequest) -> Dict[str, Any]:
    try:
        scraped_text = scrape_job_url(body.url)
    except (BlockedURLError, ScrapingNotAllowedError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ScrapeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = _run_pipeline(
        text=scraped_text,
        company_name=body.company_name or "",
        contact_email=body.contact_email or "",
        endpoint_name="url",
    )
    result["extracted_text"] = scraped_text[:800]
    return result


@router.post("/api/analyze/url", tags=["Analysis"], summary="Scrape and analyze job posting URL")
@limiter.limit("30/minute")
async def analyze_url(request: Request, body: URLAnalysisRequest) -> Dict[str, Any]:
    return await _analyze_url_impl(body)


# Compatibility programmatic helper for direct tests
async def analyse_url(request: Any, body: Optional[URLAnalysisRequest] = None) -> Dict[str, Any]:
    target_body = request if isinstance(request, URLAnalysisRequest) else body
    if target_body is None:
        raise HTTPException(status_code=400, detail="Missing request body.")
    return await _analyze_url_impl(target_body)


@router.post("/api/analyze/image", tags=["Analysis"], summary="Extract text from screenshot and analyze")
@limiter.limit("30/minute")
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    company_name: str = Form(""),
    contact_email: str = Form(""),
    gemini_api_key: Optional[str] = Form(""),
) -> Dict[str, Any]:
    content_type = file.content_type or "image/png"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{content_type}'. Must be an image.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Image exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit.")

    try:
        extracted_text = extract_text_from_image(image_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"OCR failed: {exc}") from exc

    if not extracted_text.strip() or "no text could be extracted" in extracted_text.lower():
        raise HTTPException(status_code=422, detail="No readable text could be extracted from image.")

    result = _run_pipeline(
        text=extracted_text,
        company_name=company_name,
        contact_email=contact_email,
        endpoint_name="image",
        image_bytes=image_bytes,
        mime_type=content_type,
    )
    result["extracted_text"] = extracted_text[:800]
    return result


@router.post("/api/analyze/document", tags=["Analysis"], summary="Analyze PDF/DOCX offer letter forensics")
@limiter.limit("30/minute")
async def analyze_document(
    request: Request,
    file: UploadFile = File(...),
    company_name: str = Form(""),
    contact_email: str = Form(""),
) -> Dict[str, Any]:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > MAX_DOC_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Document exceeds {MAX_DOC_UPLOAD_BYTES // (1024*1024)} MB limit.")

    try:
        file_type = validate_file(
            filename=file.filename or "",
            content_type=file.content_type or "",
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    metadata: Dict[str, Any] = {}
    try:
        if file_type == "pdf":
            extracted_text, metadata = extract_text_from_pdf(data)
        else:
            extracted_text, metadata = extract_text_from_docx(data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to extract document text: {exc}") from exc

    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="No readable text found in document.")

    # Run base pipeline
    result = _run_pipeline(
        text=extracted_text,
        company_name=company_name,
        contact_email=contact_email,
        endpoint_name="document",
    )

    # Document-specific forensic checks
    doc_checks = check_document(extracted_text, metadata=metadata)
    doc_penalty = 0
    if doc_checks["placeholders_found"]:
        doc_penalty += 15
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
# Community Reputation & Feedback Endpoints
# ---------------------------------------------------------------------------
@router.post("/api/report", tags=["Reputation"], summary="Report scam identifier to community registry")
@limiter.limit("10/minute")
async def report_entity(request: Request, body: ReportRequest) -> Dict[str, Any]:
    valid_types = {"email", "phone", "upi", "domain"}
    if body.entity_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"entity_type must be one of {valid_types}")
    return report(body.value, body.entity_type, reporter_id=body.reporter_id)


@router.get("/api/reputation/lookup", tags=["Reputation"], summary="Look up identifier in community DB")
@limiter.limit("30/minute")
async def reputation_lookup(request: Request, value: str) -> Dict[str, Any]:
    from backend.app.detector.verification.reputation import lookup
    res = lookup(value)
    if res:
        return {"found": True, **res}
    return {"found": False}


@router.post("/api/feedback", tags=["System"], summary="Submit detection feedback")
@limiter.limit("10/minute")
async def submit_feedback(request: Request, body: FeedbackRequest) -> Dict[str, Any]:
    valid_verdicts = {"correct", "incorrect", "missed_scam"}
    if body.verdict not in valid_verdicts:
        raise HTTPException(status_code=400, detail=f"verdict must be one of {valid_verdicts}")

    entry = record_feedback_entry(
        verdict=body.verdict,
        analysis_id=body.analysis_id or "",
        opt_in_text=bool(body.opt_in_text),
        raw_text=body.raw_text or "",
    )
    return {
        "status": "received",
        "message": "Feedback recorded successfully. Thank you for protecting job seekers!",
        "text_stored": entry.get("text_stored", False),
    }


@router.get("/api/stats", tags=["System"], summary="Aggregate usage statistics (Zero PII)")
@limiter.limit("30/minute")
async def api_stats(request: Request) -> Dict[str, Any]:
    return get_aggregate_stats()


# ---------------------------------------------------------------------------
# Gatekeeper & OCR System Endpoints
# ---------------------------------------------------------------------------
@router.get("/gatekeeper-status", tags=["System"], summary="Check AI Gatekeeper status")
async def gatekeeper_status() -> Dict[str, Any]:
    key = gatekeeper.get_gemini_api_key()
    has_key = bool(key and len(key.strip()) > 10)
    current_model = gatekeeper.get_gemini_model()
    return {
        "gemini_active": has_key,
        "mode": "multimodal_gemini_ai" if has_key else "offline_heuristic_classifier",
        "model": current_model if has_key else "builtin_offline_rules",
        "vision_supported": has_key,
        "message": f"Gemini ({current_model}) multimodal gatekeeper active" if has_key else "Operating in zero-config offline gatekeeper mode",
    }


@router.get("/ocr-status", tags=["System"], summary="Check OCR availability")
async def ocr_status() -> Dict[str, Any]:
    engine = get_ocr_engine()
    return {
        "ocr_available": is_ocr_available(),
        "engine": engine or "None",
        "supported_formats": ["JPEG", "PNG", "WebP", "BMP", "TIFF"],
    }


# ---------------------------------------------------------------------------
# Backward-Compatible Legacy Aliases
# ---------------------------------------------------------------------------
@router.post("/analyse-job", tags=["Legacy Aliases"], summary="Legacy alias for text analysis")
@limiter.limit("30/minute")
async def legacy_analyse_job(request: Request, body: JobAnalysisRequest):
    return await analyze_text(request=request, body=body)


@router.post("/analyse-text", tags=["Legacy Aliases"], summary="Legacy alias for text analysis")
@limiter.limit("30/minute")
async def legacy_analyse_text(request: Request, body: TextAnalysisRequest):
    return await analyze_text(request=request, body=body)


@router.post("/analyze/text", tags=["Legacy Aliases"], summary="Extension alias for text analysis")
@limiter.limit("30/minute")
async def legacy_analyze_text_alias(request: Request, body: TextAnalysisRequest):
    return await analyze_text(request=request, body=body)


@router.post("/analyse-url", tags=["Legacy Aliases"], summary="Legacy alias for url analysis")
@limiter.limit("30/minute")
async def legacy_analyse_url(request: Request, body: URLAnalysisRequest):
    return await analyze_url(request=request, body=body)


@router.post("/analyze/url", tags=["Legacy Aliases"], summary="Extension alias for url analysis")
@limiter.limit("30/minute")
async def legacy_analyze_url_alias(request: Request, body: URLAnalysisRequest):
    return await analyze_url(request=request, body=body)


@router.post("/analyse-image", tags=["Legacy Aliases"], summary="Legacy alias for image analysis")
@limiter.limit("30/minute")
async def legacy_analyse_image(
    request: Request,
    file: UploadFile = File(...),
    company_name: str = Form(""),
    contact_email: str = Form(""),
    gemini_api_key: Optional[str] = Form(""),
):
    return await analyze_image(
        request=request,
        file=file,
        company_name=company_name,
        contact_email=contact_email,
        gemini_api_key=gemini_api_key,
    )


@router.post("/analyze/image", tags=["Legacy Aliases"], summary="Extension alias for image analysis")
@limiter.limit("30/minute")
async def legacy_analyze_image_alias(
    request: Request,
    file: UploadFile = File(...),
    company_name: str = Form(""),
    contact_email: str = Form(""),
    gemini_api_key: Optional[str] = Form(""),
):
    return await analyze_image(
        request=request,
        file=file,
        company_name=company_name,
        contact_email=contact_email,
        gemini_api_key=gemini_api_key,
    )
