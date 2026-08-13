"""
analyze.py — POST /analyze endpoint.
Merges URL features, network signals, and permission signals into one
XGBoost prediction with SHAP explanation.
"""

from urllib.parse import urlparse

import tldextract
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.feature_extractor.url_features import extract_url_features
from backend.models.scan import Scan
from backend.services.heuristics_engine import evaluate
from backend.services.virustotal_client import get_domain_info
from ml.shap_analysis import ModelUnavailableError, explain_prediction

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class NetworkSignals(BaseModel):
    tracker_count: int = Field(default=0, ge=0)
    has_mixed_content: bool = False
    redirect_chain_length: int = Field(default=0, ge=0)
    third_party_domains: list[str] = Field(default_factory=list)


class PermissionSignals(BaseModel):
    permissions_requested: list[str] = Field(default_factory=list)
    rule_flags: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    network_signals: NetworkSignals | None = None
    permission_signals: PermissionSignals | None = None


class ShapReason(BaseModel):
    feature: str
    value: float | int | bool | str | None
    shap_impact: float
    human_readable: str


class AnalyzeResponse(BaseModel):
    scan_id: str
    verdict: str           # "phishing" | "suspicious" | "legitimate"
    risk_score: float      # Raw probability, 0.0 – 1.0
    risk_pct: int           # round(risk_score * 100) — how phishing-like the page is (ADR-015)
    confidence_pct: int    # round(max(p, 1-p) * 100) — how decisive the model is (ADR-015)
    top_reasons: list[ShapReason]
    flagged_rules: list[str]


# Reduce a URL to its registrable domain (e.g. "sub.example.co.uk" -> "example.co.uk").
def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname or url
    extracted = tldextract.extract(hostname)
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}"
    return hostname


# Fuse URL, network, and permission signals into one XGBoost + SHAP verdict, and persist it.
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    url = str(request.url)
    network_signals = (
        request.network_signals.model_dump() if request.network_signals else None
    )
    permission_signals = (
        request.permission_signals.model_dump() if request.permission_signals else None
    )

    domain = _extract_domain(url)
    vt_data = await get_domain_info(domain)

    rule_flags, heuristic_features = evaluate(
        network_signals,
        permission_signals,
    )

    url_features = extract_url_features(url, vt_data=vt_data)
    feature_vector = {**url_features, **heuristic_features}

    try:
        analysis = explain_prediction(feature_vector)
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    scan = Scan(
        url=url,
        verdict=analysis["label"],
        risk_score=analysis["score"],
        risk_pct=analysis["risk_pct"],
        confidence_pct=analysis["confidence_pct"],
        url_features=url_features,
        network_signals=network_signals,
        permission_signals=permission_signals,
        shap_values=analysis["top_reasons"],
        flagged_rules=rule_flags,
    )

    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    return AnalyzeResponse(
        scan_id=str(scan.id),
        verdict=scan.verdict,
        risk_score=scan.risk_score,
        risk_pct=scan.risk_pct,
        confidence_pct=scan.confidence_pct,
        top_reasons=scan.shap_values or [],
        flagged_rules=scan.flagged_rules or [],
    )
