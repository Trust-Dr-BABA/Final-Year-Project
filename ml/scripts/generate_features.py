"""
generate_features.py

Reads:
    ml/data/processed/dataset.csv

Generates:
    ml/data/processed/features.csv
"""

from pathlib import Path

import pandas as pd
from tqdm import tqdm

from ml.features.url_features import extract_url_features


# Enable progress bar for pandas
tqdm.pandas()

# Paths
BASE_DIR = Path(__file__).parent.parent

DATASET_PATH = BASE_DIR / "data" / "processed" / "dataset.csv"
FEATURES_PATH = BASE_DIR / "data" / "processed" / "features.csv"


def main():

    print(f"Loading dataset from:\n{DATASET_PATH}\n")

    df = pd.read_csv(DATASET_PATH)

    if "url" not in df.columns:
        raise ValueError("dataset.csv must contain a 'url' column")

    if "label" not in df.columns:
        raise ValueError("dataset.csv must contain a 'label' column")

    print(f"Total URLs: {len(df)}")

    # Extract features
    feature_df = df["url"].progress_apply(extract_url_features)

    # Convert dictionary column into DataFrame
    feature_df = pd.DataFrame(feature_df.tolist())

    # Combine original data + extracted features
    final_df = pd.concat(
        [
            df["url"],
            feature_df,
            df["label"],
        ],
        axis=1,
    )

    # Save
    final_df.to_csv(FEATURES_PATH, index=False)

    print("\nFeature extraction completed successfully.")
    print(f"Saved to:\n{FEATURES_PATH}")

    print("\nGenerated Columns:")
    print(final_df.columns.tolist())

    print("\nFirst Five Rows:")
    print(final_df.head())


if __name__ == "__main__":
    main()