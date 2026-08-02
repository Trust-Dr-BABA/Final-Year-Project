"""
train_model.py — XGBoost phishing classifier training script.

Usage:
    python ml/scripts/train_model.py

Outputs:
    ml/models/xgboost_phishing.pkl   — trained model
    ml/models/feature_columns.json   — ordered feature column list
"""

import json
import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FEATURES_PATH = Path(__file__).parent.parent / "data" / "processed" / "features.csv"
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    logger.info(f"Loading features from {FEATURES_PATH}")
    df = pd.read_csv(FEATURES_PATH)

    if "label" not in df.columns:
        raise ValueError("features.csv must contain a 'label' column")

    feature_cols = [c for c in df.columns if c not in ("url", "label", "tld")]
    X = df[feature_cols].fillna(-1)
    y = df["label"]

    logger.info(f"Features: {feature_cols}")
    logger.info(f"Dataset size: {len(df)} rows | {y.sum()} phishing | {(y == 0).sum()} legitimate")
    # Debug: verify feature data types
    logger.debug("\n===== Feature Data Types =====")
    logger.debug(f"\n{X.dtypes}")
    logger.debug("==============================\n")

    # ── Train / test split ────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # ── XGBoost training ─────────────────────────────────────────────────────
    # scale_pos_weight handles class imbalance automatically
    pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    logger.info(f"scale_pos_weight: {pos_weight:.2f}")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        eval_metric="logloss",
        scale_pos_weight=pos_weight,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    # ── Evaluation ────────────────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    logger.info(f"\n{'='*40}")
    logger.info(f"Test F1-Score : {f1:.4f}")
    logger.info(f"Test ROC-AUC  : {auc:.4f}")
    logger.info(f"\n{classification_report(y_test, y_pred, target_names=['Legitimate', 'Phishing'])}")
    logger.info(f"{'='*40}")

    if f1 < 0.85:
        logger.warning("F1 is below 0.85 threshold. Consider adding more data or tuning hyperparameters.")
    if auc < 0.90:
        logger.warning("ROC-AUC is below 0.90 threshold.")

    # ── Save model + feature list ─────────────────────────────────────────────
    model_path = MODELS_DIR / "xgboost_phishing.pkl"
    columns_path = MODELS_DIR / "feature_columns.json"

    joblib.dump(model, model_path)
    with open(columns_path, "w") as f:
        json.dump(feature_cols, f, indent=2)

    logger.info(f"\nModel saved → {model_path}")
    logger.info(f"Features saved → {columns_path}")


if __name__ == "__main__":
    main()
