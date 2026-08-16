"""
retrain_gate.py — Retraining-cadence safety gate (LIMITATIONS.md, "the corpus is a snapshot").

A scheduled retraining cadence needs a mechanism that runs the leakage audit, trains a candidate
model, compares it against the currently-deployed (incumbent) model on a common held-out set, and
only promotes the candidate if it doesn't regress. That mechanism is what this script is — the
piece buildable without new data arriving. Actually exercising a "cadence" needs new phishing
submissions over time, which the static corpus snapshot cannot provide on its own; running this gate
repeatedly against the same unchanged corpus would just retrain a near-identical model, which is not
what a schedule is for. This script is demonstrated once against the current corpus, not a claim
that a live cadence has been running.

Gate sequence:
  1. Leakage audit (ml/scripts/audit_dataset.py, reused via its own exit-code gate — no feature may
     exceed 0.90 standalone AUC). A failing audit rejects the candidate before it is even trained.
  2. Train a candidate on the current features.csv.
  3. Load the incumbent model from ml/models/ (if one exists) and evaluate both candidate and
     incumbent on the *same* freshly-drawn held-out split, so the comparison is apples-to-apples
     regardless of what the incumbent was originally trained/tested on.
  4. Promote the candidate (overwrite xgboost_phishing.pkl + feature_columns.json, the same atomic
     pair-write train_model.py already does) only if its F1 is not more than --tolerance below the
     incumbent's. Otherwise reject and leave the incumbent in place.
  5. Append the decision to ml/reports/retrain_gate_log.md — a history of gate runs over time, not
     overwritten on each run, since the point of a log is to see the sequence of decisions.

Usage:
    python ml/scripts/retrain_gate.py [--tolerance 0.02]

Exit status: 0 if promoted (including the first run, with no incumbent to compare against),
             1 if rejected (leakage audit failure, or an F1 regression beyond tolerance).
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import f1_score, roc_auc_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
FEATURES_PATH = BASE_DIR / "data" / "processed" / "features.csv"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "xgboost_phishing.pkl"
COLUMNS_PATH = MODELS_DIR / "feature_columns.json"
LOG_PATH = BASE_DIR / "reports" / "retrain_gate_log.md"
AUDIT_SCRIPT = Path(__file__).parent / "audit_dataset.py"

NON_FEATURE_COLUMNS = (
    "url", "label", "tld", "submission_time", "target",
    "domain_age_days", "vt_malicious_votes", "vt_harmless_votes",
)
RANDOM_STATE = 42


# Run the leakage audit as a subprocess and rely on its own documented exit-code gate (0 = pass,
# 1 = fail) rather than reimplementing its logic here — the audit is already designed to gate a
# pipeline, per its own module docstring.
def _leakage_audit_passes() -> bool:
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        logger.error("Leakage audit failed:\n%s", result.stdout.strip())
        return False
    logger.info("Leakage audit passed.")
    return True


# Fit a candidate model on a fresh train split, matching train_model.py's own architecture exactly
# so "candidate" and "the model train_model.py would produce" are the same thing.
def _train_candidate(X_train: pd.DataFrame, y_train: pd.Series) -> XGBClassifier:
    pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1, eval_metric="logloss",
        scale_pos_weight=pos_weight, random_state=RANDOM_STATE, n_jobs=-1,
    )
    model.fit(X_train, y_train, verbose=False)
    return model


# F1 and AUC for a fitted model against a held-out split.
def _evaluate(model: XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> tuple[float, float]:
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob > 0.5).astype(int)
    return f1_score(y_test, y_pred, zero_division=0), roc_auc_score(y_test, y_prob)


# The promotion rule itself, pulled out as a pure function so it's testable without a real training
# run: promote unless the candidate's F1 is more than `tolerance` below the incumbent's.
def _should_promote(candidate_f1: float, incumbent_f1: float, tolerance: float) -> bool:
    return (incumbent_f1 - candidate_f1) <= tolerance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--tolerance", type=float, default=0.02,
        help="Max F1 regression (candidate vs incumbent) still allowed to promote. Default 0.02.",
    )
    args = parser.parse_args()
    run_time = datetime.now(timezone.utc).isoformat()

    if not FEATURES_PATH.exists():
        raise SystemExit(f"{FEATURES_PATH} not found — run generate_features.py first")

    if not _leakage_audit_passes():
        _log_decision(run_time, "REJECTED", "Leakage audit failed — see ml/reports/leakage_audit.md")
        sys.exit(1)

    df = pd.read_csv(FEATURES_PATH)
    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLUMNS]
    X = df[feature_cols].fillna(-1)
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    candidate = _train_candidate(X_train, y_train)
    candidate_f1, candidate_auc = _evaluate(candidate, X_test, y_test)
    logger.info("Candidate: F1=%.4f AUC=%.4f", candidate_f1, candidate_auc)

    if not MODEL_PATH.exists() or not COLUMNS_PATH.exists():
        logger.info("No incumbent model found — promoting candidate unconditionally (first run).")
        _promote(candidate, feature_cols)
        _log_decision(
            run_time, "PROMOTED (no incumbent)",
            f"Candidate F1={candidate_f1:.4f} AUC={candidate_auc:.4f}",
        )
        return

    incumbent = joblib.load(MODEL_PATH)
    incumbent_cols = json.loads(COLUMNS_PATH.read_text())
    if incumbent_cols != feature_cols:
        # The feature set itself changed (e.g. digit_ratio replacing num_digits) — an F1 comparison
        # across different feature sets isn't a meaningful regression test, and forcing one through
        # would produce a number that looks like a fair comparison but isn't. Promote directly,
        # same as the "no incumbent" case, and say so.
        logger.info(
            "Incumbent's feature set differs from the candidate's (%s vs %s) — not a regression "
            "test, promoting the candidate as the new baseline.", incumbent_cols, feature_cols,
        )
        _promote(candidate, feature_cols)
        _log_decision(
            run_time, "PROMOTED (feature set changed)",
            f"Candidate F1={candidate_f1:.4f} AUC={candidate_auc:.4f}; incumbent used a different "
            f"feature set, so no direct comparison was possible",
        )
        return

    incumbent_f1, incumbent_auc = _evaluate(incumbent, X_test, y_test)
    logger.info("Incumbent: F1=%.4f AUC=%.4f", incumbent_f1, incumbent_auc)

    regression = incumbent_f1 - candidate_f1
    if not _should_promote(candidate_f1, incumbent_f1, args.tolerance):
        logger.error(
            "REJECTED: candidate F1 %.4f is %.4f below incumbent F1 %.4f (tolerance %.4f). "
            "Incumbent model left in place.", candidate_f1, regression, incumbent_f1, args.tolerance,
        )
        _log_decision(
            run_time, "REJECTED (regression)",
            f"Candidate F1={candidate_f1:.4f} AUC={candidate_auc:.4f} vs incumbent "
            f"F1={incumbent_f1:.4f} AUC={incumbent_auc:.4f} — regression {regression:.4f} exceeds "
            f"tolerance {args.tolerance:.4f}",
        )
        sys.exit(1)

    logger.info(
        "PROMOTED: candidate F1 %.4f vs incumbent F1 %.4f (regression %.4f within tolerance %.4f).",
        candidate_f1, incumbent_f1, regression, args.tolerance,
    )
    _promote(candidate, feature_cols)
    _log_decision(
        run_time, "PROMOTED",
        f"Candidate F1={candidate_f1:.4f} AUC={candidate_auc:.4f} vs incumbent "
        f"F1={incumbent_f1:.4f} AUC={incumbent_auc:.4f} — regression {regression:.4f} within "
        f"tolerance {args.tolerance:.4f}",
    )


# Atomic pair-write — same invariant train_model.py's own save step enforces (CLAUDE.md invariant
# #2): the .pkl and feature_columns.json must always come from the same training run.
def _promote(model: XGBClassifier, feature_cols: list[str]) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    with open(COLUMNS_PATH, "w") as f:
        json.dump(feature_cols, f, indent=2)
    logger.info("Promoted -> %s, %s", MODEL_PATH, COLUMNS_PATH)


def _log_decision(run_time: str, decision: str, detail: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = f"| {run_time} | {decision} | {detail} |\n"
    is_new = not LOG_PATH.exists()
    with LOG_PATH.open("a", encoding="utf-8") as f:
        if is_new:
            f.write("# Retrain gate log\n\n")
            f.write("Every run of `ml/scripts/retrain_gate.py`, in order. Appended, never overwritten.\n\n")
            f.write("| Run (UTC) | Decision | Detail |\n")
            f.write("|---|---|---|\n")
        f.write(line)


if __name__ == "__main__":
    main()
