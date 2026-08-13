"""
test_risk_fusion.py — Unit tests for the log-odds fusion layer (ADR-014).
"""

from backend.services.risk_fusion import SIGNAL_WEIGHTS, fuse


class TestFuseNoSignals:
    def test_no_signals_returns_base_probability_unchanged(self):
        p_fused, reasons = fuse(0.2, {})
        assert abs(p_fused - 0.2) < 1e-6
        assert reasons == []


class TestFuseIncreasesRisk:
    def test_tracker_count_increases_score(self):
        clean, _ = fuse(0.2, {"tracker_count": 0})
        dirty, _ = fuse(0.2, {"tracker_count": 40})
        assert dirty > clean

    def test_mixed_content_increases_score(self):
        clean, _ = fuse(0.2, {"has_mixed_content": 0})
        dirty, _ = fuse(0.2, {"has_mixed_content": 1})
        assert dirty > clean

    def test_combined_signals_increase_score_more_than_any_one_alone(self):
        base, _ = fuse(0.2, {})
        one_signal, _ = fuse(0.2, {"tracker_count": 40})
        both_signals, _ = fuse(0.2, {"tracker_count": 40, "has_mixed_content": 1})
        assert base < one_signal < both_signals


class TestFuseAttributions:
    def test_active_signal_produces_an_attribution(self):
        _, reasons = fuse(0.2, {"tracker_count": 40})
        assert len(reasons) == 1
        assert reasons[0]["feature"] == "tracker_count"
        assert reasons[0]["shap_impact"] > 0

    def test_zero_valued_signal_produces_no_attribution(self):
        _, reasons = fuse(0.2, {"tracker_count": 0, "has_mixed_content": 0})
        assert reasons == []

    def test_attribution_has_no_internal_identifier_in_its_sentence(self):
        _, reasons = fuse(0.2, {"tracker_count": 40})
        assert "_" not in reasons[0]["human_readable"]

    def test_unrecognised_signal_key_is_ignored_not_raised(self):
        # fuse() only reads keys it knows about — the full merged feature_vector (lexical + VT +
        # browser signals) is passed through it, so it must tolerate keys meant for other layers.
        p_fused, reasons = fuse(0.2, {"url_length": 500, "domain_age_days": -1})
        assert reasons == []
        assert abs(p_fused - 0.2) < 1e-6


class TestFuseClamping:
    def test_probability_of_one_does_not_produce_infinite_logit(self):
        p_fused, _ = fuse(1.0, {"tracker_count": 40})
        assert 0.0 < p_fused < 1.0

    def test_probability_of_zero_does_not_produce_infinite_logit(self):
        p_fused, _ = fuse(0.0, {})
        assert 0.0 < p_fused < 1.0


class TestSignalWeightsTable:
    def test_every_weight_is_positive(self):
        # A negative weight would mean a browser signal makes a page look *safer* — never intended.
        for name, (weight, _transform) in SIGNAL_WEIGHTS.items():
            assert weight > 0, f"{name} has a non-positive weight"
