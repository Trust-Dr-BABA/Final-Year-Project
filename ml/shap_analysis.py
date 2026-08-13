"""
shap_analysis.py — SHAP explainability layer.
Wraps the trained XGBoost model with a TreeExplainer to produce
per-prediction feature attribution values.
If the model artifact or SHAP dependencies are unavailable, falls back to a
simple heuristic prediction so the backend remains operational.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from backend.feature_extractor.url_features import get_feature_names
from backend.services.explainer_formatter import format_reason
from backend.services.risk_fusion import SIGNAL_WEIGHTS, fuse

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "xgboost_phishing.pkl"
COLUMNS_PATH = MODELS_DIR / "feature_columns.json"

# Every key explain_prediction() is allowed to see: every name the extractor can produce (lexical
# + VT, even though VT isn't trained on) plus every browser signal the fusion layer recognises.
# Available unconditionally — unlike feature_columns.json, this doesn't require a trained artefact
# to exist, so it works even on the ESA_ALLOW_FALLBACK development path.
_KNOWN_FEATURE_KEYS = frozenset(get_feature_names()) | frozenset(SIGNAL_WEIGHTS.keys())


# Raised when the trained model can't be served and ESA_ALLOW_FALLBACK isn't set (ADR-016).
class ModelUnavailableError(RuntimeError):
    pass

_model = None
_feature_columns = None
_explainer = None
_SHAP_AVAILABLE = True
_PANDAS_AVAILABLE = True

try:
    import pandas as pd
except ImportError:
    _PANDAS_AVAILABLE = False
    pd = None  # type: ignore

try:
    import joblib
except ImportError:
    joblib = None  # type: ignore

try:
    import shap
except ImportError:
    _SHAP_AVAILABLE = False
    shap = None  # type: ignore


# Load the trained XGBoost model and its matching feature column list from disk.
def _load_model():
    if not MODEL_PATH.exists() or not COLUMNS_PATH.exists() or not joblib or not _PANDAS_AVAILABLE:
        raise FileNotFoundError("SHAP model or required dependencies are unavailable")

    model = joblib.load(MODEL_PATH)
    with open(COLUMNS_PATH) as f:
        feature_columns = json.load(f)

    if model.n_features_in_ != len(feature_columns):
        raise ValueError(
            f"Model/feature_columns drift: model.n_features_in_={model.n_features_in_} "
            f"!= len(feature_columns)={len(feature_columns)}. "
            "The .pkl and feature_columns.json must come from the same training run."
        )

    return model, feature_columns


# Lazily load the model once and cache a SHAP TreeExplainer for reuse across requests.
def _get_explainer():
    global _model, _feature_columns, _explainer
    if _explainer is None:
        if not _SHAP_AVAILABLE:
            raise RuntimeError("SHAP is unavailable")
        _model, _feature_columns = _load_model()
        _explainer = shap.TreeExplainer(_model)
        logger.info("SHAP TreeExplainer initialized.")
    return _explainer, _model, _feature_columns


# Raise if feature_vector carries a key neither the model, VT display, nor fusion recognises —
# silently dropping an unrecognised feature is exactly the defect (D2) that left browser signals
# computed, transmitted, and never actually used for weeks. See PROJECT_STATE.md, defect D2.
def _validate_known_keys(feature_vector: dict[str, Any]) -> None:
    unknown = set(feature_vector.keys()) - _KNOWN_FEATURE_KEYS
    if unknown:
        raise ValueError(f"explain_prediction() received unrecognised feature key(s): {sorted(unknown)}")


# Assign a verdict band from the fused probability (invariant #5: thresholds require a new ADR to change).
def _label_for(probability: float) -> str:
    if probability > 0.70:
        return "phishing"
    if probability >= 0.40:
        return "suspicious"
    return "legitimate"


# Fuse a base probability with browser-signal contributions, merge+rank all attributions, and pad
# to 3 reasons if neither the base score nor the signals produced enough. Shared by both the SHAP
# path and the heuristic fallback path, so fusion (claim C2) applies no matter which produced the
# base score — this is what lets the fusion acceptance test run today, ahead of Sprint 1.5's retrain.
def _finalize(base_score: float, base_reasons: list[dict[str, Any]],
              feature_vector: dict[str, Any]) -> dict[str, Any]:
    p_fused, fusion_reasons = fuse(base_score, feature_vector)

    reasons = sorted(base_reasons + fusion_reasons, key=lambda r: abs(r["shap_impact"]), reverse=True)[:3]
    while len(reasons) < 3:
        reasons.append({
            "feature": "fallback_reason",
            "value": None,
            "shap_impact": 0.0,
            "human_readable": "No additional strong features were detected.",
        })

    # ADR-015: risk and confidence are different quantities. risk_pct is how phishing-like the
    # page is; confidence_pct is how decisive the model is, in whichever direction — always >= 50,
    # since a coin-flip prediction is exactly 0% decisive. Conflating them (confidence_pct used to
    # just be round(p*100)) forced the popup to compute `100 - confidence` to show a safe verdict,
    # which is exactly the kind of UI-side arithmetic §3.1 exists to prevent.
    return {
        "score": round(p_fused, 4),
        "risk_pct": round(p_fused * 100),
        "confidence_pct": round(max(p_fused, 1 - p_fused) * 100),
        "label": _label_for(p_fused),
        "top_reasons": reasons,
    }


# Fallback heuristic prediction when the trained model or SHAP is unavailable (development only).
def _simple_rule_prediction(feature_vector: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
    score = 0.05
    reasons: list[dict[str, Any]] = []
    if feature_vector.get("has_ip_address", 0) == 1:
        score += 0.35
        reasons.append({
            "feature": "has_ip_address",
            "value": feature_vector.get("has_ip_address"),
            "shap_impact": 0.35,
            "human_readable": format_reason("has_ip_address", feature_vector.get("has_ip_address"), 0.35),
        })
    if feature_vector.get("suspicious_tld_flag", 0) == 1:
        score += 0.25
        reasons.append({
            "feature": "suspicious_tld_flag",
            "value": feature_vector.get("suspicious_tld_flag"),
            "shap_impact": 0.25,
            "human_readable": format_reason("suspicious_tld_flag", feature_vector.get("suspicious_tld_flag"), 0.25),
        })
    if feature_vector.get("brand_impersonation", 0) == 1:
        score += 0.20
        reasons.append({
            "feature": "brand_impersonation",
            "value": feature_vector.get("brand_impersonation"),
            "shap_impact": 0.20,
            "human_readable": format_reason("brand_impersonation", feature_vector.get("brand_impersonation"), 0.20),
        })
    if feature_vector.get("url_entropy", 0) > 4.5:
        score += 0.15
        reasons.append({
            "feature": "url_entropy",
            "value": feature_vector.get("url_entropy"),
            "shap_impact": 0.15,
            "human_readable": format_reason("url_entropy", feature_vector.get("url_entropy"), 0.15),
        })

    return min(max(score, 0.0), 1.0), reasons


# Report model load status for GET /health; never raises, unlike explain_prediction().
def get_model_status() -> dict[str, Any]:
    try:
        _, _, feature_columns = _get_explainer()
    except Exception:
        return {"model_loaded": False, "feature_count": 0, "model_sha256": None}
    return {
        "model_loaded": True,
        "feature_count": len(feature_columns),
        "model_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
    }


# Score a feature vector with XGBoost and attribute the result via SHAP.
# Raises ModelUnavailableError unless ESA_ALLOW_FALLBACK=1 (ADR-016) — a serving deployment
# must never silently degrade to the heuristic fallback.
def explain_prediction(feature_vector: dict) -> dict:
    _validate_known_keys(feature_vector)
    allow_fallback = os.getenv("ESA_ALLOW_FALLBACK") == "1"

    if not MODEL_PATH.exists() or not COLUMNS_PATH.exists() or not _SHAP_AVAILABLE or not _PANDAS_AVAILABLE:
        if not allow_fallback:
            raise ModelUnavailableError("Trained model or SHAP dependencies are unavailable")
        logger.warning("SHAP model unavailable; using fallback heuristic prediction.")
        base_score, base_reasons = _simple_rule_prediction(feature_vector)
        return _finalize(base_score, base_reasons, feature_vector)

    try:
        explainer, model, feature_columns = _get_explainer()
    except Exception as exc:
        if not allow_fallback:
            raise ModelUnavailableError(f"Unable to load SHAP model: {exc}") from exc
        logger.warning("Unable to load SHAP model: %s", exc)
        base_score, base_reasons = _simple_rule_prediction(feature_vector)
        return _finalize(base_score, base_reasons, feature_vector)

    row = {col: feature_vector.get(col, -1) for col in feature_columns}
    X = pd.DataFrame([row])
    probability = float(model.predict_proba(X)[0][1])

    shap_values = explainer.shap_values(X)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    shap_values = shap_values[0]

    base_reasons = []
    for feature_name, shap_value in zip(feature_columns, shap_values):
        base_reasons.append({
            "feature": feature_name,
            "value": row[feature_name],
            "shap_impact": float(shap_value),
            "human_readable": format_reason(feature_name, row[feature_name], float(shap_value)),
        })

    return _finalize(probability, base_reasons, feature_vector)