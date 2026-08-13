"""
url_features.py — URL and domain feature extraction.
All features extracted here are fed into the XGBoost classifier.
"""

import ipaddress
import logging
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import tldextract

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".pw", ".cc", ".su", ".work", ".click", ".loan",
}

SPECIAL_CHARS = set("-_@?=%&")

# Display-only corroboration, never a trained feature (ADR-013) — VT ingests PhishTank, so training
# on its votes would be circular. Named here so callers can recognise these keys without
# re-deriving the set from feature_columns.json.
VT_COLUMNS = frozenset({"domain_age_days", "vt_malicious_votes", "vt_harmless_votes"})


# Compute Shannon entropy of a string, a proxy for randomness in the URL.
def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(text)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


# Return True if hostname is an IPv4 or IPv6 address rather than a domain name.
def _has_ip_address(hostname: str) -> bool:
    if not hostname:
        return False

    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


# Load known brand names from shared/brand_list.txt for the impersonation check.
def _load_brand_list() -> set:
    try:
        brand_path = Path(__file__).resolve().parents[2] / "shared" / "brand_list.txt"
        with open(brand_path) as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        logger.warning("brand_list.txt not found; brand impersonation check disabled.")
        return set()


BRAND_LIST = _load_brand_list()


# ── Main feature extractor ─────────────────────────────────────────────────────

# Extract every lexical, brand, and VT feature from a URL for XGBoost inference.
def extract_url_features(url: str, vt_data: dict | None = None) -> dict[str, Any]:
    features: dict[str, Any] = {}

    # ── Parse URL ─────────────────────────────────────────────────────────────
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    extracted = tldextract.extract(hostname or url)
    tld = f".{extracted.suffix}" if extracted.suffix else ""

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
    registrable = extracted.domain.lower() if extracted.domain else ""
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


# Ordered feature names — must match ml/models/feature_columns.json exactly (ROADMAP 1.3.3).
def get_feature_names() -> list[str]:
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
