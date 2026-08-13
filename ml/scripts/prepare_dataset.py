"""
prepare_dataset.py — Builds a leakage-audited training corpus from PhishTank and a directly-crawled,
path-bearing benign corpus.

Two benign sources were tried and rejected before this one — see ml/reports/leakage_audit_before.md
and the activity log in PROJECT_STATE.md. Tranco domains prefixed with a scheme, and PhiUSIIL's
"legitimate" class, are both 0% path presence: bare domains. Training on either reproduces defect
D1 (the model learns "does this URL have a path", not phishing) under a different name. The benign
class here instead comes from `fetch_deep_benign_urls.py`, which crawls real Tranco-ranked domains
and collects their real internal links — genuine deep-path URLs from genuine popular sites.

Usage:
    python ml/scripts/prepare_dataset.py

Output:
    ml/data/processed/dataset.csv      (columns: url, label, submission_time, target)
    ml/data/processed/fp_holdout.csv   (disjoint-domain deep-path benign URLs; never used for
                                         training — this is the false-positive evaluation set)
"""

import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# Load PhishTank, keeping submission_time and target rather than discarding them — the former
# enables the temporal split in Sprint 2, the latter gives ground truth for brand_impersonation.
def load_phishtank(path: Path) -> pd.DataFrame:
    logger.info("Loading PhishTank from %s", path)
    df = pd.read_csv(path, usecols=["url", "submission_time", "verified", "target"])
    df = df[df["verified"] == "yes"].drop(columns=["verified"])
    df = df.dropna(subset=["url"])
    df["label"] = 1
    logger.info("  -> %d verified phishing URLs loaded", len(df))
    return df


# Load the directly-crawled deep-path benign corpus, adding bare-domain homepage visits alongside
# the deep links so the class's path-presence rate matches the *other* class's natural rate rather
# than sitting at a forced 100% — real browsing is a mix of homepage and deep-page visits, and the
# leakage audit's 15-point structural-balance tolerance is exactly what catches a corpus that isn't.
# Homepage rows are added, not substituted, so this only grows the benign pool.
def load_deep_benign(path: Path, target_path_presence: float, n_sample: int | None = None) -> pd.DataFrame:
    logger.info("Loading deep-path benign URLs from %s", path)
    deep_rows = pd.read_csv(path, usecols=["domain", "url"]).dropna(subset=["url"])
    n_deep = len(deep_rows)

    # Solve for how many bare-homepage rows bring path presence down to the target:
    # target = n_deep / (n_deep + n_bare)  =>  n_bare = n_deep * (1/target - 1)
    domains = deep_rows["domain"].drop_duplicates().sample(frac=1, random_state=42).reset_index(drop=True)
    n_bare = round(n_deep * (1.0 / target_path_presence - 1.0)) if target_path_presence > 0 else 0
    n_bare = min(n_bare, len(domains))  # one homepage row per domain at most
    bare_domains = domains.iloc[:n_bare]

    bare_rows = pd.DataFrame({"url": ["https://" + d + "/" for d in bare_domains]})
    df = pd.concat([deep_rows[["url"]], bare_rows], ignore_index=True)

    if n_sample is not None and len(df) > n_sample:
        df = df.sample(n=n_sample, random_state=42)
    df["label"] = 0
    df["submission_time"] = pd.NaT
    df["target"] = None
    logger.info(
        "  -> %d legitimate URLs loaded (%d deep + %d added bare homepage, targeting %.1f%% path presence)",
        len(df), n_deep, n_bare, target_path_presence * 100,
    )
    return df


# Merge phishing + benign into one shuffled, deduplicated dataset.csv and report class balance.
def main():
    phishtank_path = RAW_DIR / "phishtank.csv"
    benign_path = RAW_DIR / "deep_benign_train.csv"
    holdout_path = RAW_DIR / "deep_benign_holdout.csv"

    for path in (phishtank_path, benign_path, holdout_path):
        if not path.exists():
            logger.error("%s not found. Run the corresponding fetch script first.", path)
            sys.exit(1)

    phishing_df = load_phishtank(phishtank_path)

    # Match the benign class's path-presence rate to the phishing class's own — measured, not
    # assumed, so this can never silently drift from the actual PhishTank sample in use.
    phishing_path_presence = phishing_df["url"].apply(
        lambda u: len(urlparse(str(u)).path.strip("/")) > 0
    ).mean()
    logger.info("Phishing class path presence: %.1f%% (benign will target this rate)",
                phishing_path_presence * 100)

    benign_df = load_deep_benign(benign_path, phishing_path_presence, n_sample=len(phishing_df))

    combined = pd.concat([phishing_df, benign_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["url"])
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    out_path = PROCESSED_DIR / "dataset.csv"
    combined.to_csv(out_path, index=False)

    counts = combined["label"].value_counts()
    total = len(combined)
    phish_pct = counts.get(1, 0) / total * 100
    legit_pct = counts.get(0, 0) / total * 100

    logger.info("Dataset saved to %s", out_path)
    logger.info("  Total rows : %d", total)
    logger.info("  Phishing   : %d (%.1f%%)", counts.get(1, 0), phish_pct)
    logger.info("  Legitimate : %d (%.1f%%)", counts.get(0, 0), legit_pct)

    if phish_pct < 40 or legit_pct < 40:
        logger.warning("Class imbalance detected! Consider scale_pos_weight in train_model.py")

    # The holdout comes from a disjoint Tranco rank range never touched above — it answers
    # "does this flag popular deep links it has never seen" rather than "does it overfit training URLs".
    holdout_df = pd.read_csv(holdout_path, usecols=["url"]).dropna(subset=["url"])
    holdout_df = holdout_df.drop_duplicates(subset=["url"])
    holdout_out = PROCESSED_DIR / "fp_holdout.csv"
    holdout_df.to_csv(holdout_out, index=False)
    logger.info("False-positive holdout saved to %s (%d URLs, disjoint domains)",
                holdout_out, len(holdout_df))


if __name__ == "__main__":
    main()
