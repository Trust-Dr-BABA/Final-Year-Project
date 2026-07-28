"""
url_features.py

Extract lexical URL features for phishing detection.

Task 2.1.2
"""

import math
import re
from collections import Counter
from urllib.parse import urlparse

import tldextract


# High-risk TLDs
SUSPICIOUS_TLDS = {
    "xyz",
    "top",
    "tk",
    "ml",
    "ga",
    "cf",
    "gq",
    "pw",
    "cc",
    "su",
}


IP_REGEX = re.compile(
    r"^(?:\d{1,3}\.){3}\d{1,3}$"
)


def calculate_entropy(text: str) -> float:
    """
    Shannon entropy of a string.
    Higher entropy often indicates randomly generated URLs.
    """
    if not text:
        return 0.0

    counts = Counter(text)
    length = len(text)

    entropy = 0.0
    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    return round(entropy, 4)


def has_ip_address(hostname: str) -> bool:
    """
    Check whether hostname is an IPv4 address.
    """

    if hostname is None:
        return False

    return bool(IP_REGEX.fullmatch(hostname))


def count_special_chars(url: str) -> int:
    """
    Count suspicious special characters.

    Characters:
    - _ @ ? = %
    """

    special_chars = "-_@?=%"

    return sum(url.count(ch) for ch in special_chars)


def extract_url_features(url: str) -> dict:
    """
    Extract lexical URL features.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """

    parsed = urlparse(url)

    hostname = parsed.hostname or ""

    extracted = tldextract.extract(url)

    suffix = extracted.suffix.lower()

    # subdomain depth
    if extracted.subdomain:
        subdomain_depth = len(extracted.subdomain.split("."))
    else:
        subdomain_depth = 0

    features = {

        # Basic
        "url_length": len(url),

        # Digits
        "num_digits": sum(c.isdigit() for c in url),

        # Special chars
        "num_special_chars": count_special_chars(url),

        # IP hostname
        "has_ip_address": int(has_ip_address(hostname)),

        # Subdomains
        "subdomain_depth": subdomain_depth,

        # TLD
        "tld": suffix,

        # HTTPS
        "has_https": int(parsed.scheme.lower() == "https"),

        # Shannon entropy
        "url_entropy": calculate_entropy(url),

        # High-risk TLD
        "suspicious_tld_flag": int(
            suffix in SUSPICIOUS_TLDS
        ),
    }

    return features


if __name__ == "__main__":

    sample = "https://paypal-secure-login.xyz/account/login"

    print(extract_url_features(sample))