"""virustotal_client.py — Async VirusTotal domain reputation client.

Returns domain_age_days, vt_malicious_votes, and vt_harmless_votes.
Caches responses in memory for a short TTL to avoid repeated API calls.
If the API key is missing or any error occurs, returns default values of -1.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Final

import httpx
from cachetools import TTLCache

logger = logging.getLogger(__name__)

_VT_CACHE: Final = TTLCache(maxsize=256, ttl=3600)
_DEFAULT_VT_DATA: Final = {
    "domain_age_days": -1,
    "vt_malicious_votes": -1,
    "vt_harmless_votes": -1,
}


async def _fetch_domain_info(domain: str) -> dict[str, int]:
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        logger.warning("VIRUSTOTAL_API_KEY is not set. Returning default VT values.")
        return _DEFAULT_VT_DATA.copy()

    url = f"https://www.virustotal.com/api/v3/domains/{domain}"
    headers = {"x-apikey": api_key}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        logger.warning("VirusTotal request failed for %s: %s", domain, exc)
        return _DEFAULT_VT_DATA.copy()

    if not isinstance(payload, dict):
        return _DEFAULT_VT_DATA.copy()

    attributes = payload.get("data", {}).get("attributes", {})
    if not isinstance(attributes, dict):
        return _DEFAULT_VT_DATA.copy()

    creation_date = attributes.get("creation_date")
    if isinstance(creation_date, (int, float)):
        now = datetime.now(timezone.utc).timestamp()
        domain_age_days = int(max(0.0, (now - float(creation_date)) / 86400.0))
    else:
        domain_age_days = -1

    last_analysis_stats = attributes.get("last_analysis_stats", {})
    if not isinstance(last_analysis_stats, dict):
        return _DEFAULT_VT_DATA.copy()

    try:
        vt_malicious_votes = int(last_analysis_stats.get("malicious", 0))
        vt_harmless_votes = int(last_analysis_stats.get("harmless", 0))
    except (TypeError, ValueError):
        return _DEFAULT_VT_DATA.copy()

    return {
        "domain_age_days": domain_age_days,
        "vt_malicious_votes": vt_malicious_votes,
        "vt_harmless_votes": vt_harmless_votes,
    }


async def get_domain_info(domain: str) -> dict[str, int]:
    if not domain:
        return _DEFAULT_VT_DATA.copy()

    cached = _VT_CACHE.get(domain)
    if cached is not None:
        return cached

    vt_data = await _fetch_domain_info(domain)
    _VT_CACHE[domain] = vt_data
    return vt_data
