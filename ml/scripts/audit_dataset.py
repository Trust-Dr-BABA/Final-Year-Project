"""
audit_dataset.py — Leakage and separability audit for a labelled URL corpus.

Reports, per feature, how well that feature separates the classes *on its own*. A single lexical
feature that approaches a perfect separation is not a discovery; it means the two classes differ
structurally for some reason unrelated to phishing. Also reports path-presence rate per class,
which is not a model feature but is the structural property that produced defect D1.

Usage:
    python ml/scripts/audit_dataset.py                                  # audit dataset.csv
    python ml/scripts/audit_dataset.py --input path.csv --out report.md --title "rebuilt corpus"

Exit status is 1 if any feature exceeds the AUC threshold, so the script can gate a pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.feature_extractor.url_features import extract_url_features  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DEFAULT_INPUT = BASE_DIR / "data" / "processed" / "dataset.csv"
DEFAULT_OUTPUT = BASE_DIR / "reports" / "leakage_audit.md"

# A feature separating the classes this well on its own is treated as an artefact, not a finding.
AUC_THRESHOLD = 0.90

# VirusTotal columns are constant sentinels outside a live request and are excluded from training
# by ADR-013, so auditing them would only report noise.
EXCLUDED = {"domain_age_days", "vt_malicious_votes", "vt_harmless_votes"}


# True if the URL carries a path beyond a bare "/" — the structural property behind defect D1.
def has_nontrivial_path(url: str) -> bool:
    try:
        parsed = urlparse(str(url))
    except ValueError:
        return False
    return len(parsed.path.strip("/")) > 0


# Count path segments in a URL, ignoring empty segments.
def path_segment_count(url: str) -> int:
    try:
        parsed = urlparse(str(url))
    except ValueError:
        return 0
    return len([segment for segment in parsed.path.split("/") if segment])


# Discriminative power of one feature used alone, direction-independent.
# A feature that perfectly anti-correlates with the label leaks exactly as much as one that
# correlates, so the reported power folds AUC below 0.5 back above it.
def standalone_auc(values: pd.Series, labels: pd.Series) -> tuple[float, float]:
    if values.nunique(dropna=True) < 2:
        return 0.5, 0.5
    directional = float(roc_auc_score(labels, values))
    return directional, max(directional, 1.0 - directional)


# Build the per-feature audit table for a corpus.
def audit_features(frame: pd.DataFrame) -> pd.DataFrame:
    logger.info("Extracting features for %d URLs…", len(frame))
    extracted = pd.DataFrame(frame["url"].apply(extract_url_features).tolist())

    labels = frame["label"].astype(int).reset_index(drop=True)
    extracted = extracted.reset_index(drop=True)

    rows = []
    for column in extracted.columns:
        if column in EXCLUDED:
            continue
        values = pd.to_numeric(extracted[column], errors="coerce").fillna(-1)
        directional, power = standalone_auc(values, labels)
        rows.append(
            {
                "feature": column,
                "auc": directional,
                "power": power,
                "mean_benign": float(values[labels == 0].mean()),
                "mean_phishing": float(values[labels == 1].mean()),
                "flagged": power > AUC_THRESHOLD,
            }
        )

    return pd.DataFrame(rows).sort_values("power", ascending=False).reset_index(drop=True)


# Build the structural-balance table that exposes corpus-shape artefacts.
def audit_structure(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["has_path"] = frame["url"].apply(has_nontrivial_path)
    frame["segments"] = frame["url"].apply(path_segment_count)
    frame["length"] = frame["url"].astype(str).str.len()

    rows = []
    for name, subset in (("benign", frame[frame["label"] == 0]),
                         ("phishing", frame[frame["label"] == 1])):
        rows.append(
            {
                "class": name,
                "rows": len(subset),
                "path_presence_pct": float(subset["has_path"].mean() * 100) if len(subset) else 0.0,
                "mean_segments": float(subset["segments"].mean()) if len(subset) else 0.0,
                "mean_url_length": float(subset["length"].mean()) if len(subset) else 0.0,
            }
        )
    return pd.DataFrame(rows)


# Render both tables plus a verdict into a Markdown report.
def render_report(title: str, source: Path, features: pd.DataFrame,
                  structure: pd.DataFrame) -> str:
    flagged = features[features["flagged"]]
    gap = abs(
        structure.loc[structure["class"] == "benign", "path_presence_pct"].iloc[0]
        - structure.loc[structure["class"] == "phishing", "path_presence_pct"].iloc[0]
    )

    lines = [
        f"# Leakage and separability audit — {title}",
        "",
        f"- **Source:** `{source}`",
        f"- **Rows:** {int(structure['rows'].sum())}",
        f"- **AUC flag threshold:** {AUC_THRESHOLD:.2f} (standalone, direction-independent)",
        "",
        "## Standalone discriminative power",
        "",
        "How well each feature separates the classes *by itself*. `AUC` is directional; `power` "
        "folds values below 0.5 back above it, because a perfectly anti-correlated feature leaks "
        "exactly as much as a correlated one.",
        "",
        "| Feature | AUC | Power | Mean (benign) | Mean (phishing) | Flagged |",
        "|---|---|---|---|---|---|",
    ]
    for row in features.itertuples(index=False):
        lines.append(
            f"| `{row.feature}` | {row.auc:.4f} | {row.power:.4f} | "
            f"{row.mean_benign:.3f} | {row.mean_phishing:.3f} | "
            f"{'**YES**' if row.flagged else 'no'} |"
        )

    lines += [
        "",
        "## Structural balance",
        "",
        "Not model features. These describe the *shape* of each class, which is where a corpus "
        "artefact shows up first.",
        "",
        "| Class | Rows | URLs with a path (%) | Mean path segments | Mean URL length |",
        "|---|---|---|---|---|",
    ]
    for row in structure.itertuples(index=False):
        lines.append(
            f"| {row._0 if hasattr(row, '_0') else row[0]} | {row.rows} | "
            f"{row.path_presence_pct:.1f} | {row.mean_segments:.2f} | {row.mean_url_length:.1f} |"
        )

    lines += ["", f"**Path-presence gap between classes: {gap:.1f} percentage points.**", "", "## Verdict", ""]

    if len(flagged):
        names = ", ".join(f"`{name}`" for name in flagged["feature"])
        lines += [
            f"**FAIL.** {len(flagged)} feature(s) exceed {AUC_THRESHOLD:.2f} standalone AUC: {names}.",
            "",
            "A single lexical feature does not solve phishing detection. This indicates the classes "
            "differ structurally for a reason unrelated to the label. Do not train on this corpus.",
        ]
    elif gap > 15:
        lines += [
            f"**FAIL.** No feature is individually leaky, but the path-presence gap of {gap:.1f} "
            "points exceeds the 15-point tolerance. The classes are structurally different in a way "
            "the model can exploit.",
        ]
    else:
        lines += [
            f"**PASS.** No feature exceeds {AUC_THRESHOLD:.2f} standalone AUC, and the "
            f"path-presence gap of {gap:.1f} points is within the 15-point tolerance.",
        ]

    lines.append("")
    return "\n".join(lines)


# Run the audit and write the report, exiting non-zero when the corpus fails the gate.
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--title", default="corpus")
    args = parser.parse_args()

    if not args.input.exists():
        logger.error("Dataset not found at %s", args.input)
        sys.exit(2)

    frame = pd.read_csv(args.input)
    for required in ("url", "label"):
        if required not in frame.columns:
            logger.error("Input must contain a '%s' column", required)
            sys.exit(2)
    frame = frame.dropna(subset=["url", "label"])

    features = audit_features(frame)
    structure = audit_structure(frame)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_report(args.title, args.input, features, structure), encoding="utf-8")
    logger.info("Report written to %s", args.out)

    flagged = features[features["flagged"]]
    for row in flagged.itertuples(index=False):
        logger.warning("LEAK: %s separates the classes alone (power %.4f)", row.feature, row.power)

    benign_path = structure.loc[structure["class"] == "benign", "path_presence_pct"].iloc[0]
    phish_path = structure.loc[structure["class"] == "phishing", "path_presence_pct"].iloc[0]
    logger.info("Path presence — benign %.1f%%, phishing %.1f%%", benign_path, phish_path)

    if len(flagged) or abs(benign_path - phish_path) > 15:
        logger.error("Audit FAILED. Do not train on this corpus.")
        sys.exit(1)
    logger.info("Audit passed.")


if __name__ == "__main__":
    main()
