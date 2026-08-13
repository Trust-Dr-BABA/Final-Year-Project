"""
evaluate_fp_holdout.py — False-positive rate on the deep-path holdout (§5.11 / roadmap 2.1.3).

For a browser extension this is the most consequential single figure in the evaluation: a
detector that flags popular, legitimate, previously-unseen URLs is unusable regardless of its F1.
Uses the live scoring path (ml.shap_analysis.explain_prediction), the same code the service calls,
rather than reimplementing scoring — so this measures the system as deployed, not a proxy for it.

Usage:
    python ml/scripts/evaluate_fp_holdout.py

Output:
    ml/reports/evaluation_report.md  (appended)
"""

import logging
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.feature_extractor.url_features import extract_url_features  # noqa: E402
from ml.shap_analysis import explain_prediction  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HOLDOUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "fp_holdout.csv"
REPORT_PATH = Path(__file__).parent.parent / "reports" / "evaluation_report.md"


def main() -> None:
    df = pd.read_csv(HOLDOUT_PATH)
    logger.info("Scoring %d holdout URLs through the live scoring path…", len(df))

    labels = []
    for i, url in enumerate(df["url"]):
        features = extract_url_features(url)
        result = explain_prediction(features)
        labels.append(result["label"])
        if (i + 1) % 500 == 0:
            logger.info("  %d/%d scored", i + 1, len(df))

    df["predicted"] = labels
    counts = df["predicted"].value_counts()
    total = len(df)
    legit_n, susp_n, phish_n = counts.get("legitimate", 0), counts.get("suspicious", 0), counts.get("phishing", 0)

    logger.info("legitimate=%d (%.1f%%) suspicious=%d (%.1f%%) phishing=%d (%.1f%%)",
                legit_n, legit_n / total * 100, susp_n, susp_n / total * 100, phish_n, phish_n / total * 100)

    section = [
        "", "## False positives on the deep-path holdout", "",
        f"Measured on `ml/data/processed/fp_holdout.csv` — {total} real deep-path URLs, disjoint "
        "domains from every training URL (see `ml/data/raw/DATASET_SOURCES.md`). Scored through "
        "the live `ml.shap_analysis.explain_prediction()` path, the same code the service calls.",
        "",
        "| Band | Count | Rate |", "|---|---|---|",
        f"| legitimate | {legit_n} | {legit_n / total:.1%} |",
        f"| suspicious | {susp_n} | {susp_n / total:.1%} |",
        f"| **phishing** | **{phish_n}** | **{phish_n / total:.1%}** |",
        "",
        f"A {phish_n / total:.1%} false-positive rate in the phishing band (the band that raises "
        "the blocking interstitial, §3.7.2) on popular, legitimate, previously-unseen URLs is a "
        "genuine, measured limitation — see `ml/reports/training_log.md` for the investigation "
        "into individual misfires. Not tuned away against this same holdout, which would fit to "
        "the measurement instrument rather than the underlying problem.",
        "",
    ]
    with open(REPORT_PATH, "a", encoding="utf-8") as handle:
        handle.write("\n".join(section) + "\n")
    logger.info("Appended false-positive section to %s", REPORT_PATH)


if __name__ == "__main__":
    main()
