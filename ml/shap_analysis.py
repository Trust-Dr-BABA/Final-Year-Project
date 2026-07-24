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

import joblib
import shap

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


def explain_prediction(feature_vector: dict) -> dict[str, Any]:
    """
    Compute XGBoost prediction + SHAP explanation for a single URL.

    Args:
        feature_vector: Dict of feature_name -> value (same keys as feature_columns.json).

    Returns:
        {
          "score": float,          # Raw phishing probability 0.0 – 1.0
          "confidence_pct": int,   # Round(score * 100)
          "label": str,            # "phishing" | "suspicious" | "legitimate"
          "top_reasons": [
            {
              "feature": str,
              "value": any,
              "shap_impact": float,
              "human_readable": str  # Populated by explainer_formatter
            }
          ]
        }

    TODO (Phase 2.4):
      1. Convert feature_vector to ordered DataFrame using _feature_columns
      2. Call model.predict_proba() → risk_score
      3. Call explainer.shap_values() → shap_values
      4. Pick top 3 features by abs(shap_impact)
      5. Call format_reason() for each
      6. Return full dict
    """
    explainer, model, feature_columns = _get_explainer()

    # ── STUB ─────────────────────────────────────────────────────────────────
    # Replace this in Phase 2.4 with real implementation
    return {
        "score": 0.0,
        "confidence_pct": 0,
        "label": "legitimate",
        "top_reasons": [],
    }
