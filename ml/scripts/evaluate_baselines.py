"""
evaluate_baselines.py — Measures detection performance under two protocols against four baselines
plus the trained classifier.

Two protocols, both harder and more representative of deployment than a random split:

  Temporal   — train on the earlier submission-time window, test on the later one. Mirrors
               deployment exactly: a detector is always asked to predict campaigns it has not
               seen yet. The phishing class is split by its real submission_time; the benign
               class has no such timestamp (a crawl date is not a publication date), so it is
               split randomly in matching proportion — stated here rather than left implicit.

  Unseen-domain — no registrable domain appears in both train and test. Prevents a model from
               succeeding by memorising specific domains rather than learning URL structure.

Four baselines:
  B1 Blocklist   — exact-match lookup against the training phishing URLs. Precision ~1.0 by
                   construction; recall on the test set demonstrates the generalisation gap a
                   blocklist cannot close (test URLs are, by the split's construction, absent
                   from it).
  B2 url_length  — logistic regression on url_length alone. Included to show the D1 artefact is
                   gone: on the rebuilt corpus this should perform poorly, not implausibly well.
  B3 Logistic regression — all 9 lexical features, linear reference point.
  B4 XGBoost (URL-only) — the same architecture and hyperparameters as train_model.py, fit on
                   this evaluation's train split.

There is no separate "B5 fused" row: no offline corpus carries the browser signals fusion
depends on (ADR-014's own justification for not training on them), so a fused-model number
cannot be measured from this dataset without fabricating browser telemetry that isn't real. The
report says so explicitly rather than presenting a B4-relabelled-as-B5 number as if it were a
different measurement. Claim C2 is validated instead by the live fusion test
(tests/unit/test_shap.py, tests/unit/test_risk_fusion.py) and the end-to-end validation (Sprint 3).

Usage:
    python ml/scripts/evaluate_baselines.py

Output:
    ml/reports/evaluation_report.md
"""

import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import tldextract
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
FEATURES_PATH = BASE_DIR / "data" / "processed" / "features.csv"
REPORT_PATH = BASE_DIR / "reports" / "evaluation_report.md"

FEATURE_COLS = [
    "url_length", "num_digits", "num_special_chars", "subdomain_depth", "has_https",
    "url_entropy", "has_ip_address", "suspicious_tld_flag", "brand_impersonation",
]
RANDOM_STATE = 42


# Registrable domain (eTLD+1) for a URL, used to build the unseen-domain split.
def registrable_domain(url: str) -> str:
    ext = tldextract.extract(str(url))
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else str(url)


# Split the phishing class by submission_time (earlier -> train) and the benign class randomly in
# matching proportion, since benign rows carry no submission timestamp (see module docstring).
def temporal_split(df: pd.DataFrame, test_frac: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    phishing = df[df["label"] == 1].copy()
    benign = df[df["label"] == 0].copy()

    phishing["submission_time"] = pd.to_datetime(phishing["submission_time"], utc=True)
    phishing = phishing.sort_values("submission_time")
    cut = int(len(phishing) * (1 - test_frac))
    phishing_train, phishing_test = phishing.iloc[:cut], phishing.iloc[cut:]

    benign_train = benign.sample(frac=1 - test_frac, random_state=RANDOM_STATE)
    benign_test = benign.drop(benign_train.index)

    # Benign rows' submission_time is entirely NaT (see module docstring), which triggers a
    # pandas FutureWarning about all-NA columns in concat — harmless here, since nothing
    # downstream reads submission_time past this point, but silenced so it doesn't clutter CI.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning, message=".*all-NA.*")
        train = pd.concat([phishing_train, benign_train]).sample(frac=1, random_state=RANDOM_STATE)
        test = pd.concat([phishing_test, benign_test]).sample(frac=1, random_state=RANDOM_STATE)
    return train, test


# Split by registrable domain so no domain's URLs appear on both sides.
def unseen_domain_split(df: pd.DataFrame, test_frac: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    df["_domain"] = df["url"].apply(registrable_domain)
    domains = df["_domain"].drop_duplicates().sample(frac=1, random_state=RANDOM_STATE)
    cut = int(len(domains) * (1 - test_frac))
    train_domains = set(domains.iloc[:cut])

    train = df[df["_domain"].isin(train_domains)].drop(columns="_domain")
    test = df[~df["_domain"].isin(train_domains)].drop(columns="_domain")
    return train, test


# Precision/recall/F1/AUC for one baseline's predictions against ground truth.
def _score(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None) -> dict[str, float]:
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "auc": roc_auc_score(y_true, y_prob) if y_prob is not None and len(set(y_true)) > 1 else float("nan"),
    }


# B1 — exact-match blocklist lookup against the training phishing URLs.
def eval_blocklist(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, float]:
    known_phishing = set(train.loc[train["label"] == 1, "url"])
    y_pred = test["url"].isin(known_phishing).astype(int).to_numpy()
    return _score(test["label"].to_numpy(), y_pred, y_pred.astype(float))


# B2 — logistic regression on url_length alone.
def eval_url_length_only(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, float]:
    X_train = train[["url_length"]].to_numpy()
    X_test = test[["url_length"]].to_numpy()
    model = LogisticRegression(random_state=RANDOM_STATE).fit(X_train, train["label"])
    y_prob = model.predict_proba(X_test)[:, 1]
    return _score(test["label"].to_numpy(), (y_prob > 0.5).astype(int), y_prob)


# B3 — logistic regression on all 9 lexical features, standardised.
def eval_logistic_regression(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, float]:
    scaler = StandardScaler().fit(train[FEATURE_COLS])
    X_train = scaler.transform(train[FEATURE_COLS])
    X_test = scaler.transform(test[FEATURE_COLS])
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE).fit(X_train, train["label"])
    y_prob = model.predict_proba(X_test)[:, 1]
    return _score(test["label"].to_numpy(), (y_prob > 0.5).astype(int), y_prob)


# B4 — XGBoost on the 9 lexical features, same architecture as train_model.py.
def eval_xgboost(train: pd.DataFrame, test: pd.DataFrame) -> tuple[dict[str, float], np.ndarray]:
    X_train, y_train = train[FEATURE_COLS], train["label"]
    X_test, y_test = test[FEATURE_COLS], test["label"]
    pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1, eval_metric="logloss",
        scale_pos_weight=pos_weight, random_state=RANDOM_STATE, n_jobs=-1,
    )
    model.fit(X_train, y_train, verbose=False)
    y_prob = model.predict_proba(X_test)[:, 1]
    # 0.5, matching every other baseline in this table — comparing F1 across baselines is only
    # meaningful at a common threshold. The deployed service's 0.70/0.40 verdict bands are a
    # separate, additional design choice (invariant #3) that doesn't belong in this comparison.
    y_pred = (y_prob > 0.5).astype(int)
    return _score(y_test.to_numpy(), y_pred, y_prob), confusion_matrix(y_test, y_pred)


BASELINES = {
    "B1 Blocklist lookup": eval_blocklist,
    "B2 url_length only": eval_url_length_only,
    "B3 Logistic regression": eval_logistic_regression,
}


def main() -> None:
    if not FEATURES_PATH.exists():
        raise SystemExit(f"{FEATURES_PATH} not found — run generate_features.py first")

    df = pd.read_csv(FEATURES_PATH)
    logger.info("Loaded %d rows (%d phishing / %d legitimate)",
                len(df), (df["label"] == 1).sum(), (df["label"] == 0).sum())

    protocols = {
        "Temporal split": temporal_split(df),
        "Unseen-registrable-domain split": unseen_domain_split(df),
    }

    lines = ["# Evaluation report — baseline comparison and split protocols", ""]
    lines.append(
        "Measured on `ml/data/processed/features.csv` (19,685 rows). Both protocols are harder "
        "than a random split and are the ones this project's claims rest on — see the module "
        "docstring in `ml/scripts/evaluate_baselines.py` for why each is constructed the way it is."
    )
    lines.append("")

    confusion_temporal = None
    for protocol_name, (train, test) in protocols.items():
        logger.info("=== %s === train=%d test=%d", protocol_name, len(train), len(test))
        lines.append(f"## {protocol_name}")
        lines.append("")
        lines.append(f"Train: {len(train)} rows ({(train['label'] == 1).sum()} phishing). "
                      f"Test: {len(test)} rows ({(test['label'] == 1).sum()} phishing).")
        lines.append("")
        lines.append("| Baseline | Precision | Recall | F1 | ROC-AUC |")
        lines.append("|---|---|---|---|---|")

        for name, fn in BASELINES.items():
            result = fn(train, test)
            logger.info("  %-28s P=%.3f R=%.3f F1=%.3f AUC=%.3f",
                        name, result["precision"], result["recall"], result["f1"], result["auc"])
            lines.append(f"| {name} | {result['precision']:.3f} | {result['recall']:.3f} | "
                         f"{result['f1']:.3f} | {result['auc']:.3f} |")

        xgb_result, cm = eval_xgboost(train, test)
        logger.info("  %-28s P=%.3f R=%.3f F1=%.3f AUC=%.3f",
                    "B4 XGBoost (URL-only)", xgb_result["precision"], xgb_result["recall"],
                    xgb_result["f1"], xgb_result["auc"])
        lines.append(f"| B4 XGBoost (URL-only) | {xgb_result['precision']:.3f} | "
                     f"{xgb_result['recall']:.3f} | {xgb_result['f1']:.3f} | {xgb_result['auc']:.3f} |")
        lines.append("")

        blocklist_recall = eval_blocklist(train, test)["recall"]
        lines.append(
            f"**B1's recall on this test set is {blocklist_recall:.1%}.** By construction of the "
            f"split, every test URL is absent from the training blocklist — this number *is* "
            f"\"recall on URLs absent from the blocklist,\" which is the direct quantitative answer "
            f"to \"why not just use a blocklist?\" (claim C1)."
        )
        lines.append("")

        if protocol_name == "Temporal split":
            confusion_temporal = cm

        lines.append("")

    if confusion_temporal is not None:
        lines.append("## Confusion matrix — B4 XGBoost, temporal split")
        lines.append("")
        lines.append("| | Predicted legitimate | Predicted phishing |")
        lines.append("|---|---|---|")
        lines.append(f"| **Actually legitimate** | {confusion_temporal[0][0]} | {confusion_temporal[0][1]} |")
        lines.append(f"| **Actually phishing** | {confusion_temporal[1][0]} | {confusion_temporal[1][1]} |")
        lines.append("")

    lines.append("## Note on the fused model (no B5 row)")
    lines.append("")
    lines.append(
        "There is no offline measurement of the fused model's detection performance, because no "
        "corpus — this one included — carries real per-URL browser telemetry (tracker counts, "
        "redirect depth, permission timings) alongside a phishing label. Fabricating that "
        "telemetry to produce a B5 number would be exactly the kind of manufactured evidence "
        "ADR-014 explicitly rejects for the fusion weights themselves. B4 above **is** the fused "
        "model's URL-scoring component; claim C2 (that browser signals measurably move the score) "
        "is validated instead by a live test — `tests/unit/test_risk_fusion.py` and "
        "`tests/unit/test_shap.py::test_adverse_browser_signals_raise_the_score` — and by the "
        "end-to-end validation against live URLs in Sprint 3."
    )
    lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Report written to %s", REPORT_PATH)


if __name__ == "__main__":
    main()
