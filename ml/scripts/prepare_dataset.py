"""
prepare_dataset.py — Merges PhishTank and Tranco CSVs into a clean training dataset.

Usage:
    python ml/scripts/prepare_dataset.py

Output:
    ml/data/processed/dataset.csv  (columns: url, label)
"""

import logging
import os
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_phishtank(path: Path) -> pd.DataFrame:
    """Load PhishTank CSV and return a DataFrame with columns: url, label=1."""
    logger.info(f"Loading PhishTank from {path}")
    df = pd.read_csv(path, usecols=["url"])
    df = df.dropna(subset=["url"])
    df["label"] = 1
    logger.info(f"  → {len(df)} phishing URLs loaded")
    return df


def load_tranco(path: Path, n_sample: int = 8000) -> pd.DataFrame:
    """Load Tranco Top-1M and return sampled legitimate URLs with label=0."""
    logger.info(f"Loading Tranco from {path}")
    df = pd.read_csv(path, header=None, names=["rank", "domain"])
    df = df.dropna(subset=["domain"])
    df["url"] = "https://" + df["domain"]
    df = df[["url"]].sample(n=min(n_sample, len(df)), random_state=42)
    df["label"] = 0
    logger.info(f"  → {len(df)} legitimate URLs sampled")
    return df


def main():
    phishtank_path = RAW_DIR / "phishtank.csv"
    tranco_path = RAW_DIR / "tranco.csv"

    if not phishtank_path.exists():
        logger.error(f"PhishTank CSV not found at {phishtank_path}. Download it first.")
        sys.exit(1)
    if not tranco_path.exists():
        logger.error(f"Tranco CSV not found at {tranco_path}. Download it first.")
        sys.exit(1)

    phishing_df = load_phishtank(phishtank_path)
    legitimate_df = load_tranco(tranco_path, n_sample=len(phishing_df))

    combined = pd.concat([phishing_df, legitimate_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["url"])
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    out_path = PROCESSED_DIR / "dataset.csv"
    combined.to_csv(out_path, index=False)

    # Report class balance
    counts = combined["label"].value_counts()
    total = len(combined)
    phish_pct = counts.get(1, 0) / total * 100
    legit_pct = counts.get(0, 0) / total * 100

    logger.info(f"\nDataset saved to {out_path}")
    logger.info(f"  Total rows : {total}")
    logger.info(f"  Phishing   : {counts.get(1, 0)} ({phish_pct:.1f}%)")
    logger.info(f"  Legitimate : {counts.get(0, 0)} ({legit_pct:.1f}%)")

    if phish_pct < 40 or legit_pct < 40:
        logger.warning("Class imbalance detected! Consider setting scale_pos_weight in train_model.py")


if __name__ == "__main__":
    main()
