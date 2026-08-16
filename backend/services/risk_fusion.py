"""
risk_fusion.py — Fuses the URL model's probability with browser-signal contributions in log-odds
space (ADR-014).

No labelled corpus carries per-URL tracker counts or permission-prompt timings, so browser signals
cannot be trained features. Instead each signal contributes a fixed, documented weight added
directly to the model's log-odds output. This works because SHAP values for a tree ensemble are
themselves additive log-odds contributions (Lundberg & Lee, 2017) — a hand-set weight added in the
same space is the same kind of quantity, so model attributions and browser-signal attributions can
be ranked in one list with no schema change anywhere downstream (see ml/shap_analysis.py).

Weights and their justification are documented in ml/reports/fusion_weights.md.
"""

import math
from collections.abc import Callable
from typing import Any

from backend.services.explainer_formatter import format_reason

_EPSILON = 1e-6


# Diminishing-returns transform: the Nth occurrence matters less than the first. Reaches ~63% of
# its way to 1.0 at value == scale, and saturates smoothly beyond it.
def _saturating(scale: float) -> Callable[[float], float]:
    def transform(value: float) -> float:
        return 1.0 - math.exp(-max(value, 0.0) / scale)

    return transform


# Binary flags pass through unchanged — already 0 or 1.
def _identity(value: float) -> float:
    return float(value)


# (weight, transform) per browser signal, in log-odds. Weights are hand-set (ADR-014), not
# learned; each is documented in ml/reports/fusion_weights.md and probed by the Sprint 2
# sensitivity analysis. Scales (10 trackers, 3 redirects) match heuristics_engine.py's own
# excessive_trackers / long_redirect_chain rule thresholds, so a signal saturates roughly where
# the rule-flag layer already calls it "excessive".
SIGNAL_WEIGHTS: dict[str, tuple[float, Callable[[float], float]]] = {
    "tracker_count": (1.5, _saturating(10.0)),
    "has_mixed_content": (1.0, _identity),
    "redirect_chain_length": (1.2, _saturating(3.0)),
    "cam_mic_on_first_visit": (2.0, _identity),
    "notification_prompt_on_load": (0.8, _identity),
    "location_on_load": (1.5, _identity),
    # Scale matches heuristics_engine.py's own scam_language_detected threshold (>=3), same
    # convention as tracker_count/redirect_chain_length. Weighted below cam_mic_on_first_visit
    # deliberately: an OS-level permission API call is unambiguous, but page-text phrase matching
    # is noisier — legitimate banking/e-commerce pages genuinely use urgent security language
    # ("verify your identity", "your account may be suspended") for real reasons, so a handful of
    # incidental matches must stay a weak signal, not a strong one.
    "scam_keyword_hits": (1.8, _saturating(3.0)),
    # Scale matches heuristics_engine.py's own multiple_sensitive_fields_requested threshold (>=2
    # distinct categories — a single password field, the ordinary login-page case, contributes
    # zero). Weighted the same as scam_keyword_hits rather than as strongly as cam_mic_on_first_visit:
    # both are DOM/content-based signals without real-world labelled validation data behind them,
    # unlike an OS-level permission API call, which is unambiguous by construction.
    "sensitive_field_count": (1.8, _saturating(2.0)),
}


# Natural log-odds of a probability, clamped so a 0 or 1 prediction never produces an infinite logit.
def _logit(p: float) -> float:
    p = min(max(p, _EPSILON), 1.0 - _EPSILON)
    return math.log(p / (1.0 - p))


# Inverse of _logit — maps fused log-odds back to a probability.
def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


# Fuse the URL model's probability with browser-signal contributions; returns (p_fused, attributions).
def fuse(p_url: float, signals: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
    z = _logit(p_url)
    attributions: list[dict[str, Any]] = []

    for name, (weight, transform) in SIGNAL_WEIGHTS.items():
        if name not in signals:
            continue
        value = signals[name]
        contribution = weight * transform(value)
        if contribution == 0:
            continue
        z += contribution
        attributions.append(
            {
                "feature": name,
                "value": value,
                "shap_impact": contribution,
                "human_readable": format_reason(name, value, contribution),
            }
        )

    return _sigmoid(z), attributions
