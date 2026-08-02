"""
shap_analysis.py — SHAP explainability layer.
Wraps the trained XGBoost model with a TreeExplainer to produce
per-prediction feature attribution values.

TODO (Phase 2.4): Implement explain_prediction() fully.
"""

import json
import logging
from pathlib import Path
from typing import Any
import pandas as pd
import joblib
import shap
from backend.services.explainer_formatter import format_reason

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "xgboost_phishing.pkl"
COLUMNS_PATH = MODELS_DIR / "feature_columns.json"


def _load_model():
    """Load the trained XGBoost model and feature column list."""
    model = joblib.load(MODEL_PATH)
    with open(COLUMNS_PATH) as f:
        feature_columns = json.load(f)
    return model, feature_columns


# Cache model in module scope (loaded once per process)
_model = None
_feature_columns = None
_explainer = None


def _get_explainer():
    """Lazily load model and create SHAP TreeExplainer."""
    global _model, _feature_columns, _explainer
    if _explainer is None:
        _model, _feature_columns = _load_model()
        _explainer = shap.TreeExplainer(_model)
        logger.info("SHAP TreeExplainer initialized.")
    return _explainer, _model, _feature_columns


def explain_prediction(feature_vector: dict) -> dict:
    """
    Generate prediction + SHAP explanation for a single URL.
    """

    explainer, model, feature_columns = _get_explainer()

    # Arrange features in same order used during training
    row = {}
    for col in feature_columns:
        row[col] = feature_vector.get(col, -1)

    X = pd.DataFrame([row])

    # Prediction
    probability = float(model.predict_proba(X)[0][1])

    if probability > 0.70:
        label = "phishing"
    elif probability >= 0.40:
        label = "suspicious"
    else:
        label = "legitimate"

    # SHAP values
    shap_values = explainer.shap_values(X)

    # XGBoost binary classifier
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    shap_values = shap_values[0]

    reasons = []

    for feature_name, shap_value in zip(feature_columns, shap_values):

        reasons.append({

            "feature": feature_name,

            "value": row[feature_name],

            "shap_impact": float(shap_value),

            "human_readable": format_reason(
                feature_name,
                row[feature_name],
                float(shap_value)
            )["reason"]

        })

    # Top 3 most important features
    reasons = sorted(
        reasons,
        key=lambda x: abs(x["shap_impact"]),
        reverse=True
    )[:3]

    return {

        "score": round(probability, 4),

        "confidence_pct": round(probability * 100),

        "label": label,

        "top_reasons": reasons


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