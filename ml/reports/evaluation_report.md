# Evaluation report — baseline comparison and split protocols

Measured on `ml/data/processed/features.csv` (19,685 rows). Both protocols are harder than a random split and are the ones this project's claims rest on — see the module docstring in `ml/scripts/evaluate_baselines.py` for why each is constructed the way it is.

## Temporal split

Train: 15748 rows (8000 phishing). Test: 3937 rows (2000 phishing).

| Baseline | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| B1 Blocklist lookup | 0.000 | 0.000 | 0.000 | 0.500 |
| B2 url_length only | 0.668 | 0.494 | 0.568 | 0.674 |
| B3 Logistic regression | 0.828 | 0.665 | 0.738 | 0.826 |
| B4 XGBoost (URL-only) | 0.877 | 0.620 | 0.726 | 0.851 |

**B1's recall on this test set is 0.0%.** By construction of the split, every test URL is absent from the training blocklist — this number *is* "recall on URLs absent from the blocklist," which is the direct quantitative answer to "why not just use a blocklist?" (claim C1).


## Unseen-registrable-domain split

Train: 16214 rows (8507 phishing). Test: 3471 rows (1493 phishing).

| Baseline | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| B1 Blocklist lookup | 0.000 | 0.000 | 0.000 | 0.500 |
| B2 url_length only | 0.468 | 0.413 | 0.439 | 0.574 |
| B3 Logistic regression | 0.717 | 0.616 | 0.663 | 0.793 |
| B4 XGBoost (URL-only) | 0.815 | 0.601 | 0.692 | 0.840 |

**B1's recall on this test set is 0.0%.** By construction of the split, every test URL is absent from the training blocklist — this number *is* "recall on URLs absent from the blocklist," which is the direct quantitative answer to "why not just use a blocklist?" (claim C1).


## Confusion matrix — B4 XGBoost, temporal split

| | Predicted legitimate | Predicted phishing |
|---|---|---|
| **Actually legitimate** | 1763 | 174 |
| **Actually phishing** | 760 | 1240 |

## Note on the fused model (no B5 row)

There is no offline measurement of the fused model's detection performance, because no corpus — this one included — carries real per-URL browser telemetry (tracker counts, redirect depth, permission timings) alongside a phishing label. Fabricating that telemetry to produce a B5 number would be exactly the kind of manufactured evidence ADR-014 explicitly rejects for the fusion weights themselves. B4 above **is** the fused model's URL-scoring component; claim C2 (that browser signals measurably move the score) is validated instead by a live test — `tests/unit/test_risk_fusion.py` and `tests/unit/test_shap.py::test_adverse_browser_signals_raise_the_score` — and by the end-to-end validation against live URLs in Sprint 3.

## Calibration — temporal split test set

Measured on 3937 test URLs (2000 phishing). 10 equal-width bins.

| Metric | Before | After Platt scaling |
|---|---|---|
| Brier score | 0.1629 | 0.1641 |
| Expected Calibration Error | 0.0820 | 0.0803 |

![Reliability diagram](reliability_diagram.png)

| Bin | Mean predicted | Observed accuracy | Count |
|---|---|---|---|
| 0.0–0.1 | 0.054 | 0.141 | 834 |
| 0.1–0.2 | 0.146 | 0.266 | 628 |
| 0.2–0.3 | 0.249 | 0.350 | 429 |
| 0.3–0.4 | 0.349 | 0.466 | 326 |
| 0.4–0.5 | 0.444 | 0.565 | 306 |
| 0.5–0.6 | 0.549 | 0.642 | 162 |
| 0.6–0.7 | 0.647 | 0.723 | 148 |
| 0.7–0.8 | 0.753 | 0.839 | 155 |
| 0.8–0.9 | 0.857 | 0.903 | 226 |
| 0.9–1.0 | 0.971 | 0.961 | 723 |


Platt scaling was fitted because ECE (0.0820) exceeded 0.05. It improved calibration (0.0820 → 0.0803).

## Explanation faithfulness — top-3 SHAP ablation (claim C3)

For each of 3937 temporal-split test URLs, the top-3 SHAP-attributed features were neutralised to their training medians and the URL re-scored. Both shifts are measured in log-odds, the space SHAP natively attributes in.

| Metric | Value |
|---|---|
| URLs evaluated | 3937 |
| Mean absolute error (predicted vs. observed shift) | 1.0027 |
| Directional agreement (all cases) | 87.5% |
| Directional agreement (\|predicted shift\| > 0.05, n=3905) | 87.6% |

Acceptance target: ≥ 90% directional agreement. Not met on the full set (87.5%).

Exact agreement between predicted and observed shift is not expected: SHAP attributes a *specific* prediction under the *observed* feature distribution, and simultaneously intervening on three features moves the input off that distribution on a model that is not additive in its inputs. Directional agreement is the criterion that actually tests faithfulness; the MAE quantifies the size of the resulting interaction effects.

## False positives on the deep-path holdout

Measured on `ml/data/processed/fp_holdout.csv` — 1,488 real deep-path URLs from 806 domains,
disjoint from every domain used in training (see `ml/data/raw/DATASET_SOURCES.md`). For a browser
extension this is the most consequential single figure in this report: a detector that flags
mainstream, previously-unseen sites is unusable regardless of its F1.

| Band | Count | Rate |
|---|---|---|
| legitimate | 1,170 | 78.6% |
| suspicious | 187 | 12.6% |
| **phishing** | **131** | **8.8%** |

An 8.8% false-positive rate in the phishing band (the band that raises the blocking interstitial,
§3.7.2) on popular, legitimate URLs is a genuine, measured limitation. It is not a one-off: the
roadmap's own named acceptance example, `https://github.com/torvalds/linux/blob/master/README`,
scores 0.564 ("suspicious") rather than clearing the `< 0.40` bar, driven almost entirely by
`url_entropy` on a URL where every other lexical feature reads as clean. Full investigation and
misfire samples are recorded in `ml/reports/training_log.md`. This was not tuned away against this
same holdout set — doing so would fit to the measurement instrument rather than fix the underlying
model, the exact error Section 4.7.1 documents correcting once already.
