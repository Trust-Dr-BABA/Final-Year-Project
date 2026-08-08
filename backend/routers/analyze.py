"""
analyze.py — POST /analyze endpoint.

Merges URL features, browser network/permission signals,
XGBoost prediction, SHAP explanation, and PostgreSQL storage.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.scan import Scan
from backend.services.heuristics_engine import evaluate
from ml.features.url_features import extract_url_features
from ml.shap_analysis import explain_prediction


logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────

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
    verdict: str
    risk_score: float
    confidence_pct: int
    top_reasons: list[ShapReason]
    flagged_rules: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a URL using URL features, browser signals,
    XGBoost and SHAP, then save the result to PostgreSQL.
    """

    logger.info("Received analysis request for: %s", request.url)

    # ── 1. Extract lexical URL features ──────────────────────────────────────

    url_features = extract_url_features(request.url)

    logger.info("URL features extracted for: %s", request.url)

    # ── 2. Evaluate network + permission signals ─────────────────────────────

    flagged_rules, heuristic_features = evaluate(
        request.network_signals,
        request.permission_signals,
    )

    logger.info("Heuristic rules triggered: %s", flagged_rules)

    # ── 3. Run XGBoost + SHAP ────────────────────────────────────────────────
    #
    # explain_prediction() internally:
    # - loads the trained XGBoost model
    # - loads feature_columns.json
    # - arranges the 8 features in the correct order
    # - calculates predict_proba()
    # - calculates SHAP values
    # - generates top 3 human-readable reasons

    prediction = explain_prediction(url_features)

    risk_score = prediction["score"]
    confidence_pct = prediction["confidence_pct"]
    verdict = prediction["label"]
    top_reasons = prediction["top_reasons"]

    # ── 4. Save complete scan to PostgreSQL ─────────────────────────────────

    scan = Scan(
        url=request.url,
        verdict=verdict,
        risk_score=risk_score,
        confidence_pct=confidence_pct,
        url_features=url_features,
        network_signals=request.network_signals,
        permission_signals=request.permission_signals,
        shap_values=top_reasons,
        flagged_rules=flagged_rules,
    )

    db.add(scan)

    await db.commit()
    await db.refresh(scan)

    logger.info(
        "Scan saved successfully: %s | verdict=%s | score=%.4f",
        scan.id,
        verdict,
        risk_score,
    )

    # ── 5. Return API response ──────────────────────────────────────────────

    return AnalyzeResponse(
        scan_id=str(scan.id),
        verdict=verdict,
        risk_score=risk_score,
        confidence_pct=confidence_pct,
        top_reasons=[
            ShapReason(**reason)
            for reason in top_reasons
        ],
        flagged_rules=flagged_rules,
    )