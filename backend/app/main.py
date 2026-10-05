"""
LeakedIn FastAPI Application Entrypoint.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.detector.ml import is_model_ready
from backend.app.ocr import is_ocr_available

app = FastAPI(
    title="LeakedIn — Job Posting Scanner API",
    description=(
        "AI-powered recruitment fraud detection. "
        "Uses a hybrid ML + rule-based + domain verification approach "
        "to identify fake job postings and protect job seekers."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow frontend (served separately or from a different port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, prefix="/api/v1")

@app.get("/health", summary="API health check")
async def health():
    model_status = is_model_ready()
    ocr_status = is_ocr_available()
    return {
        "status": "ok" if model_status else "degraded",
        "ml_model_loaded": model_status,
        "ocr_available": ocr_status,
        "service": "LeakedIn Job Posting Scanner",
        "version": "1.0.0",
    }

# Mount frontend web app (Module 6)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "LeakedIn API is running. Visit /docs for API documentation."}

