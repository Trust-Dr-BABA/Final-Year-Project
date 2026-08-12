"""
main.py — FastAPI application entry point.
Registers all routers, configures CORS, and exposes the health check endpoint.
"""

from dotenv import load_dotenv

load_dotenv()  # must run before any module-level os.getenv() in the imports below

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import check_db_reachable
from backend.routers import analyze, history
from ml.shap_analysis import get_model_status

app = FastAPI(
    title="Explainable Security Analyst API",
    description="AI-powered phishing and privacy risk detection with SHAP explanations.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow Chrome extension and local dashboard origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analyze.router, tags=["Analysis"])
app.include_router(history.router, tags=["History"])


# ── Health check ──────────────────────────────────────────────────────────────
# Reports model, dependency, and database status so a demo can be verified before it starts (ADR-016).
@app.get("/health", summary="Health check")
async def health():
    model_status = get_model_status()
    return {
        "status": "ok",
        "version": "0.1.0",
        "model_loaded": model_status["model_loaded"],
        "feature_count": model_status["feature_count"],
        "model_sha256": model_status["model_sha256"],
        "vt_key_configured": bool(os.getenv("VIRUSTOTAL_API_KEY")),
        "db_reachable": await check_db_reachable(),
    }
