"""
explainer_formatter.py — Converts raw SHAP feature names + values into
plain-English human-readable strings for display in the popup and dashboard.
"""

import json
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "shared" / "feature_name_to_human_readable.json"

def _load_templates() -> dict:
    """Load feature name → template mapping from shared/."""
    try:
        with open(_TEMPLATE_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"feature_name_to_human_readable.json not found at {_TEMPLATE_PATH}")
        return {}

TEMPLATES: dict = _load_templates()


def format_reason(feature_name: str, value: object, shap_impact: float) -> dict:
    """
    Convert a SHAP feature name and its value into a human-readable explanation.

    Args:
        feature_name: Snake_case feature name (e.g., "domain_age_days")
        value:        The actual feature value
        shap_impact:  The SHAP impact (positive = increases phishing probability)

    Returns:
        Dict with keys:
            "reason": Plain-English sentence safe to display in the UI.
            "impact": Rounded SHAP impact float.
        Falls back to a generic message if no template is found.
    """
    template = TEMPLATES.get(feature_name)

    if not template:
        logger.debug(f"No template for feature: {feature_name}")
        reason = f"Suspicious signal detected ({feature_name})"
    else:
        try:
            reason = template.replace("{value}", str(value))
        except Exception:
            reason = template

    return {
        "reason": reason,
        "impact": round(float(shap_impact), 4)
    }
