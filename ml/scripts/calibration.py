"""
calibration.py — Measures whether the model's probability output means what it claims to mean.

The interface displays a confidence percentage (ADR-015: confidence_pct = max(p, 1-p)). That
number is decoration unless the underlying probabilities are calibrated — among pages the model
assigns roughly 0.8, close to 80% should actually be phishing. This script measures that directly
rather than assuming it, on the temporal-split test set (the harder, deployment-realistic protocol).

If Expected Calibration Error is poor, Platt scaling is fit on a validation split carved out of
the training set (never on the test set — fitting a calibrator on test data would just be
overfitting one layer higher) and before/after figures are both reported.

Usage:
    python ml/scripts/calibration.py

Output:
    ml/reports/evaluation_report.md  (appended)
    ml/reports/reliability_diagram.png
"""

import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless — this script never opens a display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.scripts.evaluate_baselines import (  # noqa: E402
    FEATURE_COLS, FEATURES_PATH, RANDOM_STATE, fit_xgboost, temporal_split,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REPORT_PATH = Path(__file__).parent.parent / "reports" / "evaluation_report.md"
DIAGRAM_PATH = Path(__file__).parent.parent / "reports" / "reliability_diagram.png"
N_BINS = 10
ECE_GOOD_THRESHOLD = 0.05  # below this, calibration is considered acceptable without further fitting


# Expected Calibration Error: the count-weighted mean gap between predicted confidence and
# observed accuracy across equal-width probability bins.
def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = N_BINS) -> tuple[float, list[dict]]:
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(y_prob, bin_edges[1:-1]), 0, n_bins - 1)

    total = len(y_true)
    ece = 0.0
    bins = []
    for b in range(n_bins):
        mask = bin_idx == b
        count = int(mask.sum())
        if count == 0:
            bins.append({"bin": b, "range": (bin_edges[b], bin_edges[b + 1]), "count": 0,
                         "mean_confidence": float("nan"), "accuracy": float("nan")})
            continue
        mean_confidence = float(y_prob[mask].mean())
        accuracy = float(y_true[mask].mean())
        ece += (count / total) * abs(mean_confidence - accuracy)
        bins.append({"bin": b, "range": (bin_edges[b], bin_edges[b + 1]), "count": count,
                     "mean_confidence": mean_confidence, "accuracy": accuracy})
    return ece, bins


# Plot predicted probability against observed frequency per bin, with the perfect-calibration diagonal.
def plot_reliability_diagram(bins_before: list[dict], bins_after: list[dict] | None, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")

    def _plot(bins, label, marker):
        xs = [b["mean_confidence"] for b in bins if b["count"] > 0]
        ys = [b["accuracy"] for b in bins if b["count"] > 0]
        sizes = [20 + b["count"] / 5 for b in bins if b["count"] > 0]
        ax.scatter(xs, ys, s=sizes, label=label, marker=marker, alpha=0.8)
        ax.plot(xs, ys, alpha=0.5)

    _plot(bins_before, "Before calibration", "o")
    if bins_after is not None:
        _plot(bins_after, "After Platt scaling", "s")

    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed frequency of phishing")
    ax.set_title("Reliability diagram — temporal split test set")
    ax.legend()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _bins_table(bins: list[dict]) -> str:
    lines = ["| Bin | Mean predicted | Observed accuracy | Count |", "|---|---|---|---|"]
    for b in bins:
        if b["count"] == 0:
            continue
        lines.append(f"| {b['range'][0]:.1f}–{b['range'][1]:.1f} | {b['mean_confidence']:.3f} | "
                     f"{b['accuracy']:.3f} | {b['count']} |")
    return "\n".join(lines)


def main() -> None:
    df = pd.read_csv(FEATURES_PATH)
    train, test = temporal_split(df)
    logger.info("train=%d test=%d", len(train), len(test))

    model = fit_xgboost(train)
    y_test = test["label"].to_numpy()
    y_prob = model.predict_proba(test[FEATURE_COLS])[:, 1]

    brier = brier_score_loss(y_test, y_prob)
    ece, bins_before = expected_calibration_error(y_test, y_prob)
    logger.info("Before calibration: Brier=%.4f ECE=%.4f", brier, ece)

    bins_after = None
    brier_after = ece_after = None
    if ece > ECE_GOOD_THRESHOLD:
        logger.info("ECE exceeds %.2f — fitting Platt scaling on a validation split", ECE_GOOD_THRESHOLD)
        # Split the *training* set again for calibration fitting — the test set must stay unseen
        # by anything that touches the model, including the calibrator, or this measurement would
        # be evaluating overfitting rather than calibration.
        fit_part, cal_part = train_test_split(
            train, test_size=0.2, stratify=train["label"], random_state=RANDOM_STATE
        )
        base_for_calibration = fit_xgboost(fit_part)
        calibrated = CalibratedClassifierCV(base_for_calibration, method="sigmoid", cv="prefit")
        calibrated.fit(cal_part[FEATURE_COLS], cal_part["label"])

        y_prob_after = calibrated.predict_proba(test[FEATURE_COLS])[:, 1]
        brier_after = brier_score_loss(y_test, y_prob_after)
        ece_after, bins_after = expected_calibration_error(y_test, y_prob_after)
        logger.info("After calibration:  Brier=%.4f ECE=%.4f", brier_after, ece_after)

    plot_reliability_diagram(bins_before, bins_after, DIAGRAM_PATH)
    logger.info("Reliability diagram written to %s", DIAGRAM_PATH)

    section = ["", "## Calibration — temporal split test set", "",
               f"Measured on {len(test)} test URLs ({int(y_test.sum())} phishing). "
               f"{N_BINS} equal-width bins.", "",
               "| Metric | Before | After Platt scaling |", "|---|---|---|",
               f"| Brier score | {brier:.4f} | {f'{brier_after:.4f}' if brier_after is not None else '—'} |",
               f"| Expected Calibration Error | {ece:.4f} | {f'{ece_after:.4f}' if ece_after is not None else '—'} |",
               "", "![Reliability diagram](reliability_diagram.png)", "",
               _bins_table(bins_before), ""]

    if ece <= ECE_GOOD_THRESHOLD:
        section.append(f"\nECE of {ece:.4f} is within the {ECE_GOOD_THRESHOLD:.2f} threshold taken "
                       "as acceptable calibration — no correction was fitted.")
    else:
        improved = ece_after < ece
        section.append(f"\nPlatt scaling was fitted because ECE ({ece:.4f}) exceeded "
                       f"{ECE_GOOD_THRESHOLD:.2f}. It "
                       f"{'improved' if improved else 'did not improve'} calibration "
                       f"({ece:.4f} → {ece_after:.4f}).")

    with open(REPORT_PATH, "a", encoding="utf-8") as handle:
        handle.write("\n".join(section) + "\n")
    logger.info("Appended calibration section to %s", REPORT_PATH)


if __name__ == "__main__":
    main()
