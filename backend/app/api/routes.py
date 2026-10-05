"""
FastAPI routes for the LeakedIn Job Posting Scanner API.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.detector import aggregator

router = APIRouter()


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
