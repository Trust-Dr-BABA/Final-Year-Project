"""
generate_features.py

Reads:
    ml/data/processed/dataset.csv

Generates:
    ml/data/processed/features.csv
"""

import logging
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.feature_extractor.url_features import extract_url_features

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent

DATASET_PATH = BASE_DIR / "data" / "processed" / "dataset.csv"
FEATURES_PATH = BASE_DIR / "data" / "processed" / "features.csv"


# Extract features for every URL in dataset.csv and write the result to features.csv.
def main():
    logger.info(f"Loading dataset from: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    if "url" not in df.columns:
        raise ValueError("dataset.csv must contain a 'url' column")

    if "label" not in df.columns:
        raise ValueError("dataset.csv must contain a 'label' column")

    logger.info(f"Total URLs: {len(df)}")

    # Extract features
    feature_df = df["url"].apply(extract_url_features)

    # Convert dictionary column into DataFrame
    feature_df = pd.DataFrame(feature_df.tolist())

    # Combine original data + extracted features. submission_time/target ride along for the
    # temporal split (Sprint 2) rather than being extracted features themselves — train_model.py
    # excludes them from the trained column set, same as the VT columns (ADR-013).
    carry_along = [c for c in ("submission_time", "target") if c in df.columns]
    final_df = pd.concat(
        [
            df["url"],
            feature_df,
            df["label"],
            df[carry_along],
        ],
        axis=1,
    )

    # Save
    final_df.to_csv(FEATURES_PATH, index=False)

    logger.info(f"Feature extraction completed successfully. Saved to: {FEATURES_PATH}")
    logger.info(f"Generated columns: {final_df.columns.tolist()}")
    logger.debug(f"First five rows:\n{final_df.head()}")


if __name__ == "__main__":
    main()