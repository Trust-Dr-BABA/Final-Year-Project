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

from backend.services.explainer_formatter import format_reason

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "xgboost_phishing.pkl"
COLUMNS_PATH = MODELS_DIR / "feature_columns.json"


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


# Fallback heuristic prediction when the trained model or SHAP is unavailable.
def _simple_rule_prediction(feature_vector: dict[str, Any]) -> dict[str, Any]:
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

    score = min(max(score, 0.0), 1.0)
    if score > 0.70:
        label = "phishing"
    elif score >= 0.40:
        label = "suspicious"
    else:
        label = "legitimate"

    reasons = sorted(reasons, key=lambda x: abs(x["shap_impact"]), reverse=True)[:3]
    while len(reasons) < 3:
        reasons.append({
            "feature": "fallback_reason",
            "value": None,
            "shap_impact": 0.0,
            "human_readable": "No additional strong features were detected.",
        })

    return {
        "score": round(score, 4),
        "confidence_pct": round(score * 100),
        "label": label,
        "top_reasons": reasons,
    }


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
    allow_fallback = os.getenv("ESA_ALLOW_FALLBACK") == "1"

    if not MODEL_PATH.exists() or not COLUMNS_PATH.exists() or not _SHAP_AVAILABLE or not _PANDAS_AVAILABLE:
        if not allow_fallback:
            raise ModelUnavailableError("Trained model or SHAP dependencies are unavailable")
        logger.warning("SHAP model unavailable; using fallback heuristic prediction.")
        return _simple_rule_prediction(feature_vector)

    try:
        explainer, model, feature_columns = _get_explainer()
    except Exception as exc:
        if not allow_fallback:
            raise ModelUnavailableError(f"Unable to load SHAP model: {exc}") from exc
        logger.warning("Unable to load SHAP model: %s", exc)
        return _simple_rule_prediction(feature_vector)

    row = {col: feature_vector.get(col, -1) for col in feature_columns}
    X = pd.DataFrame([row])
    probability = float(model.predict_proba(X)[0][1])

    if probability > 0.70:
        label = "phishing"
    elif probability >= 0.40:
        label = "suspicious"
    else:
        label = "legitimate"

    shap_values = explainer.shap_values(X)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    shap_values = shap_values[0]

    reasons = []
    for feature_name, shap_value in zip(feature_columns, shap_values):
        reasons.append({
            "feature": feature_name,
            "value": row[feature_name],
            "shap_impact": float(shap_value),
            "human_readable": format_reason(feature_name, row[feature_name], float(shap_value)),
        })

    reasons = sorted(reasons, key=lambda x: abs(x["shap_impact"]), reverse=True)[:3]

    return {
        "score": round(probability, 4),
        "confidence_pct": round(probability * 100),
        "label": label,
        "top_reasons": reasons,
    }