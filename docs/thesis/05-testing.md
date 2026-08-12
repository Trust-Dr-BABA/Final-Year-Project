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

**Pending.** Marked **⟨M-nn⟩** and listed in the register below. Each requires an execution of the
offline pipeline against the rebuilt corpus. A pending marker is not a placeholder for a plausible
number; it is a statement that the measurement has not yet been taken, and the register exists so
that no marker can reach a final submission unnoticed.

**Table 5.1 — Pending measurement register**

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

**Table 5.2 — Standalone discriminative power, original corpus** ⟨M-01⟩

| Feature | ROC-AUC alone | Mean (benign) | Mean (phishing) | Flagged |
|---|---|---|---|---|
| `url_length` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |
| `num_digits` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |
| `num_special_chars` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |
| `subdomain_depth` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |
| `has_https` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |
| `url_entropy` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |
| `has_ip_address` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |
| `suspicious_tld_flag` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |
| `brand_impersonation` | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ | ⟨M-01⟩ |

**Table 5.3 — Structural balance, original corpus** ⟨M-02⟩

| Property | Benign | Phishing |
|---|---|---|
| URLs with a non-trivial path | ⟨M-02⟩ | ⟨M-02⟩ |
| Mean path segments | ⟨M-02⟩ | ⟨M-02⟩ |
| Mean URL length | ⟨M-02⟩ | ⟨M-02⟩ |

*Expected shape of this result, stated in advance so that it constitutes a prediction rather than a
description: path presence near zero for the benign class and near total for the phishing class,
with `url_length` exceeding 0.90 AUC alone.* Recording the expectation before the run is what makes
the audit a test rather than an illustration.

### 5.4.3 Rebuilt corpus

The corpus was rebuilt with a path-bearing benign source so that both classes have realistic URL
structure. The ranking list was not discarded but repurposed as the false-positive holdout of
Section 5.11.

**Table 5.4 — Standalone discriminative power, rebuilt corpus** ⟨M-03⟩

| Feature | ROC-AUC alone | Δ vs original | Flagged |
|---|---|---|---|
| `url_length` | ⟨M-03⟩ | ⟨M-03⟩ | ⟨M-03⟩ |
| *(remaining features as Table 5.2)* | ⟨M-03⟩ | ⟨M-03⟩ | ⟨M-03⟩ |

**Table 5.5 — Structural balance, rebuilt corpus** ⟨M-04⟩

| Property | Benign | Phishing | Difference |
|---|---|---|---|
| URLs with a non-trivial path | ⟨M-04⟩ | ⟨M-04⟩ | ⟨M-04⟩ |

**Acceptance criteria for the rebuilt corpus:** no single feature above 0.90 AUC; path-presence rates
within 15 percentage points of each other; at least 15,000 rows with neither class below 40%.

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
| D2 — signals discarded | TC-U-22 | A vector containing a browser signal raises rather than dropping it | ⟨pending fusion layer⟩ |
| D2 — signals inert | TC-I-06 | Identical URL with adverse signals scores strictly higher | ⟨pending fusion layer⟩ |
| D4 — artefact drift | TC-U-23 | Loading a model whose arity ≠ manifest length raises, reporting both | Pass |
| D5 — silent fallback | TC-U-17 | Missing artefact raises without the override | Pass |
| D1 — corpus artefact | Audit gate | No feature exceeds 0.90 AUC alone | ⟨M-03⟩ |

## 5.6 Integration testing

**Table 5.9 — Integration test cases**

| ID | Objective | Precondition | Input | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| **TC-I-01** | Assessment returns a conforming response | Collaborators doubled, session doubled | Valid URL, no signals | 200; `scan_id`, `verdict`, `risk_score`, `confidence_pct`, `top_reasons`, `flagged_rules` all present and correctly typed | As expected | Pass |
| **TC-I-02** | Malformed URL rejected at the boundary | — | `"not-a-url"` | 422, field named, no record written | As expected | Pass |
| **TC-I-03** | Negative count rejected | — | `tracker_count: -1` | 422 | As expected | Pass |
| **TC-I-04** | Reputation failure does not alter the verdict | Reputation double raises | Fixed URL, fixed signals | Same verdict and score as the success case; corroboration shows sentinels | As expected | Pass |
| **TC-I-05** | Model unavailable yields 503 | No artefact, override unset | Valid URL | 503; no record written | As expected | Pass |
| **TC-I-06** | Adverse signals raise the score | Fusion layer active | Same URL, clean vs adverse signals | Adverse strictly greater; at least one browser signal present in `top_reasons` | — | ⟨pending fusion layer⟩ |
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
| **TC-S-10** | Interstitial raised only on the phishing band | Fusion and model active | Navigate a known phishing URL, then a benign one | Overlay on the first, none on the second | — | ⟨pending trained model⟩ |
| **TC-S-11** | Dismissal does not persist | TC-S-10 complete | Dismiss, then re-navigate to the same URL | Warning raised again | — | ⟨pending trained model⟩ |

TC-S-06 through TC-S-09 form a useful chain. TC-S-08 confirms the system refuses to invent a verdict;
TC-S-09 confirms that the refusal is configuration rather than breakage; and TC-S-07 confirms that
the signals measured in the browser genuinely reached the reasoning layer, which is the empirical
counterpart to the defect in Section 4.7.2.

The observed value of 11 tracker domains in TC-S-06 also validates the threshold choice in
Algorithm 4.4 from the other direction: a mainstream commercial site sits just above the
`excessive_trackers` boundary, which is where a threshold intended to mark "unusually many" ought to
sit.

## 5.8 Corpus composition

**Table 5.11 — Corpus composition** ⟨M-05⟩

| Property | Value |
|---|---|
| Total rows | ⟨M-05⟩ |
| Phishing rows | ⟨M-05⟩ |
| Benign rows | ⟨M-05⟩ |
| Class balance | ⟨M-05⟩ |
| Distinct registrable domains | ⟨M-05⟩ |
| Submission date range | ⟨M-05⟩ |
| Temporal split boundary | ⟨M-05⟩ |

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

**Table 5.12 — Detection performance by protocol** ⟨M-06⟩ ⟨M-07⟩ ⟨M-08⟩

| Protocol | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| Random split | ⟨M-06⟩ | ⟨M-06⟩ | ⟨M-06⟩ | ⟨M-06⟩ |
| Temporal split | ⟨M-07⟩ | ⟨M-07⟩ | ⟨M-07⟩ | ⟨M-07⟩ |
| Unseen registrable domain | ⟨M-08⟩ | ⟨M-08⟩ | ⟨M-08⟩ | ⟨M-08⟩ |

**Table 5.13 — Confusion matrix, temporal split** ⟨M-09⟩

| | Predicted phishing | Predicted legitimate |
|---|---|---|
| **Actually phishing** | ⟨M-09⟩ | ⟨M-09⟩ |
| **Actually legitimate** | ⟨M-09⟩ | ⟨M-09⟩ |

The temporal figure is the headline result of this project. Where it falls below the random-split
figure, the gap is itself a finding: it quantifies how much of an apparently strong random-split
result comes from campaign overlap rather than genuine generalisation.

## 5.10 Baseline comparison

Claim C1 asserts that the system generalises beyond a blocklist. That is an empirical claim about a
comparison, so the comparison is made explicitly.

**Table 5.14 — Baseline comparison under the temporal split** ⟨M-10⟩

| # | Configuration | Precision | Recall | F1 | Notes |
|---|---|---|---|---|---|
| B1 | Blocklist lookup against the training set | ⟨M-10⟩ | ⟨M-10⟩ | ⟨M-10⟩ | Perfect precision by construction; recall bounded by overlap |
| B2 | `url_length` threshold only | ⟨M-10⟩ | ⟨M-10⟩ | ⟨M-10⟩ | Included to demonstrate the D1 artefact is gone |
| B3 | Logistic regression, same features | ⟨M-10⟩ | ⟨M-10⟩ | ⟨M-10⟩ | Linear reference |
| B4 | XGBoost, URL features only | ⟨M-10⟩ | ⟨M-10⟩ | ⟨M-10⟩ | The model without fusion |
| B5 | Full fused system | ⟨M-10⟩ | ⟨M-10⟩ | ⟨M-10⟩ | As deployed |

Two comparisons carry the argument. **B5 against B1, restricted to URLs absent from the blocklist,**
is the direct quantitative answer to "why not just use a blocklist" — B1's recall on that subset is
zero by definition, so any non-zero recall from B5 is generalisation the blocklist cannot provide.
**B5 against B4** isolates the contribution of the browser signals and is therefore the measurement
that substantiates claim C2.

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

**Table 5.15 — False positives, popular deep-path holdout** ⟨M-11⟩

| Metric | Value |
|---|---|
| URLs evaluated | ⟨M-11⟩ |
| Classified *phishing* | ⟨M-11⟩ |
| Classified *suspicious* | ⟨M-11⟩ |
| False-positive rate (phishing band) | ⟨M-11⟩ |

### 5.11.2 Calibration

The interface asserts a confidence percentage. Calibration is the evidence that the number means
anything: among pages assigned roughly 0.8, close to 80% should be phishing.

**Table 5.16 — Calibration** ⟨M-12⟩

| Metric | Value | Interpretation |
|---|---|---|
| Brier score | ⟨M-12⟩ | Mean squared error of the probability; lower is better |
| Expected calibration error | ⟨M-12⟩ | Mean gap between confidence and accuracy across bins |
| Bins used | 10, equal width | — |

⟨M-13⟩ — reliability diagram, predicted probability against observed frequency, with the diagonal
marked.

Where calibration is poor, Platt scaling or isotonic regression is fitted on a validation partition —
never on the test partition — and the before-and-after figures are both reported.

Without this section the phrase "94% confident" in the interface would be decoration, and an examiner
would be entitled to say so.

## 5.12 Explanation faithfulness and sensitivity

### 5.12.1 Faithfulness

Claim C3 asserts that the stated reasons are the operative ones. This is testable by intervention:
neutralise the reasons the system gave, and see whether the score moves as they predicted.

**Procedure.** For each of *N* test URLs: record the score and the three highest-ranked
contributions; set those three features to their training medians; re-score; compare the observed
change against the sum of the three attributions.

**Table 5.17 — Explanation faithfulness** ⟨M-14⟩

| Metric | Value | Acceptance |
|---|---|---|
| URLs evaluated | ⟨M-14⟩ | — |
| Directional agreement | ⟨M-14⟩ | ≥ 90% |
| Mean absolute error, predicted vs observed shift | ⟨M-14⟩ | — |

Exact agreement is not expected and its absence is not a failure. SHAP attributes a specific
prediction under a specific feature distribution; intervening on three features simultaneously moves
the input off that distribution, and tree ensembles are not additive in the input. Directional
agreement is the meaningful criterion, and the magnitude error quantifies the interaction effects.

### 5.12.2 Fusion weight sensitivity

The fusion weights are set by hand (ADR-014), which obliges the work to show that conclusions do not
rest on their precise values.

**Table 5.18 — Fusion weight sensitivity** ⟨M-15⟩

| Perturbation | Verdict changes | F1 change |
|---|---|---|
| All weights ×0.5 | ⟨M-15⟩ | ⟨M-15⟩ |
| All weights ×2.0 | ⟨M-15⟩ | ⟨M-15⟩ |
| Tracker weight only, ×0 | ⟨M-15⟩ | ⟨M-15⟩ |
| Each weight ±25%, one at a time | ⟨M-15⟩ | ⟨M-15⟩ |

## 5.13 Performance

**Table 5.19 — Assessment latency** ⟨M-16⟩

| Condition | p50 | p95 | Budget (NFR-01) |
|---|---|---|---|
| Cold reputation cache | ⟨M-16⟩ | ⟨M-16⟩ | p95 ≤ 10 s |
| Warm reputation cache | ⟨M-16⟩ | ⟨M-16⟩ | p95 ≤ 1 s |

The gap between the two conditions is dominated by the external call, which carries a five-second
timeout. This is the strongest justification for the response cache: without it, every assessment
would sit in the cold-cache distribution.

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

**Design.** Thirty URLs: fifteen live phishing URLs drawn from a current feed, and fifteen legitimate
URLs of which at least ten carry deep paths. The deep-path requirement is not incidental — it targets
precisely the blind spot the original corpus created.

**Table 5.21 — End-to-end result** ⟨M-17⟩

| Metric | Value | Acceptance |
|---|---|---|
| URLs assessed | 30 | — |
| Correctly classified | ⟨M-17⟩ | ≥ 26/30 |
| False positives among deep-path legitimate URLs | ⟨M-17⟩ | 0 |
| Mean assessment latency | ⟨M-17⟩ | — |

The per-URL record — URL, expected verdict, observed verdict, risk percentage, principal reason and
outcome — is tabulated in Appendix D.

The second acceptance criterion is the demanding one. Twenty-six of thirty is achievable with a
mediocre detector that happens to be conservative; zero false positives on popular deep-path URLs is
not, and it is the condition that determines whether the extension is usable in practice.

## 5.16 Defect log

**Table 5.22 — Defect log**

| # | Description | Severity | Detected by | Status |
|---|---|---|---|---|
| D1 | Corpus separable on path presence rather than phishing | Critical | Audit script written after an implausible F1 | Resolved — corpus rebuilt, audit now a pipeline gate |
| D2 | Browser signals discarded before scoring | Critical | Code reading; no test detected it | Resolved — unknown keys raise; fusion layer added |
| D3 | Numerical library ABI break | Major | Import failure after a routine install | Resolved — exact upper bound with a stated reason |
| D4 | Artefact and column manifest out of step | Major | Manual inspection | Resolved — written together, arity asserted on load |
| D5 | Four silent routes to a heuristic verdict | Critical | Review against ADR-016 | Resolved — raises unless overridden; health endpoint added |
| D6 | Missing `webNavigation` permission | Major | All network signals reading zero | Resolved |
| D7 | Permission interception in the isolated world | Major | Analysis of execution contexts | **Open** — requires main-world injection |
| D8 | Permission signals arrive after assessment | Major | Sequence analysis | **Open** — requires bounded wait or re-assessment |
| D9 | Test suite passed locally, failed in CI | Minor | First CI execution | Resolved — import path configured for the bare runner |
| D10 | Asynchronous double on a synchronous method | Minor | Failing assertion | Resolved — the test was wrong, not the client |

D7 and D8 are recorded as open. Both affect the permission signal family, which is therefore
non-functional in the current build. Presenting it as working would misrepresent the system, and the
limitation is carried forward into Section 6.3.
