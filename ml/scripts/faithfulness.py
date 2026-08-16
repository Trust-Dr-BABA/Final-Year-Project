"""
faithfulness.py — Tests whether the model's SHAP explanations are faithful, not decorative.

For each test URL: record its top-3 SHAP-attributed features, neutralise those three features to
their training medians, and re-score. If the explanations are faithful, the score should move in
the direction — and roughly by the magnitude — those three attributions predicted. This is claim
C3, and it is tested by intervention rather than assumed, because SHAP's local-accuracy guarantee
only says the attributions sum to the *original* prediction; it says nothing about what happens
under a multi-feature intervention on a non-additive model, which is exactly what this measures.

Both the predicted shift and the observed shift are computed in log-odds (margin) space, matching
the space SHAP's TreeExplainer natively attributes in for a tree ensemble with a logistic
objective — the same space ADR-014's fusion design relies on.

Usage:
    python ml/scripts/faithfulness.py

Output:
    ml/reports/evaluation_report.md  (appended)
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import shap

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services.risk_fusion import _logit  # noqa: E402
from ml.scripts.evaluate_baselines import FEATURE_COLS, FEATURES_PATH, fit_xgboost, temporal_split  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REPORT_PATH = Path(__file__).parent.parent / "reports" / "evaluation_report.md"


# For one row, neutralise its top-3 SHAP-attributed features to the training medians and
# re-score; return (predicted log-odds shift, observed log-odds shift).
def _ablate_one(model, medians: pd.Series, row: pd.Series, shap_row: np.ndarray) -> tuple[float, float]:
    top3_idx = np.argsort(-np.abs(shap_row))[:3]
    top3_cols = [FEATURE_COLS[i] for i in top3_idx]

    predicted_shift = -float(shap_row[top3_idx].sum())  # removing these contributions

    modified = row.copy()
    for col in top3_cols:
        modified[col] = medians[col]

    p_before = model.predict_proba(row[FEATURE_COLS].to_frame().T)[0][1]
    p_after = model.predict_proba(modified[FEATURE_COLS].to_frame().T)[0][1]
    # risk_fusion._logit is a scalar function (shared with the serving path, ADR-014) — no need
    # for faithfulness.py's own numpy-array version, which was never actually called with more
    # than one element at a time anyway.
    observed_shift = float(_logit(p_after) - _logit(p_before))

    return predicted_shift, observed_shift


def main() -> None:
    df = pd.read_csv(FEATURES_PATH)
    train, test = temporal_split(df)
    logger.info("train=%d test=%d", len(train), len(test))

    model = fit_xgboost(train)
    medians = train[FEATURE_COLS].median()
    explainer = shap.TreeExplainer(model)

    X_test = test[FEATURE_COLS].reset_index(drop=True)
    shap_values = explainer.shap_values(X_test)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    predicted_shifts, observed_shifts = [], []
    for i in range(len(X_test)):
        predicted, observed = _ablate_one(model, medians, X_test.iloc[i], shap_values[i])
        predicted_shifts.append(predicted)
        observed_shifts.append(observed)
        if (i + 1) % 1000 == 0:
            logger.info("  %d/%d ablated", i + 1, len(X_test))

    predicted_shifts = np.array(predicted_shifts)
    observed_shifts = np.array(observed_shifts)

    mae = float(np.mean(np.abs(predicted_shifts - observed_shifts)))
    same_sign = np.sign(predicted_shifts) == np.sign(observed_shifts)
    directional_agreement = float(same_sign.mean())

    # Near-zero predicted shifts make a sign comparison close to a coin flip — report both the
    # full figure (the one the acceptance criterion is stated against) and the figure restricted
    # to non-trivial predicted shifts, rather than silently choosing whichever looks better.
    nontrivial = np.abs(predicted_shifts) > 0.05
    directional_agreement_nontrivial = float(same_sign[nontrivial].mean()) if nontrivial.any() else float("nan")

    logger.info("N=%d  MAE=%.4f  directional agreement=%.1f%% (all) / %.1f%% (|predicted|>0.05, n=%d)",
                len(X_test), mae, directional_agreement * 100,
                directional_agreement_nontrivial * 100, int(nontrivial.sum()))

    section = [
        "", "## Explanation faithfulness — top-3 SHAP ablation (claim C3)", "",
        f"For each of {len(X_test)} temporal-split test URLs, the top-3 SHAP-attributed features "
        "were neutralised to their training medians and the URL re-scored. Both shifts are "
        "measured in log-odds, the space SHAP natively attributes in.", "",
        "| Metric | Value |", "|---|---|",
        f"| URLs evaluated | {len(X_test)} |",
        f"| Mean absolute error (predicted vs. observed shift) | {mae:.4f} |",
        f"| Directional agreement (all cases) | {directional_agreement:.1%} |",
        f"| Directional agreement (\\|predicted shift\\| > 0.05, n={int(nontrivial.sum())}) | "
        f"{directional_agreement_nontrivial:.1%} |",
        "",
        f"Acceptance target: ≥ 90% directional agreement. "
        f"{'Met' if directional_agreement >= 0.90 else 'Not met'} on the full set "
        f"({directional_agreement:.1%}).",
        "",
        "Exact agreement between predicted and observed shift is not expected: SHAP attributes a "
        "*specific* prediction under the *observed* feature distribution, and simultaneously "
        "intervening on three features moves the input off that distribution on a model that is "
        "not additive in its inputs. Directional agreement is the criterion that actually tests "
        "faithfulness; the MAE quantifies the size of the resulting interaction effects.",
        "",
    ]
    with open(REPORT_PATH, "a", encoding="utf-8") as handle:
        handle.write("\n".join(section) + "\n")
    logger.info("Appended faithfulness section to %s", REPORT_PATH)


if __name__ == "__main__":
    main()
