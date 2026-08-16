"""test_sensitivity.py — Unit tests for ml/scripts/sensitivity.py's fusion helper.

Regression coverage for an aliasing bug (found 2026-08-15): _fuse_all() was called with
risk_fusion.SIGNAL_WEIGHTS passed directly as its `weights` argument, and clearing that global dict
in place also cleared `weights` since both names pointed at the same object — every reported
"baseline" was silently fused with an empty weight table instead of the shipped one, because the
`weights` parameter had already been wiped by the time it was read.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services import risk_fusion  # noqa: E402
from ml.scripts.sensitivity import TYPICAL_PAGE_SIGNALS, _fuse_all  # noqa: E402


class TestFuseAllDoesNotAliasTheGlobalWeightsTable:
    # The exact call pattern that triggered the bug: passing risk_fusion.SIGNAL_WEIGHTS directly
    # as `weights`, not a defensive copy of it.
    def test_passing_the_live_global_dict_still_applies_real_weights(self):
        expected, _ = risk_fusion.fuse(0.2, TYPICAL_PAGE_SIGNALS)

        p_fused = _fuse_all([0.2], risk_fusion.SIGNAL_WEIGHTS)[0]

        # If the aliasing bug is present, SIGNAL_WEIGHTS ends up empty inside _fuse_all, fuse()
        # finds no recognised keys, and this collapses to the unfused base probability (0.2)
        # instead of the properly fused value.
        assert abs(p_fused - expected) < 1e-9
        assert abs(p_fused - 0.2) > 1e-6  # TYPICAL_PAGE_SIGNALS has a nonzero tracker_count

    def test_the_global_weights_table_is_unchanged_after_the_call(self):
        before = dict(risk_fusion.SIGNAL_WEIGHTS)
        _fuse_all([0.2, 0.5], risk_fusion.SIGNAL_WEIGHTS)
        assert risk_fusion.SIGNAL_WEIGHTS == before

    def test_a_zeroed_weight_table_actually_takes_effect(self):
        zeroed = {name: (0.0, transform) for name, (_, transform) in risk_fusion.SIGNAL_WEIGHTS.items()}

        p_shipped = _fuse_all([0.2], risk_fusion.SIGNAL_WEIGHTS)[0]
        p_zeroed = _fuse_all([0.2], zeroed)[0]

        # A genuinely different weights argument must produce a genuinely different result —
        # proves _fuse_all uses the *passed* table, not whatever risk_fusion.SIGNAL_WEIGHTS
        # happened to hold beforehand.
        # No signal weights active at all -> logit/sigmoid round-trips back to the base probability
        # (not exact equality: floating-point log/exp round-trip, not a no-op).
        assert abs(p_zeroed - 0.2) < 1e-9
        assert abs(p_shipped - p_zeroed) > 1e-6
