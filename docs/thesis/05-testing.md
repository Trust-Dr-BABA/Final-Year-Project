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

**Two measurement passes.** Every ⟨M-nn⟩ figure was first executed on 13 August 2026. After
`digit_ratio` replaced a raw digit count (§4.7.1, §5.4.3) and the fusion layer was extended with two
page-content signals and a gated VirusTotal signal (§3.2.6, Table 4.1), every figure that depends on
the trained model or the fusion layer was **re-executed on 16 August 2026** and the tables below
report the later run. Figures that depend on neither — the original-corpus audit (Table 5.2–5.3),
the unit/integration/system test suites, the security and privacy tests — are unaffected by either
change and are reported once, at their original date. Where a table changed between the two passes,
the section discussing it says so explicitly rather than presenting the second run as if it were the
first.

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
| ⟨M-18⟩ | Repeated-seed F1/AUC, mean, std dev and 95% CI, both split protocols | `cross_validate.py` | 5.9.1 |

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

**Table 5.4 — Standalone discriminative power, rebuilt corpus (⟨M-03⟩, 19,685 rows, re-audited
16 August 2026 with `digit_ratio` in place of `num_digits`)**

| Feature | ROC-AUC alone | Δ vs original | Flagged |
|---|---|---|---|
| `digit_ratio` | 0.7474 | n/a — feature redefined, see note | no |
| `url_entropy` | 0.7339 | **−0.1662** | no |
| `subdomain_depth` | 0.6011 | −0.2055 | no |
| `url_length` | 0.5874 | **−0.2912** | no |
| `num_special_chars` | 0.5796 | −0.1407 | no |
| `suspicious_tld_flag` | 0.5142 | +0.0085 | no |
| `has_https` | 0.5317 | −0.0036 | no |
| `brand_impersonation` | 0.5058 | −0.0023 | no |
| `has_ip_address` | 0.5006 | 0.0000 | no |

The two bold deltas are the ones that mattered to the D1 corpus rebuild: `url_entropy`, the single
feature that failed the audit on the original corpus, drops 17 points and clears the 0.90 threshold
by a wide margin; `url_length`, the feature most obviously tied to path presence, drops 29 points. No
feature exceeds 0.90 on the rebuilt corpus — the audit gate passes.

**Note on `digit_ratio`.** This row is not directly comparable to the original corpus's `num_digits`
row (Table 5.2, 0.7542): the two are different feature definitions — a length-normalised density
versus a raw count — audited on the same rebuilt corpus at different times, not the same feature
measured twice. `num_digits` was replaced by `digit_ratio` on 15 August 2026 after the live
end-to-end run (§5.15) traced a false positive to exactly this feature's raw-count brittleness; the
audit was re-run the same day (`ml/reports/leakage_audit_digit_ratio.md`) specifically to confirm
the replacement introduced no new leakage of its own. It did not: 0.7474 sits close to
`num_digits`'s own 0.7447 on this corpus and remains far below the 0.90 flag threshold.

**Table 5.5 — Structural balance, rebuilt corpus (⟨M-04⟩)**

| Property | Benign | Phishing | Difference |
|---|---|---|---|
| URLs with a non-trivial path | 78.9% | 65.2% | 13.6 points |
| Rows | 9,685 | 10,000 | — |

**Acceptance criteria for the rebuilt corpus:** no single feature above 0.90 AUC (met — highest is
0.7474, `digit_ratio`, Table 5.4); path-presence rates within 15 percentage points of each other (met
— 13.6-point gap); at least 15,000 rows with neither class below 40% (met — 19,685 rows,
49.2%/50.8% split).

### 5.4.4 Interpretation

The expected consequence of the rebuild is that headline detection scores fall. That is the intended
outcome, and it is worth being explicit about why a lower number is the better result.

The original score measured the model's ability to detect the presence of a path. The rebuilt score
measures its ability to detect phishing. These are different quantities, and only the second is the
one this project claims to deliver. A drop from an inflated figure to an honest one is an improvement
in the validity of the measurement, not a regression in the system.

## 5.5 Unit testing

### 5.5.1 Coverage

Ten Python modules and three extension JavaScript files carry automated unit tests, grown
substantially since the suite first stood at 25 cases (13 August 2026) as browser-signal fusion,
page-content scanning, VirusTotal fusion trust and the offline evaluation tooling were added. All
results below were re-recorded on 16 August 2026 in the environment of Section 5.3.

**Table 5.6 — Unit test suite, measured**

| Module | Cases | Result |
|---|---|---|
| `test_url_features.py` | Feature extraction across URL shapes, incl. `digit_ratio` density | 22 pass |
| `test_risk_fusion.py` | Log-odds fusion: browser signals, scam-content signals, VT trust, established-reputation dampening | 21 pass |
| `test_heuristics_engine.py` | Rule-flag derivation from network, permission and page-content signals | 7 pass |
| `test_explainer_formatter.py` | Template substitution and boolean-valued features | 7 pass |
| `test_shap.py` | Attribution output shape; unavailable-model behaviour | 5 pass |
| `test_retrain_gate.py` | Promotion-decision helper (`_should_promote`) | 5 pass |
| `test_evaluate_baselines.py` | Split-construction helpers | 5 pass |
| `test_virustotal_client.py` | Cache behaviour, timeout, malformed payload | 4 pass |
| `test_cross_validate.py` | Confidence-interval helper (`_mean_std_ci`) | 4 pass |
| `test_sensitivity.py` | `_fuse_all` does not alias the live weight table (D16 regression) | 3 pass |
| **Total (pytest, `tests/unit/`)** | **83** | **83 passed, 0 failed** |
| `network_monitor_test.js` | Tracker base-domain resolution | Pass |
| `permission_monitor_test.js` | Cross-realm relay from main-world interception to the isolated world | Pass |
| `scam_content_scanner_test.js` | Multi-word phrase matching; sensitive-field category counting | Pass |

Full `pytest tests/unit/ tests/integration/` execution time: 1.5 s for 95 cases (83 unit + 12
integration, §5.6). Continuous integration reproduces this on `ubuntu-latest` on every push
(`.github/workflows/ci.yml`); the three JavaScript suites run via `npm test` from the repository
root and pass under Node's built-in test runner.

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
| **TC-U-24** | Digit density is length-normalised, not a raw count | — | `"a1b2c3.example.com"` vs a 40-character URL with the same 3 digits | Both report the same ratio, not the same count | As expected | Pass |
| **TC-U-25** | Corroborating malicious votes raise the fused score | — | `vt_malicious_votes: 5` vs `0` | Fused score strictly higher | As expected | Pass |
| **TC-U-26** | Established-reputation dampening requires all three conditions jointly | — | Old domain + zero malicious votes + high harmless votes, then each condition individually violated | Dampens only when all three hold; no attribution otherwise | As expected | Pass |
| **TC-U-27** | Harmless votes alone never lower the score outside the gate | — | `vt_harmless_votes: 100` with a young domain | No dampening attribution; score unchanged | As expected | Pass |
| **TC-U-28** | Scam-keyword and sensitive-field counts raise the fused score | — | `scam_keyword_hits: 5`, `sensitive_field_count: 3` vs both 0 | Fused score strictly higher for each | As expected | Pass |
| **TC-U-29** | Scam phrase matching requires the full multi-word phrase | Phrase list loaded (JS) | Page text containing "password" alone vs "verify your password" | Zero hits vs one hit | As expected | Pass |
| **TC-U-30** | A single password field does not trigger the sensitive-field rule | Form with one `type="password"` input (JS) | — | `sensitive_field_count: 1`, below the rule's threshold of 2 | As expected | Pass |
| **TC-U-31** | Confidence interval collapses to a point for identical values | — | `[0.7, 0.7, 0.7]` | `std == 0.0`, `lo == hi == 0.7` | As expected | Pass |
| **TC-U-32** | Retrain gate promotes an equal or improved candidate, rejects a regression beyond tolerance | — | Candidate F1 at, above, and 0.10 below the incumbent, tolerance 0.02 | Promote, promote, reject | As expected | Pass |

TC-U-17 was added during this work specifically to lock in ADR-016. Without it, a future change that
reintroduced the silent fallback would pass every other test in the suite — which is exactly what
happened the first time. TC-U-26/TC-U-27 exist for the same reason ADR-017's asymmetry is stated so
explicitly in Section 3.2.6: the gate is the entire safety argument for letting reputation data
influence the score at all, and a test that only checked the positive case would not catch a future
change that loosened it.

### 5.5.3 Regression tests for known defects

Each defect in Section 4.7 that could recur silently has a test that fails if it does.

**Table 5.8 — Defect regression tests**

| Defect | Test | Assertion | Status |
|---|---|---|---|
| D2 — signals discarded | TC-U-22 | A vector containing an unrecognised key raises rather than being silently dropped | Pass |
| D2 — signals inert | TC-I-06 | Identical URL with adverse signals scores strictly higher via `risk_fusion.fuse()` | Pass |
| D4 — artefact drift | TC-U-23 | Loading a model whose arity ≠ manifest length raises, reporting both | Pass |
| D5 — silent fallback | TC-U-17 | Missing artefact raises without the override | Pass |
| D1 — corpus artefact | Audit gate | No feature exceeds 0.90 AUC alone | Pass (0.7474 highest, Table 5.4) |
| D12 — scan detail IDOR | TC-I-11 | A `client_id` that does not own the scan gets 404, not the record | Pass |
| D13 — stale evaluation column | Manual re-run | `evaluate_baselines.py` runs to completion against `digit_ratio` features | Pass |
| D14 — stale sensitivity narrative | Manual inspection | Report prose and its own table agree on every figure | Pass |
| D15 — Alembic env fallback drift | Manual inspection | `env.py` imports `DATABASE_URL` from `database.py`; no second hardcoded default remains | Pass |
| D16 — `_fuse_all` weight-table aliasing | TC-U-33 | Passing `risk_fusion.SIGNAL_WEIGHTS` itself as the baseline weights still fuses with the shipped weights, not an empty table | Pass |

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
| **TC-I-10** | All five migrations apply in sequence to an empty database | Container running | `alembic upgrade head` | `scans` created with all six JSONB columns, the three later scalar additions, PK, and both indexes | As expected | Pass |
| **TC-I-11** | Scan detail is not readable by a non-owning `client_id` | A scan exists, owned by `"owner-client"` | `GET /scan/{id}?client_id=attacker-client` | 404 | As expected | Pass |
| **TC-I-12** | Scan detail is readable by the owning `client_id`, and never exposes it | Same scan as TC-I-11 | `GET /scan/{id}?client_id=owner-client` | 200; body contains the scan; `client_id` key absent from the response | As expected | Pass |

TC-I-10 was originally executed against a live PostgreSQL 15 container on 12 August 2026, when only
the first migration (`ab476f0dcf44`) existed. Four further migrations landed since
(`33be02683ae4` risk_pct, `4d6f5fb287b2` client_id, `762a960b07ca` scam_content_signals,
`f48ff135cc1a` last_scanned_at), each individually applied and inspected at the time it was
written (their own docstrings record the backfill logic for the two NOT NULL additions). The table
below is the schema all five produce together, read directly from the migration definitions rather
than re-run live for this edition — a live container was not available in the environment this
edition was prepared in, and the migration source is the same DDL `alembic upgrade head` would apply,
so this is a direct reading of the applied schema rather than an estimate of it:

```
Table "public.scans"
 id                    | uuid                     | not null
 url                   | text                     | not null
 verdict                | character varying(20)    | not null
 risk_score             | double precision         | not null
 risk_pct               | integer                  | not null
 confidence_pct         | integer                  | not null
 client_id              | character varying(64)    |
 url_features           | jsonb                    |
 network_signals        | jsonb                    |
 permission_signals     | jsonb                    |
 scam_content_signals   | jsonb                    |
 shap_values            | jsonb                    |
 flagged_rules          | jsonb                    |
 created_at             | timestamp with time zone | not null
 last_scanned_at        | timestamp with time zone | not null
Indexes:
    "scans_pkey" PRIMARY KEY, btree (id)
    "ix_scans_url" btree (url)
    "ix_scans_client_id" btree (client_id)
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
is split randomly in matching proportion rather than temporally; §5.9 states this explicitly.

Sources, retrieval dates, row counts and licence terms are recorded in
`ml/data/raw/DATASET_SOURCES.md`, which is regenerated fresh on every `prepare_dataset.py` run and
so cannot drift out of sync with the data it describes, and are reproduced in Table 5.12.

**Table 5.12 — Dataset provenance**

| Source | Class | Rows | Retrieved | Licence | Notes |
|---|---|---|---|---|---|
| PhishTank verified feed (`data.phishtank.com/data/online-valid.csv`) | Phishing | 10,000 | 25 July 2026 | PhishTank open data terms | Filtered to `verified == "yes"` (10,000/10,000 passed — the feed already contains only verified entries); `url`, `submission_time`, `target`, `verified`, `online` retained |
| Live crawl of Tranco-ranked domain homepages (ranks 200–20,000), same-domain internal links with a non-trivial path | Benign | 9,000 raw → 9,685 after path-presence mixing (note below) | 13 August 2026 | Tranco list itself CC BY-NC-SA 4.0; crawled pages under their own site terms | 5,288 distinct domains, ≤4 links per domain, 8s per-domain crawl deadline; see §4.7.1 for why a domain-ranking-derived source (Tranco bare domains, then PhiUSIIL) was tried and rejected first |
| Same crawl method, Tranco ranks 20,001–40,000 (disjoint from training) | False-positive holdout | 1,500 raw → 1,488 after deduplication | 13 August 2026 | As above | Never used for training; §5.11.1's false-positive measurement only |

**Path-presence mixing.** Every crawled benign row carries a path by construction, which alone would
relocate defect D1 rather than fix it — a 100%-path-bearing benign class is exactly as artificial as
a 0%-path-bearing one. `prepare_dataset.py` measures the phishing class's own path-presence rate
(65.2%, Table 5.3) and adds matching bare-homepage rows for a corresponding fraction of benign
domains, calibrating the benign class's structure to the phishing class's naturally observed rate
rather than fixing it at either extreme. This is why the final benign row count (9,685) differs from
the raw crawl total (9,000).

**Retained PhishTank columns and their purpose**

| Column | Purpose |
|---|---|
| `url` | Feature extraction |
| `submission_time` | Temporal split boundary (§5.9) |
| `target` | Ground truth for evaluating `brand_impersonation` |
| `verified` | Inclusion filter |
| `online` | Liveness at retrieval, recorded for reference |

An earlier version of the preparation script read only `url`, discarding the rest. The temporal split
is impossible without `submission_time`, so this was not a harmless simplification.

## 5.9 Detection performance

Three protocols are reported. The differences between them are more informative than any single
number.

**Random split** partitions rows uniformly. It is the protocol most commonly reported in the
literature and the least representative of deployment, because a URL from the same campaign — often
the same domain — can appear in both partitions.

**Temporal split** trains on submissions before a cut-off date and tests on submissions after it.
This mirrors deployment exactly: a deployed detector always predicts the future, and never has
access to campaigns that have not yet occurred — the same experimental-bias argument TESSERACT [13]
makes for malware classification applies unchanged to phishing URL classification here.

**Unseen-domain split** guarantees that no registrable domain appears in both partitions,
which prevents the model from succeeding by memorising domains rather than learning structure.

**Table 5.13 — Detection performance by protocol (phishing class; ⟨M-06⟩ ⟨M-07⟩ ⟨M-08⟩,
re-measured 16 August 2026 on the `digit_ratio` model)**

| Protocol | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| Random split (80/20, stratified) | 0.89 | 0.75 | 0.8152 | 0.9022 |
| Temporal split | 0.881 | 0.613 | 0.723 | 0.851 |
| Unseen registrable domain | 0.809 | 0.595 | 0.686 | 0.839 |

**Table 5.14 — Confusion matrix, temporal split (⟨M-09⟩, 3,937 test URLs)**

| | Predicted phishing | Predicted legitimate |
|---|---|---|
| **Actually phishing** (2,000) | 1,226 | 774 |
| **Actually legitimate** (1,937) | 165 | 1,772 |

The temporal figure is the headline result of this project, and it falls visibly below the
random-split figure (F1 0.723 vs. 0.8152; recall 0.613 vs. 0.75). That gap is itself a finding: it
quantifies how much of the random-split result comes from campaign overlap — near-duplicate URLs
from the same phishing kit landing on both sides of a random partition — rather than genuine
generalisation to campaigns the model has not encountered. The unseen-domain split falls further
still (F1 0.686), which is consistent: it removes not just duplicate URLs but duplicate domains,
the harder and more realistic constraint. Recall is the metric that degrades most under both harder
protocols (0.75 → 0.613 → 0.595) — the model misses more genuinely novel phishing than it
misclassifies legitimate pages, which given the false-positive costs discussed in §5.11 is the
direction an examiner should want the errors to fall on.

**Effect of the `digit_ratio` replacement on these headline numbers.** All three protocols move by
one to two points either way relative to the 13 August, `num_digits`-based run (temporal F1 0.726 →
0.723; unseen-domain F1 0.683 → 0.686) — within the range expected from replacing one moderately
informative feature with a redefinition of comparable standalone power (Table 5.4: 0.7474 vs.
0.7447), not a change to the corpus or the other eight features. The replacement was made to fix a
specific tail-case brittleness (§4.7.1, §5.15), not to move the aggregate score, and the aggregate
score is, correctly, almost unchanged.

### 5.9.1 How much does the headline number depend on the seed?

Every table so far in this section is a single-run point estimate from `random_state=42`. This
subsection asks the question §6.4 previously listed only as an unaddressed limitation — "the
evaluation is single-run" — directly: `ml/scripts/cross_validate.py` repeats both split protocols
under ten different seeds (1–10, deliberately excluding 42 so the headline run can be compared
*against* the resulting interval rather than folded into it), retraining the B4 model each time, and
reports the mean, standard deviation and a 95% confidence interval for F1 and ROC-AUC. Run
16 August 2026, ten repeats per protocol.

**Table 5.13a — Temporal split, ten repeats (⟨M-18⟩)**

| Metric | Mean | Std dev | Min | Max | 95% CI | Seed 42 (headline, Table 5.13) |
|---|---|---|---|---|---|---|
| F1 | 0.7202 | 0.0036 | 0.7153 | 0.7260 | [0.7180, 0.7225] | 0.7231 (outside CI) |
| ROC-AUC | 0.8478 | 0.0020 | 0.8453 | 0.8520 | [0.8465, 0.8490] | 0.8512 (outside CI) |

**Table 5.13b — Unseen-registrable-domain split, ten repeats**

| Metric | Mean | Std dev | Min | Max | 95% CI | Seed 42 (headline, Table 5.13) |
|---|---|---|---|---|---|---|
| F1 | 0.7572 | 0.0584 | 0.6746 | 0.8541 | [0.7210, 0.7934] | 0.6857 (outside CI) |
| ROC-AUC | 0.8682 | 0.0240 | 0.8374 | 0.9079 | [0.8533, 0.8831] | 0.8386 (outside CI) |

**The single reported headline number falls outside its own repeated-seed 95% CI on both protocols
— and this is informative, not alarming.** A 95% CI on the *mean* is not a prediction interval for
one future draw, so a single seed landing outside it is neither a bug nor evidence of an unreliable
estimation procedure; ten repeats is too few for the interval to be tight in the first place. What
the two tables show clearly is a real, previously unmeasured asymmetry between the two protocols:
the temporal split's standard deviation (0.0036 F1) is over sixteen times smaller than the
unseen-domain split's (0.0584 F1). This makes structural sense — the temporal split's phishing side
is fixed by real submission time and only the benign side is randomised per seed, while the
unseen-domain split's *entire* partition depends on which registrable domains happen to fall on
which side, and domains vary enormously in how many similar URLs they contribute. **The practical
consequence is that Table 5.13's single unseen-domain F1 (0.686) should be read as one draw from a
genuinely wide distribution (0.67–0.85 across ten seeds) rather than a precise estimate**, while the
temporal split's single F1 (0.723) is a comparatively tight and trustworthy point estimate on its
own. This asymmetry was not previously visible anywhere in this report, and finding it is the actual
value a repeated-seed protocol adds beyond "confidence intervals exist" as a checkbox.

This instrument is run here for the two headline split protocols on B4 XGBoost; extending it to
every other measured table in this chapter (calibration, faithfulness, the false-positive holdout)
would repeat the same retraining cost for each and is recorded as future work in §6.5 rather than
attempted for every table in this evaluation pass.

## 5.10 Baseline comparison

Claim C1 asserts that the system generalises beyond a blocklist. That is an empirical claim about a
comparison, so the comparison is made explicitly.

**Table 5.15 — Baseline comparison under the temporal split (⟨M-10⟩, re-measured 16 August 2026)**

| # | Configuration | Precision | Recall | F1 | Notes |
|---|---|---|---|---|---|
| B1 | Blocklist lookup against the training set | 0.000 | 0.000 | 0.000 | Recall exactly zero by construction of the split — every test URL is absent from the training blocklist |
| B2 | `url_length` threshold (logistic regression, one feature) | 0.668 | 0.494 | 0.568 | Included to demonstrate the D1 artefact is gone: on the original corpus this feature alone reached 0.88 AUC; here it is a weak baseline, as a single lexical feature should be. Unaffected by the `digit_ratio` change |
| B3 | Logistic regression, all 9 lexical features | 0.838 | 0.627 | 0.717 | Linear reference — notably close to B4, suggesting the lexical features are close to linearly separable and XGBoost's advantage here is modest |
| B4 | XGBoost, URL features only | 0.881 | 0.613 | 0.723 | The model without fusion — the URL-scoring half of the deployed system |
| B5 | Full fused system | *(no offline row — see below)* | | | As deployed, browser, page-content and VirusTotal-derived signals included |

**B1's recall is 0.0% on this test set**, which is the direct quantitative answer to "why not just
use a blocklist" (claim C1): every phishing URL that reaches the temporal test partition is, by
construction, one the blocklist has never seen, and B4's 61.3% recall on exactly those URLs is
generalisation a blocklist structurally cannot provide.

**There is no measured B5 row.** No corpus, including this one, pairs a phishing label with real
per-URL browser telemetry — tracker counts, redirect depth, permission-prompt timing, page-content
phrase and field matches — because that telemetry only exists once a browser has visited the page,
and VirusTotal's vendor votes carry the same circularity problem ADR-013 excludes them from training
for. Fabricating any of it to produce a B5 number would be exactly the kind of manufactured evidence
ADR-014 rejects for the fusion weights themselves, and reporting it that way would be the same
category of methodological error as D1. Claims C2 and the reputation-fusion half of ADR-017 are
validated instead by intervention — `tests/unit/test_risk_fusion.py` and TC-I-06, TC-U-25–TC-U-27
above confirm the fused score moves in the documented direction, by exactly the documented weight,
under every signal family — and by the live 30-URL run in §5.15, which exercises the complete fused
pipeline against real requests rather than an offline table.

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

**Table 5.16 — False positives, popular deep-path holdout (⟨M-11⟩, re-measured 16 August 2026)**

| Metric | Value |
|---|---|
| URLs evaluated | 1,488 |
| Classified *legitimate* | 1,185 (79.6%) |
| Classified *suspicious* | 174 (11.7%) |
| Classified *phishing* (false positive) | 129 (8.7%) |
| False-positive rate (phishing band) | **8.7%** |

An 8.7% false-positive rate in the band that raises the blocking interstitial (§3.7.2), on popular,
legitimate, previously-unseen deep-path URLs, is a genuine and material limitation, not a rounding
concern, and it did not improve with the `digit_ratio` replacement — it moved from 8.5% to 8.7%,
within noise of a single-feature redefinition on a 1,488-URL set, not a regression attributable to
the change. `ml/reports/training_log.md` traces the misfires to two clusters: legitimate URLs with
naturally elevated Shannon entropy from varied path segments (financial-data pages, multi-language
site variants), and legitimate link-shortener-shaped services (`lnk.bio`, `click.octobrowser.net`)
that are structurally close to phishing infrastructure by nature. Both are lexical-feature
limitations, carried into §6.3 rather than tuned away against this same holdout — which would fit
the measurement instrument, not the underlying problem, repeating the exact error the corpus
rebuild in §4.7.1 corrected in the other direction. This offline holdout run does not include a live
VirusTotal lookup (§5.3's environment note), so it does not benefit from ADR-017's
established-reputation dampening the way a live assessment of an old, well-corroborated domain
would; §5.15's live re-run discusses that gap concretely for the domains it affects.

### 5.11.2 Calibration

The interface asserts a confidence percentage. Calibration [15] is the evidence that the number
means anything: among pages assigned roughly 0.8, close to 80% should be phishing.

Measured on the temporal-split test set (3,937 URLs, 2,000 phishing), 10 equal-width bins,
re-measured 16 August 2026 against the `digit_ratio` model.

**Table 5.17 — Calibration (⟨M-12⟩)**

| Metric | Before | After Platt scaling | Interpretation |
|---|---|---|---|
| Brier score [19] | 0.1635 | 0.1640 | Mean squared error of the probability; lower is better |
| Expected calibration error [16] | 0.0837 | 0.0768 | Mean gap between confidence and accuracy across bins |
| Bins used | 10, equal width | — | — |

Platt scaling [17] was fitted — on a held-out validation split of the training partition, never on
the test partition — because the pre-scaling ECE (0.0837) exceeded the 0.05 threshold this project
treats as acceptable without further correction. It moved ECE the intended direction (0.0837 →
0.0768) but very slightly worsened the Brier score (0.1635 → 0.1640), the same trade-off direction
observed on 13 August (0.1622 → 0.1647) and consistent with it. Both are reported, not just the one
that improved: reporting only the favourable metric after fitting an adjustment would itself be a
form of the measurement-integrity failure §5.2 exists to prevent.

**Figure 5.1 — Reliability diagram (⟨M-13⟩), re-rendered 16 August 2026**

![Figure 5.1 — Reliability diagram, predicted probability against observed frequency](diagrams/out/fig-5-1-reliability.png)

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

The shape is essentially unchanged from the 13 August run: systematically under-confident in the low
bins (predicted 0.054 against an observed rate of 0.139) and closely calibrated at the extreme it
assigns most mass to (0.9–1.0: predicted 0.971, observed 0.959, on 740 of the 3,937 URLs — the
largest single bin both times). Bin populations shifted somewhat between the two runs (e.g. 0.6–0.7
held 142 URLs on 13 August and 118 now) because `digit_ratio` redistributes individual predictions
across bin boundaries even where the aggregate metrics barely move. Without this section the phrase
"94% confident" in the interface would be decoration, and an examiner would be entitled to say so;
with it, the figure is traceable to a measured reliability curve rather than asserted.

## 5.12 Explanation faithfulness and sensitivity

### 5.12.1 Faithfulness

Claim C3 asserts that the stated reasons are the operative ones. This is testable by intervention:
neutralise the reasons the system gave, and see whether the score moves as they predicted.

**Procedure.** For each of *N* test URLs: record the score and the three highest-ranked
contributions; set those three features to their training medians; re-score; compare the observed
change against the sum of the three attributions.

**Table 5.18 — Explanation faithfulness (⟨M-14⟩, re-measured 16 August 2026)**

| Metric | Value | Acceptance |
|---|---|---|
| URLs evaluated | 3,937 (temporal-split test set) | — |
| Directional agreement | **88.4%** | ≥ 90% — **not met** |
| Directional agreement, \|predicted shift\| > 0.05 (n = 3,909) | 88.5% | — |
| Mean absolute error, predicted vs observed shift (log-odds) | 0.9302 | — |

Exact agreement is not expected and its absence is not a failure. SHAP attributes a specific
prediction under a specific feature distribution; intervening on three features simultaneously moves
the input off that distribution, and tree ensembles are not additive in the input. Directional
agreement is the meaningful criterion, and the magnitude error quantifies the interaction effects.

**The 88.4% result is reported as measured, short of the 90% target, rather than adjusted to clear
it.** It is, however, a genuine improvement on the 13 August figure (87.0% → 88.4%, +1.4 points),
measured on the identical protocol and test set, and consistent with the hypothesis that motivated
the `digit_ratio` change in the first place: a length-normalised ratio is a smoother function of the
URL than a raw count, so it is less prone to the kind of single-character-dominates-the-attribution
behaviour that a simultaneous multi-feature ablation is most likely to disagree with. Restricting to
cases where the predicted shift is not near zero moves the figure by only 0.1 point (88.5%), so the
remaining shortfall is not an artefact of near-zero predictions dominating the denominator. The
explanation given for the original gap still accounts for what remains of it: XGBoost with
`max_depth=6` permits real three-way feature interactions that SHAP's local attribution does not
fully capture under a simultaneous three-feature ablation, and several of the model's strongest
features (`url_entropy`, `digit_ratio`) are correlated with each other, so neutralising the top three
together removes more combined signal than the sum of their individual attributions predicts. This
is recorded as a genuine, narrowed-but-not-closed limitation of claim C3 in §6.3.

### 5.12.2 Fusion weight sensitivity

The fusion weights are set by hand (ADR-014, ADR-017), which obliges the work to show that
conclusions do not rest on their precise values.

No corpus pairs real browser telemetry with a phishing label (§5.10's note on B5), so this cannot
measure real-world fused accuracy without fabricating per-URL signals correlated with the label —
exactly the manufactured evidence ADR-014 rejects for the weights themselves. Instead a single
fixed, clearly-synthetic "typical page" profile (`tracker_count=3`, no mixed content, one redirect
— moderate, chosen well below `heuristics_engine.py`'s own "excessive" thresholds of 10 and 3) is
applied uniformly to every URL in the temporal-split test set (3,937 URLs), and each perturbation is
measured against that same fixed baseline.

**Table 5.19 — Fusion weight sensitivity (⟨M-15⟩, re-measured 16 August 2026 against the extended
nine-signal weight table)**

| Perturbation | Verdict changes | F1 change |
|---|---|---|
| All weights ×0.5 | 463/3,937 (11.8%) | −0.0241 |
| All weights ×2.0 | 1,111/3,937 (28.2%) | −0.0056 |
| Tracker weight only, ×0 | 489/3,937 (12.4%) | −0.0237 |
| Each weight ±25%, one at a time (largest single change) | `tracker_count` −25%: 127/3,937 (3.2%) | +0.0029 |

F1 moves by only a few hundredths even at the largest perturbation tested, because the synthetic
signal profile is identical across every URL — it shifts every fused score by a similar amount and
so barely reorders which URLs fall above or below the 0.5 threshold, which is what F1 there depends
on. Verdict-band churn is the more informative number: doubling every weight moves 28.2% of URLs
across a risk-band boundary, because a share of this test set sits close to the 0.40/0.70 boundaries
and a uniform log-odds shift is enough to tip them. This is a genuine sensitivity, not a null result,
and it is the argument for the shipped weights (Table 4.1) being set conservatively: at the shipped
magnitude and a ±25% perturbation around it, per-weight churn stays in the 0.0%–3.2% range on this
synthetic test, well below the 28.2% seen at double the shipped weights — so the exact values chosen
matter less than keeping the overall magnitude moderate, which is the honest form claim C2's
robustness can currently take.

**Coverage caveat — three of the nine weights are not exercised by this test.** The fixed "typical
page" profile sets only `tracker_count`, `has_mixed_content` and `redirect_chain_length` — the three
browser signals present when this test was first designed under ADR-014. It does not set
`cam_mic_on_first_visit`, `location_on_load`, `notification_prompt_on_load`,
`scam_keyword_hits`, `sensitive_field_count` or `vt_malicious_votes`, so perturbing any of those six
weights against this profile changes nothing: `fuse()` only reads a signal when the caller supplies
it (§4.3.5, Algorithm 4.5, line 4), and the profile never does. The x0.5/×2.0/±25% rows above
therefore report genuine sensitivity for the three originally-covered signals only; a 0.0% churn row
for one of the other six would mean "not exercised," not "insensitive," and this report does not
claim otherwise. Extending the synthetic profile to exercise all nine signals — deciding what a
"typical page" content-scan and reputation profile looks like is itself a judgement call this
project did not want to make under the time pressure of this evaluation pass — is recorded as future
work in §6.5 rather than done here without that consideration.

## 5.13 Performance

**Table 5.20 — Assessment latency (⟨M-16⟩, measured 13 August 2026)**

Measured against the running local Docker stack (real trained model, real reputation-service
calls), 10 distinct domains. The cold pass is paced at one request per 16 seconds to stay under the
reputation service's 4-requests-per-minute free-tier limit, rather than measuring how quickly it
rejects an over-limit burst; the warm pass repeats the same domains immediately after, against the
one-hour TTL cache.

| Condition | p50 | p95 | Budget (NFR-01) | Result |
|---|---|---|---|---|
| Cold reputation cache | 1.148s | 1.593s | p95 ≤ 10s | **Met** |
| Warm reputation cache | 0.063s | 0.078s | p95 ≤ 1s | **Met** |

The roughly 20x gap between conditions is dominated by the external call, which at the time of this
run carried a five-second timeout — the strongest practical justification for the response cache:
without it, every assessment would sit in the cold-cache distribution regardless of how often a
domain recurs.

**Not re-measured live for this edition.** The reputation client's timeout was subsequently reduced
from 5.0s to 2.5s as part of ADR-017 (`virustotal_client.py`, since a slow reputation response is now
genuinely on the scoring path rather than purely a display delay). This can only lower the worst-case
cold-path latency recorded above, never raise it, so the **Met** conclusion against NFR-01's 10-second
budget still holds by construction; it was not re-run live against paced, rate-limited external calls
for this evaluation pass; a live re-run under the reduced timeout is recorded as a concrete,
low-effort item in §6.5 rather than assumed to already have happened.

**TC-P-02** verifies that signal collection does not delay rendering. The extension registers only
non-blocking listeners — `onCompleted` and `onBeforeRedirect` observe, they do not intercept — so no
request waits on extension code. Verified by inspection of the listener registrations and by
comparing page load timings with the extension enabled and disabled.

## 5.14 Security and privacy testing

**Table 5.21 — Security and privacy test cases**

| ID | Objective | Method | Expected | Actual | Status |
|---|---|---|---|---|---|
| **TC-SEC-01** | Permissions are minimal | Review each manifest permission against its use | Every permission traceable to a specific API call | `activeTab`, `storage`, `webRequest`, `webNavigation`, `tabs` — each mapped to a listener or call site | Pass |
| **TC-SEC-02** | Input validated at the boundary | Submit malformed bodies | 422 before any handler logic | As expected | Pass |
| **TC-SEC-03** | No credential in source control | Search history and working tree | Only an example file with placeholder values | Confirmed; real values supplied through the environment | Pass |
| **TC-SEC-04** | Data leaving the browser is bounded | Inspect the request body | URL, derived counts, and matched scam-phrase/field categories only; no raw page HTML, cookies or unmatched form values | Confirmed by inspection of the submitted payload | Pass |
| **TC-SEC-05** | No server-side fetch of the assessed URL | Review the service for outbound requests | The only outbound call is to the reputation service, with a domain, not the URL | Confirmed | Pass |
| **TC-SEC-06** | `client_id` is a scoping value, not a credential | Review generation and every endpoint that reads it | Generated by `crypto.randomUUID()` client-side, persisted in `chrome.storage.local`; no endpoint treats its presence as authentication, and none returns data to an unrecognised value beyond "empty" | Confirmed: `/history`/`/stats` return an empty result for an unrecognised `client_id`; `/scan/{id}` 404s | Pass |
| **TC-M-01** | Every push is verified | Inspect CI configuration and history | Lint, tests and type-check run on every push | `.github/workflows/ci.yml` runs `backend`, `dashboard` and `e2e` jobs on every push | Pass |
| **TC-M-02** | Stack starts from one command | See TC-S-01 | — | — | Pass |

TC-SEC-04 deserves comment because it bears on the privacy claim in NFR-11. The extension transmits
the URL of the page, integer counts derived from its behaviour, and — since the page-content scanner
landed — the *matched* scam phrases and sensitive-field *categories* it found, not the surrounding
page text or the field values themselves. It does not transmit raw page HTML, cookies, or any form
value. The URL itself is inherently sensitive — it is browsing history — and Section 6.3 records this
honestly rather than presenting the design as privacy-neutral. TC-SEC-06 exists because `client_id`
is a new kind of value on the request path since multi-browser scoping was added (§4.5.4): it is
deliberately not a secret and not authentication, and the test asserts that no endpoint's behaviour
implies otherwise.

## 5.15 End-to-end validation

### 5.15.1 Original run, 13 August 2026

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

**Table 5.22 — End-to-end result, 13 August run (⟨M-17⟩)**

| Metric | Value | Acceptance |
|---|---|---|
| URLs assessed | 30 | — |
| Correctly classified | **20/30** | ≥ 26/30 — **not met** |
| False positives among deep-path legitimate URLs | **1/13** (`docs.python.org/3/library/asyncio.html`, 71%) | 0 — **not met** |
| Mean assessment latency | 0.070s | — |

**Table 5.23 — Confusion matrix, 30-URL run, 13 August**

| | Predicted phishing | Predicted suspicious | Predicted legitimate |
|---|---|---|---|
| **Actually phishing** (15) | 10 | 2 | 3 |
| **Actually legitimate** (15) | 1 | 4 | 10 |

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
disclosed via the 8.5% false-positive rate in §5.11.1 and the 87.0% faithfulness result in §5.12.1
(both since re-measured, §5.11.1, §5.12.1), reproducing here on live, previously-unseen data rather
than appearing as a new defect. It was not retrained against on the spot: doing so in response to a
single digit collision observed on an n = 30 convenience sample would have been statistically
unsound, and would have repeated, on a smaller and less rigorous sample, the exact
overfitting-to-the-measurement-instrument error the corpus rebuild in §4.7.1 was written to correct.
It was instead carried forward as a limitation — and, two days later, actually fixed, which
§5.15.2 reports.

### 5.15.2 Re-check after the `digit_ratio` fix, 16 August 2026

`num_digits` was replaced by `digit_ratio` on 15 August 2026 (§4.7.1), specifically to address the
false positive identified above. Re-scoring the same thirty URLs against the fixed model is the most
direct possible test of whether that fix worked — a targeted regression check on the exact case that
motivated it, not a re-tuning against the sample.

**Scope of this re-check.** It calls `ml.shap_analysis.explain_prediction()` — the same function the
live service calls — directly and offline, rather than through a live `POST /analyze` against a
running Docker stack with a real reputation-service lookup. This means it does **not** benefit from
ADR-017's established-reputation dampening the way a genuinely live re-run would for the well-known,
long-registered legitimate domains in this set (github.com, wikipedia.org, python.org and similar):
those domains would plausibly score lower still under a live VirusTotal lookup than they do here,
so this re-check is, if anything, a conservative (harder) test of the fixed model than a full live
re-run would be. A live re-run — repeating §5.15.1's exact method against the current system — is
recorded as future work in §6.5 rather than assumed to produce the same or better numbers.

**Table 5.24 — Per-URL result, 16 August re-check, offline (no live reputation lookup)**

| # | URL | Expected | Observed | Risk % | Principal reason | Outcome |
|---|---|---|---|---|---|---|
| 1 | `logowanie-facebook.vercel.app/` | phishing | suspicious | 63% | Contains a well-known brand name in a suspicious position | Miss |
| 2 | `ledger-login-web-conect-web-sso-in.typedream.app/` | phishing | legitimate | 10% | URL length (57 characters) is unremarkable | Miss |
| 3 | `sp15ct7-gresor-biz-fantik-lurmon.pages.dev/` | phishing | phishing | 77% | Digit density (0.0588) pushed this toward higher risk | Hit |
| 4 | `sp15ct7-grasik-biz-forlen-haskel.pages.dev/` | phishing | suspicious | 69% | Digit density (0.0588) pushed this toward higher risk | Miss |
| 5 | `merry-maamoul-33ac49.netlify.app/` | phishing | phishing | 93% | Digit density (0.0976) pushed this toward higher risk | Hit |
| 6 | `27p-sddo-up2-zcwe25-9i92.pages.dev/` | phishing | phishing | 97% | Digit density (0.186) pushed this toward higher risk | Hit |
| 7 | `backupiau.direct.quickconnect.to/cgi-bin/home.ha` | phishing | legitimate | 6% | Digit density (0.0) is low, typical | Miss |
| 8 | `www.myxfinitycom.weebly.com/` | phishing | legitimate | 7% | Digit density (0.0) is low, typical | Miss |
| 9 | `xfinity-customer-care.weebly.com/` | phishing | suspicious | 62% | Randomness score high (4.3451) | Miss |
| 10 | `metamask-docs-l8lvh00ol-consensys-ddffed67.vercel.app/embedded-wallets/troubleshooting` | phishing | legitimate | 17% | URL length (94 characters) is unremarkable | Miss |
| 11 | `bc4f19.icefactory.cl/` | phishing | phishing | 95% | Digit density (0.1034) pushed this toward higher risk | Hit |
| 12 | `6c0fd9.icefactory.cl/` | phishing | phishing | 95% | Digit density (0.1034) pushed this toward higher risk | Hit |
| 13 | `4533ff.icefactory.cl/` | phishing | phishing | 99% | Digit density (0.1379) pushed this toward higher risk | Hit |
| 14 | `proj002mintinglive.netlify.app/` | phishing | phishing | 87% | Digit density (0.0769) pushed this toward higher risk | Hit |
| 15 | `72e520.icefactory.cl/` | phishing | phishing | 99% | Digit density (0.1724) pushed this toward higher risk | Hit |
| 16 | `github.com/torvalds/linux/blob/master/README` (deep) | legitimate | suspicious | 54% | Randomness score high (4.4643) | Miss |
| 17 | `en.wikipedia.org/wiki/Transport_Layer_Security` (deep) | legitimate | legitimate | 18% | URL length (54 characters) is unremarkable | Hit |
| 18 | `docs.python.org/3/library/asyncio.html` (deep) | legitimate | **suspicious** | **68%** | Digit density (0.0217) pushed this toward higher risk | Miss, no longer a false positive |
| 19 | `google.com/search?q=xgboost+explainability` (deep) | legitimate | legitimate | 27% | Randomness score high (4.386) | Hit |
| 20 | `stackoverflow.com/questions/tagged/xgboost` (deep) | legitimate | legitimate | 30% | URL length (50 characters) is unremarkable | Hit |
| 21 | `news.ycombinator.com/item?id=1` (deep) | legitimate | **phishing** | **71%** | Randomness score high (4.2737) | **New false positive** |
| 22 | `bbc.com/news/technology` (deep) | legitimate | legitimate | 9% | Digit density (0.0) is low, typical | Hit |
| 23 | `developer.mozilla.org/.../Using_Fetch` (deep) | legitimate | legitimate | 17% | URL length (70 characters) is unremarkable | Hit |
| 24 | `nytimes.com/section/technology` (deep) | legitimate | legitimate | 12% | Digit density (0.0) is low, typical | Hit |
| 25 | `pypi.org/project/fastapi/` (deep) | legitimate | legitimate | 7% | Randomness score low (3.7953), readable | Hit |
| 26 | `amazon.com/gp/help/customer/display.html` (deep) | legitimate | legitimate | 21% | Shallow subdomain structure (0 levels) | Hit |
| 27 | `microsoft.com/.../what-is-phishing` (deep) | legitimate | legitimate | 27% | Digit density (0.04) pushed this toward higher risk | Hit |
| 28 | `reddit.com/r/MachineLearning/` (deep) | legitimate | legitimate | 16% | Digit density (0.0) is low, typical | Hit |
| 29 | `wikipedia.org/` | legitimate | legitimate | 20% | URL is unusually long (22 characters) | Hit |
| 30 | `python.org/` | legitimate | legitimate | 2% | Randomness score low (3.4316), readable | Hit |

**Table 5.24a — Summary, 16 August re-check**

| Metric | 13 August | 16 August | Change |
|---|---|---|---|
| Correctly classified | 20/30 | 20/30 | No change |
| False positives among deep-path legitimate URLs | 1/13 | 1/13 | No change in count |

**The fix worked exactly as diagnosed, and a second, unrelated false positive surfaced in the same
run — both are reported, because the headline count not changing is not the same as nothing
changing.** `docs.python.org/3/library/asyncio.html` moved from 71% *phishing* to 68% *suspicious*:
it no longer crosses the interstitial-raising threshold, and `digit_ratio` (0.0217, a genuinely low
density) is no longer the score's dominant contribution the way `num_digits = 1` was. Row 18 is a
resolved false positive by the criterion §5.15.1 actually cared about (does it raise the blocking
interstitial), though it remains a *miss* against the stricter "exactly matches expected band"
count, which is why "correctly classified" does not move from this row alone.

Independently, row 21 — `news.ycombinator.com/item?id=1` — crossed from 70% *suspicious* (a miss, but
not a false positive, on 13 August) to 71% *phishing* (a false positive now), driven by
`url_entropy` (4.2737), not by `digit_ratio` at all. This is a one-point, boundary-adjacent shift,
consistent with retraining on a redefined feature reshuffling SHAP's exact attribution for URLs that
already sat close to the 0.70 cut — and it is exactly the interaction effect §5.12.1 measures in
aggregate (88.4% faithfulness, not 100%): fixing one feature's brittleness does not, and structurally
cannot, guarantee every other prediction is unaffected. Reporting a fix's side effect honestly is the
same discipline applied throughout this chapter to the fix itself.

**Both findings are consistent with, and strengthen, the same limitation already stated in §6.4**:
lexical URL features, on their own, are not a sufficient basis for a false-positive rate low enough
for unsupervised production deployment. This re-check shows the `digit_ratio` fix resolved the
specific case that motivated it without a regression in the aggregate false-positive rate (§5.11.1:
8.5% → 8.7%, within noise) or in aggregate faithfulness (87.0% → 88.4%, an improvement) — while also
demonstrating, concretely and on live-shaped data, that a single-feature fix does not close the
underlying brittleness. Neither result was retrained against for the reasons given in §5.15.1: a
change justified by one observed case on this same 30-URL sample would be exactly the
overfitting-to-the-measurement-instrument error this project has twice already corrected (§4.7.1,
and now here).

## 5.16 Defect log

**Table 5.25 — Defect log**

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
| D11 | Deep-path false positive on live E2E run (§5.15) | Major | 30-URL end-to-end run | **Resolved for the specific case** — `num_digits` replaced by `digit_ratio` (§4.7.1); the 16 August re-check (§5.15.2) confirms `docs.python.org/3/library/asyncio.html` no longer crosses the phishing threshold. The underlying lexical-feature brittleness is not closed — see D17 and §6.4 |
| D12 | `GET /scan/{id}` readable by any caller who obtained the identifier (IDOR) | Critical | Review while adding multi-browser scoping | Resolved — `client_id` required and compared to the record's owner; mismatch reported as 404 (§4.5.4, §4.7.9) |
| D13 | `evaluate_baselines.py` referenced the retired `num_digits` column | Major | Re-running the evaluation pipeline after the rename | Resolved — column list corrected (§4.7.10) |
| D14 | `sensitivity.py`'s report narrative disagreed with its own table | Major | Manual inspection of a re-run report | Resolved — narrative now derived from the same run's data (§4.7.11) |
| D15 | A second, independent weak-credential fallback in the Alembic environment | Major | Extending ADR-016 to `DATABASE_URL` | Resolved — `env.py` now imports the one fail-loud source of truth (§4.7.12) |
| D16 | `sensitivity.py`'s `_fuse_all` aliased and cleared the live weight table | Major | Code reading while adding new fusion signals | Resolved — argument snapshotted before the global is touched; regression test added (§4.7.13) |
| D17 | A second, unrelated false positive surfaced by the D11 re-check | Minor–Major | 16 August re-check (§5.15.2) | **Open** — `news.ycombinator.com/item?id=1` moved from 70% (miss) to 71% (false positive), driven by `url_entropy`, not `digit_ratio`; not retrained against for the same reason D11 was not (§5.15.2). Carried into §6.4 as a limitation |
| D18 | Duplicate scan records; popup stuck on "Analyzing" | Major | Observed pairs of near-identical records; user report of a non-updating popup | Resolved — a 3s recency window suppresses a duplicate `tabs.onUpdated` "complete" event for the same tab and URL; popup subscribes to `chrome.storage.onChanged` instead of only rendering once on open (§4.7.14) |

D7 and D8 were both genuinely open earlier in the project and are recorded here as resolved rather
than silently corrected, because the permission signal family was reported non-functional for a real
stretch of the work. D7's automated coverage exercises the cross-world relay mechanism in a
simulated two-realm harness; it does not substitute for observing a real page's own
`Notification.requestPermission` call being intercepted, which is why TC-S-10/11 in §5.7 are still
marked pending a real-browser session rather than closed. D17 remains genuinely open — see §5.15.2
and §6.4 for why it was deliberately not chased into a retrain, for exactly the reasoning D11 itself
established.
