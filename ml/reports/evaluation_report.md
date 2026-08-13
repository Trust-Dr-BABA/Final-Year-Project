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
