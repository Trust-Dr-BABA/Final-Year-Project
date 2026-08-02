"""
url_features.py — URL and domain feature extraction.
All features extracted here are fed into the XGBoost classifier.

Phase 2 implementation target. Skeleton is ready; implement each TODO.
"""

import hashlib
import logging
import math
import re
from typing import Any

import tldextract

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".pw", ".cc", ".su", ".work", ".click", ".loan",
}

SPECIAL_CHARS = set("-_@?=%&")


def _shannon_entropy(text: str) -> float:
    """Compute Shannon entropy of a string."""
    if not text:
        return 0.0
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(text)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def _has_ip_address(hostname: str) -> bool:
    """Return True if hostname is an IPv4 address."""
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    return bool(re.match(pattern, hostname))


def _load_brand_list() -> set:
    """Load brand names from shared/brand_list.txt."""
    try:
        import os
        brand_path = os.path.join(
            os.path.dirname(__file__), "../../shared/brand_list.txt"
        )
        with open(brand_path) as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        logger.warning("brand_list.txt not found; brand impersonation check disabled.")
        return set()


BRAND_LIST = _load_brand_list()


# ── Main feature extractor ─────────────────────────────────────────────────────

def extract_url_features(url: str, vt_data: dict | None = None) -> dict[str, Any]:
    """
    Extract all features from a URL for XGBoost inference.

    Args:
        url: The full URL string to analyse.
        vt_data: Optional VirusTotal domain data dict with keys:
                 domain_age_days, vt_malicious_votes, vt_harmless_votes.
                 If None, VT features default to -1.

    Returns:
        A flat dict of feature_name -> value, ready for model inference.
    """
    features: dict[str, Any] = {}

    # ── Parse URL ─────────────────────────────────────────────────────────────
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        extracted = tldextract.extract(url)
        tld = f".{extracted.suffix}" if extracted.suffix else ""
    except Exception:
        hostname = ""
        tld = ""
        extracted = tldextract.extract(url)

    # ── Lexical features ──────────────────────────────────────────────────────
    features["url_length"] = len(url)
    features["num_digits"] = sum(c.isdigit() for c in url)
    features["num_special_chars"] = sum(c in SPECIAL_CHARS for c in url)
    features["subdomain_depth"] = hostname.count(".") - 1 if hostname else 0
    features["has_https"] = int(url.startswith("https://"))
    features["url_entropy"] = round(_shannon_entropy(url), 4)
    features["has_ip_address"] = int(_has_ip_address(hostname))

    # ── Suspicious TLD flag ───────────────────────────────────────────────────
    features["suspicious_tld_flag"] = int(tld.lower() in SUSPICIOUS_TLDS)

    # ── Brand impersonation ───────────────────────────────────────────────────
    # True if a known brand appears in the URL but is NOT the registrable domain
    registrable = extracted.domain.lower()
    brand_hit = any(
        brand in url.lower() and brand != registrable
        for brand in BRAND_LIST
    )
    features["brand_impersonation"] = int(brand_hit)

    # ── VirusTotal features (populated by VT client in Phase 2) ───────────────
    # Defaults to -1 if VT data is unavailable (timeout / API error)
    vt = vt_data or {}
    features["domain_age_days"]    = vt.get("domain_age_days", -1)
    features["vt_malicious_votes"] = vt.get("vt_malicious_votes", -1)
    features["vt_harmless_votes"]  = vt.get("vt_harmless_votes", -1)

    return features


def get_feature_names() -> list[str]:
    """Return the ordered list of feature names (must match feature_columns.json)."""
    return [
        "url_length",
        "num_digits",
        "num_special_chars",
        "subdomain_depth",
        "has_https",
        "url_entropy",
        "has_ip_address",
        "suspicious_tld_flag",
        "brand_impersonation",
        "domain_age_days",
        "vt_malicious_votes",
        "vt_harmless_votes",
    ]
