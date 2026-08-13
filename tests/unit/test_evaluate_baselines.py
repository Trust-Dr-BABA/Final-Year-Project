"""
test_evaluate_baselines.py — Guards the two split protocols against the exact leakage they exist
to prevent: a URL or a domain appearing on both sides of a train/test split silently inflates
every downstream metric.
"""

import pandas as pd

from ml.scripts.evaluate_baselines import registrable_domain, temporal_split, unseen_domain_split


def _sample_frame(n_phishing: int = 40, n_benign: int = 40) -> pd.DataFrame:
    phishing = pd.DataFrame({
        "url": [f"http://phish-{i}.example/path" for i in range(n_phishing)],
        "label": 1,
        "submission_time": pd.date_range("2026-01-01", periods=n_phishing, freq="D", tz="UTC"),
        "url_length": 30,
    })
    benign = pd.DataFrame({
        "url": [f"https://benign-{i}.example/page" for i in range(n_benign)],
        "label": 0,
        "submission_time": pd.NaT,
        "url_length": 25,
    })
    return pd.concat([phishing, benign], ignore_index=True)


class TestTemporalSplit:
    def test_no_url_appears_in_both_train_and_test(self):
        train, test = temporal_split(_sample_frame())
        assert set(train["url"]) & set(test["url"]) == set()

    def test_phishing_train_urls_all_precede_phishing_test_urls(self):
        train, test = temporal_split(_sample_frame())
        train_phish_max = train.loc[train["label"] == 1, "submission_time"].max()
        test_phish_min = test.loc[test["label"] == 1, "submission_time"].min()
        assert train_phish_max <= test_phish_min

    def test_both_classes_present_on_both_sides(self):
        train, test = temporal_split(_sample_frame())
        for split in (train, test):
            assert (split["label"] == 1).any()
            assert (split["label"] == 0).any()


class TestUnseenDomainSplit:
    def test_no_domain_appears_in_both_train_and_test(self):
        train, test = unseen_domain_split(_sample_frame())
        train_domains = {registrable_domain(u) for u in train["url"]}
        test_domains = {registrable_domain(u) for u in test["url"]}
        assert train_domains & test_domains == set()

    def test_registrable_domain_ignores_subdomain(self):
        assert registrable_domain("https://a.b.example.com/x") == registrable_domain("https://example.com/y")
