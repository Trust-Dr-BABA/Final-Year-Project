"""
analyze.py — POST /analyze endpoint.
Merges URL features, network signals, and permission signals into one
XGBoost prediction with SHAP explanation.

TODO (Phase 4): Implement full feature pipeline integration.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    url: str
    network_signals: dict | None = None
    permission_signals: dict | None = None


class ShapReason(BaseModel):
    feature: str
    value: float | int | bool | str | None
    shap_impact: float
    human_readable: str


class AnalyzeResponse(BaseModel):
    scan_id: str
    verdict: str           # "phishing" | "suspicious" | "legitimate"
    risk_score: float      # Raw probability, 0.0 – 1.0
    confidence_pct: int    # Round(risk_score * 100), shown in popup/dashboard
    top_reasons: list[ShapReason]
    flagged_rules: list[str]


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """
    Main analysis endpoint. Accepts a URL and optional browser signals,
    returns an XGBoost verdict with SHAP explanation and confidence score.

    TODO (Phase 4.2): Wire up the full ML pipeline:
      1. extract_url_features(request.url)
      2. heuristics_engine.evaluate(request.network_signals, request.permission_signals)
      3. model.predict_proba(features)
      4. shap_explainer.explain(features)
      5. Write Scan to DB
      6. Return AnalyzeResponse
    """
    logger.info(f"Received analysis request for: {request.url}")

    # ── STUB — replace in Phase 4 ──────────────────────────────────────────
    import uuid
    stub_response = AnalyzeResponse(
        scan_id=str(uuid.uuid4()),
        verdict="legitimate",
        risk_score=0.05,
        confidence_pct=5,
        top_reasons=[],
        flagged_rules=[],
    )
    return stub_response
