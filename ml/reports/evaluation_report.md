# Evaluation report — baseline comparison and split protocols

Measured on `ml/data/processed/features.csv` (19,685 rows). Both protocols are harder than a random split and are the ones this project's claims rest on — see the module docstring in `ml/scripts/evaluate_baselines.py` for why each is constructed the way it is.

## Temporal split

Train: 15748 rows (8000 phishing). Test: 3937 rows (2000 phishing).

| Baseline | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| B1 Blocklist lookup | 0.000 | 0.000 | 0.000 | 0.500 |
| B2 url_length only | 0.668 | 0.494 | 0.568 | 0.674 |
| B3 Logistic regression | 0.838 | 0.627 | 0.717 | 0.828 |
| B4 XGBoost (URL-only) | 0.881 | 0.613 | 0.723 | 0.851 |

**B1's recall on this test set is 0.0%.** By construction of the split, every test URL is absent from the training blocklist — this number *is* "recall on URLs absent from the blocklist," which is the direct quantitative answer to "why not just use a blocklist?" (claim C1).


## Unseen-registrable-domain split

Train: 16214 rows (8507 phishing). Test: 3471 rows (1493 phishing).

| Baseline | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| B1 Blocklist lookup | 0.000 | 0.000 | 0.000 | 0.500 |
| B2 url_length only | 0.468 | 0.413 | 0.439 | 0.574 |
| B3 Logistic regression | 0.738 | 0.585 | 0.653 | 0.782 |
| B4 XGBoost (URL-only) | 0.809 | 0.595 | 0.686 | 0.839 |

**B1's recall on this test set is 0.0%.** By construction of the split, every test URL is absent from the training blocklist — this number *is* "recall on URLs absent from the blocklist," which is the direct quantitative answer to "why not just use a blocklist?" (claim C1).


## Confusion matrix — B4 XGBoost, temporal split

| | Predicted legitimate | Predicted phishing |
|---|---|---|
| **Actually legitimate** | 1772 | 165 |
| **Actually phishing** | 774 | 1226 |

## Note on the fused model (no B5 row)

There is no offline measurement of the fused model's detection performance, because no corpus — this one included — carries real per-URL browser telemetry (tracker counts, redirect depth, permission timings) alongside a phishing label. Fabricating that telemetry to produce a B5 number would be exactly the kind of manufactured evidence ADR-014 explicitly rejects for the fusion weights themselves. B4 above **is** the fused model's URL-scoring component; claim C2 (that browser signals measurably move the score) is validated instead by a live test — `tests/unit/test_risk_fusion.py` and `tests/unit/test_shap.py::test_adverse_browser_signals_raise_the_score` — and by the end-to-end validation against live URLs in Sprint 3.

## False positives on the deep-path holdout

Measured on `ml/data/processed/fp_holdout.csv` — 1488 real deep-path URLs, disjoint domains from every training URL (see `ml/data/raw/DATASET_SOURCES.md`). Scored through the live `ml.shap_analysis.explain_prediction()` path, the same code the service calls.

| Band | Count | Rate |
|---|---|---|
| legitimate | 1185 | 79.6% |
| suspicious | 174 | 11.7% |
| **phishing** | **129** | **8.7%** |

A 8.7% false-positive rate in the phishing band (the band that raises the blocking interstitial, §3.7.2) on popular, legitimate, previously-unseen URLs is a genuine, measured limitation — see `ml/reports/training_log.md` for the investigation into individual misfires. Not tuned away against this same holdout, which would fit to the measurement instrument rather than the underlying problem.


## Calibration — temporal split test set

Measured on 3937 test URLs (2000 phishing). 10 equal-width bins.

| Metric | Before | After Platt scaling |
|---|---|---|
| Brier score | 0.1635 | 0.1640 |
| Expected Calibration Error | 0.0837 | 0.0768 |

![Reliability diagram](reliability_diagram.png)

| Bin | Mean predicted | Observed accuracy | Count |
|---|---|---|---|
| 0.0–0.1 | 0.054 | 0.139 | 797 |
| 0.1–0.2 | 0.146 | 0.253 | 657 |
| 0.2–0.3 | 0.247 | 0.358 | 441 |
| 0.3–0.4 | 0.351 | 0.505 | 374 |
| 0.4–0.5 | 0.447 | 0.542 | 277 |
| 0.5–0.6 | 0.551 | 0.680 | 172 |
| 0.6–0.7 | 0.647 | 0.729 | 118 |
| 0.7–0.8 | 0.757 | 0.770 | 135 |
| 0.8–0.9 | 0.851 | 0.925 | 226 |
| 0.9–1.0 | 0.971 | 0.959 | 740 |


Platt scaling was fitted because ECE (0.0837) exceeded 0.05. It improved calibration (0.0837 → 0.0768).

## Explanation faithfulness — top-3 SHAP ablation (claim C3)

For each of 3937 temporal-split test URLs, the top-3 SHAP-attributed features were neutralised to their training medians and the URL re-scored. Both shifts are measured in log-odds, the space SHAP natively attributes in.

| Metric | Value |
|---|---|
| URLs evaluated | 3937 |
| Mean absolute error (predicted vs. observed shift) | 0.9302 |
| Directional agreement (all cases) | 88.4% |
| Directional agreement (\|predicted shift\| > 0.05, n=3909) | 88.5% |

Acceptance target: ≥ 90% directional agreement. Not met on the full set (88.4%).

Exact agreement between predicted and observed shift is not expected: SHAP attributes a *specific* prediction under the *observed* feature distribution, and simultaneously intervening on three features moves the input off that distribution on a model that is not additive in its inputs. Directional agreement is the criterion that actually tests faithfulness; the MAE quantifies the size of the resulting interaction effects.

## Fusion weight sensitivity

Baseline: temporal-split test set (3937 URLs), a single fixed 'typical page' browser-signal profile ({'tracker_count': 3, 'has_mixed_content': 0, 'redirect_chain_length': 1}) applied uniformly to every URL, fused with the shipped weights. Baseline F1 at 0.5 threshold: 0.7710. 'Verdict changes' counts URLs whose risk band (phishing / suspicious / legitimate) moves relative to this baseline when a weight is perturbed.

| Perturbation | Verdict changes | F1 change |
|---|---|---|
| All weights x0.5 | 463/3937 (11.8%) | -0.0241 |
| All weights x2.0 | 1111/3937 (28.2%) | -0.0056 |
| Tracker weight only, x0 | 489/3937 (12.4%) | -0.0237 |
| Each weight +/-25%, one at a time | largest single change: tracker_count -25% (127/3937, 3.2%) | largest \|F1 change\|: +0.0029 |

F1 moves by a few hundredths even under the largest perturbation (weights x2.0), because the browser-signal profile is identical across every URL and so shifts every fused score by a similar amount — it barely reorders which URLs rank above or below the 0.5 threshold, which is what F1 there depends on. Verdict-band churn is the more informative number: doubling every weight moves 28.2% of URLs across a risk-band boundary, because a share of this test set sits near the 0.40/0.70 boundaries already and a uniform log-odds shift is enough to tip them. This is a genuine sensitivity, not a null result, and it is the argument for why the shipped weights (`ml/reports/fusion_weights.md`) are set conservatively rather than aggressively: at the shipped magnitude and a +/-25% perturbation around it, per-weight churn stays in the 0.0%-3.2% range on this synthetic uniform-signal test, well below the 28.2% seen at 2x, so the specific values chosen matter less than keeping the overall magnitude moderate. **Coverage caveat:** the fixed "typical page" profile only sets has_mixed_content, redirect_chain_length, tracker_count, so this particular run does not exercise cam_mic_on_first_visit, location_on_load, notification_prompt_on_load, scam_keyword_hits, sensitive_field_count, vt_malicious_votes — their +/-25% and x0.5/x2.0 rows above are correspondingly 0, not evidence those weights are insensitive, only that this synthetic profile never triggers them.


## Repeated-seed evaluation (confidence intervals)

Every other section in this report is a single-run point estimate from seed 42. This section repeats both split protocols under 10 different seeds (1–10, deliberately excluding 42 so it can be compared against the resulting interval rather than folded into it), retraining B4 XGBoost each time, to show the run-to-run variance a single seed hides. 95% CIs are a normal approximation ($\bar{x} \pm 1.96 \cdot s/\sqrt{n}$) for the *mean*, not a prediction interval for any one future draw — an individual seed, including 42, is not guaranteed to fall inside it even when the estimation procedure is working correctly.

**Temporal split** (10 repeats)

| Metric | Mean | Std dev | Min | Max | 95% CI | Seed 42 (headline) |
|---|---|---|---|---|---|---|
| F1 | 0.7202 | 0.0036 | 0.7153 | 0.7260 | [0.7180, 0.7225] | 0.7231 (outside CI) |
| ROC-AUC | 0.8478 | 0.0020 | 0.8453 | 0.8520 | [0.8465, 0.8490] | 0.8512 (outside CI) |

**Unseen-registrable-domain split** (10 repeats)

| Metric | Mean | Std dev | Min | Max | 95% CI | Seed 42 (headline) |
|---|---|---|---|---|---|---|
| F1 | 0.7572 | 0.0584 | 0.6746 | 0.8541 | [0.7210, 0.7934] | 0.6857 (outside CI) |
| ROC-AUC | 0.8682 | 0.0240 | 0.8374 | 0.9079 | [0.8533, 0.8831] | 0.8386 (outside CI) |

The unseen-registrable-domain split's standard deviation is far larger than the temporal split's (F1 std an order of magnitude bigger) — which domains happen to land in the test set matters a great deal for this protocol specifically, more than for the temporal split, where the phishing side is fixed by real submission time and only the benign side is randomised. The single previously-reported unseen-domain F1 (this report's own B4 row) should be read as one draw from a genuinely wide distribution, not a tight estimate — this is the concrete content of "the evaluation is single-run" as a limitation, not just its label.

