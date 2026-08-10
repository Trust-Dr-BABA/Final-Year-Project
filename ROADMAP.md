# ROADMAP — Explainable Multi-Signal Phishing Detection in the Browser

> **Last updated:** 2026-08-09
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
| **D4** | **Artifact drift, unguarded.** `feature_columns.json` lists 12 columns; `features.csv` has 8. No `xgboost_phishing.pkl` exists. Nothing asserts the model and the column list agree. | `ml/models/` | Sprint 0 |
| **D5** | **Every failure path returns a plausible verdict.** Missing model, missing deps, wrong mount path — all fall through to `_simple_rule_prediction()`. The Docker image never installs the `[ml]` extras, and compose mounts models to `/app/models` while the loader reads `/app/ml/models`. A demo would appear to work with the ML core inert. | `ml/shap_analysis.py:135`, `backend/Dockerfile:14`, `docker/docker-compose.yml:35` | Sprint 0 |

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

- [ ] **0.1.1** Add the missing runtime deps to `backend/pyproject.toml`: `alembic`,
      `python-dotenv`, `greenlet`. Move `pandas` and `joblib` from `[ml]` into the base
      dependencies — `ml/shap_analysis.py` imports them on the request path, so they are not
      optional in a serving container.
- [ ] **0.1.2** Create `.venv` and install: `pip install -e "./backend[ml,dev]"`. Record the exact
      commands in `README.md`.
- [ ] **0.1.3** Fix `backend/Dockerfile:14` to install `.[ml]` rather than `.` — the image
      currently ships without xgboost, shap or pandas.
- [ ] **0.1.4** Fix the model volume mount in `docker/docker-compose.yml:35`: `/app/models` →
      `/app/ml/models`, matching `MODELS_DIR` in `ml/shap_analysis.py:18`.

**Acceptance:** `pytest tests/ -q` runs to completion locally (failures allowed, collection errors
not). `docker compose up` starts all three services with no import errors in the backend log.

### 0.2 — Fail loudly, not quietly

- [ ] **0.2.1** Gate the fallback in `ml/shap_analysis.py`: `explain_prediction()` raises
      `ModelUnavailableError` unless `ESA_ALLOW_FALLBACK=1` is set. Development keeps the
      fallback; deployment does not silently degrade.
- [ ] **0.2.2** Add a load-time lockstep assertion: `model.n_features_in_ == len(feature_columns)`,
      raising with both values on mismatch. This one check catches D4 and every future recurrence.
- [ ] **0.2.3** Extend `GET /health` in `backend/main.py` to return
      `{status, version, model_loaded, feature_count, model_sha256, vt_key_configured, db_reachable}`.
      This becomes the pre-demo checklist on defense day.

**Acceptance:** with no `.pkl` present and `ESA_ALLOW_FALLBACK` unset, `POST /analyze` returns
**503**, not a fabricated verdict. `GET /health` reports `model_loaded: false`. With the model
present, both flip.

### 0.3 — Database migrations

- [x] **0.3.1** `alembic init` inside `backend/`; wire `alembic.ini` to `DATABASE_URL` from env.
      _Merged from `origin/main` 2026-08-09; `env.py` is async-correct._
- [/] **0.3.2** Autogenerate and apply the initial `scans` migration.
      Migration `ab476f0dcf44_create_scans_table` exists and matches
      `backend/models/scan.py` exactly. **Still to verify: `alembic upgrade head` against a
      running database.**

**Acceptance:** `alembic upgrade head` applies cleanly against the compose Postgres; `\d scans`
shows all JSONB columns.

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
**Not yet executed** — the code is in place, but this must be observed in a real browser before
0.4 is closed.

### 0.5 — Continuous integration

- [ ] **0.5.1** Add `.github/workflows/ci.yml`: `pytest`, `npx tsc --noEmit` in `dashboard/`,
      and `ruff check`. A green CI badge is a cheap, visible professionalism signal.
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

- [ ] **1.1.1** Write `ml/scripts/audit_dataset.py`. For a given dataset it reports, per feature:
      single-feature ROC-AUC, class-conditional means, and the **path-presence rate per class**
      (fraction of URLs with a non-trivial path). Flags any feature exceeding 0.90 AUC alone.
- [ ] **1.1.2** Run it against the *current* `dataset.csv` and save the output to
      `ml/reports/leakage_audit_before.md`.

**Acceptance:** the "before" audit demonstrates the D1 artifact numerically — expect path-presence
near 0% for label 0 and near 100% for label 1, and `url_length` AUC above 0.90. **This table is a
deliverable, not scaffolding:** the before/after pair is what converts a methodological flaw into
evidence of methodological awareness, and it belongs in the evaluation chapter.

### 1.2 — Rebuild the dataset honestly

- [ ] **1.2.1** Rewrite `ml/scripts/prepare_dataset.py` to stop discarding PhishTank metadata.
      `usecols=["url"]` at line 28 throws away `submission_time`, `target` (the impersonated brand)
      and `verified`/`online` — all free, and all needed later: `submission_time` enables the
      temporal split (1.2 of Sprint 2), `target` gives ground truth for evaluating
      `brand_impersonation`. Filter to `verified == yes`.
- [ ] **1.2.2** Source a **path-bearing benign corpus** so both classes have realistic URL
      structure. Preferred: sample benign full URLs from a public URL-level corpus (PhiUSIIL/UCI,
      or a Common Crawl index sample). Crawling 10k Tranco domains for real internal URLs is the
      fallback if no corpus is usable — correct but slow.
- [ ] **1.2.3** Reserve Tranco top-1000 (with real deep paths) as a **held-out false-positive
      evaluation set**, never as training negatives. This is the set that answers "does it flag
      Wikipedia?".
- [ ] **1.2.4** Update `ml/data/raw/DATASET_SOURCES.md` with every source, download date, row
      count and licence. This is the provenance citation in the report.
- [ ] **1.2.5** Re-run the audit → `ml/reports/leakage_audit_after.md`.

**Acceptance:** no single feature exceeds 0.90 AUC alone; path-presence rate within 15 percentage
points across classes; ≥ 15,000 rows, each class ≥ 40%.

### 1.3 — Feature set parity

- [ ] **1.3.1** Regenerate `features.csv` with the *current* extractor. The existing file predates
      `brand_impersonation` and is missing it entirely.
- [ ] **1.3.2** Remove the three VirusTotal columns from the trained feature set per **ADR-013**.
      They stay in `url_features.py` and on the scan record for display and corroboration — they
      are simply not learned from. See ADR-013 for the circularity argument; this is a defensible
      design decision, not an omission, and should be presented as such.
- [ ] **1.3.3** Assert that `get_feature_names()` in `url_features.py` matches the generated
      columns exactly — a unit test, so the two cannot drift again.

**Acceptance:** `pytest tests/unit/test_url_features.py` passes with a new parity test; `features.csv`
column set equals `get_feature_names()` minus the VT columns.

### 1.4 — Implement the fusion layer (claim C2)

- [ ] **1.4.1** Create `backend/services/risk_fusion.py` implementing **ADR-014**: the URL model
      yields `p_url`; each browser signal contributes a fixed, documented weight added in
      **log-odds space**; the sum maps back through a sigmoid to the final score.
- [ ] **1.4.2** Emit one attribution entry per active browser signal in the *same* shape SHAP
      already produces — `{feature, value, shap_impact, human_readable}` via
      `explainer_formatter.format_reason()`. Because SHAP values are themselves additive log-odds
      contributions, the two families are directly comparable and can be ranked in one list.
      **No schema change is needed anywhere downstream** — popup, dashboard and DB all work as-is.
- [ ] **1.4.3** Rewrite `explain_prediction()` so it no longer silently drops unknown keys (D2).
      Unrecognised features must raise, not vanish.
- [ ] **1.4.4** Document every weight and its justification in `ml/reports/fusion_weights.md`.

**Acceptance:** `POST /analyze` with `tracker_count: 40, has_mixed_content: true` returns a
strictly higher score than the same URL with clean signals, and `top_reasons` contains at least
one browser-signal attribution.

### 1.5 — Retrain

- [ ] **1.5.1** Run `python ml/scripts/train_model.py`. It already writes `.pkl` and
      `feature_columns.json` from one run — the previous drift came from hand-editing the JSON
      afterwards. The Sprint 0 lockstep assertion now prevents that.
- [ ] **1.5.2** Record the honest metrics. **Expect F1 to fall** relative to the old inflated
      number — that fall is the point, and a drop from a leaky 0.97 to an honest 0.90 is a
      *stronger* result, not a weaker one. Say so explicitly in the report.

**Acceptance:** `GET /health` reports `model_loaded: true` with matching `feature_count`;
`https://github.com/torvalds/linux/blob/master/README` scores **below 0.40**;
a known-live PhishTank URL scores **above 0.70**.

---

## Sprint 2 — Rigorous evaluation and the remaining defects

**Week 2, to 2026-08-23 · Theme: make claims C1 and C3 provable.**

This is the sprint that separates "built a classifier" from "evaluated a classifier". Most items
are cheap to compute and disproportionately persuasive in a viva.

### 2.1 — Evaluation protocols

- [ ] **2.1.1** **Temporal split** on `submission_time`: train on the earlier window, test on the
      later. This is the standard rigorous protocol for phishing detection and is far more
      convincing than a random split, because it mirrors deployment — you always predict the
      future. Report random and temporal side by side.
- [ ] **2.1.2** **Unseen-registrable-domain holdout**: guarantee no eTLD+1 appears in both train
      and test. Prevents the model from memorising domains.
- [ ] **2.1.3** **False-positive rate on the Tranco top-1000 deep-URL set** from 1.2.3. For a
      browser extension this single number is the most persuasive evidence it is usable —
      a detector that cries wolf on popular sites is worthless regardless of its F1.

### 2.2 — Baselines (claim C1)

- [ ] **2.2.1** Implement four baselines and one table: (a) blocklist lookup against the training
      PhishTank set, (b) `url_length` threshold only, (c) logistic regression on the same features,
      (d) URL-only XGBoost, (e) full fused model.
- [ ] **2.2.2** Report precision/recall/F1/AUC for each under both splits.

**Acceptance:** the table shows the fused model beating the blocklist *specifically on URLs absent
from the blocklist* — the direct, quantitative answer to "why not just use a blocklist?". Baseline
(b) is included precisely to show the D1 artifact is gone: it should now perform poorly.

### 2.3 — Calibration (justifies the word "confidence")

- [ ] **2.3.1** Reliability diagram, Brier score and Expected Calibration Error on the temporal
      test set.
- [ ] **2.3.2** If ECE is poor, fit Platt scaling or isotonic regression on a validation split and
      report before/after.

**Acceptance:** `ml/reports/evaluation_report.md` contains the reliability diagram. The product
displays a confidence percentage in its core UX; this is the evidence that number means anything.
Without it, "92% confident" is a decorative number — an easy and damaging viva question.

### 2.4 — Explanation faithfulness (claim C3)

- [ ] **2.4.1** Implement a top-k ablation check: for N test URLs, neutralise the top-3 SHAP
      features to their training medians, re-score, and measure the score shift against the shift
      the attributions predicted.
- [ ] **2.4.2** Report mean absolute error between predicted and observed shift, plus the fraction
      of cases where the score moves in the predicted direction.

**Acceptance:** ≥ 90% directional agreement, documented. This validates the project's central
claim rather than assuming it — very few undergraduate projects evaluate their own explanations,
and doing so is the clearest available differentiator.

### 2.5 — Fix the confidence semantics (ADR-015)

- [ ] **2.5.1** Split the two concepts: `risk_pct = round(p * 100)`;
      `confidence_pct = round(max(p, 1-p) * 100)`. Today `confidence_pct` *is* the phishing
      probability, which makes the dashboard's "Average Confidence" card meaningless (it averages
      risk) and forces `popup.js:75` to compute `100 - confidence` for safe pages.
- [ ] **2.5.2** Propagate through `backend/models/scan.py`, `routers/analyze.py`, `routers/history.py`,
      `dashboard/lib/types.ts`, `extension/popup/popup.js`. Add an Alembic migration for the new column.

**Acceptance:** a legitimate page shows "96% confident this page is safe" and a phishing page
"94% confident this is phishing", both read directly from the response with no arithmetic in the UI.

### 2.6 — Extension correctness

- [ ] **2.6.1** Move permission interception to the **main world** (`"world": "MAIN"` in the
      manifest content-script entry, or an injected `<script>`). The current isolated-world patch
      of `Notification.requestPermission` cannot observe the page's own calls — the permission
      signal family is currently **non-functional**, not merely incomplete.
- [ ] **2.6.2** Resolve the ordering race: analysis fires on `tabs.onUpdated` complete, but
      `content_script.js` posts permission signals 3.5s after `load`. Either await the message
      with a bounded timeout before analysing, or re-analyse when it arrives.
- [ ] **2.6.3** Create `extension/modules/permission_monitor.js` and move the heuristics out of
      `content_script.js`, matching the documented module layout.
- [ ] **2.6.4** Write `tests/manual/permission_monitor_test.md` with a local fixture page that
      requests camera on load, and verify no false flags on `https://google.com`.

**Acceptance:** loading the fixture page produces `cam_mic_on_first_visit` in the stored
`permissionSignals`, and that flag reaches `top_reasons` in the popup.

### 2.7 — Performance

- [ ] **2.7.1** Benchmark `/analyze` p50/p95, VT cache cold and warm. Record in the report.

**Acceptance:** p95 under 10s cold, under 1s warm.

---

## Sprint 3 — Complete the product surface

**Week 3, to 2026-08-30 · Theme: a demo that survives being clicked on.**

### 3.1 — Dashboard

- [ ] **3.1.1** `npm install recharts date-fns` — **not currently installed**, despite the previous
      roadmap marking this done. Note `dashboard/AGENTS.md`: this is **Next.js 16**, not 14; read
      `node_modules/next/dist/docs/` before writing App Router code rather than assuming Next 14
      conventions.
- [ ] **3.1.2** Replace the placeholder `<div>` at `dashboard/app/page.tsx:83` with a real
      `RiskDistributionChart`.
- [ ] **3.1.3** Build `app/history/page.tsx` — sortable, paginated table: URL, verdict badge,
      risk %, confidence %, timestamp; row click → detail.
- [ ] **3.1.4** Build `app/scan/[id]/page.tsx` — verdict banner, risk bar, network signals card,
      permission flags card, VT corroboration card (per ADR-013, shown but not modelled).
- [ ] **3.1.5** `components/charts/ShapWaterfallChart.tsx` — horizontal bars, top 5 attributions,
      red increases risk / green decreases, labelled with `human_readable`. Browser-signal
      attributions render identically to SHAP ones, which is the visual payoff of ADR-014.
- [ ] **3.1.6** `components/charts/RiskSparkline.tsx` — risk over time for repeat scans of a URL.

**Acceptance:** `npx tsc --noEmit` clean; every page renders against live backend data; no
snake_case anywhere in the rendered DOM.

### 3.2 — Deployment

- [ ] **3.2.1** Deploy backend to Railway or Render; provision Postgres; run `alembic upgrade head`.
- [ ] **3.2.2** Deploy dashboard to Vercel with `NEXT_PUBLIC_BACKEND_URL` set.
- [ ] **3.2.3** Point `extension/config.js` at both live URLs; record them in `PROJECT_STATE.md`.

**Acceptance:** live `GET /health` returns `model_loaded: true` within 3 seconds. Scan records
persist across a redeploy.

### 3.3 — End-to-end validation

- [ ] **3.3.1** `tests/e2e/system_test.md` — **30 URLs**: 15 live PhishTank, 15 legitimate
      *including deep-path URLs* (GitHub file view, Wikipedia article, a docs page, a search
      results page). The previous plan's 10 URLs cannot support any statistical claim, and its
      legitimate examples were all bare domains — exactly the blind spot D1 created.
- [ ] **3.3.2** Execute; record URL, expected, actual, risk %, pass/fail, and the confusion matrix.
- [ ] **3.3.3** Fix whatever it surfaces.

**Acceptance:** ≥ 26/30 correct, **with zero false positives among the deep-path legitimate URLs**.
That second condition is the real bar.

### 3.4 — Stretch (only if 3.1–3.3 are complete)

- [ ] **3.4.1** [STRETCH] Exfiltration heuristic: POST bodies > 10KB to a non-tracker third party.
- [ ] **3.4.2** [STRETCH] "Mark as safe" false-positive reporting → `POST /report`.
- [ ] **3.4.3** [STRETCH] Unlisted Chrome Web Store submission.

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
| **3** | to 2026-08-30 | Complete the product | Deployed; 26/30 E2E; zero deep-URL false positives |
| **4** | to 2026-09-06 | Write-up and defense | Report, README, demo video, viva prep |

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| No usable path-bearing benign corpus found | Medium | High — blocks Sprint 1 | Fall back to crawling Tranco domains for internal URLs; budget 1 day, run overnight |
| Honest F1 drops below 0.85 | Medium | Medium | This is acceptable and expected. Report it, explain why it is more credible than the leaky 0.97, and analyse the errors. Do **not** tune against the test set |
| VT free tier exhausted during demo | Low | Medium | 1-hour TTL cache already in place; VT is corroboration only (ADR-013), so exhaustion degrades display, never the verdict |
| Deployment platform free tier cold-starts | Medium | Low | Warm the live endpoint before the demo; `/health` is in the pre-flight check |
| Sprint 3 overruns | Medium | Medium | Cut §3.4 stretch, then §3.1.6, then §3.1.5. Never cut Sprints 1–2 |
