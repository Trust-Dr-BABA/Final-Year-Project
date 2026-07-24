"""
heuristics_engine.py — Rule-based evaluation of network and permission signals.
Returns a list of triggered rule flags and derived heuristic features
to be merged into the XGBoost feature vector.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def evaluate(
    network_signals: dict | None,
    permission_signals: dict | None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Evaluate network and permission signals against heuristic rules.

    Args:
        network_signals:   Dict from the extension: tracker_count, has_mixed_content,
                           redirect_chain_length, third_party_domains.
        permission_signals: Dict from the extension: permissions_requested, rule_flags.

    Returns:
        Tuple of:
          - rule_flags: list[str]  — triggered rule identifiers (for popup display)
          - heuristic_features: dict — numeric features to merge into XGBoost input
    """
    rule_flags: list[str] = []
    heuristic_features: dict[str, Any] = {
        "tracker_count": 0,
        "has_mixed_content": 0,
        "redirect_chain_length": 0,
        "cam_mic_on_first_visit": 0,
        "notification_prompt_on_load": 0,
        "location_on_load": 0,
    }

    # ── Network signal features ───────────────────────────────────────────────
    if network_signals:
        heuristic_features["tracker_count"] = network_signals.get("tracker_count", 0)
        heuristic_features["has_mixed_content"] = int(
            network_signals.get("has_mixed_content", False)
        )
        heuristic_features["redirect_chain_length"] = network_signals.get(
            "redirect_chain_length", 0
        )

        # Heuristic rules on network signals
        if network_signals.get("tracker_count", 0) > 10:
            rule_flags.append("excessive_trackers")
        if network_signals.get("has_mixed_content", False):
            rule_flags.append("has_mixed_content")
        if network_signals.get("redirect_chain_length", 0) > 3:
            rule_flags.append("long_redirect_chain")

    # ── Permission signal features ────────────────────────────────────────────
    if permission_signals:
        triggered = permission_signals.get("rule_flags", [])

        if "cam_mic_on_first_visit" in triggered:
            rule_flags.append("cam_mic_on_first_visit")
            heuristic_features["cam_mic_on_first_visit"] = 1

        if "notification_prompt_on_load" in triggered:
            rule_flags.append("notification_prompt_on_load")
            heuristic_features["notification_prompt_on_load"] = 1

        if "location_on_load" in triggered:
            rule_flags.append("location_on_load")
            heuristic_features["location_on_load"] = 1

    if rule_flags:
        logger.info(f"Heuristics triggered: {rule_flags}")

    return rule_flags, heuristic_features
