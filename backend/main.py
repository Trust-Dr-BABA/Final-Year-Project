"""
main.py — FastAPI application entry point.
Registers all routers, configures CORS, and exposes the health check endpoint.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import analyze, history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analyze.router, tags=["Analysis"])
app.include_router(history.router, tags=["History"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", summary="Health check")
async def health():
    """Returns 200 OK when the service is running."""
    return {"status": "ok", "version": "0.1.0"}
