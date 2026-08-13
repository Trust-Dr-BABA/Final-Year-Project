# Chapter 5 — Testing and Evaluation

## 5.1 Testing strategy

The system has two kinds of correctness and they need different treatment. Software correctness —
does the code do what the specification says — is addressed by conventional testing at unit,
integration and system level. Model correctness — does the classifier do anything useful on data it
has never seen — is a measurement problem, and no amount of unit testing touches it.

Testing is therefore organised in six levels.

| Level | Question answered | Method | Section |
|---|---|---|---|
| **Unit** | Does each function compute what its specification states? | Automated, isolated, no network | 5.5 |
| **Integration** | Do the components agree at their boundaries? | Automated, collaborators replaced by doubles | 5.6 |
| **System** | Does the deployed stack behave correctly end to end? | Manual and scripted against a running stack | 5.7 |
| **Model evaluation** | Does the classifier generalise? | Held-out protocols, baseline comparison | 5.9–5.11 |
| **Explanation evaluation** | Are the stated reasons the operative ones? | Ablation | 5.12 |
| **Non-functional** | Latency, security, privacy | Benchmark and inspection | 5.13–5.14 |

A rule applies throughout: **no unit test performs a real network call.** The reputation service
permits four requests per minute on the free tier, and a test suite that exhausted that allowance
would be unusable in continuous integration and would also make results depend on a third party's
availability. Every external interaction is replaced by a double.

## 5.2 Measurement integrity

Section 1.3 stated the rule that every quantitative figure in this document comes from a recorded
execution. This section makes the rule operational, because a claim of integrity that cannot be
checked is worth nothing.

Figures in this chapter fall into two classes, and they are marked differently.

**Measured.** Reported as a plain value with the date and environment of the run that produced it.
These are complete.

**Pending.** Marked **⟨M-nn⟩** at the point a figure was first specified, before the corresponding
script had been run. A pending marker was never a placeholder for a plausible number; it was a
statement that the measurement had not yet been taken. Every entry in the register below was
subsequently executed and recorded — the tag is retained beside each result throughout this
chapter as a traceability anchor back to this table, not because the value is still outstanding.

**Table 5.1 — Measurement register, all entries executed 13 August 2026**

| Tag | Quantity | Produced by | Section |
|---|---|---|---|
| ⟨M-01⟩ | Per-feature standalone ROC-AUC, original corpus | `audit_dataset.py` | 5.4 |
| ⟨M-02⟩ | Path-presence rate per class, original corpus | `audit_dataset.py` | 5.4 |
| ⟨M-03⟩ | Per-feature standalone ROC-AUC, rebuilt corpus | `audit_dataset.py` | 5.4 |
| ⟨M-04⟩ | Path-presence rate per class, rebuilt corpus | `audit_dataset.py` | 5.4 |
| ⟨M-05⟩ | Corpus composition: rows, class balance, date range | `prepare_dataset.py` | 5.8 |
| ⟨M-06⟩ | Precision, recall, F1, AUC under random split | `train_model.py` | 5.9 |
| ⟨M-07⟩ | Precision, recall, F1, AUC under temporal split | `train_model.py` | 5.9 |
| ⟨M-08⟩ | Precision, recall, F1, AUC under unseen-domain split | `train_model.py` | 5.9 |
| ⟨M-09⟩ | Confusion matrix, temporal split | `train_model.py` | 5.9 |
| ⟨M-10⟩ | Baseline comparison table, five configurations | `evaluate_baselines.py` | 5.10 |
| ⟨M-11⟩ | False-positive rate, popular deep-path holdout | `evaluate_baselines.py` | 5.11 |
| ⟨M-12⟩ | Brier score and expected calibration error | `calibration.py` | 5.11 |
| ⟨M-13⟩ | Reliability diagram | `calibration.py` | 5.11 |
| ⟨M-14⟩ | Directional agreement and mean absolute error, ablation | `faithfulness.py` | 5.12 |
| ⟨M-15⟩ | Fusion weight sensitivity | `sensitivity.py` | 5.12 |
| ⟨M-16⟩ | Assessment latency, p50 and p95, cold and warm cache | `bench_latency.py` | 5.13 |
| ⟨M-17⟩ | End-to-end outcome over the 30-URL set | Manual, scripted | 5.15 |

## 5.3 Test environment

| Property | Value |
|---|---|
| Operating system | Windows 11 Pro 24H2 |
| Python | 3.11.15 |
| Node.js | 24 LTS |
| Database | PostgreSQL 15 (Alpine), containerised |
| Browser | Google Chrome, developer mode, unpacked extension |
| Continuous integration | GitHub Actions, `ubuntu-latest`, Python 3.11, Node 24 |
| Test runner | pytest 8.2.0; Node built-in runner for extension JavaScript |
| Linter | ruff 0.5.0 |

The interpreter version is pinned in CI as well as locally. Section 4.7.3 records why: the system
interpreter was too recent for several pinned scientific packages, and an unpinned environment would
have reintroduced that failure on a different machine.

## 5.4 Dataset audit

This section carries more evidential weight than any other in the chapter, because it is what
converts a methodological flaw into a documented finding.

### 5.4.1 Method

`audit_dataset.py` takes a labelled corpus and reports, for every feature:

- **Standalone ROC-AUC** — the area under the ROC curve using that feature alone as the score. A
  value near 0.5 means the feature is uninformative in isolation; a value above 0.90 means it very
  nearly solves the task by itself, which for a single lexical feature is implausible and indicates
  an artefact rather than a discovery.
- **Class-conditional means** — the mean of the feature within each class, which shows the direction
  and scale of any separation.
- **Path-presence rate per class** — the proportion of URLs in each class carrying a non-trivial
  path. This is not a model feature. It is a structural property of the corpus, included precisely
  because the defect in Section 4.7.1 was structural.

Any feature exceeding 0.90 AUC alone is flagged and the corpus is treated as suspect.

### 5.4.2 Original corpus

The original corpus paired PhishTank URLs against domains from a ranking list, prefixed with a
scheme. Expected structure: benign URLs bare, malicious URLs path-bearing.

**Table 5.2 — Standalone discriminative power, original corpus (⟨M-01⟩, 20,000 rows)**

| Feature | ROC-AUC alone | Mean (benign) | Mean (phishing) | Flagged |
|---|---|---|---|---|
| `url_entropy` | 0.9001 | 3.745 | 4.332 | **YES** |
| `url_length` | 0.8786 | 21.852 | 58.953 | no |
| `subdomain_depth` | 0.8066 | 0.109 | 0.785 | no |
| `num_digits` | 0.7542 | 0.262 | 6.134 | no |
| `num_special_chars` | 0.7203 | 0.112 | 2.071 | no |
| `has_https` | 0.5353 | 1.000 | 0.929 | no |
| `brand_impersonation` | 0.5081 | 0.006 | 0.022 | no |
| `suspicious_tld_flag` | 0.5057 | 0.021 | 0.033 | no |
| `has_ip_address` | 0.5006 | 0.000 | 0.001 | no |

`has_https`'s reported AUC is its *power* (§5.4.1) — its raw, directional AUC is 0.4647, folded
above 0.5 because an anti-correlated feature leaks exactly as much as a correlated one.

**Table 5.3 — Structural balance, original corpus (⟨M-02⟩)**

| Property | Benign | Phishing |
|---|---|---|
| URLs with a non-trivial path | 0.0% | 65.2% |
| Mean path segments | 0.00 | 1.22 |
| Mean URL length | 21.9 | 59.0 |

*Expected shape of this result, stated in advance so that it constitutes a prediction rather than a
description: path presence near zero for the benign class and near total for the phishing class,
with `url_length` exceeding 0.90 AUC alone.* Recording the expectation before the run is what makes
the audit a test rather than an illustration.

### 5.4.3 Rebuilt corpus

The corpus was rebuilt with a path-bearing benign source so that both classes have realistic URL
structure. The ranking list was not discarded but repurposed as the false-positive holdout of
Section 5.11.

**Table 5.4 — Standalone discriminative power, rebuilt corpus (⟨M-03⟩, 19,685 rows)**

| Feature | ROC-AUC alone | Δ vs original | Flagged |
|---|---|---|---|
| `num_digits` | 0.7447 | −0.0095 | no |
| `url_entropy` | 0.7339 | **−0.1662** | no |
| `subdomain_depth` | 0.6011 | −0.2055 | no |
| `url_length` | 0.5874 | **−0.2912** | no |
| `num_special_chars` | 0.5796 | −0.1407 | no |
| `suspicious_tld_flag` | 0.5142 | +0.0085 | no |
| `has_https` | 0.5317 | −0.0036 | no |
| `brand_impersonation` | 0.5058 | −0.0023 | no |
| `has_ip_address` | 0.5006 | 0.0000 | no |

The two bold deltas are the ones that mattered: `url_entropy`, the single feature that failed the
audit on the original corpus, drops 17 points and clears the 0.90 threshold by a wide margin;
`url_length`, the feature most obviously tied to path presence, drops 29 points. No feature exceeds
0.90 on the rebuilt corpus — the audit gate passes.

**Table 5.5 — Structural balance, rebuilt corpus (⟨M-04⟩)**

| Property | Benign | Phishing | Difference |
|---|---|---|---|
| URLs with a non-trivial path | 78.9% | 65.2% | 13.6 points |
| Rows | 9,685 | 10,000 | — |

**Acceptance criteria for the rebuilt corpus:** no single feature above 0.90 AUC (met — highest is
0.7447); path-presence rates within 15 percentage points of each other (met — 13.6-point gap); at
least 15,000 rows with neither class below 40% (met — 19,685 rows, 49.2%/50.8% split).

### 5.4.4 Interpretation

The expected consequence of the rebuild is that headline detection scores fall. That is the intended
outcome, and it is worth being explicit about why a lower number is the better result.

The original score measured the model's ability to detect the presence of a path. The rebuilt score
measures its ability to detect phishing. These are different quantities, and only the second is the
one this project claims to deliver. A drop from an inflated figure to an honest one is an improvement
in the validity of the measurement, not a regression in the system.

## 5.5 Unit testing

### 5.5.1 Coverage

Six modules carry automated unit tests. All results below were recorded on 13 August 2026 in the
environment of Section 5.3.

**Table 5.6 — Unit test suite, measured**

| Module | Cases | Result |
|---|---|---|
| `test_url_features.py` | Feature extraction across URL shapes | Pass |
| `test_explainer_formatter.py` | Template substitution and boolean-valued features | Pass |
| `test_shap.py` | Attribution output shape; unavailable-model behaviour | Pass |
| `test_virustotal_client.py` | Cache behaviour, timeout, malformed payload | Pass |
| `network_monitor_test.js` | Tracker base-domain resolution | Pass |
| **Total (pytest)** | **25** | **25 passed, 0 failed** |

Full suite execution time: 5.7 s. Continuous integration reproduces this on `ubuntu-latest`; the
`backend` job on commit `8378be5` reports the same 25 passing.

### 5.5.2 Selected unit test cases

**Table 5.7 — Unit test cases**

| ID | Objective | Precondition | Input | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| **TC-U-01** | Entropy of an empty string is defined | — | `""` | `0.0`, no exception | As expected | Pass |
| **TC-U-02** | Entropy rises with randomness | — | Readable URL vs generated URL | Generated URL scores higher | As expected | Pass |
| **TC-U-03** | Raw IPv4 host detected | — | `http://192.168.1.1/login` | `has_ip_address = 1` | As expected | Pass |
| **TC-U-04** | Hostname not misread as an address | — | `https://example.com` | `has_ip_address = 0` | As expected | Pass |
| **TC-U-05** | High-risk TLD detected | — | `http://login.secure.tk` | `suspicious_tld_flag = 1` | As expected | Pass |
| **TC-U-06** | Ordinary TLD not flagged | — | `https://example.com` | `suspicious_tld_flag = 0` | As expected | Pass |
| **TC-U-07** | Brand outside its own domain flagged | Brand list loaded | `http://paypal.secure-login.tk/` | `brand_impersonation = 1` | As expected | Pass |
| **TC-U-08** | Brand on its own domain not flagged | Brand list loaded | `https://paypal.com/signin` | `brand_impersonation = 0` | As expected | Pass |
| **TC-U-09** | Scheme detected | — | `http://` and `https://` variants | `has_https` 0 and 1 respectively | As expected | Pass |
| **TC-U-10** | Reputation absent yields sentinels | No API key set | Any domain | All three fields `-1` | As expected | Pass |
| **TC-U-11** | Transport failure yields sentinels | Client double raises | Any domain | All three fields `-1`, no exception escapes | As expected | Pass |
| **TC-U-12** | Malformed payload yields sentinels | Double returns a list | Any domain | All three fields `-1` | As expected | Pass |
| **TC-U-13** | Repeat query served from cache | One prior call within TTL | Same domain twice | Exactly one outbound call | As expected | Pass |
| **TC-U-14** | Boolean feature renders both polarities | Templates loaded | `has_https` true, then false | Two distinct sentences, neither containing an identifier | As expected | Pass |
| **TC-U-15** | Unknown feature degrades safely | Templates loaded | `feature_that_does_not_exist` | Generic sentence, no exception, no identifier leaked | As expected | Pass |
| **TC-U-16** | No identifier reaches output | — | Every returned reason | No `_` in any `human_readable` | As expected | Pass |
| **TC-U-17** | Model absent raises rather than fabricates | No artefact, override unset | Any feature vector | `ModelUnavailableError` | As expected | Pass |
| **TC-U-18** | Override permits development fallback | No artefact, override set | Any feature vector | Result returned, marked as fallback | As expected | Pass |
| **TC-U-19** | Tracker subdomain resolves to base | List loaded | `ssl.google-analytics.com` | `google-analytics.com` | As expected | Pass |
| **TC-U-20** | Tracker variants counted once | List loaded | `ssl.` and `www.` variants of one tracker | Count of 1 | As expected | Pass |
| **TC-U-21** | Non-tracker host returns no match | List loaded | `example.com` | `null` | As expected | Pass |

TC-U-17 was added during this work specifically to lock in ADR-016. Without it, a future change that
reintroduced the silent fallback would pass every other test in the suite — which is exactly what
happened the first time.

### 5.5.3 Regression tests for known defects

Each defect in Section 4.7 that could recur silently has a test that fails if it does.

**Table 5.8 — Defect regression tests**

| Defect | Test | Assertion | Status |
|---|---|---|---|
| D2 — signals discarded | TC-U-22 | A vector containing an unrecognised key raises rather than being silently dropped | Pass |
| D2 — signals inert | TC-I-06 | Identical URL with adverse signals scores strictly higher via `risk_fusion.fuse()` | Pass |
| D4 — artefact drift | TC-U-23 | Loading a model whose arity ≠ manifest length raises, reporting both | Pass |
| D5 — silent fallback | TC-U-17 | Missing artefact raises without the override | Pass |
| D1 — corpus artefact | Audit gate | No feature exceeds 0.90 AUC alone | Pass (0.7447 highest, Table 5.4) |

## 5.6 Integration testing

**Table 5.9 — Integration test cases**

| ID | Objective | Precondition | Input | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| **TC-I-01** | Assessment returns a conforming response | Collaborators doubled, session doubled | Valid URL, no signals | 200; `scan_id`, `verdict`, `risk_score`, `confidence_pct`, `top_reasons`, `flagged_rules` all present and correctly typed | As expected | Pass |
| **TC-I-02** | Malformed URL rejected at the boundary | — | `"not-a-url"` | 422, field named, no record written | As expected | Pass |
| **TC-I-03** | Negative count rejected | — | `tracker_count: -1` | 422 | As expected | Pass |
| **TC-I-04** | Reputation failure does not alter the verdict | Reputation double raises | Fixed URL, fixed signals | Same verdict and score as the success case; corroboration shows sentinels | As expected | Pass |
| **TC-I-05** | Model unavailable yields 503 | No artefact, override unset | Valid URL | 503; no record written | As expected | Pass |
| **TC-I-06** | Adverse signals raise the score | Fusion layer active | Same URL, clean vs adverse signals | Adverse strictly greater; at least one browser signal present in `top_reasons` | Fused score strictly greater with `excessive_trackers` present in `top_reasons`, attribution equal to `weight x transform(value)` | Pass |
| **TC-I-07** | Unknown identifier rejected | — | `GET /scan/not-a-uuid` | 400 | As expected | Pass |
| **TC-I-08** | Absent record reported | Empty database | `GET /scan/<random uuid>` | 404 | As expected | Pass |
| **TC-I-09** | Pagination bounded | — | `limit=500` | 422 | As expected | Pass |
| **TC-I-10** | Migration applies to an empty database | Container running | `alembic upgrade head` | `scans` created with all five JSONB columns, PK and URL index | As expected | Pass |

TC-I-10 was executed against a live PostgreSQL 15 container on 12 August 2026. The applied schema
was confirmed by inspection:

```
Table "public.scans"
 id                 | uuid                     | not null
 url                | text                     | not null
 verdict            | character varying(20)    | not null
 risk_score         | double precision         | not null
 confidence_pct     | integer                  | not null
 url_features       | jsonb                    |
 network_signals    | jsonb                    |
 permission_signals | jsonb                    |
 shap_values        | jsonb                    |
 flagged_rules      | jsonb                    |
 created_at         | timestamp with time zone | not null
Indexes:
    "scans_pkey" PRIMARY KEY, btree (id)
    "ix_scans_url" btree (url)
```

## 5.7 System testing

**Table 5.10 — System test cases**

| ID | Objective | Precondition | Procedure | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| **TC-S-01** | Stack starts from one command | Docker available, environment file present | `docker compose up -d` | Database healthy; service starts with no import error in the log | Service log showed only "Application startup complete" | Pass |
| **TC-S-02** | Health reports true state, model absent | No artefact mounted | `GET /health` | `model_loaded: false`, `feature_count: 0`, `model_sha256: null` | Exactly as expected | Pass |
| **TC-S-03** | Health reports database reachability | Database stopped, then started | `GET /health` in both conditions | `db_reachable` false then true | Observed false with no database, true once the container was healthy | Pass |
| **TC-S-04** | Health reports credential configuration | Key present in environment | `GET /health` | `vt_key_configured: true` | As expected | Pass |
| **TC-S-05** | Extension loads without error | Chrome developer mode | Load unpacked from `extension/` | No manifest error; no service-worker exception | No errors reported on the extension card; service-worker console clean | Pass |
| **TC-S-06** | Network signals collected on a real page | Extension loaded | Navigate to a major news domain, inspect extension storage | Non-zero tracker count | `tracker_count: 11`, `redirect_chain_length: 5`, 11 distinct third-party domains recorded | Pass |
| **TC-S-07** | Signals survive to assessment | TC-S-06 complete | Observe the assessment request | Signals present in the submitted body | Rule flags `excessive_trackers` and `long_redirect_chain` returned, confirming both signals were received and evaluated | Pass |
| **TC-S-08** | Fail-loud path visible end to end | No artefact, override unset | Navigate any page | Extension shows an error state; no verdict displayed | Service returned 503; extension displayed the error state and logged a handled failure | Pass |
| **TC-S-09** | Development override restores service | Override set on the container | Repeat TC-S-08 | Verdict returned via the documented fallback | Assessment returned `legitimate`, risk 0.05, with the two rule flags above | Pass |
| **TC-S-10** | Interstitial raised only on the phishing band | Fusion and model active, extension built (§3.7.2) | Navigate a known phishing URL, then a benign one | Overlay on the first, none on the second | — | **Pending real-browser run** — see `tests/manual/interstitial_test.md`; not testable in the Node-VM harness used elsewhere, so this awaits the same manual pass as D7/D8 below rather than an automated result |
| **TC-S-11** | Dismissal does not persist | TC-S-10 complete | Dismiss, then re-navigate to the same URL | Warning raised again | — | **Pending real-browser run**, same test plan |

TC-S-06 through TC-S-09 form a useful chain. TC-S-08 confirms the system refuses to invent a verdict;
TC-S-09 confirms that the refusal is configuration rather than breakage; and TC-S-07 confirms that
the signals measured in the browser genuinely reached the reasoning layer, which is the empirical
counterpart to the defect in Section 4.7.2.

The observed value of 11 tracker domains in TC-S-06 also validates the threshold choice in
Algorithm 4.4 from the other direction: a mainstream commercial site sits just above the
`excessive_trackers` boundary, which is where a threshold intended to mark "unusually many" ought to
sit.

## 5.8 Corpus composition

**Table 5.11 — Corpus composition (⟨M-05⟩)**

| Property | Value |
|---|---|
| Total rows | 19,685 |
| Phishing rows | 10,000 |
| Benign rows | 9,685 |
| Class balance | 50.8% phishing / 49.2% benign |
| Distinct registrable domains | 4,710 |
| Submission date range (phishing class) | 19 January 2017 – 23 July 2026 |
| Temporal split boundary (80/20 by submission time) | 24 May 2026 |

The benign class carries no submission timestamp — a crawl date is not a publication date — so it
is split randomly in matching proportion rather than temporally; §5.9 and Appendix B state this
explicitly.

Sources, retrieval dates, row counts and licence terms are recorded in `ml/data/raw/DATASET_SOURCES.md`
and reproduced in Appendix B.

## 5.9 Detection performance

Three protocols are reported. The differences between them are more informative than any single
number.

**Random split** partitions rows uniformly. It is the protocol most commonly reported in the
literature and the least representative of deployment, because a URL from the same campaign — often
the same domain — can appear in both partitions.

**Temporal split** trains on submissions before a cut-off date and tests on submissions after it.
This mirrors deployment exactly: a deployed detector always predicts the future, and never has
access to campaigns that have not yet occurred.

**Unseen-domain split** guarantees that no registrable domain appears in both partitions,
which prevents the model from succeeding by memorising domains rather than learning structure.

**Table 5.12 — Detection performance by protocol (phishing class; ⟨M-06⟩ ⟨M-07⟩ ⟨M-08⟩)**

| Protocol | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| Random split (80/20, stratified) | 0.889 | 0.756 | 0.817 | 0.903 |
| Temporal split | 0.873 | 0.621 | 0.726 | 0.852 |
| Unseen registrable domain | 0.807 | 0.591 | 0.683 | 0.839 |

**Table 5.13 — Confusion matrix, temporal split (⟨M-09⟩, 3,937 test URLs)**

| | Predicted phishing | Predicted legitimate |
|---|---|---|
| **Actually phishing** (2,000) | 1,242 | 758 |
| **Actually legitimate** (1,937) | 181 | 1,756 |

The temporal figure is the headline result of this project, and it falls visibly below the
random-split figure (F1 0.726 vs. 0.817; recall 0.621 vs. 0.756). That gap is itself a finding: it
quantifies how much of the random-split result comes from campaign overlap — near-duplicate URLs
from the same phishing kit landing on both sides of a random partition — rather than genuine
generalisation to campaigns the model has not encountered. The unseen-domain split falls further
still (F1 0.683), which is consistent: it removes not just duplicate URLs but duplicate domains,
the harder and more realistic constraint. Recall is the metric that degrades most under both harder
protocols (0.756 → 0.621 → 0.591) — the model misses more genuinely novel phishing than it
misclassifies legitimate pages, which given the false-positive costs discussed in §5.11 is the
direction an examiner should want the errors to fall on.

## 5.10 Baseline comparison

Claim C1 asserts that the system generalises beyond a blocklist. That is an empirical claim about a
comparison, so the comparison is made explicitly.

**Table 5.14 — Baseline comparison under the temporal split (⟨M-10⟩)**

| # | Configuration | Precision | Recall | F1 | Notes |
|---|---|---|---|---|---|
| B1 | Blocklist lookup against the training set | 0.000 | 0.000 | 0.000 | Recall exactly zero by construction of the split — every test URL is absent from the training blocklist |
| B2 | `url_length` threshold (logistic regression, one feature) | 0.668 | 0.494 | 0.568 | Included to demonstrate the D1 artefact is gone: on the original corpus this feature alone reached 0.88 AUC; here it is a weak baseline, as a single lexical feature should be |
| B3 | Logistic regression, all 9 lexical features | 0.828 | 0.666 | 0.739 | Linear reference — notably close to B4, suggesting the lexical features are close to linearly separable and XGBoost's advantage here is modest |
| B4 | XGBoost, URL features only | 0.873 | 0.621 | 0.726 | The model without fusion — the URL-scoring half of the deployed system |
| B5 | Full fused system | *(no offline row — see below)* | | | As deployed, browser signals included |

**B1's recall is 0.0% on this test set**, which is the direct quantitative answer to "why not just
use a blocklist" (claim C1): every phishing URL that reaches the temporal test partition is, by
construction, one the blocklist has never seen, and B4's 62.1% recall on exactly those URLs is
generalisation a blocklist structurally cannot provide.

**There is no measured B5 row.** No corpus, including this one, pairs a phishing label with real
per-URL browser telemetry — tracker counts, redirect depth, permission-prompt timing — because that
telemetry only exists once a browser has visited the page. Fabricating it to produce a B5 number
would be exactly the kind of manufactured evidence ADR-014 rejects for the fusion weights
themselves, and reporting it that way would be the same category of methodological error as D1.
Claim C2 (browser signals measurably move the score) is validated instead by intervention —
`tests/unit/test_risk_fusion.py` and TC-I-06 above confirm the fused score strictly increases under
adverse signals, by exactly the documented weight — and by the live 30-URL run in §5.15, which
exercises the complete fused pipeline against real requests rather than an offline table.

B2 is included for a reason worth stating: on the original corpus it would have performed
implausibly well. Its poor performance on the rebuilt corpus is confirmation that the artefact was
removed rather than merely diluted.

## 5.11 False positives on popular sites and calibration

### 5.11.1 Deep-path holdout

For a browser extension this is the most consequential single figure in the chapter. A detector that
flags mainstream sites is worthless regardless of its F1, because users disable it within a day.

The holdout consists of the top thousand entries of a domain-ranking list with real deep paths —
article pages, repository file views, documentation pages, search results — none of which appeared in
training.

**Table 5.15 — False positives, popular deep-path holdout (⟨M-11⟩)**

| Metric | Value |
|---|---|
| URLs evaluated | 1,488 |
| Classified *legitimate* | 1,161 (78.0%) |
| Classified *suspicious* | 201 (13.5%) |
| Classified *phishing* (false positive) | 126 (8.5%) |
| False-positive rate (phishing band) | **8.5%** |

An 8.5% false-positive rate in the band that raises the blocking interstitial (§3.7.2), on popular,
legitimate, previously-unseen deep-path URLs, is a genuine and material limitation, not a rounding
concern. `ml/reports/training_log.md` traces the misfires to two clusters: legitimate URLs with
naturally elevated Shannon entropy from varied path segments (financial-data pages, multi-language
site variants), and legitimate link-shortener-shaped services (`lnk.bio`, `click.octobrowser.net`)
that are structurally close to phishing infrastructure by nature. Both are lexical-feature
limitations, carried into §6.3 rather than tuned away against this same holdout — which would fit
the measurement instrument, not the underlying problem, repeating the exact error the corpus
rebuild in §4.7.1 corrected in the other direction.

### 5.11.2 Calibration

The interface asserts a confidence percentage. Calibration is the evidence that the number means
anything: among pages assigned roughly 0.8, close to 80% should be phishing.

Measured on the temporal-split test set (3,937 URLs, 2,000 phishing), 10 equal-width bins.

**Table 5.16 — Calibration (⟨M-12⟩)**

| Metric | Before | After Platt scaling | Interpretation |
|---|---|---|---|
| Brier score | 0.1622 | 0.1647 | Mean squared error of the probability; lower is better |
| Expected calibration error | 0.0821 | 0.0799 | Mean gap between confidence and accuracy across bins |
| Bins used | 10, equal width | — | — |

Platt scaling was fitted — on a held-out validation split of the training partition, never on the
test partition — because the pre-scaling ECE (0.0821) exceeded the 0.05 threshold this project
treats as acceptable without further correction. It moved ECE the intended direction (0.0821 →
0.0799) but very slightly worsened the Brier score (0.1622 → 0.1647). Both are reported, not just
the one that improved: reporting only the favourable metric after fitting an adjustment would
itself be a form of the measurement-integrity failure §5.2 exists to prevent.

**Figure 5.1 — Reliability diagram (⟨M-13⟩)**

![Figure 5.1 — Reliability diagram, predicted probability against observed frequency](diagrams/out/fig-5-1-reliability.png)

| Bin | Mean predicted | Observed accuracy | Count |
|---|---|---|---|
| 0.0–0.1 | 0.055 | 0.137 | 830 |
| 0.1–0.2 | 0.143 | 0.271 | 645 |
| 0.2–0.3 | 0.250 | 0.333 | 418 |
| 0.3–0.4 | 0.350 | 0.459 | 314 |
| 0.4–0.5 | 0.444 | 0.606 | 307 |
| 0.5–0.6 | 0.546 | 0.604 | 169 |
| 0.6–0.7 | 0.645 | 0.768 | 142 |
| 0.7–0.8 | 0.752 | 0.771 | 144 |
| 0.8–0.9 | 0.857 | 0.922 | 245 |
| 0.9–1.0 | 0.971 | 0.960 | 723 |

The model is systematically under-confident in the low bins (predicted 0.055 against an observed
rate of 0.137) and closely calibrated at the extremes it assigns most mass to (0.9–1.0: predicted
0.971, observed 0.960, on 723 of the 3,937 URLs). Without this section the phrase "94% confident"
in the interface would be decoration, and an examiner would be entitled to say so; with it, the
figure is traceable to a measured reliability curve rather than asserted.

## 5.12 Explanation faithfulness and sensitivity

### 5.12.1 Faithfulness

Claim C3 asserts that the stated reasons are the operative ones. This is testable by intervention:
neutralise the reasons the system gave, and see whether the score moves as they predicted.

**Procedure.** For each of *N* test URLs: record the score and the three highest-ranked
contributions; set those three features to their training medians; re-score; compare the observed
change against the sum of the three attributions.

**Table 5.17 — Explanation faithfulness (⟨M-14⟩)**

| Metric | Value | Acceptance |
|---|---|---|
| URLs evaluated | 3,937 (temporal-split test set) | — |
| Directional agreement | **87.0%** | ≥ 90% — **not met** |
| Directional agreement, \|predicted shift\| > 0.05 (n = 3,920) | 87.1% | — |
| Mean absolute error, predicted vs observed shift (log-odds) | 0.9913 | — |

Exact agreement is not expected and its absence is not a failure. SHAP attributes a specific
prediction under a specific feature distribution; intervening on three features simultaneously moves
the input off that distribution, and tree ensembles are not additive in the input. Directional
agreement is the meaningful criterion, and the magnitude error quantifies the interaction effects.

**The 87.0% result is reported as measured, short of the 90% target, rather than adjusted to clear
it.** Restricting to cases where the predicted shift is not near zero moves the figure by only 0.1
point (87.1%), so the shortfall is not an artefact of near-zero predictions dominating the
denominator. Two explanations are consistent with the gap and neither is fixable by re-tuning
against this same measurement: XGBoost with `max_depth=6` permits real three-way feature
interactions that SHAP's local attribution does not fully capture under a simultaneous
three-feature ablation, and several of the model's strongest features (`url_entropy`,
`num_digits`) are correlated with each other, so neutralising the top three together removes more
combined signal than the sum of their individual attributions predicts. This is recorded as a
genuine limitation of claim C3 in §6.3, not resolved here.

### 5.12.2 Fusion weight sensitivity

The fusion weights are set by hand (ADR-014), which obliges the work to show that conclusions do not
rest on their precise values.

No corpus pairs real browser telemetry with a phishing label (§5.10's note on B5), so this cannot
measure real-world fused accuracy without fabricating per-URL signals correlated with the label —
exactly the manufactured evidence ADR-014 rejects for the weights themselves. Instead a single
fixed, clearly-synthetic "typical page" profile (`tracker_count=3`, no mixed content, one redirect
— moderate, chosen well below `heuristics_engine.py`'s own "excessive" thresholds of 10 and 3) is
applied uniformly to every URL in the temporal-split test set (3,937 URLs), and each perturbation is
measured against that same fixed baseline.

**Table 5.18 — Fusion weight sensitivity (⟨M-15⟩)**

| Perturbation | Verdict changes | F1 change |
|---|---|---|
| All weights ×0.5 | 387/3,937 (9.8%) | +0.0337 |
| All weights ×2.0 | 1,727/3,937 (43.9%) | +0.0385 |
| Tracker weight only, ×0 | 355/3,937 (9.0%) | +0.0318 |
| Each weight ±25%, one at a time (largest single change) | `tracker_count` +25%: 934/3,937 (23.7%) | +0.0569 |

F1 moves by only a few hundredths even at the largest perturbation tested, because the synthetic
signal profile is identical across every URL — it shifts every fused score by a similar amount and
so barely reorders which URLs fall above or below the 0.5 threshold, which is what F1 there depends
on. Verdict-band churn is the more informative number, and it is **not small at the extremes**:
doubling every weight moves 43.9% of URLs across a risk-band boundary, because a large share of this
test set already sits close to the 0.40/0.70 boundaries and a uniform log-odds shift is enough to
tip them. This is a genuine sensitivity, not a null result, and it is the argument for the shipped
weights (`ml/reports/fusion_weights.md`) being set conservatively: at the shipped magnitude and a
±25% perturbation around it, churn stays in the 9–24% range on this synthetic test, well below the
44% seen at double the shipped weights — so the exact values chosen matter less than keeping the
overall magnitude moderate, which is the honest form claim C2's robustness can currently take.

## 5.13 Performance

**Table 5.19 — Assessment latency (⟨M-16⟩)**

Measured against the running local Docker stack (real trained model, real reputation-service
calls), 10 distinct domains. The cold pass is paced at one request per 16 seconds to stay under the
reputation service's 4-requests-per-minute free-tier limit, rather than measuring how quickly it
rejects an over-limit burst; the warm pass repeats the same domains immediately after, against the
one-hour TTL cache.

| Condition | p50 | p95 | Budget (NFR-01) | Result |
|---|---|---|---|---|
| Cold reputation cache | 1.148s | 1.593s | p95 ≤ 10s | **Met** |
| Warm reputation cache | 0.063s | 0.078s | p95 ≤ 1s | **Met** |

The roughly 20x gap between conditions is dominated by the external call, which carries a
five-second timeout — the strongest practical justification for the response cache: without it,
every assessment would sit in the cold-cache distribution regardless of how often a domain recurs.

**TC-P-02** verifies that signal collection does not delay rendering. The extension registers only
non-blocking listeners — `onCompleted` and `onBeforeRedirect` observe, they do not intercept — so no
request waits on extension code. Verified by inspection of the listener registrations and by
comparing page load timings with the extension enabled and disabled.

## 5.14 Security and privacy testing

**Table 5.20 — Security and privacy test cases**

| ID | Objective | Method | Expected | Actual | Status |
|---|---|---|---|---|---|
| **TC-SEC-01** | Permissions are minimal | Review each manifest permission against its use | Every permission traceable to a specific API call | `activeTab`, `storage`, `webRequest`, `webNavigation`, `tabs` — each mapped to a listener or call site | Pass |
| **TC-SEC-02** | Input validated at the boundary | Submit malformed bodies | 422 before any handler logic | As expected | Pass |
| **TC-SEC-03** | No credential in source control | Search history and working tree | Only an example file with placeholder values | Confirmed; real values supplied through the environment | Pass |
| **TC-SEC-04** | Data leaving the browser is bounded | Inspect the request body | URL and derived counts only; no page content, cookies or form data | Confirmed by inspection of the submitted payload | Pass |
| **TC-SEC-05** | No server-side fetch of the assessed URL | Review the service for outbound requests | The only outbound call is to the reputation service, with a domain, not the URL | Confirmed | Pass |
| **TC-M-01** | Every push is verified | Inspect CI configuration and history | Lint, tests and type-check run on every push | Both jobs green on `8378be5` | Pass |
| **TC-M-02** | Stack starts from one command | See TC-S-01 | — | — | Pass |

TC-SEC-04 deserves comment because it bears on the privacy claim in NFR-11. The extension transmits
the URL of the page and integer counts derived from its behaviour. It does not transmit page content,
form values, cookies or the list of requests. The URL itself is inherently sensitive — it is browsing
history — and Section 6.3 records this honestly rather than presenting the design as privacy-neutral.

## 5.15 End-to-end validation

**Design.** Thirty URLs, executed against the running local Docker stack via live `POST /analyze`
calls (real reputation-service lookups included): fifteen live phishing URLs sampled from the
OpenPhish public feed (`https://openphish.com/feed.txt`, fetched 13 August 2026, every 20th of 300
active entries taken for hosting-pattern diversity) — deliberately not PhishTank, the training
corpus's own source, to rule out any chance of overlap — and fifteen legitimate URLs, thirteen of
which carry deep paths. The deep-path weighting is not incidental — it targets precisely the blind
spot the original corpus created (§4.7.1).

Live deployment to the target hosting platforms (§4.2) requires provisioning external accounts and
was deferred to a later stage of the project, outside this submission's scope; this run exercises
the identical Docker image locally instead, since the detection-accuracy claim under test does not
depend on hosting location, only on the service running. `tests/e2e/system_test.md` records the
full method.

**Table 5.21 — End-to-end result (⟨M-17⟩)**

| Metric | Value | Acceptance |
|---|---|---|
| URLs assessed | 30 | — |
| Correctly classified | **20/30** | ≥ 26/30 — **not met** |
| False positives among deep-path legitimate URLs | **1/13** (`docs.python.org/3/library/asyncio.html`, 71%) | 0 — **not met** |
| Mean assessment latency | 0.070s | — |

**Table 5.22 — Confusion matrix, 30-URL run**

| | Predicted phishing | Predicted suspicious | Predicted legitimate |
|---|---|---|---|
| **Actually phishing** (15) | 10 | 2 | 3 |
| **Actually legitimate** (15) | 1 | 4 | 10 |

The per-URL record — URL, expected verdict, observed verdict, risk percentage and principal reason —
is tabulated in Appendix D.

**Neither acceptance criterion is met, and both misses are reported as measured rather than
adjusted.** The second criterion is the demanding one by design: twenty-six of thirty is achievable
with a mediocre but conservative detector, while zero false positives on popular deep-path URLs is
not, and it is the condition that actually determines whether the extension is usable in practice.
The single deep-path false positive was root-caused via SHAP rather than dismissed:
`docs.python.org/3/library/asyncio.html` was scored 71% phishing almost entirely on `num_digits = 1`
(the `3` in the Python version segment of the path, contributing +0.87 log-odds on its own) — a raw
digit *count* rather than a length-normalised ratio, so a single incidental digit in an otherwise
clean 46-character URL is enough to dominate the score. Three of the fifteen live phishing misses
follow the same brittleness in the opposite direction: `url_length` carries a strong *negative*
learned weight (Table 5.4's own audit shows it retains meaningful — if reduced — discriminative
power), which under-scores phishing URLs hosted on trusted free platforms (`vercel.app`,
`typedream.app`) whose URLs happen to be long. This is the same lexical-feature brittleness already
disclosed via the 8.5% false-positive rate in §5.11.1 and the 87.0% faithfulness result in §5.12.1,
reproducing here on live, previously-unseen data rather than appearing as a new defect. It was not
retrained against: doing so in response to a single digit collision observed on an n = 30
convenience sample would be statistically unsound, and would repeat, on a smaller and less rigorous
sample, the exact overfitting-to-the-measurement-instrument error the corpus rebuild in §4.7.1 was
written to correct. It is instead carried forward as a limitation in §6.3: **lexical URL features,
on their own, are not a sufficient basis for a false-positive rate low enough for unsupervised
production deployment**, and a length-normalised digit ratio in place of a raw count is identified
there as the most promising, currently-unimplemented fix.

## 5.16 Defect log

**Table 5.23 — Defect log**

| # | Description | Severity | Detected by | Status |
|---|---|---|---|---|
| D1 | Corpus separable on path presence rather than phishing | Critical | Audit script written after an implausible F1 | Resolved — corpus rebuilt, audit now a pipeline gate |
| D2 | Browser signals discarded before scoring | Critical | Code reading; no test detected it | Resolved — unknown keys raise; fusion layer added |
| D3 | Numerical library ABI break | Major | Import failure after a routine install | Resolved — exact upper bound with a stated reason |
| D4 | Artefact and column manifest out of step | Major | Manual inspection | Resolved — written together, arity asserted on load |
| D5 | Four silent routes to a heuristic verdict | Critical | Review against ADR-016 | Resolved — raises unless overridden; health endpoint added |
| D6 | Missing `webNavigation` permission | Major | All network signals reading zero | Resolved |
| D7 | Permission interception in the isolated world | Major | Analysis of execution contexts | Resolved — `permission_monitor.js` re-declared with `"world": "MAIN"` in the manifest, relayed to the isolated world via `CustomEvent`; automated cross-realm test added. Real-browser confirmation still pending (TC-S-10/11) |
| D8 | Permission signals arrive after assessment | Major | Sequence analysis | Resolved — `background.js` re-runs the assessment when a genuinely new permission flag arrives after the first pass already completed, rather than delaying every assessment for a signal window that usually produces nothing |
| D9 | Test suite passed locally, failed in CI | Minor | First CI execution | Resolved — import path configured for the bare runner |
| D10 | Asynchronous double on a synchronous method | Minor | Failing assertion | Resolved — the test was wrong, not the client |
| D11 | Deep-path false positive on live E2E run (§5.15) | Major | 30-URL end-to-end run | **Open** — root-caused to `num_digits` as a raw count rather than a length-normalised ratio; not retrained against an n = 30 sample (see §5.15's reasoning). Carried into §6.3 as a limitation |

D7 and D8 were both genuinely open earlier in the project and are recorded here as resolved rather
than silently corrected, because the permission signal family was reported non-functional for a real
stretch of the work. D7's automated coverage exercises the cross-world relay mechanism in a
simulated two-realm harness; it does not substitute for observing a real page's own
`Notification.requestPermission` call being intercepted, which is why TC-S-10/11 in §5.7 are still
marked pending a real-browser session rather than closed. D11 remains genuinely open — see §5.15 and
§6.3 for why it was deliberately not chased into a retrain.
