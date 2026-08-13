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

# Continuous lexical features whose SHAP attribution can land on either side of zero depending on
# context — unlike the fusion-layer signals (tracker_count, redirect_chain_length, ...), which are
# always risk-increasing by construction (every fusion weight is positive). Rendering these with a
# single unconditionally alarming template — "randomness score is high" — regardless of whether
# the attribution actually *raised* the score would misrepresent the model's own reasoning, which
# is a faithfulness problem in the presentation layer, not just an awkward sentence.
_RISK_INCREASING_TEMPLATES = {
    "url_length": "URL is unusually long ({value} characters)",
    "num_digits": "URL contains {value} digit characters, which is unusual",
    "num_special_chars": "URL contains {value} special characters often used in obfuscation",
    "subdomain_depth": "URL has {value} subdomain levels, which is unusually deep",
    "url_entropy": "URL string randomness score is high ({value}), suggesting generated text",
}
_RISK_DECREASING_TEMPLATES = {
    "url_length": "URL length ({value} characters) is unremarkable",
    "num_digits": "URL contains few digit characters ({value}), which is typical",
    "num_special_chars": "URL contains few special characters ({value}), which is typical",
    "subdomain_depth": "URL has a shallow subdomain structure ({value} level(s))",
    "url_entropy": "URL string randomness score is low ({value}), consistent with readable text",
}


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

    if feature_name in _RISK_INCREASING_TEMPLATES:
        direction = _RISK_INCREASING_TEMPLATES if shap_impact > 0 else _RISK_DECREASING_TEMPLATES
        return direction[feature_name].replace("{value}", str(value))

    template = TEMPLATES.get(feature_name)

    if not template:
        logger.debug(f"No template for feature: {feature_name}")
        return "Suspicious signal detected."

    try:
        return template.replace("{value}", str(value))
    except Exception:
        return template
