import unittest

from backend.services.explainer_formatter import format_reason


class TestExplainerFormatter(unittest.TestCase):

    def test_domain_age_days(self):
        result = format_reason("domain_age_days", 2, 0.45)

        self.assertEqual(
            result,
            "Domain was registered only 2 days ago"
        )

    def test_url_length(self):
        result = format_reason("url_length", 120, 0.80)

        self.assertEqual(
            result,
            "URL is unusually long (120 characters)"
        )

    def test_has_https_true(self):
        result = format_reason("has_https", 1, -0.10)

        self.assertEqual(
            result,
            "Page uses a secure HTTPS connection"
        )

    def test_has_https_false(self):
        result = format_reason("has_https", 0, 0.30)

        self.assertEqual(
            result,
            "Page does not use a secure HTTPS connection"
        )

    def test_unknown_feature(self):
        result = format_reason("unknown_feature", 5, 0.2)

        self.assertIn(
            "Suspicious signal detected",
            result
        )


if __name__ == "__main__":
    unittest.main()