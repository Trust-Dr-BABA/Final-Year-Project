import unittest

from backend.services.explainer_formatter import format_reason


class TestExplainerFormatter(unittest.TestCase):

    def test_domain_age_days(self):
        result = format_reason("domain_age_days", 2, 0.45)

        self.assertEqual(
            result["reason"],
            "Domain was registered only 2 days ago"
        )
        self.assertEqual(result["impact"], 0.45)

    def test_url_length(self):
        result = format_reason("url_length", 120, 0.80)

        self.assertEqual(
            result["reason"],
            "URL is unusually long (120 characters)"
        )
        self.assertEqual(result["impact"], 0.8)

    def test_unknown_feature(self):
        result = format_reason("unknown_feature", 5, 0.2)

        self.assertIn(
            "Suspicious signal detected",
            result["reason"]
        )
        self.assertEqual(result["impact"], 0.2)


if __name__ == "__main__":
    unittest.main()