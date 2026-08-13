# Leakage and separability audit — original corpus (PhishTank vs bare Tranco domains)

- **Source:** `ml\data\processed\dataset.csv`
- **Rows:** 20000
- **AUC flag threshold:** 0.90 (standalone, direction-independent)

## Standalone discriminative power

How well each feature separates the classes *by itself*. `AUC` is directional; `power` folds values below 0.5 back above it, because a perfectly anti-correlated feature leaks exactly as much as a correlated one.

| Feature | AUC | Power | Mean (benign) | Mean (phishing) | Flagged |
|---|---|---|---|---|---|
| `url_entropy` | 0.9001 | 0.9001 | 3.745 | 4.332 | **YES** |
| `url_length` | 0.8786 | 0.8786 | 21.852 | 58.953 | no |
| `subdomain_depth` | 0.8066 | 0.8066 | 0.109 | 0.785 | no |
| `num_digits` | 0.7542 | 0.7542 | 0.262 | 6.134 | no |
| `num_special_chars` | 0.7203 | 0.7203 | 0.112 | 2.071 | no |
| `has_https` | 0.4647 | 0.5353 | 1.000 | 0.929 | no |
| `brand_impersonation` | 0.5081 | 0.5081 | 0.006 | 0.022 | no |
| `suspicious_tld_flag` | 0.5057 | 0.5057 | 0.021 | 0.033 | no |
| `has_ip_address` | 0.5006 | 0.5006 | 0.000 | 0.001 | no |

## Structural balance

Not model features. These describe the *shape* of each class, which is where a corpus artefact shows up first.

| Class | Rows | URLs with a path (%) | Mean path segments | Mean URL length |
|---|---|---|---|---|
| benign | 10000 | 0.0 | 0.00 | 21.9 |
| phishing | 10000 | 65.2 | 1.22 | 59.0 |

**Path-presence gap between classes: 65.2 percentage points.**

## Verdict

**FAIL.** 1 feature(s) exceed 0.90 standalone AUC: `url_entropy`.

A single lexical feature does not solve phishing detection. This indicates the classes differ structurally for a reason unrelated to the label. Do not train on this corpus.
