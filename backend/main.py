"""
main.py — FastAPI application entry point.
Registers all routers, configures CORS, and exposes the health check endpoint.
"""

from dotenv import load_dotenv

load_dotenv()  # must run before any module-level os.getenv() in the imports below

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.database import check_db_reachable
from backend.rate_limit import limiter
from backend.routers import analyze, history
from ml.shap_analysis import get_model_status

# Public docs describing the full API surface are useful in development but free reconnaissance
# for an attacker once this is actually reachable from the internet — off by default, opt in for
# local/dev work only.
_is_production = os.getenv("ENVIRONMENT", "development") == "production"

app = FastAPI(
    title="Explainable Security Analyst API",
    description="AI-powered phishing and privacy risk detection with SHAP explanations.",
    version="0.1.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Only the dashboard (a real web page, subject to browser CORS enforcement) needs an entry here.
# The extension is exempt from CORS entirely — Chrome grants cross-origin fetch to any host covered
# by manifest.json's host_permissions regardless of what this server sends — so this list is not
# what lets the extension reach the API; it's what stops an arbitrary third-party website's JS from
# reading scan data cross-origin.
_dashboard_origins = [
    origin.strip()
    for origin in os.getenv("DASHBOARD_ORIGIN", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_dashboard_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# Attach baseline hardening headers to every response — clickjacking/MIME-sniffing/referrer
# protection for the handful of headers that cost nothing and have no compatibility downside.
@app.middleware("http")
async def _security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


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
