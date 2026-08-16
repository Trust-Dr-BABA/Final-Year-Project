from backend.services.heuristics_engine import evaluate


class TestEvaluateNoSignals:
    def test_no_signals_returns_zeroed_defaults_and_no_flags(self):
        rule_flags, features = evaluate(None, None, None)
        assert rule_flags == []
        assert features["scam_keyword_hits"] == 0
        assert features["sensitive_field_count"] == 0


class TestScamContentSignals:
    def test_below_threshold_sets_feature_but_no_rule_flag(self):
        rule_flags, features = evaluate(None, None, {"scam_keyword_hits": 2})
        assert features["scam_keyword_hits"] == 2
        assert "scam_language_detected" not in rule_flags

    def test_at_threshold_triggers_rule_flag(self):
        rule_flags, features = evaluate(None, None, {"scam_keyword_hits": 3})
        assert features["scam_keyword_hits"] == 3
        assert "scam_language_detected" in rule_flags

    def test_missing_key_defaults_to_zero(self):
        rule_flags, features = evaluate(None, None, {})
        assert features["scam_keyword_hits"] == 0
        assert "scam_language_detected" not in rule_flags


class TestSensitiveFieldSignals:
    def test_single_password_field_is_not_flagged(self):
        # An ordinary login page: one category (password) is not itself a signal.
        rule_flags, features = evaluate(None, None, {"sensitive_field_count": 1})
        assert features["sensitive_field_count"] == 1
        assert "multiple_sensitive_fields_requested" not in rule_flags

    def test_two_categories_triggers_rule_flag(self):
        rule_flags, features = evaluate(None, None, {"sensitive_field_count": 2})
        assert features["sensitive_field_count"] == 2
        assert "multiple_sensitive_fields_requested" in rule_flags

    def test_missing_key_defaults_to_zero(self):
        rule_flags, features = evaluate(None, None, {})
        assert features["sensitive_field_count"] == 0
        assert "multiple_sensitive_fields_requested" not in rule_flags
