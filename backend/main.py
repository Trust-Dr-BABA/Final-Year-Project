"""
main.py — FastAPI application entry point.
Registers all routers, configures CORS, and exposes the health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import analyze, history

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
# Returns 200 OK when the service is running.
@app.get("/health", summary="Health check")
async def health():
    return {"status": "ok", "version": "0.1.0"}
