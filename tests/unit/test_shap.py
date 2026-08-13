import os
import unittest
from pathlib import Path
from unittest.mock import patch

import ml.shap_analysis as shap_analysis
from ml.shap_analysis import ModelUnavailableError, explain_prediction


class TestSHAP(unittest.TestCase):

    # Force the "no model artefact" condition directly rather than relying on none being present
    # on disk — a trained .pkl is gitignored but very much present once anyone runs train_model.py.
    def test_explain_prediction_raises_without_fallback_flag(self):
        with patch.dict(os.environ, {}, clear=False), \
             patch.object(shap_analysis, "MODEL_PATH", Path("/nonexistent/model.pkl")):
            os.environ.pop("ESA_ALLOW_FALLBACK", None)
            with self.assertRaises(ModelUnavailableError):
                explain_prediction({"url_length": 10})

    def test_explain_prediction(self):

        sample = {
            "url_length": 120,
            "num_digits": 8,
            "num_special_chars": 14,
            "has_ip_address": 0,
            "subdomain_depth": 2,
            "has_https": 0,
            "url_entropy": 5.3,
            "suspicious_tld_flag": 1
        }

        result = explain_prediction(sample)

        # confidence should be integer
        self.assertIsInstance(result["confidence_pct"], int)

        # confidence between 0 and 100
        self.assertGreaterEqual(result["confidence_pct"], 0)
        self.assertLessEqual(result["confidence_pct"], 100)

        # exactly 3 reasons
        self.assertEqual(len(result["top_reasons"]), 3)

        # no snake_case exposed to UI
        for reason in result["top_reasons"]:

            self.assertNotIn(
                "_",
                reason["human_readable"]
            )

    # D2 regression: explain_prediction() previously built its model input row with
    # {col: vector.get(col, -1) for col in feature_columns}, which silently discarded every key
    # feature_columns didn't already list — browser signals vanished with no error for weeks.
    # An unrecognised key must now raise, never disappear.
    def test_unknown_feature_key_raises(self):
        with self.assertRaises(ValueError):
            explain_prediction({"url_length": 10, "this_key_does_not_exist": 1})

    # D2 regression, claim C2: adverse browser signals must move the score, not just ride along
    # as display strings in flagged_rules while the number underneath stays the same.
    def test_adverse_browser_signals_raise_the_score(self):
        clean = {"url_length": 20, "num_digits": 0, "num_special_chars": 0, "has_ip_address": 0,
                  "subdomain_depth": 0, "has_https": 1, "url_entropy": 3.0, "suspicious_tld_flag": 0}
        dirty = {**clean, "tracker_count": 40, "has_mixed_content": 1, "redirect_chain_length": 6}

        clean_result = explain_prediction(clean)
        dirty_result = explain_prediction(dirty)

        self.assertGreater(dirty_result["score"], clean_result["score"])
        dirty_feature_names = {r["feature"] for r in dirty_result["top_reasons"]}
        self.assertTrue(dirty_feature_names & {"tracker_count", "has_mixed_content", "redirect_chain_length"})


if __name__ == "__main__":
    unittest.main()