"""
bench_latency.py — Measures POST /analyze wall-clock latency, cold and warm VirusTotal cache.

The dominant cost in a request is the VirusTotal lookup (5s timeout on a cache miss); everything
else — feature extraction, XGBoost inference, SHAP attribution, fusion — is local computation on a
single row and is fast by comparison. Cold and warm are measured as genuinely separate conditions
using the *same* set of distinct domains twice: the first pass populates the 1-hour TTL cache
(backend/services/virustotal_client.py), the second pass hits it.

The cold pass is paced (~15s between requests) to stay under VirusTotal's free-tier rate limit
(4 requests/minute) — an unpaced burst would trip VT's own rate limiting and measure "how fast VT
rejects a request" rather than "how slow a real cold lookup is", which is a different, misleading
number.

Usage:
    python ml/scripts/bench_latency.py --base-url http://127.0.0.1:8200

Output:
    ml/reports/evaluation_report.md  (appended)
"""

import argparse
import logging
import time
from pathlib import Path
from statistics import median

import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REPORT_PATH = Path(__file__).parent.parent / "reports" / "evaluation_report.md"

# Distinct domains so each represents a genuine, independent VT cache entry.
TEST_URLS = [
    "https://example.com/",
    "https://wikipedia.org/",
    "https://github.com/",
    "https://mozilla.org/",
    "https://python.org/",
    "https://w3.org/",
    "https://apache.org/",
    "https://debian.org/",
    "https://gnu.org/",
    "https://kernel.org/",
]

VT_RATE_LIMIT_PACING_S = 16  # 4 req/min free tier -> comfortably under one request per 15s


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[idx]


def time_one_request(client: httpx.Client, url: str) -> float:
    start = time.monotonic()
    response = client.post("/analyze", json={"url": url}, timeout=30.0)
    elapsed = time.monotonic() - start
    response.raise_for_status()
    return elapsed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url) as client:
        health = client.get("/health", timeout=10.0).json()
        logger.info("Target: %s | model_loaded=%s vt_key_configured=%s",
                    args.base_url, health.get("model_loaded"), health.get("vt_key_configured"))

        logger.info("Cold pass: %d distinct domains, paced %ds apart", len(TEST_URLS), VT_RATE_LIMIT_PACING_S)
        cold_times = []
        for i, url in enumerate(TEST_URLS):
            elapsed = time_one_request(client, url)
            cold_times.append(elapsed)
            logger.info("  [cold %d/%d] %s -> %.3fs", i + 1, len(TEST_URLS), url, elapsed)
            if i < len(TEST_URLS) - 1:
                time.sleep(VT_RATE_LIMIT_PACING_S)

        logger.info("Warm pass: same %d domains, no pacing (VT cache should be hot)", len(TEST_URLS))
        warm_times = []
        for i, url in enumerate(TEST_URLS):
            elapsed = time_one_request(client, url)
            warm_times.append(elapsed)
            logger.info("  [warm %d/%d] %s -> %.3fs", i + 1, len(TEST_URLS), url, elapsed)

    cold_p50, cold_p95 = median(cold_times), percentile(cold_times, 95)
    warm_p50, warm_p95 = median(warm_times), percentile(warm_times, 95)
    logger.info("Cold: p50=%.3fs p95=%.3fs | Warm: p50=%.3fs p95=%.3fs", cold_p50, cold_p95, warm_p50, warm_p95)

    section = [
        "", "## Latency — POST /analyze", "",
        f"Measured against `{args.base_url}` ({len(TEST_URLS)} distinct domains, real model loaded). "
        "Cold pass paced at one request per "
        f"{VT_RATE_LIMIT_PACING_S}s to stay under VirusTotal's free-tier rate limit rather than "
        "measuring how fast VT rejects an over-limit burst; warm pass repeats the same domains "
        "immediately after, against the 1-hour TTL cache.", "",
        "| Condition | p50 | p95 | NFR-01 budget |", "|---|---|---|---|",
        f"| Cold VT cache | {cold_p50:.3f}s | {cold_p95:.3f}s | ≤ 10s |",
        f"| Warm VT cache | {warm_p50:.3f}s | {warm_p95:.3f}s | ≤ 1s |",
        "",
        f"{'Met' if cold_p95 <= 10 else 'Not met'} (cold), "
        f"{'met' if warm_p95 <= 1 else 'not met'} (warm) against NFR-01.",
        "",
    ]
    with open(REPORT_PATH, "a", encoding="utf-8") as handle:
        handle.write("\n".join(section) + "\n")
    logger.info("Appended latency section to %s", REPORT_PATH)


if __name__ == "__main__":
    main()
