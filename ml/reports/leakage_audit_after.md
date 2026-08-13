# Leakage and separability audit — rebuilt corpus (PhishTank vs crawled deep-path benign, path-presence matched)

- **Source:** `ml\data\processed\dataset.csv`
- **Rows:** 19685
- **AUC flag threshold:** 0.90 (standalone, direction-independent)

## Standalone discriminative power

How well each feature separates the classes *by itself*. `AUC` is directional; `power` folds values below 0.5 back above it, because a perfectly anti-correlated feature leaks exactly as much as a correlated one.

| Feature | AUC | Power | Mean (benign) | Mean (phishing) | Flagged |
|---|---|---|---|---|---|
| `num_digits` | 0.7447 | 0.7447 | 0.601 | 6.134 | no |
| `url_entropy` | 0.7339 | 0.7339 | 3.946 | 4.332 | no |
| `subdomain_depth` | 0.6011 | 0.6011 | 0.556 | 0.785 | no |
| `url_length` | 0.5874 | 0.5874 | 37.832 | 58.953 | no |
| `num_special_chars` | 0.5796 | 0.5796 | 1.094 | 2.071 | no |
| `has_https` | 0.4683 | 0.5317 | 0.993 | 0.929 | no |
| `suspicious_tld_flag` | 0.5142 | 0.5142 | 0.004 | 0.033 | no |
| `brand_impersonation` | 0.5040 | 0.5040 | 0.014 | 0.022 | no |
| `has_ip_address` | 0.5006 | 0.5006 | 0.000 | 0.001 | no |

## Structural balance

Not model features. These describe the *shape* of each class, which is where a corpus artefact shows up first.

| Class | Rows | URLs with a path (%) | Mean path segments | Mean URL length |
|---|---|---|---|---|
| benign | 9685 | 78.9 | 1.22 | 37.8 |
| phishing | 10000 | 65.2 | 1.22 | 59.0 |

**Path-presence gap between classes: 13.6 percentage points.**

## Verdict

**PASS.** No feature exceeds 0.90 standalone AUC, and the path-presence gap of 13.6 points is within the 15-point tolerance.
