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

    def test_scam_keyword_hits_increases_score(self):
        clean, _ = fuse(0.2, {"scam_keyword_hits": 0})
        dirty, _ = fuse(0.2, {"scam_keyword_hits": 5})
        assert dirty > clean

    def test_sensitive_field_count_increases_score(self):
        clean, _ = fuse(0.2, {"sensitive_field_count": 0})
        dirty, _ = fuse(0.2, {"sensitive_field_count": 3})
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
        # A negative weight in this table would mean a browser/VT signal makes a page look *safer* —
        # never intended for anything in SIGNAL_WEIGHTS specifically. fuse()'s established-reputation
        # dampening is a deliberate, tightly-gated exception that lives outside this table on purpose
        # (see TestEstablishedReputationDampening) — it cannot be expressed as a single-signal entry
        # here since it depends on three signals jointly.
        for name, (weight, _transform) in SIGNAL_WEIGHTS.items():
            assert weight > 0, f"{name} has a non-positive weight"

    def test_vt_harmless_votes_is_never_a_standalone_entry(self):
        # Asymmetry invariant (ADR-013/014): a clean VT result must never lower the score on its
        # own — only the gated established-reputation path in fuse() may do that, and only when
        # domain age and vote count both clear a high bar. If vt_harmless_votes ever gets added
        # here directly, that invariant is gone.
        assert "vt_harmless_votes" not in SIGNAL_WEIGHTS


class TestEstablishedReputationDampening:
    _OLD_DOMAIN = {"domain_age_days": 400, "vt_malicious_votes": 0, "vt_harmless_votes": 61}

    def test_old_clean_well_corroborated_domain_lowers_score(self):
        base, _ = fuse(0.86, {})
        dampened, _ = fuse(0.86, self._OLD_DOMAIN)
        assert dampened < base

    def test_produces_a_vt_established_reputation_attribution(self):
        _, reasons = fuse(0.86, self._OLD_DOMAIN)
        assert len(reasons) == 1
        assert reasons[0]["feature"] == "vt_established_reputation"
        assert reasons[0]["shap_impact"] < 0

    def test_does_not_fire_for_a_young_domain(self):
        signals = {**self._OLD_DOMAIN, "domain_age_days": 30}
        base, _ = fuse(0.86, {})
        result, reasons = fuse(0.86, signals)
        assert abs(result - base) < 1e-9
        assert reasons == []

    def test_does_not_fire_if_any_vendor_flags_malicious(self):
        # vt_malicious_votes=1 still raises the score on its own (SIGNAL_WEIGHTS) — the point of
        # this test is that no vt_established_reputation attribution appears alongside it, not
        # that the score is unchanged from base.
        signals = {**self._OLD_DOMAIN, "vt_malicious_votes": 1}
        _, reasons = fuse(0.86, signals)
        assert [r["feature"] for r in reasons] == ["vt_malicious_votes"]

    def test_does_not_fire_with_too_few_harmless_votes(self):
        signals = {**self._OLD_DOMAIN, "vt_harmless_votes": 3}
        base, _ = fuse(0.86, {})
        result, reasons = fuse(0.86, signals)
        assert abs(result - base) < 1e-9
        assert reasons == []

    def test_does_not_fire_when_vt_data_is_unavailable(self):
        # -1 defaults (no VT key, timeout, error) must never accidentally satisfy the gate.
        signals = {"domain_age_days": -1, "vt_malicious_votes": -1, "vt_harmless_votes": -1}
        base, _ = fuse(0.86, {})
        result, reasons = fuse(0.86, signals)
        assert abs(result - base) < 1e-9
        assert reasons == []

    def test_more_harmless_votes_dampens_more(self):
        few, _ = fuse(0.86, {**self._OLD_DOMAIN, "vt_harmless_votes": 10})
        many, _ = fuse(0.86, {**self._OLD_DOMAIN, "vt_harmless_votes": 100})
        assert many < few
