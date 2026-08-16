"""
test_url_features.py — Unit tests for URL feature extraction.
All VirusTotal API calls are mocked — no real network calls.
"""

from pathlib import Path

import pandas as pd
import pytest

from backend.feature_extractor.url_features import extract_url_features, get_feature_names


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
        assert features["has_ip_address"] == 1

    def test_domain_not_flagged_as_ip(self):
        features = extract_url_features("https://google.com")
        assert features["has_ip_address"] == 0


class TestHttpsFlag:
    def test_http_is_zero(self):
        features = extract_url_features("http://example.com")
        assert features["has_https"] == 0

    def test_https_is_one(self):
        features = extract_url_features("https://example.com")
        assert features["has_https"] == 1


class TestBrandImpersonation:
    def test_exact_brand_in_subdomain_flagged(self):
        features = extract_url_features("http://paypal.secure-login.tk/")
        assert features["brand_impersonation"] == 1

    def test_brand_as_registrable_domain_not_flagged(self):
        features = extract_url_features("https://paypal.com/signin")
        assert features["brand_impersonation"] == 0

    def test_unrelated_domain_not_flagged(self):
        features = extract_url_features("https://example.com/login")
        assert features["brand_impersonation"] == 0

    # L1: homoglyph-normalised, bounded edit-distance matching against hostname tokens — catches
    # typosquats a plain substring check misses entirely.
    def test_cyrillic_homoglyph_flagged(self):
        # "pаypal" using Cyrillic а (U+0430), visually indistinguishable from Latin a.
        features = extract_url_features("http://pаypal-verify.tk/account")
        assert features["brand_impersonation"] == 1

    def test_leetspeak_digit_substitution_flagged(self):
        features = extract_url_features("http://paypa1-login.tk/secure")
        assert features["brand_impersonation"] == 1

    def test_single_letter_typo_in_long_brand_flagged(self):
        features = extract_url_features("http://microsofy-support.tk/reset")
        assert features["brand_impersonation"] == 1

    def test_distance_beyond_threshold_not_flagged(self):
        # "apple" (5 chars, threshold 1). "azzle" is 2 substitutions away (a-Z-Z-l-e vs a-P-P-l-e)
        # and, unlike "appleseed", does not contain "apple" as a literal substring either — this
        # isolates the fuzzy layer's distance boundary from the pre-existing exact-substring layer.
        features = extract_url_features("https://azzle-orchard.example.com/")
        assert features["brand_impersonation"] == 0


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
            "url_length", "digit_ratio", "num_special_chars", "subdomain_depth",
            "has_https", "url_entropy", "has_ip_address", "suspicious_tld_flag",
            "brand_impersonation", "domain_age_days", "vt_malicious_votes", "vt_harmless_votes",
        ]
        for key in expected_keys:
            assert key in features, f"Missing feature key: {key}"

    def test_extract_output_matches_get_feature_names(self):
        """extract_url_features() must return exactly the keys get_feature_names() promises — the
        two drifted apart once before (D4: a 12-column manifest against an 8-column features.csv)."""
        assert set(extract_url_features("https://example.com").keys()) == set(get_feature_names())


class TestFeatureColumnParity:
    """ROADMAP 1.3.3 — features.csv's trained columns must equal get_feature_names() minus the
    VT columns (ADR-013: VT is display-only corroboration, never trained on). Regenerate with
    `python ml/scripts/generate_features.py` if this fails after changing the extractor."""

    FEATURES_CSV = Path(__file__).resolve().parents[2] / "ml" / "data" / "processed" / "features.csv"
    VT_COLUMNS = {"domain_age_days", "vt_malicious_votes", "vt_harmless_votes"}
    NON_FEATURE_COLUMNS = {"url", "label", "submission_time", "target"}

    def test_features_csv_matches_extractor_minus_vt(self):
        if not self.FEATURES_CSV.exists():
            pytest.skip(f"{self.FEATURES_CSV} not generated in this environment")

        csv_columns = set(pd.read_csv(self.FEATURES_CSV, nrows=0).columns)
        trained_csv_columns = csv_columns - self.NON_FEATURE_COLUMNS - self.VT_COLUMNS
        expected = set(get_feature_names()) - self.VT_COLUMNS
        assert trained_csv_columns == expected
