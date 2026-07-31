import unittest

from ml.shap_analysis import explain_prediction


class TestSHAP(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()