"""
run_system_test.py — Sprint 3.4 end-to-end validation.
POSTs 30 real, unseen URLs (15 live-phishing, 15 legitimate incl. deep paths) at the running local
backend's /analyze, records verdict/risk against expectation, and writes the confusion matrix and
full table to ml/reports/e2e_validation.md. Requires `docker compose up` already running.
"""

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"
OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "reports" / "e2e_validation.md"

# Sampled every 20th line from the live OpenPhish feed (https://openphish.com/feed.txt),
# fetched 2026-08-13, for hosting-pattern diversity. Not PhishTank (the training source).
PHISHING_URLS = [
    "https://logowanie-facebook.vercel.app/",
    "https://ledger-login-web-conect-web-sso-in.typedream.app/",
    "https://sp15ct7-gresor-biz-fantik-lurmon.pages.dev/",
    "https://sp15ct7-grasik-biz-forlen-haskel.pages.dev/",
    "https://merry-maamoul-33ac49.netlify.app/",
    "https://27p-sddo-up2-zcwe25-9i92.pages.dev/",
    "https://backupiau.direct.quickconnect.to/cgi-bin/home.ha",
    "http://www.myxfinitycom.weebly.com/",
    "https://xfinity-customer-care.weebly.com/",
    "http://metamask-docs-l8lvh00ol-consensys-ddffed67.vercel.app/embedded-wallets/troubleshooting",
    "http://bc4f19.icefactory.cl/",
    "http://6c0fd9.icefactory.cl/",
    "http://4533ff.icefactory.cl/",
    "http://proj002mintinglive.netlify.app/",
    "https://72e520.icefactory.cl/",
]

# Real legitimate URLs, weighted toward deep paths — D1's blind spot was bare-homepage-only benign.
LEGITIMATE_URLS = [
    "https://github.com/torvalds/linux/blob/master/README",
    "https://en.wikipedia.org/wiki/Transport_Layer_Security",
    "https://docs.python.org/3/library/asyncio.html",
    "https://www.google.com/search?q=explainable+phishing+detection",
    "https://stackoverflow.com/questions/tagged/xgboost",
    "https://news.ycombinator.com/item?id=1",
    "https://www.bbc.com/news/technology",
    "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch",
    "https://www.nytimes.com/section/technology",
    "https://pypi.org/project/fastapi/",
    "https://www.amazon.com/gp/help/customer/display.html",
    "https://www.microsoft.com/en-us/security/business/security-101/what-is-phishing",
    "https://www.reddit.com/r/MachineLearning/",
    "https://www.wikipedia.org/",
    "https://www.python.org/",
]

DEEP_PATH_LEGITIMATE = {
    "https://github.com/torvalds/linux/blob/master/README",
    "https://en.wikipedia.org/wiki/Transport_Layer_Security",
    "https://docs.python.org/3/library/asyncio.html",
    "https://www.google.com/search?q=explainable+phishing+detection",
    "https://stackoverflow.com/questions/tagged/xgboost",
    "https://news.ycombinator.com/item?id=1",
    "https://www.bbc.com/news/technology",
    "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch",
    "https://www.nytimes.com/section/technology",
    "https://pypi.org/project/fastapi/",
    "https://www.amazon.com/gp/help/customer/display.html",
    "https://www.microsoft.com/en-us/security/business/security-101/what-is-phishing",
    "https://www.reddit.com/r/MachineLearning/",
}


def verdict_from_score(risk_pct: int) -> str:
    if risk_pct > 70:
        return "phishing"
    if risk_pct >= 40:
        return "suspicious"
    return "legitimate"


def analyze(client: httpx.Client, url: str) -> dict:
    start = time.monotonic()
    try:
        resp = client.post(f"{BACKEND_URL}/analyze", json={"url": url}, timeout=15.0)
        resp.raise_for_status()
        result = resp.json()
        result["_latency_s"] = time.monotonic() - start
        return result
    except Exception as exc:
        return {"error": str(exc), "_latency_s": time.monotonic() - start}


def run() -> None:
    resp = httpx.get(f"{BACKEND_URL}/health", timeout=5.0)
    resp.raise_for_status()
    health = resp.json()
    if not health.get("model_loaded"):
        raise SystemExit(f"Model not loaded, aborting: {health}")
    logger.info("Backend healthy: %s", health)

    rows = []
    with httpx.Client() as client:
        for url in PHISHING_URLS:
            result = analyze(client, url)
            rows.append({"url": url, "expected": "phishing", "deep_path": False, **result})
            logger.info("phishing  | %s | %s", url, result.get("verdict", result.get("error")))
            time.sleep(0.5)

        for url in LEGITIMATE_URLS:
            result = analyze(client, url)
            rows.append(
                {
                    "url": url,
                    "expected": "legitimate",
                    "deep_path": url in DEEP_PATH_LEGITIMATE,
                    **result,
                }
            )
            logger.info("legitimate| %s | %s", url, result.get("verdict", result.get("error")))
            time.sleep(0.5)

    write_report(rows)


def write_report(rows: list[dict]) -> None:
    correct = 0
    errors = 0
    deep_path_fps = 0
    latencies = [row["_latency_s"] for row in rows if "_latency_s" in row]
    confusion = {"phishing": {"phishing": 0, "suspicious": 0, "legitimate": 0, "error": 0},
                 "legitimate": {"phishing": 0, "suspicious": 0, "legitimate": 0, "error": 0}}

    lines = [
        "# Sprint 3.4 — End-to-End Validation (30 URLs)",
        "",
        f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
        "Local Docker stack, live `POST /analyze` calls (real VirusTotal lookups included). "
        "See `tests/e2e/system_test.md` for method and the deployment-deferral rationale.",
        "",
        "| # | Expected | Actual | Risk % | Deep path | Principal reason | URL |",
        "|---|---|---|---|---|---|---|",
    ]

    for i, row in enumerate(rows, start=1):
        expected = row["expected"]
        if "error" in row:
            actual = "error"
            errors += 1
            risk_display = "—"
            reason = row["error"][:80]
            confusion[expected]["error"] += 1
        else:
            actual = row["verdict"]
            risk_display = f"{row['risk_pct']}%"
            top_reasons = row.get("top_reasons") or []
            reason = top_reasons[0]["human_readable"] if top_reasons else "—"
            confusion[expected][actual] += 1
            # Strict pass/fail per the roadmap's binary correctness bar: legitimate must land
            # legitimate, phishing must land phishing.
            if expected == actual:
                correct += 1
            if expected == "legitimate" and actual == "phishing" and row.get("deep_path"):
                deep_path_fps += 1

        lines.append(
            f"| {i} | {expected} | {actual} | {risk_display} | "
            f"{'yes' if row.get('deep_path') else 'no'} | {reason} | `{row['url']}` |"
        )

    total = len(rows)
    lines += [
        "",
        "## Confusion matrix (strict: expected == actual)",
        "",
        f"- Correct: {correct}/{total}",
        f"- Errors (URL unreachable / dead at test time): {errors}",
        f"- False positives among deep-path legitimate URLs: {deep_path_fps}",
        f"- Mean assessment latency: {sum(latencies) / len(latencies):.3f}s "
        f"(includes live VirusTotal lookups)",
        "",
        "| Expected \\ Actual | phishing | suspicious | legitimate | error |",
        "|---|---|---|---|---|",
        f"| phishing | {confusion['phishing']['phishing']} | {confusion['phishing']['suspicious']} | "
        f"{confusion['phishing']['legitimate']} | {confusion['phishing']['error']} |",
        f"| legitimate | {confusion['legitimate']['phishing']} | {confusion['legitimate']['suspicious']} | "
        f"{confusion['legitimate']['legitimate']} | {confusion['legitimate']['error']} |",
        "",
        f"**Acceptance (ROADMAP.md 3.4):** >= 26/30 correct, zero false positives among deep-path "
        f"legitimate URLs. Result: {correct}/30 correct, {deep_path_fps} deep-path false positives "
        f"-> {'PASS' if correct >= 26 and deep_path_fps == 0 else 'FAIL'}.",
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Wrote %s", OUTPUT_PATH)
    logger.info("Correct: %d/%d, errors: %d, deep-path FPs: %d", correct, total, errors, deep_path_fps)


if __name__ == "__main__":
    run()
