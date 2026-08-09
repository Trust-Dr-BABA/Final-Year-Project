"""
shap_analysis.py — SHAP explainability layer.
Wraps the trained XGBoost model with a TreeExplainer to produce
per-prediction feature attribution values.
If the model artifact or SHAP dependencies are unavailable, falls back to a
simple heuristic prediction so the backend remains operational.
"""

import json
import logging
from pathlib import Path
from typing import Any

from backend.services.explainer_formatter import format_reason

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "xgboost_phishing.pkl"
COLUMNS_PATH = MODELS_DIR / "feature_columns.json"

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


def _load_model():
    """Load the trained XGBoost model and feature column list."""
    if not MODEL_PATH.exists() or not COLUMNS_PATH.exists() or not joblib or not _PANDAS_AVAILABLE:
        raise FileNotFoundError("SHAP model or required dependencies are unavailable")

    model = joblib.load(MODEL_PATH)
    with open(COLUMNS_PATH) as f:
        feature_columns = json.load(f)
    return model, feature_columns


def _get_explainer():
    """Lazily load model and create SHAP TreeExplainer."""
    global _model, _feature_columns, _explainer
    if _explainer is None:
        if not _SHAP_AVAILABLE:
            raise RuntimeError("SHAP is unavailable")
        _model, _feature_columns = _load_model()
        _explainer = shap.TreeExplainer(_model)
        logger.info("SHAP TreeExplainer initialized.")
    return _explainer, _model, _feature_columns


def _simple_rule_prediction(feature_vector: dict[str, Any]) -> dict[str, Any]:
    """Fallback heuristic prediction when the trained model or SHAP is unavailable."""
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


def explain_prediction(feature_vector: dict) -> dict:
    """
    Generate prediction + SHAP explanation for a single URL.
    """
    if not MODEL_PATH.exists() or not COLUMNS_PATH.exists() or not _SHAP_AVAILABLE or not _PANDAS_AVAILABLE:
        logger.warning("SHAP model unavailable; using fallback heuristic prediction.")
        return _simple_rule_prediction(feature_vector)

    try:
        explainer, model, feature_columns = _get_explainer()
    except Exception as exc:
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
if __name__ == "__main__":

    sample = {

        "url_length": 120,
        "num_digits": 8,
        "num_special_chars": 14,
        "has_ip_address": 0,
        "subdomain_depth": 2,
        "has_https": 0,
        "url_entropy": 5.3,
        "suspicious_tld_flag": 1

    }

    result = explain_prediction(sample)

    print(result)