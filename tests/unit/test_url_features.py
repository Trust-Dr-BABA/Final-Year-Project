"""
test_url_features.py — Unit tests for URL feature extraction.
All VirusTotal API calls are mocked — no real network calls.
"""

from unittest.mock import patch

import pytest

from backend.feature_extractor.url_features import extract_url_features


PHISHING_URLS = [
    "http://paypal-secure-login.xyz/verify?token=abc123",
    "http://192.168.1.1/bank/login.php",
    "http://amazon-account-suspended.tk/claim",
]

LEGITIMATE_URLS = [
    "https://www.google.com/search?q=test",
    "https://github.com/openai/gpt-4",
    "https://docs.python.org/3/library/os.html",
]

FAKE_VT_BENIGN = {"domain_age_days": 3650, "vt_malicious_votes": 0, "vt_harmless_votes": 70}
FAKE_VT_MALICIOUS = {"domain_age_days": 2, "vt_malicious_votes": 15, "vt_harmless_votes": 0}


class TestUrlLength:
    def test_long_phishing_url(self):
        features = extract_url_features(PHISHING_URLS[0])
        assert features["url_length"] > 30

    def test_normal_legitimate_url(self):
        features = extract_url_features(LEGITIMATE_URLS[0])
        assert features["url_length"] < 100


class TestSuspiciousTldFlag:
    def test_xyz_is_flagged(self):
        features = extract_url_features("http://example.xyz/login")
        assert features["suspicious_tld_flag"] == 1

    def test_tk_is_flagged(self):
        features = extract_url_features("http://example.tk/login")
        assert features["suspicious_tld_flag"] == 1

    def test_com_is_not_flagged(self):
        features = extract_url_features("https://google.com")
        assert features["suspicious_tld_flag"] == 0

    def test_org_is_not_flagged(self):
        features = extract_url_features("https://wikipedia.org/wiki/Python")
        assert features["suspicious_tld_flag"] == 0


class TestIpInHostname:
    def test_ip_address_detected(self):
        features = extract_url_features("http://192.168.1.1/login")
        assert features["has_ip_in_hostname"] == 1

    def test_domain_not_flagged_as_ip(self):
        features = extract_url_features("https://google.com")
        assert features["has_ip_in_hostname"] == 0


class TestHttpsFlag:
    def test_http_is_zero(self):
        features = extract_url_features("http://example.com")
        assert features["has_https"] == 0

    def test_https_is_one(self):
        features = extract_url_features("https://example.com")
        assert features["has_https"] == 1


class TestVirusTotalFeatures:
    def test_vt_data_merged_correctly(self):
        """VT data passed in should appear in feature dict."""
        features = extract_url_features("https://google.com", vt_data=FAKE_VT_BENIGN)
        assert features["domain_age_days"] == 3650
        assert features["vt_malicious_votes"] == 0

    def test_vt_defaults_to_minus_one_when_missing(self):
        """When no VT data is provided, VT features should default to -1."""
        features = extract_url_features("https://google.com", vt_data=None)
        assert features["domain_age_days"] == -1
        assert features["vt_malicious_votes"] == -1


class TestAllFeaturesPresent:
    def test_feature_keys_complete(self):
        """Ensure all expected feature keys are present in output."""
        features = extract_url_features("https://example.com")
        expected_keys = [
            "url_length", "num_digits", "num_special_chars", "subdomain_depth",
            "has_https", "url_entropy", "has_ip_in_hostname", "suspicious_tld_flag",
            "brand_impersonation", "domain_age_days", "vt_malicious_votes", "vt_harmless_votes",
        ]
        for key in expected_keys:
            assert key in features, f"Missing feature key: {key}"
