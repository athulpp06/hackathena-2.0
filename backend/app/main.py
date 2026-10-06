"""
main.py - FastAPI application entrypoint for LeakedIn API v2.0.

Security & Hardening:
  - Strict CORS defaults (preventing wildcard credential exploits)
  - Rate limiting via slowapi with IP spoofing protection
  - Structured logging (never logs message content)
  - Lifespan context manager for database initialization
  - /health endpoint with model metadata, gatekeeper, and OCR readiness
"""

import logging
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.app.api.routes import router
from backend.app.db.analytics import init_analytics_db
from backend.app.detector.gatekeeper import is_gemini_available
from backend.app.detector.ml import get_model_metadata, is_model_ready
from backend.app.detector.verification.reputation import init_db
from backend.app.limiter import limiter
from backend.app.ocr import is_ocr_available

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Safe defaults: localhost dev ports. Overridable via ALLOWED_ORIGINS env var.
_default_origins = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"
_raw_origins = os.getenv("ALLOWED_ORIGINS", _default_origins)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
_allow_all = "*" in ALLOWED_ORIGINS


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting LeakedIn API v2.0.0. CORS origins: %s", ALLOWED_ORIGINS)
    try:
        init_db()
        init_analytics_db()
    except Exception as exc:
        logger.warning("Database initialization warning: %s", exc)
    yield
    logger.info("LeakedIn API shutting down.")


app = FastAPI(
    title="LeakedIn API",
    version="2.0.0",
    description=(
        "AI-powered recruitment scam detection platform. "
        "Combines AI Gatekeeper, calibrated ML inference, multilingual heuristics, "
        "domain verification, community threat intelligence, and offer letter forensics."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, cast(Any, _rate_limit_exceeded_handler))
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else ALLOWED_ORIGINS,
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(router, prefix="")
app.include_router(router, prefix="/api/v1")

# Mount static frontend
_frontend_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")
    _assets_dir = os.path.join(_frontend_dir, "assets")
    if os.path.exists(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")


@app.get("/health", tags=["System"], summary="Health check")
async def health_check() -> dict:
    """Operational status + model and component metadata."""
    meta = get_model_metadata()
    return {
        "status": "ok",
        "service": "LeakedIn Job Posting Scanner",
        "ml_model_loaded": is_model_ready(),
        "model_ready": is_model_ready(),
        "model_version": meta.get("version", "2.0.0"),
        "model_metrics": meta.get("metrics", {}),
        "ocr_available": is_ocr_available(),
        "gemini_gatekeeper_available": is_gemini_available(),
        "privacy_note": "User content is analyzed in-memory and never permanently stored.",
    }


# Compatibility alias
health = health_check


@app.get("/", tags=["System"], summary="API root / UI entrypoint")
async def root():
    index_path = os.path.join(_frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(content={
        "message": "LeakedIn API v2.0.0 — AI-powered recruitment scam detector",
        "docs": "/docs",
        "health": "/health",
    })


@app.get("/styles.css", include_in_schema=False)
async def get_css():
    css_path = os.path.join(_frontend_dir, "styles.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    return Response(status_code=404)


@app.get("/app.js", include_in_schema=False)
async def get_js():
    js_path = os.path.join(_frontend_dir, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return Response(status_code=404)


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    fav_path = os.path.join(_frontend_dir, "assets", "brand", "favicon.ico")
    if os.path.exists(fav_path):
        return FileResponse(fav_path, media_type="image/x-icon")
    return Response(status_code=404)

