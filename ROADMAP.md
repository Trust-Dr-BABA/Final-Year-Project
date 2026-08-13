# ROADMAP — Explainable Multi-Signal Phishing Detection in the Browser

> **Last updated:** 2026-08-12
> **Submission deadline:** 2026-09-06 (4 weeks)
> **Current sprint:** Sprint 0 — Make it run, and make it fail loudly
> **Planning docs:** this file (what to build) + [`PROJECT_STATE.md`](PROJECT_STATE.md) (where we are, and why we chose it)

---

## 1. What this project claims

> A Chrome MV3 extension observes each page a user visits and extracts three independent
> signal families — **lexical URL structure**, **browser-level network behaviour** (third-party
> trackers, mixed content, redirect chains), and **permission-request behaviour** (camera, mic,
> geolocation, notifications requested before user interaction). A FastAPI service fuses them into
> a single calibrated risk score, and returns the *specific reasons* for that score in plain
> English, derived from SHAP attributions over the trained model and from documented weights over
> the browser signals. A Next.js dashboard renders the full history and per-scan explanation.

Three claims follow from that, and the roadmap exists to make each one **demonstrably true**
rather than merely asserted:

| Claim | What makes it true | Where it is proven |
|---|---|---|
| **C1** — Detection generalises beyond a blocklist | Model must beat a blocklist baseline *on URLs absent from training*, under a temporal split | Sprint 2 |
| **C2** — Detection is genuinely multi-signal | Browser signals must measurably move the score and appear in explanations | Sprint 1 |
| **C3** — Explanations are faithful, not decorative | Ablating the top-3 cited reasons must move the score as those reasons predict | Sprint 2 |

An examiner will attack whichever of these is weakest. Sprint ordering is chosen accordingly:
**credibility first, product surface second, write-up third.**

---

## 2. How to read this roadmap

- Work is organised as **Sprint 0 (2 days) + four one-week sprints**. This replaces the earlier
  8-phase/12-week structure, which no longer matches the calendar.
- Every task has an **acceptance criterion that can be checked by running something**. "Written"
  is not "done"; if the criterion has not been executed, the box stays open.
- Tasks are ordered by grade impact within a sprint. Complete top-to-bottom.
- `[ ]` not started · `[/]` in progress · `[x]` verified complete · `[~]` deliberately descoped
- After each task: tick the box here, then update **Current Sprint** and the activity log in
  `PROJECT_STATE.md`.

**Descoping rule.** If a sprint runs over, cut from the bottom of Sprint 3 first, then Sprint 3's
stretch items. Never cut from Sprint 1 or Sprint 2 — those carry C1–C3. Never cut SHAP.

---

## 3. Honest starting position (audited 2026-08-09)

The previous roadmap's checkboxes had drifted from the code. This is the verified state.

**Working:**

- URL feature extractor: 9 trained features — 8 lexical plus brand impersonation — and 3 VirusTotal fields (`backend/feature_extractor/url_features.py`)
- Async VirusTotal client with TTL cache and 5s timeout (`backend/services/virustotal_client.py`)
- Heuristics engine over network + permission signals (`backend/services/heuristics_engine.py`)
- Human-readable feature templates, all 21 features covered (`shared/feature_name_to_human_readable.json`)
- `/analyze`, `/history`, `/stats`, `/scan/{id}` implemented against a correct SQLAlchemy model
- Extension: network monitor (trackers, mixed content, top-level redirects), 5-state popup, API client
- 500-entry EasyPrivacy tracker list, 50-brand list
- Dashboard: Next.js 16 + Tailwind 4, typed API client, overview page, badge components
- Unit tests for URL features, explainer formatter, SHAP, VT client; one integration test

**Four defects that would fail a viva, and one that would fail a demo:**

| # | Defect | Evidence | Fixed in |
|---|---|---|---|
| **D1** | **Dataset is trivially separable.** The legitimate class is Tranco *bare domains* (`https://hdzytech.com`); the phishing class is PhishTank *full URLs with paths*. `url_length` alone nearly separates them — the model learns "does this URL have a path", not phishing. Inflates F1 to a meaningless ~0.97 and will flag every legitimate deep link in the live demo. | `ml/scripts/prepare_dataset.py:40` | Sprint 1 |
| **D2** | **Multi-signal fusion (claim C2) is not wired in.** Browser-signal features are computed, merged into the feature vector, then silently filtered out against `feature_columns.json`. They survive only as display strings. | `backend/routers/analyze.py:92` → `ml/shap_analysis.py:145` | Sprint 1 |
| **D3** | **VirusTotal features are dead weight *and* would be circular.** `generate_features.py` never passes `vt_data`, so all three VT columns are constant `-1` across 20,000 training rows. Training on them properly would be worse: VirusTotal ingests PhishTank, so VT votes restate the label. | `ml/scripts/generate_features.py:44` | Sprint 1 (ADR-013) |
| ~~D4~~ | **Artifact drift, unguarded.** `feature_columns.json` lists 12 columns; `features.csv` has 8. No `xgboost_phishing.pkl` exists. Nothing asserts the model and the column list agree. — **guard fixed 2026-08-12**: `_load_model()` now raises on `n_features_in_` mismatch. `feature_columns.json`/`features.csv` disagreement itself is still open, closed by Sprint 1's retrain. | `ml/models/` | Sprint 0 |
| ~~D5~~ | **Every failure path returns a plausible verdict.** Missing model, missing deps, wrong mount path — all fall through to `_simple_rule_prediction()`. The Docker image never installs the `[ml]` extras, and compose mounts models to `/app/models` while the loader reads `/app/ml/models`. A demo would appear to work with the ML core inert. — **fixed 2026-08-12**: fallback gated behind `ESA_ALLOW_FALLBACK`, Dockerfile installs `.[ml]`, compose mount corrected; all verified live. | `ml/shap_analysis.py:135`, `backend/Dockerfile:14`, `docker/docker-compose.yml:35` | Sprint 0 |

**Extension defects:** `manifest.json` lacks the `webNavigation` permission that
`network_monitor.js:41` requires; `content_script.js` patches permission APIs in the isolated
world, where it cannot observe the page's real calls; permission signals are posted 3.5s after
`load` but analysis fires at `tabs.onUpdated` complete, so they arrive too late to be used.

---

## Sprint 0 — Make it run, and make it fail loudly

**Days 1–2 · Theme: eliminate silent degradation.**

Everything downstream depends on being able to trust what the system reports about itself.
Today a broken model, a missing dependency and a wrong mount path all produce the same
confident-looking output.

### 0.1 — Reproducible environment

- [x] **0.1.1** Add the missing runtime deps to `backend/pyproject.toml`: `alembic`,
      `python-dotenv`, `greenlet`. Move `pandas` and `joblib` from `[ml]` into the base
      dependencies — `ml/shap_analysis.py` imports them on the request path, so they are not
      optional in a serving container.
      _Done 2026-08-12: also wired `load_dotenv()` into `backend/main.py` (must run before the
      module-level `os.getenv()` calls in `database.py`/`virustotal_client.py`) since nothing
      previously loaded `.env` outside Docker's `env_file:`._
- [x] **0.1.2** Create `.venv` and install: `pip install -e "./backend[ml,dev]"`. Record the exact
      commands in `README.md`.
      _Done 2026-08-12: reinstalled into the existing Python 3.11.15 `.venv`; `pytest tests/ -q`
      passes 25/25 (one new test added, see 0.2.1). Commands already correct in `README.md`._
- [x] **0.1.3** Fix `backend/Dockerfile:14` to install `.[ml]` rather than `.` — the image
      currently ships without xgboost, shap or pandas.
      _Done 2026-08-12._
- [x] **0.1.4** Fix the model volume mount in `docker/docker-compose.yml:35`: `/app/models` →
      `/app/ml/models`, matching `MODELS_DIR` in `ml/shap_analysis.py:18`.
      _Done 2026-08-12._

**Acceptance:** `pytest tests/ -q` runs to completion locally (failures allowed, collection errors
not) — **verified, 25/25 passing.** `docker compose up` starts all three services with no import
errors in the backend log — **verified: `docker compose up -d --build backend` (postgres already
up from 0.3.2) started cleanly, log shows only "Application startup complete", and
`GET /health` returned `db_reachable: true` from inside the compose network.**

### 0.2 — Fail loudly, not quietly

- [x] **0.2.1** Gate the fallback in `ml/shap_analysis.py`: `explain_prediction()` raises
      `ModelUnavailableError` unless `ESA_ALLOW_FALLBACK=1` is set. Development keeps the
      fallback; deployment does not silently degrade.
      _Done 2026-08-12: `tests/conftest.py` sets `ESA_ALLOW_FALLBACK=1` by default (no `.pkl` is
      committed, so tests need the heuristic path); new test
      `test_explain_prediction_raises_without_fallback_flag` covers the unset case.
      `backend/routers/analyze.py` catches `ModelUnavailableError` and returns 503._
- [x] **0.2.2** Add a load-time lockstep assertion: `model.n_features_in_ == len(feature_columns)`,
      raising with both values on mismatch. This one check catches D4 and every future recurrence.
      _Done 2026-08-12, in `_load_model()`._
- [x] **0.2.3** Extend `GET /health` in `backend/main.py` to return
      `{status, version, model_loaded, feature_count, model_sha256, vt_key_configured, db_reachable}`.
      This becomes the pre-demo checklist on defense day.
      _Done 2026-08-12: added `get_model_status()` (`ml/shap_analysis.py`) and
      `check_db_reachable()` (`backend/database.py`), both non-raising. Verified live: with no
      `.pkl` and no DB running, returned `model_loaded: false, db_reachable: false`; with Postgres
      up, `db_reachable` flipped to `true`._

**Acceptance:** with no `.pkl` present and `ESA_ALLOW_FALLBACK` unset, `POST /analyze` returns
**503**, not a fabricated verdict — **verified via unit test.** `GET /health` reports
`model_loaded: false` — **verified live, see above.** With the model present, both flip
(**not yet observed — no `.pkl` exists until Sprint 1.5 trains one**).

### 0.3 — Database migrations

- [x] **0.3.1** `alembic init` inside `backend/`; wire `alembic.ini` to `DATABASE_URL` from env.
      _Merged from `origin/main` 2026-08-09; `env.py` is async-correct._
- [x] **0.3.2** Autogenerate and apply the initial `scans` migration.
      Migration `ab476f0dcf44_create_scans_table` exists and matches
      `backend/models/scan.py` exactly.
      _Verified 2026-08-12: started Postgres via `docker compose up -d postgres`, ran
      `alembic upgrade head` against it — applied cleanly, `\d scans` confirmed all JSONB columns
      (`url_features`, `network_signals`, `permission_signals`, `shap_values`, `flagged_rules`)._

**Acceptance:** `alembic upgrade head` applies cleanly against the compose Postgres; `\d scans`
shows all JSONB columns. **Verified.**

### 0.4 — Extension loads without errors

- [x] **0.4.1** Add `"webNavigation"` to `manifest.json` permissions. Without it
      `chrome.webNavigation.onBeforeNavigate` throws and **all** network signals are lost silently.
      _Merged from `origin/main` 2026-08-09 — resolves defect D6._
- [x] **0.4.2** Add real 16/48/128px PNGs to `extension/icons/` and the `icons` block to the manifest.
      _Merged from `origin/main` 2026-08-09._
- [x] **0.4.3** Tracker matching now follows EasyPrivacy `||domain^` semantics — subdomains of a
      listed tracker match, and collapse onto the base domain so they count once. Covered by
      `tests/unit/network_monitor_test.js`.

**Acceptance:** extension loads via "Load unpacked" with zero manifest errors and zero service
worker exceptions; navigating to `https://cnn.com` logs a non-zero `tracker_count`.
**Verified 2026-08-13** in a real Chrome install: no manifest errors, no service-worker exceptions
(the one console line logged was `explain_prediction` correctly returning 503 per ADR-016 — no
`.pkl` is committed and `ESA_ALLOW_FALLBACK` wasn't set on the container yet — a handled error, not
a crash). `chrome.storage.local` showed `net_785867352` (edition.cnn.com after a redirect) with
`tracker_count: 11`, `redirect_chain_length: 5`, `third_party_domains` length 11. Set
`ESA_ALLOW_FALLBACK: "1"` on the `backend` service in `docker/docker-compose.yml` right after —
compose is the local dev stack, not the Sprint 3 production deploy, so ADR-016 says the fallback
should stay on here.

### 0.5 — Continuous integration

- [x] **0.5.1** Add `.github/workflows/ci.yml`: `pytest`, `npx tsc --noEmit` in `dashboard/`,
      and `ruff check`. A green CI badge is a cheap, visible professionalism signal.
      _Done 2026-08-12: two jobs (`backend`, `dashboard`). Added root `ruff.toml` (no prior config
      existed) with two targeted `E402` per-file-ignores for genuinely load-order-dependent imports
      (`backend/main.py`'s `load_dotenv()`, `ml/scripts/generate_features.py`'s `sys.path` patch);
      fixed one real unused import in `test_url_features.py`. `ruff check backend ml tests`,
      `pytest`, and `dashboard`'s `npx tsc --noEmit` all verified green locally before wiring in._
- [x] **0.5.2** Fix the root `package.json` workspace list — it declares `extension` as a
      workspace, but `extension/` has no `package.json`.
      _Fixed 2026-08-10: removed `extension` from `workspaces`. Root install was also silently
      broken — `node_modules` had no hoisted deps and `dashboard/` carried its own independent
      standalone install (two lockfiles, two copies of Next/React). Also fixed
      `"next dev --workspace=dashboard"` in the root scripts, which passed an npm flag straight to
      the `next` CLI and would have failed; now `"npm run dev --workspace=dashboard"`. Reinstalled
      from a clean root `npm install` — single lockfile, single install._

**Acceptance:** CI green on `main`.

---

## Sprint 1 — Rebuild the ML core

**Week 1, to 2026-08-16 · Theme: make claims C1 and C2 true.**

This sprint carries most of the grade. Nothing downstream is worth doing on top of a dataset that
measures the wrong thing.

### 1.1 — Quantify the flaw before fixing it

- [x] **1.1.1** Write `ml/scripts/audit_dataset.py`. For a given dataset it reports, per feature:
      single-feature ROC-AUC, class-conditional means, and the **path-presence rate per class**
      (fraction of URLs with a non-trivial path). Flags any feature exceeding 0.90 AUC alone.
- [x] **1.1.2** Run it against the *current* `dataset.csv` and save the output to
      `ml/reports/leakage_audit_before.md`.

**Acceptance:** the "before" audit demonstrates the D1 artifact numerically — expect path-presence
near 0% for label 0 and near 100% for label 1, and `url_length` AUC above 0.90. **This table is a
deliverable, not scaffolding:** the before/after pair is what converts a methodological flaw into
evidence of methodological awareness, and it belongs in the evaluation chapter.
**Verified 2026-08-13:** `url_entropy` flagged at 0.9001 AUC; path presence benign 0.0% vs phishing
65.2% (65.2-point gap). Exactly the predicted shape.

### 1.2 — Rebuild the dataset honestly

- [x] **1.2.1** Rewrite `ml/scripts/prepare_dataset.py` to stop discarding PhishTank metadata.
      _Done: retains `submission_time`, `target`; filters to `verified == yes` (10,000/10,000 passed)._
- [x] **1.2.2** Source a **path-bearing benign corpus**.
      _PhiUSIIL was tried first and rejected — audited empirically at 0.0% path presence, identical
      artefact to bare Tranco domains, just a different source. Built
      `ml/scripts/fetch_deep_benign_urls.py` instead: crawls real Tranco-ranked domain homepages
      (rank 200–20,000) for real internal links via `asyncio` with a hard per-domain deadline
      (an earlier Common Crawl index-based approach was abandoned after it hung for 50 minutes
      under the index server's rate limiting). 9,000 genuine deep-path URLs from 5,288 domains in
      476s. See `ml/data/raw/DATASET_SOURCES.md` for the full account._
- [x] **1.2.3** Reserve a held-out false-positive evaluation set.
      _1,488 deep-path URLs from a disjoint rank range (20,001–40,000, zero domain overlap with
      training) → `ml/data/processed/fp_holdout.csv`, replacing the originally-planned Tranco
      top-1000 (which, being bare domains, couldn't answer "does it flag a real deep link")._
- [x] **1.2.4** Update `ml/data/raw/DATASET_SOURCES.md` with every source, download date, row
      count and method.
- [x] **1.2.5** Re-run the audit → `ml/reports/leakage_audit_after.md`.

**Acceptance:** no single feature exceeds 0.90 AUC alone; path-presence rate within 15 percentage
points across classes; ≥ 15,000 rows, each class ≥ 40%.
**Verified 2026-08-13, PASS.** No feature exceeds 0.90 (`url_length` fell from 0.8786 → 0.4993);
path-presence gap 13.6 points (78.9% vs 65.2%) — closed by measuring the phishing class's *own*
path-presence rate and mixing matching bare-homepage rows into the benign class, rather than
forcing either class to 100% or 0%. 19,685 rows, 50.8%/49.2% split.

### 1.3 — Feature set parity

- [x] **1.3.1** Regenerate `features.csv` with the *current* extractor (now includes
      `brand_impersonation`, previously missing — this was the 12-vs-8 column drift, D4).
- [x] **1.3.2** Remove the three VirusTotal columns from the trained feature set per **ADR-013**.
- [x] **1.3.3** Assert that `get_feature_names()` matches the generated columns exactly.

**Acceptance:** `pytest tests/unit/test_url_features.py` passes with a new parity test; `features.csv`
column set equals `get_feature_names()` minus the VT columns. **Verified — 15/15 passing.**

### 1.4 — Implement the fusion layer (claim C2)

- [x] **1.4.1** Create `backend/services/risk_fusion.py` implementing **ADR-014**.
- [x] **1.4.2** Emit one attribution entry per active browser signal in the *same* shape SHAP
      already produces. No schema change needed downstream.
- [x] **1.4.3** Rewrite `explain_prediction()` so it no longer silently drops unknown keys (D2) —
      raises `ValueError` instead, with a regression test locking this in.
- [x] **1.4.4** Document every weight and its justification in `ml/reports/fusion_weights.md`.

**Acceptance:** `POST /analyze` with `tracker_count: 40, has_mixed_content: true` returns a
strictly higher score than the same URL with clean signals, and `top_reasons` contains at least
one browser-signal attribution.
**Verified live 2026-08-13** against the rebuilt+running container: clean 0.107 → dirty 0.801,
`tracker_count`/`redirect_chain_length` both in `top_reasons` alongside `url_entropy`.

### 1.5 — Retrain

- [x] **1.5.1** Run `python ml/scripts/train_model.py`. Writes `.pkl` + `feature_columns.json`
      together; lockstep assertion verified (`feature_count: 9`).
- [x] **1.5.2** Record the honest metrics.

**Acceptance:** `GET /health` reports `model_loaded: true` with matching `feature_count`;
`https://github.com/torvalds/linux/blob/master/README` scores **below 0.40**;
a known-live PhishTank URL scores **above 0.70**.
**Partially met, measured honestly (`ml/reports/training_log.md`).** F1 0.8188, AUC 0.9017 — down
from the leaky ~0.97, which is the expected and correct direction. Known phishing-style URLs score
0.95–0.98 (met). The GitHub example scores **0.564** ("suspicious"), not under 0.40 — `url_entropy`
is the dominant contribution on a URL where every other feature reads clean. Aggregate check
against the full 1,488-URL holdout: 78.6% legitimate, 12.6% suspicious, **8.8% phishing-band false
positives**. Not re-tuned against this one named example or against the holdout itself — see
`training_log.md` for why that would be the same error Sprint 1.1–1.2 just corrected. Carried
forward as a measured limitation; calibration in §2.3 is the relevant follow-up, not feature
hand-tuning.

---

## Sprint 2 — Rigorous evaluation and the remaining defects

**Week 2, to 2026-08-23 · Theme: make claims C1 and C3 provable.**

This is the sprint that separates "built a classifier" from "evaluated a classifier". Most items
are cheap to compute and disproportionately persuasive in a viva.

### 2.1 — Evaluation protocols

- [x] **2.1.1** **Temporal split** on `submission_time`.
      _`ml/scripts/evaluate_baselines.py::temporal_split()`. Phishing sorted and split by real
      timestamp; benign has no submission timestamp (a crawl date isn't a publication date) so is
      split randomly in matching proportion — stated explicitly rather than left implicit._
- [x] **2.1.2** **Unseen-registrable-domain holdout**.
      _`unseen_domain_split()` — domains assigned wholesale to train or test via `tldextract`._
- [x] **2.1.3** **False-positive rate on the deep-path holdout** from 1.2.3 (superseding the
      originally-planned Tranco top-1000, which was bare domains — see 1.2.3's note).

**Verified 2026-08-13.** Both splits guarded by leakage tests
(`tests/unit/test_evaluate_baselines.py`: no shared URL/domain between train and test).

### 2.2 — Baselines (claim C1)

- [x] **2.2.1** Four baselines implemented: blocklist, `url_length`-only, logistic regression,
      URL-only XGBoost. **No fifth "fused" row** — no offline corpus carries real browser
      telemetry to score against, which is the same reason ADR-014's weights aren't learned; stated
      explicitly in `evaluation_report.md` rather than presenting B4 relabelled as B5.
- [x] **2.2.2** Precision/recall/F1/AUC reported for each, both splits, uniform 0.5 threshold
      (an early version compared XGBoost at its 0.70 production threshold against everything else
      at 0.5 — an unfair comparison, caught and fixed before this was reported).

**Acceptance:** the table shows the fused model beating the blocklist *specifically on URLs absent
from the blocklist*. **Verified — blocklist recall is exactly 0.0% on both splits** (by
construction, every test URL is absent from it), which is precisely claim C1's evidence.
`url_length`-only is now genuinely weak (F1 0.44–0.57) — confirms D1 stayed fixed. Full table in
`ml/reports/evaluation_report.md`.

### 2.3 — Calibration (justifies the word "confidence")

- [x] **2.3.1** Reliability diagram, Brier score and ECE on the temporal test set
      (`ml/scripts/calibration.py`).
- [x] **2.3.2** ECE (0.082) exceeded the 0.05 threshold, so Platt scaling was fit on a validation
      split carved from training (never from test). It did not meaningfully help (0.082 → 0.080;
      Brier score slightly worsened, 0.1629 → 0.1641) — reported as measured, not adjusted further.

**Acceptance:** `ml/reports/evaluation_report.md` contains the reliability diagram. **Met** —
diagram at `ml/reports/reliability_diagram.png`, embedded in the report.

### 2.4 — Explanation faithfulness (claim C3)

- [x] **2.4.1** Top-3 SHAP ablation implemented (`ml/scripts/faithfulness.py`), neutralising to
      training medians, both shifts measured in log-odds (SHAP's native space).
- [x] **2.4.2** MAE and directional agreement reported.

**Acceptance:** ≥ 90% directional agreement, documented.
**Measured 2026-08-13: 87.5% on 3,937 URLs — not met.** Reported honestly rather than adjusted to
clear the bar. MAE 1.0027 log-odds. Exact agreement was never expected (SHAP attributes a specific
prediction under the observed distribution; a 3-feature simultaneous intervention moves off that
distribution on a non-additive model) but the shortfall from 90% is real and stated as such.

### 2.5 — Fix the confidence semantics (ADR-015)

- [x] **2.5.1** Split the two concepts: `risk_pct = round(p * 100)`;
      `confidence_pct = round(max(p, 1-p) * 100)`.
- [x] **2.5.2** Propagated through `backend/models/scan.py`, `routers/analyze.py`,
      `routers/history.py` (via `Scan.to_dict()`), `dashboard/lib/types.ts`,
      `dashboard/components/ConfidenceBadge.tsx` (its confidence-based colour fallback was now
      meaningless, since confidence is always ≥ 50 post-fix — colour now driven by verdict alone),
      `extension/popup/popup.js`. Alembic migration `33be02683ae4_add_risk_pct`, backfilled from
      existing `risk_score` before the `NOT NULL` constraint, applied and verified against a live
      Postgres (`\d scans` shows `risk_pct integer not null`).

**Acceptance:** a legitimate page shows "96% confident this page is safe" and a phishing page
"94% confident this is phishing", both read directly from the response with no arithmetic in the UI.
**Verified** — `popup.js` no longer computes `100 - confidence`; `tests/unit/test_shap.py` locks in
`risk_pct != confidence_pct` except at the 50/50 knife-edge.

### 2.6 — Extension correctness

- [x] **2.6.1** Moved permission interception to the **main world**:
      `extension/modules/permission_monitor.js`, declared with `"world": "MAIN"` in `manifest.json`.
      The old isolated-world patch is confirmed non-functional by construction (it patches a
      different `Notification` object than the one the page calls); the new script patches the
      page's actual globals and relays via a `CustomEvent` to `content_script.js` (isolated world,
      has `chrome.runtime` access), which forwards to the service worker.
- [x] **2.6.2** Resolved the ordering race: `background.js` now re-runs analysis (via a shared
      `runAnalysis()`) when a `PERMISSION_SIGNALS` message carries a rule flag not present in the
      previously stored signals for that tab and the initial analysis already completed — rather
      than delaying every analysis to wait for a signal that usually never arrives.
- [x] **2.6.3** Created `extension/modules/permission_monitor.js`; `content_script.js` is now a
      pure relay (interception logic fully moved out).
- [x] **2.6.4** `tests/manual/permission_monitor_test.md` + two fixture pages
      (`tests/manual/fixtures/camera_on_load.html`, `notification_on_load.html`) covering both the
      interception fix and the re-analysis fix, plus a `google.com` no-false-flag check. Automated
      coverage added too: `tests/unit/permission_monitor_test.js` exercises the full MAIN-world →
      `CustomEvent` → isolated-world → `chrome.runtime.sendMessage` chain via two linked VM
      contexts sharing a fake `document` — passing locally (`npm test`).

**Acceptance:** loading the fixture page produces `cam_mic_on_first_visit` in the stored
`permissionSignals`, and that flag reaches `top_reasons` in the popup.
**Code-complete and automated-test-verified 2026-08-13; real-browser verification of the manual
plan is still needed** (same pattern as Sprint 0.4 — requires a human at a GUI Chrome instance).

### 2.7 — Performance

- [x] **2.7.1** Benchmark `/analyze` p50/p95, VT cache cold and warm (`ml/scripts/bench_latency.py`,
      10 distinct domains, cold pass paced under VT's free-tier rate limit to avoid measuring
      "how fast VT rejects a burst" instead of a genuine cold lookup).

**Acceptance:** p95 under 10s cold, under 1s warm.
**Verified against the live Docker container 2026-08-13: cold p50=1.148s p95=1.593s; warm
p50=0.063s p95=0.078s. Both comfortably met.**

### 2.8 — Brand impersonation: homoglyph + edit-distance matching

Not an original roadmap item — added mid-Sprint-2 to close a documented limitation
(`backend/feature_extractor/url_features.py`'s brand check was exact-substring only, so
`pаypal.com` with a Cyrillic а or `paypa1-login.tk` passed through undetected) rather than leaving
it for a hypothetical future pass, since the fix was bounded and directly measurable.

- [x] **2.8.1** Homoglyph normalisation (Cyrillic/Greek confusables, leetspeak digit substitution)
      plus bounded Levenshtein distance, applied to hostname tokens only — not the path, where
      coincidental distance matches would be far too noisy.
- [x] **2.8.2** Measured false-positive cost against `fp_holdout.csv` **before** committing to the
      change: old vs new logic, 14 → 15 hits across 1,488 URLs — one new false positive
      (`mail.google.com`, `"mail"` at distance 1 from brand `"gmail"`), accepted rather than
      special-cased. See `ml/reports/training_log.md`, Run 2.
- [x] **2.8.3** Regenerated `features.csv`, retrained, re-ran the full Sprint 2 evaluation suite so
      `evaluation_report.md` stays consistent with the committed model. F1/AUC moved by <0.002 —
      statistically indistinguishable from Run 1, as expected for a near-zero-signal feature.

**Acceptance:** unit tests cover homoglyph and leetspeak cases (`TestBrandImpersonation` in
`test_url_features.py`); FP cost measured, not assumed, against the same holdout used elsewhere in
Sprint 2. **Verified.**

---

## Sprint 3 — Complete the product surface

**Week 3, to 2026-08-30 · Theme: a demo that survives being clicked on.**

### 3.1 — Dashboard

- [x] **3.1.1** `npm install recharts date-fns` — installed into `dashboard/package.json`
      specifically (a first attempt landed them in the root workspace's `package.json` instead;
      caught and corrected — root deps are for repo tooling, not dashboard code).
- [x] **3.1.2** Replaced the placeholder `<div>` with a real `RiskDistributionChart`.
- [x] **3.1.3** Built `app/history/page.tsx` — sortable (client-side, current page), paginated
      table: URL, verdict badge, risk %, confidence %, timestamp; row click → detail.
- [x] **3.1.4** Built `app/scan/[id]/page.tsx` — verdict banner, risk bar, network signals card,
      permission flags card, VT corroboration card (per ADR-013, shown but not modelled).
- [x] **3.1.5** `components/charts/ShapWaterfallChart.tsx` — horizontal bars, top 5 attributions,
      red increases risk / green decreases, labelled with `human_readable`.
- [x] **3.1.6** `components/charts/RiskSparkline.tsx` — risk over time for repeat scans of a URL
      (client-side filtered from a broad history fetch — `/history` has no per-URL filter; a real,
      accepted gap for a research-scale demo dataset).
- [x] **3.1.7 (added mid-sprint)** Full visual redesign, requested explicitly: both dashboard and
      extension needed light/dark theming with a toggle, and a visual identity distinct from "the
      generic AI-generated dashboard look" (navy background, indigo accents, Inter font,
      glassmorphism, rounded-2xl cards, soft shadows — all present in the original scaffold).
      Replaced with warm neutrals (paper/ink, not navy/slate), a single teal accent kept separate
      from the semantic verdict colours, sharp 3px corners, hairline borders, Space Grotesk +
      JetBrains Mono instead of Inter. `ThemeToggle` uses a CSS-only icon swap (both icons always
      render; `data-theme` selects which is visible) specifically to avoid a real hydration
      mismatch a first, React-state-based version produced — see the commit for the full
      diagnostic trail (an inline `<script>` for the no-flash theme application also doesn't work
      under Next.js App Router the way a plain HTML `<script>` would; fixed with `next/script
      strategy="beforeInteractive"`). Applied the same palette to the extension popup
      (`extension/popup/`), using `localStorage` + a separate blocking `theme_init.js` file rather
      than an inline script — manifest.json's CSP (`script-src 'self'`) blocks inline script
      content outright, a real constraint the dashboard's `next/script` fix doesn't share.

**Acceptance:** `npx tsc --noEmit` clean; every page renders against live backend data; no
snake_case anywhere in the rendered DOM.
**Verified 2026-08-13** — production build (`next build`) succeeds; both themes screenshotted via
headless Chrome against the live backend with real accumulated scan data (200+ scans from this
session's own testing); zero hydration errors after the fixes above; ESLint's newer
`react-hooks/static-components` and `react-hooks/set-state-in-effect` rules caught two real issues
(a component defined inside another component's render in `HistoryTable`, and a synchronous
setState-in-effect in an early `ThemeToggle` draft) — both fixed, not suppressed.

### 3.2 — Extension: phishing interstitial

Today the popup is passive — the user has to click the toolbar icon to see a verdict, which most
people never do. Chrome's own Safe Browsing warns with a full-page interstitial; this closes that
gap for the `phishing` tier specifically.

- [x] **3.2.1** Content script (`extension/modules/interstitial.js`) injects a full-viewport
      overlay (blurred scrim + centered warning card) when `background.js` sees
      `verdict: "phishing"` for the active tab — gated on the verdict label itself (the 0.70
      threshold lives once, in `ml/shap_analysis.py::_label_for()`, not duplicated in extension JS).
      Rendered inside a **closed Shadow DOM** — the page under assessment is untrusted by
      definition, so it should not be able to inspect or style-interfere with the warning shown
      about it (see Test 5 in the manual plan).
- [x] **3.2.2** Overlay shows the top 3 reasons and two actions: **Leave this page** (messages
      `background.js`, which calls `chrome.tabs.remove` — content scripts have no direct `tabs`
      API access) and **I understand the risks, continue** (removes the overlay element locally;
      nothing is persisted to `chrome.storage` or anywhere else, so a fresh navigation to the same
      URL re-warns).
- [x] **3.2.3** Wired live against the Sprint 1 trained model (confirmed serving —
      `model_loaded: true`), not the heuristic fallback.

**Acceptance:** visiting a known-live PhishTank URL blurs the page and shows the warning card
within the same tick the popup would have updated; clicking "continue" reveals the underlying
page; a fresh navigation to the same URL re-triggers the warning (no persisted bypass).
**Code-complete; real-browser verification via `tests/manual/interstitial_test.md` still needed**
(same category as D7/D8 and Sprint 0.4 — DOM-injection behaviour that isn't meaningfully testable
in a Node sandbox, so no jsdom dependency was added just to simulate it).

### 3.3 — Deployment

- [ ] **3.3.1** Deploy backend to Railway or Render; provision Postgres; run `alembic upgrade head`.
- [ ] **3.3.2** Deploy dashboard to Vercel with `NEXT_PUBLIC_BACKEND_URL` set.
- [ ] **3.3.3** Point `extension/config.js` at both live URLs; record them in `PROJECT_STATE.md`.

**Acceptance:** live `GET /health` returns `model_loaded: true` within 3 seconds. Scan records
persist across a redeploy.

### 3.4 — End-to-end validation

- [ ] **3.4.1** `tests/e2e/system_test.md` — **30 URLs**: 15 live PhishTank, 15 legitimate
      *including deep-path URLs* (GitHub file view, Wikipedia article, a docs page, a search
      results page). The previous plan's 10 URLs cannot support any statistical claim, and its
      legitimate examples were all bare domains — exactly the blind spot D1 created.
- [ ] **3.4.2** Execute; record URL, expected, actual, risk %, pass/fail, and the confusion matrix.
- [ ] **3.4.3** Fix whatever it surfaces.

**Acceptance:** ≥ 26/30 correct, **with zero false positives among the deep-path legitimate URLs**.
That second condition is the real bar.

### 3.5 — Stretch (only if 3.1–3.4 are complete)

- [ ] **3.5.1** [STRETCH] Exfiltration heuristic: POST bodies > 10KB to a non-tracker third party.
- [ ] **3.5.2** [STRETCH] "Mark as safe" false-positive reporting → `POST /report`.
- [ ] **3.5.3** [STRETCH] Unlisted Chrome Web Store submission.

---

## Sprint 4 — Write-up and defense

**Week 4, to 2026-09-06 · Theme: make the work legible to an examiner.**

### 4.1 — Evaluation report

- [ ] **4.1.1** Finalise `ml/reports/evaluation_report.md`: dataset provenance and the leakage
      audit before/after; both split protocols; the baseline table; calibration; faithfulness;
      false-positive rate on popular deep URLs; latency. **Real measured numbers only.**
- [ ] **4.1.2** Write the methodology narrative around the leakage audit — how the flaw was found,
      what it would have cost, how it was fixed, and what the honest metrics are. Examiners reward
      a documented mistake far more than a suspiciously perfect result.
- [ ] **4.1.3** `LIMITATIONS.md`: browser-sandbox scope (no OS traffic, no HTTPS payloads),
      dataset freshness, VT free-tier limits, fusion weights are hand-set rather than learned,
      research-scale deployment.

### 4.2 — Documentation

- [ ] **4.2.1** Finalise `README.md`: problem, architecture diagram, setup from a fresh clone,
      live links, headline results.
- [ ] **4.2.2** Verify a fresh clone reproduces the documented setup. Actually do this — on a
      clean directory.
- [ ] **4.2.3** Confirm Swagger `/docs` is reachable on the live deployment.

### 4.3 — Defense

- [ ] **4.3.1** Record a 2-minute demo: popup scan → phishing verdict with reasons → full report →
      SHAP waterfall → history.
- [ ] **4.3.2** Five-slide technical summary: architecture → multi-signal fusion → explainability →
      evaluation → limitations and future work.
- [ ] **4.3.3** Prepare answers to the questions this design invites:

  1. *"Why XGBoost, not a neural network?"* — Tabular features, small data, no GPU; SHAP
     `TreeExplainer` is exact and fast for tree ensembles, whereas deep-model attribution is
     approximate. Explainability-first design makes this the right tool.
  2. *"Why rules for permissions, not ML?"* — Near-binary signal with no labelled corpus; a
     documented weight is faster, auditable, and yields a cleaner explanation than a learned one.
  3. *"Why not just use a blocklist?"* — §2.2 baseline table: the model catches URLs absent from
     the blocklist by generalising from structure. Quantified under a temporal split.
  4. **"Isn't using VirusTotal circular, since VT ingests PhishTank?"** — Yes, which is exactly
     why VT is *not* a trained feature (ADR-013). It is live corroboration shown to the user.
     **Anticipating this question is worth more than avoiding it.**
  5. *"How do you know your dataset isn't leaking?"* — The audit script and the before/after
     table; the D1 artifact was found, quantified and removed.
  6. *"How do you know the explanations are real?"* — §2.4 faithfulness ablation.
  7. *"What can't a browser extension see?"* — OS-level traffic, other applications, HTTPS
     payload contents. Scope is the browser sandbox, stated explicitly, not overclaimed.

- [ ] **4.3.4** Pre-defense check: live `/health` green, dashboard loads, demo video accessible.

---

## Sprint summary

| Sprint | Window | Theme | Exit criterion |
|---|---|---|---|
| **0** | Days 1–2 | Make it run, fail loudly | `/health` truthful; CI green; extension loads clean |
| **1** | to 2026-08-16 | Rebuild the ML core (C1, C2) | Honest dataset; fusion live; deep legit URL scores < 0.40 |
| **2** | to 2026-08-23 | Rigorous evaluation (C1, C3) | Baselines, calibration, faithfulness measured |
| **3** | to 2026-08-30 | Complete the product | Deployed; phishing interstitial live; 26/30 E2E; zero deep-URL false positives |
| **4** | to 2026-09-06 | Write-up and defense | Report, README, demo video, viva prep |

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| No usable path-bearing benign corpus found | Medium | High — blocks Sprint 1 | Fall back to crawling Tranco domains for internal URLs; budget 1 day, run overnight |
| Honest F1 drops below 0.85 | Medium | Medium | This is acceptable and expected. Report it, explain why it is more credible than the leaky 0.97, and analyse the errors. Do **not** tune against the test set |
| VT free tier exhausted during demo | Low | Medium | 1-hour TTL cache already in place; VT is corroboration only (ADR-013), so exhaustion degrades display, never the verdict |
| Deployment platform free tier cold-starts | Medium | Low | Warm the live endpoint before the demo; `/health` is in the pre-flight check |
| Sprint 3 overruns | Medium | Medium | Cut §3.5 stretch, then §3.2 (interstitial — 3.4's E2E acceptance doesn't depend on it), then §3.1.6, then §3.1.5. Never cut Sprints 1–2 |
