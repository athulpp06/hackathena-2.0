"""
LeakedIn FastAPI Application Entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.detector.ml import is_model_ready

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
    return {
        "status": "ok" if model_status else "degraded",
        "ml_model_loaded": model_status,
        "service": "LeakedIn Job Posting Scanner",
        "version": "1.0.0",
    }

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "LeakedIn API is running. Visit /docs for API documentation."}
