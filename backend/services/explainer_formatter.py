"""
explainer_formatter.py — Converts raw SHAP feature names + values into
plain-English human-readable strings for display in the popup and dashboard.
"""

import json
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "shared" / "feature_name_to_human_readable.json"

# Load feature name -> human-readable template mapping from shared/.
def _load_templates() -> dict:
    try:
        with open(_TEMPLATE_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"feature_name_to_human_readable.json not found at {_TEMPLATE_PATH}")
        return {}

TEMPLATES: dict = _load_templates()


# Convert a SHAP feature name and value into a plain-English sentence for the UI (ADR-010).
def format_reason(feature_name: str, value: object, shap_impact: float) -> str:
    if feature_name == "has_https":
        if value:
            return "Page uses a secure HTTPS connection"
        return "Page does not use a secure HTTPS connection"

    if feature_name == "has_ip_address":
        if value:
            return "URL uses a raw IP address instead of a domain name"
        return "URL uses a hostname instead of an IP address"

    if feature_name == "brand_impersonation":
        if value:
            return "URL contains a well-known brand name in a suspicious position"
        return "URL does not contain suspicious brand impersonation"

    template = TEMPLATES.get(feature_name)

    if not template:
        logger.debug(f"No template for feature: {feature_name}")
        return "Suspicious signal detected."

    try:
        return template.replace("{value}", str(value))
    except Exception:
        return template
