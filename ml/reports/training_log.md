# Training log

One entry per `train_model.py` run against a committed corpus. Numbers here are measured, not
estimated — this file is the source for the thesis's headline detection-performance figures until
Sprint 2's full evaluation protocol (temporal split, unseen-domain split, baselines, calibration)
supersedes it.

## Run 1 — 13 August 2026, first training on the rebuilt corpus

**Corpus.** `ml/data/processed/features.csv`, 19,685 rows (10,000 phishing / 9,685 legitimate),
built from PhishTank (verified feed) and the crawled deep-path benign corpus — see
`ml/data/raw/DATASET_SOURCES.md`. Passed the leakage audit (`ml/reports/leakage_audit_after.md`):
no feature exceeds 0.90 standalone AUC, path-presence gap 13.6 points.

**Features (9, matching `get_feature_names()` minus the three VT columns per ADR-013):**
`url_length`, `num_digits`, `num_special_chars`, `subdomain_depth`, `has_https`, `url_entropy`,
`has_ip_address`, `suspicious_tld_flag`, `brand_impersonation`.

**Split.** Random 80/20, stratified, `random_state=42`. This is the *weaker* of the two protocols
this project uses — the temporal and unseen-domain splits in Sprint 2 are the ones the headline
claims rest on. This run exists to produce a working artefact and an honest baseline number, not
to be the final reported figure.

**Result:**

| Metric | Value |
|---|---|
| F1 (phishing class) | 0.8188 |
| ROC-AUC | 0.9017 |
| Precision (phishing) | 0.89 |
| Recall (phishing) | 0.76 |
| Precision (legitimate) | 0.78 |
| Recall (legitimate) | 0.90 |
| `scale_pos_weight` | 0.97 |

**Compare against the pre-rebuild corpus.** The previous training run (on the corpus later found
to carry defect D1 — see `ml/reports/leakage_audit_before.md`) reported approximately 0.97 F1. That
figure measured whether a URL had a path, not whether it was phishing. **0.82 is the honest number,
and it is a stronger result than 0.97 was, precisely because it is measuring the right thing.**

**Sanity checks (informal, not the formal Sprint 2 protocol):**

- `https://en.wikipedia.org/wiki/Phishing` → 0.256, *legitimate*. Correct.
- `http://paypal-secure-login-verify.tk/account/update?id=93921` → 0.981, *phishing*. Correct.
- `http://192.168.1.44/bank-login/secure.php?session=8ac2f91` → 0.954, *phishing*. Correct.
- `https://github.com/torvalds/linux/blob/master/README` → **0.564, *suspicious*** (not
  *legitimate*). This is the roadmap's own named acceptance example, and this run does not clear
  its `< 0.40` bar. Investigated rather than hidden: `url_entropy` (4.46) is the dominant
  contribution — every other feature reads as clean (`num_digits: 0`, `num_special_chars: 0`,
  `subdomain_depth: 0`, `has_ip_address: 0`, `suspicious_tld_flag: 0`, `brand_impersonation: 0`).
  Shannon entropy on a multi-segment descriptive path (`torvalds/linux/blob/master/README`) lands
  close to the phishing class's mean entropy simply because the path has varied characters, which
  is a real limitation of a purely lexical entropy feature rather than a bug.

**Aggregate false-positive check against the held-out deep-path corpus**
(`ml/data/processed/fp_holdout.csv`, 1,488 URLs, disjoint domains from training):

| Band | Count | Rate |
|---|---|---|
| legitimate | 1,170 | 78.6% |
| suspicious | 187 | 12.6% |
| **phishing** | **131** | **8.8%** |

An 8.8% false-positive rate in the phishing band (which triggers the blocking interstitial) on
popular, legitimate, previously-unseen URLs is a genuine, measured limitation of this model — not
a one-off on the hand-picked GitHub example above. Skimming the misfires shows two rough clusters:
legitimate URLs with naturally elevated entropy from varied path segments (financial-data pages,
multi-language site variants), and URLs from link-shortener-shaped legitimate services
(`lnk.bio`, `click.octobrowser.net`) that are structurally close to phishing infrastructure by
nature. Both are documented in the thesis limitations section rather than tuned away against this
same holdout set, which would just be fitting to it.

**Decision: this is accepted as Sprint 1.5's output, not re-tuned to force the GitHub example to
pass.** Adjusting feature weights until one hand-picked URL crosses a threshold is the same
methodological error this project spent Section 4.7.1 correcting — optimising against a single
example rather than measuring generalisation. Sprint 2's calibration work (§5.11 in the thesis) is
the correct venue for addressing this, with the full 1,488-URL holdout as the measurement, not one
URL as the target.
