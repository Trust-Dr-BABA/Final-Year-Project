# PROJECT STATE — Explainable Multi-Signal Phishing Detection in the Browser

> **Purpose.** The live state of the project: what is actually true right now, every architectural
> decision and its rationale, and the running activity log.
> **Companion doc:** [`ROADMAP.md`](ROADMAP.md) — what to build and in what order.
> **Read this first** at the start of every session, then find the current task in the roadmap.

---

## Current status

| Field | Value |
|---|---|
| **Deadline** | 2026-09-06 (4 weeks from 2026-08-09) |
| **Current sprint** | Sprint 3 — Complete the product surface |
| **Current task** | `3.2.1` — phishing interstitial content-script overlay |
| **Recently merged** | Sprints 0–2 complete; Sprint 3.1 complete as of 2026-08-13 |
| **Status** | 🟢 Sprint 0, 1 and 2 all done and verified. Sprint 3.1 (dashboard pages + charts + full visual redesign) done and verified in both themes. Moving to 3.2 (interstitial) |
| **Blocked?** | No |
| **Last full audit** | 2026-08-13 |

### Live endpoints

| Service | URL | Status |
|---|---|---|
| Backend API | `localhost:8000` (Docker, local dev only) | ✅ Running, model loaded, fusion live |
| Dashboard | _(not deployed — Sprint 3.2.2)_ | ⏳ Pending |
| PostgreSQL | `localhost:5432` (Docker) | ✅ Migrated to `33be02683ae4` (adds `risk_pct`) |
| Demo video | _(Sprint 4.3.1)_ | ⏳ Pending |

---

## Where the project actually is

Audited against the working tree on 2026-08-09. The previous state file's checkboxes had drifted
substantially from the code; this section is the corrected baseline.

### Implemented and working

| Component | State |
|---|---|
| URL feature extraction | 9 trained features (8 lexical + `brand_impersonation`) plus 3 VirusTotal fields kept for display |
| VirusTotal client | Async, 5s timeout, `TTLCache` (256 entries / 1h), graceful `-1` fallback |
| Heuristics engine | 6 rule flags + 6 derived numeric features over network and permission signals |
| Human-readable templates | All 21 feature names mapped in `shared/feature_name_to_human_readable.json` |
| Backend endpoints | `/analyze`, `/history`, `/stats`, `/scan/{id}`, `/health` — all implemented |
| Database model | `Scan` ORM with JSONB columns; correct. **Migration not yet generated** |
| Extension — network | Tracker counting (500 EasyPrivacy domains), mixed content, top-level-only redirect counting |
| Extension — popup | 5-state UI, dark theme, retry, dashboard link |
| Dashboard | Next.js 16 + Tailwind 4, typed API client, overview page, verdict/confidence badges |
| Tests | Unit: URL features, explainer formatter, SHAP, VT client, network monitor (JS). Integration: `/analyze` schema |

### Not implemented, despite prior claims

| Previously marked done | Reality |
|---|---|
| Trained model | **No `xgboost_phishing.pkl` exists.** Never committed (gitignored) and not present locally |
| `recharts` / `date-fns` installed | **Not in `dashboard/package.json`** |
| `permission_monitor.js` | **File does not exist**; heuristics live inline in `content_script.js` |
| ML notebooks (01–05) | **`ml/notebooks/` does not exist** |
| `ml/features/url_features.py` | **Deleted** — consolidated into `backend/feature_extractor/url_features.py` |
| Dashboard history / scan-detail pages | **Not created** |

### Open defects

Full detail and evidence in [`ROADMAP.md` §3](ROADMAP.md). Summary:

| # | Defect | Sprint |
|---|---|---|
| ~~D1~~ | Dataset trivially separable — benign class is bare Tranco domains, phishing class is full URLs with paths — **fixed 2026-08-13**: rebuilt with crawled deep-path benign URLs, path-presence gap 65.2→13.6 points, `url_length` AUC 0.88→0.50 | 1 |
| ~~D2~~ | Browser-signal features silently dropped by `explain_prediction()`; multi-signal fusion not actually wired in — **fixed 2026-08-13**: `risk_fusion.py` (ADR-014), unknown keys now raise | 1 |
| **D3** | VT features constant `-1` across all training rows, and would be label-circular if populated — **by design, not a defect**: VT is deliberately excluded from training per ADR-013; the `-1` sentinel is correct for a value the model never sees | 1 |
| ~~D4~~ | `feature_columns.json` (12 cols) ≠ `features.csv` (8 cols); nothing asserts lockstep — **fully fixed 2026-08-13**: guard added 08-12, retrain 08-13 now writes a matching 9-column pair (`brand_impersonation` restored) | 0/1 |
| ~~D5~~ | Every failure path silently falls back to a heuristic verdict; Docker omits `[ml]` extras; model volume mounted to the wrong path — **fixed** 2026-08-12, verified live (see activity log) | 0 |
| ~~D6~~ | ~~`manifest.json` missing `webNavigation`~~ — **fixed**, merged from `origin/main` 2026-08-09 | ✅ |
| ~~D7~~ | Permission interception runs in the isolated world → cannot observe the page's real calls; signal family non-functional — **fixed 2026-08-13**: `extension/modules/permission_monitor.js` runs in the MAIN world (`"world": "MAIN"`), relays via `CustomEvent` to the isolated-world `content_script.js`. Automated test passing; real-browser verification still pending (see ROADMAP §2.6) | 2 |
| ~~D8~~ | Permission signals arrive ~3.5s after analysis has already fired — **fixed 2026-08-13**: `background.js` re-runs analysis when a new permission rule flag arrives after the initial analysis completed, instead of delaying every analysis to wait for a signal that usually never comes | 2 |

---

## Architectural decision records

Decisions are append-only. To change one, add a superseding ADR — do not edit history.

| # | Decision | Rationale | Date | Status |
|---|---|---|---|---|
| ADR-001 | Chrome MV3 | MV2 deprecated; MV3 required for new extensions | 2026-07-24 | Active |
| ADR-002 | XGBoost, not a neural network | Tabular features, small data, no GPU; SHAP `TreeExplainer` is *exact* for tree ensembles while deep-model attribution is approximate. Explainability-first design | 2026-07-24 | Active |
| ADR-003 | Rules for permission signals, not ML | Near-binary signal with no labelled corpus; faster, auditable, cleaner explanations | 2026-07-24 | Active |
| ADR-004 | Single unified model, not three | Avoids maintaining three pipelines on a short timeline | 2026-07-24 | Active |
| ADR-005 | FastAPI | Async-first, auto OpenAPI, Pydantic validation | 2026-07-24 | Active |
| ADR-006 | Next.js App Router | SSR, TypeScript-first, zero-config Vercel deploy | 2026-07-24 | Active |
| ADR-007 | PostgreSQL with JSONB for SHAP output | Variable-length attribution arrays; relational metadata | 2026-07-24 | Active |
| ADR-008 | VirusTotal instead of WHOIS | WHOIS is slow (3–12s), rate-limited and format-inconsistent; VT returns age and reputation in one call | 2026-07-24 | **Amended by ADR-013** |
| ADR-009 | `confidence_pct` alongside `risk_score` | "87% confident" reads better than "0.87" | 2026-07-24 | **Superseded by ADR-015** |
| ADR-010 | All feature names translated before reaching any UI | No snake_case may ever be user-visible | 2026-07-24 | Active |
| ADR-011 | Never cut SHAP explainability | Core academic contribution; examiners evaluate it specifically | 2026-07-24 | Active |
| ADR-012 | Baseline comparison in evaluation | Must show the model beats a blocklist on unseen URLs | 2026-07-24 | Active |
| **ADR-013** | **VirusTotal is a live corroboration signal, never a trained feature** | See below | 2026-08-09 | Active |
| **ADR-014** | **Browser signals fuse via transparent log-odds weights, not as trained features** | See below | 2026-08-09 | Active |
| **ADR-015** | **`risk_pct` and `confidence_pct` are separate quantities** | See below | 2026-08-09 | Active |
| **ADR-016** | **Fail loudly: no silent fallback in a serving deployment** | See below | 2026-08-09 | Active |

### ADR-013 — VirusTotal is corroboration, not a feature

**Amends ADR-008. VT stays; it just stops being modelled.**

Training on VirusTotal verdicts would be **circular**. VirusTotal ingests PhishTank feeds, so for
any PhishTank-sourced training row, `vt_malicious_votes > 0` is close to a restatement of the
label. A model trained on it would report excellent metrics that measure nothing but the leak, and
this is exactly the kind of flaw an examiner probes.

Two practical constraints point the same way: the free tier (4 req/min, 500/day) cannot label
20,000 domains, and no *time-consistent* VT snapshot for the training epoch is obtainable — VT
reputation today reflects knowledge accumulated after the URL was labelled.

**Decision.** VT is queried live during `/analyze`, displayed in the popup and dashboard as
independent corroboration, and persisted on the scan record. It is removed from
`feature_columns.json`. Degradation to `-1` on timeout affects display only and can never change
a verdict.

**Why this is a strength.** It converts a hidden methodological flaw into a prepared answer:
*"Isn't using VirusTotal circular?"* — *"Yes, which is precisely why it isn't a trained feature."*

### ADR-014 — Transparent log-odds fusion for browser signals

Claim C2 (detection is genuinely multi-signal) requires browser signals to affect the score. But
no labelled corpus carries per-URL tracker counts or permission-prompt timings, and synthesising
them would be indefensible.

**Decision.** The URL model produces `p_url`. Each browser signal contributes a fixed, documented
weight added in **log-odds space**; the sum passes back through a sigmoid.

This works because SHAP values *are* additive log-odds contributions. A hand-set weight and a SHAP
value therefore live on the same scale and can be ranked in a single `top_reasons` list, rendered
by the same waterfall chart, with no schema change anywhere downstream. Each browser signal's
attribution is exactly its weight — trivially auditable, unlike a learned coefficient.

**Cost, stated honestly:** the weights are hand-set, not learned. This is recorded in
`LIMITATIONS.md`, justified in `ml/reports/fusion_weights.md`, and probed by a sensitivity
analysis in Sprint 2.

### ADR-015 — Separate risk from confidence

**Supersedes ADR-009.** Today `confidence_pct = round(p_phishing * 100)`. That conflates two
different quantities, with visible consequences: the dashboard's "Average Confidence Score" card
actually averages *risk*, and `popup.js:75` must compute `100 - confidence` to render a safe page.

**Decision.**

- `risk_pct = round(p * 100)` — how phishing-like the page is
- `confidence_pct = round(max(p, 1-p) * 100)` — how decisive the model is, either way

"94% confident this is phishing" and "96% confident this page is safe" then both read directly
from the response, with no arithmetic in any UI. The average-confidence card becomes a real
decisiveness metric. Calibration evidence for these numbers is produced in Sprint 2.3.

### ADR-016 — Fail loudly

The system currently has four independent paths to `_simple_rule_prediction()`: no model file, no
SHAP install, no pandas, wrong mount path. All four return a confident-looking verdict with
placeholder reasons. A demo could run start to finish with the ML core inert and nothing would say so.

**Decision.** `explain_prediction()` raises unless `ESA_ALLOW_FALLBACK=1` (development only).
`/health` reports `model_loaded`, `feature_count`, `model_sha256`, `vt_key_configured` and
`db_reachable`. Model load asserts `model.n_features_in_ == len(feature_columns)`.

---

## Directory structure (verified 2026-08-12)

```
fyp/
├── backend/
│   ├── main.py                          ✅ FastAPI app, CORS, /health (now reports model/db status)
│   ├── database.py                      ✅ Async engine + get_db + check_db_reachable()
│   ├── Dockerfile                       ✅ Installs .[ml] (D5 fixed)
│   ├── pyproject.toml                   ✅ alembic/python-dotenv/greenlet + pandas/joblib in base deps
│   ├── models/scan.py                   ✅ Scan ORM
│   ├── alembic/                         ✅ Async env.py + create_scans_table migration
│   ├── alembic.ini                      ✅ Reads DATABASE_URL from env
│   ├── routers/
│   │   ├── analyze.py                   ✅ POST /analyze — full pipeline, 503 on ModelUnavailableError
│   │   └── history.py                   ✅ /history, /stats, /scan/{id}
│   ├── services/
│   │   ├── heuristics_engine.py         ✅ 6 rules + 6 derived features
│   │   ├── explainer_formatter.py       ✅ Template substitution
│   │   ├── virustotal_client.py         ✅ Async + TTLCache
│   │   └── risk_fusion.py               🔲 Sprint 1.4 (ADR-014)
│   └── feature_extractor/url_features.py ✅ 9 trained features + 3 VT (display only per ADR-013)
│
├── extension/
│   ├── manifest.json                    ✅ webNavigation + icons (D6 fixed 2026-08-09)
│   ├── background.js                    ✅ Orchestration, badge, storage
│   ├── content_script.js                ⚠️  Isolated-world patching — non-functional (D7)
│   ├── config.js                        ✅ Backend + dashboard URLs
│   ├── tracker_domains.json             ✅ 500 EasyPrivacy domains (bundled copy)
│   ├── modules/
│   │   ├── network_monitor.js           ✅ Trackers, mixed content, top-level redirects
│   │   └── permission_monitor.js        🔲 Sprint 2.6.3
│   ├── services/api_client.js           ✅ AbortController timeout
│   ├── popup/                           ✅ 5-state UI, dark theme
│   ├── README.md                        ✅ Load-unpacked setup guide
│   └── icons/                           ✅ 16/48/128 PNGs
│
├── dashboard/                           Next.js 16 + React 19 + Tailwind 4
│   ├── app/
│   │   ├── layout.tsx                   ✅ Root layout + Navbar
│   │   ├── page.tsx                     ⚠️  Chart is a placeholder div (Sprint 3.1.2)
│   │   ├── history/                     🔲 Sprint 3.1.3
│   │   └── scan/[id]/                   🔲 Sprint 3.1.4
│   ├── components/                      ✅ VerdictBadge, ConfidenceBadge, layout/
│   │   └── charts/                      🔲 Sprint 3.1.5–3.1.6
│   ├── lib/{api,types}.ts               ✅ Typed client + schemas
│   └── package.json                     ⚠️  recharts + date-fns not installed
│
├── ml/
│   ├── data/
│   │   ├── raw/                         ✅ phishtank.csv (10k), tranco.csv (10k), DATASET_SOURCES.md
│   │   └── processed/                   ⚠️  dataset.csv + features.csv both carry the D1 artifact
│   ├── models/
│   │   ├── feature_columns.json         ⚠️  12 columns; no model to match them (D4 guard is fixed, drift itself is Sprint 1)
│   │   └── xgboost_phishing.pkl         🔲 Does not exist
│   ├── scripts/
│   │   ├── prepare_dataset.py           ⚠️  Discards PhishTank metadata; bare-domain negatives (D1)
│   │   ├── generate_features.py         ⚠️  Never passes vt_data (D3)
│   │   ├── train_model.py               ✅ Correct; writes .pkl + columns together
│   │   └── audit_dataset.py             🔲 Sprint 1.1.1
│   ├── reports/                         🔲 Sprint 1–4
│   └── shap_analysis.py                 ⚠️  Silently drops unknown features (D2, Sprint 1.4); fallback now gated behind ESA_ALLOW_FALLBACK (D5 fixed), lockstep-asserted, and exposes get_model_status()
│
├── shared/
│   ├── brand_list.txt                   ✅ 50 brands
│   ├── tracker_domains.json             ✅ 500 EasyPrivacy domains
│   ├── TRACKER_DOMAINS_SOURCE.md        ✅ Provenance
│   └── feature_name_to_human_readable.json ✅ 21 templates
│
├── tests/
│   ├── conftest.py                      ✅ Env defaults + ESA_ALLOW_FALLBACK=1 for dev/test
│   ├── unit/                            ✅ 5 Python + 1 JS test module (25 cases)
│   ├── integration/                     ✅ test_analyze_endpoint.py
│   ├── manual/                          ✅ network_monitor_test.md
│   └── e2e/                             🔲 Sprint 3.3.1
│
├── docker/docker-compose.yml            ✅ Model volume mount fixed → /app/ml/models (D5 fixed)
├── .github/workflows/ci.yml             ✅ backend (ruff + pytest) + dashboard (tsc) jobs
├── ruff.toml                            ✅ New — two targeted E402 per-file-ignores
├── CLAUDE.md                            ✅ Agent-facing guide
├── README.md                            ✅ Thesis-facing overview
├── ROADMAP.md                           ✅ Sprint plan
└── PROJECT_STATE.md                     ✅ This file
```

---

## Working agreements

**Session start.** Read this file → note the current task → open `ROADMAP.md` → read the task
*and its acceptance criterion* → work.

**Task completion.** A task is done when its acceptance criterion has been **executed and
observed**, not when the code is written. Then: tick the box in `ROADMAP.md`, advance
**Current task** here, and add an activity log row.

**When blocked.** Set **Blocked?** to `Yes — <what and why>` and stop rather than working around it.

**Invariants — breaking any of these is a bug, not a style choice:**

1. No snake_case feature name may ever reach the popup or dashboard (ADR-010).
2. `feature_columns.json` and `xgboost_phishing.pkl` are written by the same training run and never
   edited by hand (D4).
3. Verdict thresholds: `> 0.70` phishing, `0.40–0.70` suspicious, `< 0.40` legitimate. Changing
   these requires a new ADR.
4. A VirusTotal failure degrades display only — it can never change a verdict (ADR-013).
5. No silent fallback in a serving deployment (ADR-016).
6. Evaluation numbers in any report are measured, never estimated or carried over from a prior run.

---

## Activity log

| Date | Agent | Action |
|---|---|---|
| 2026-07-24 | AntiGravity | Initial planning framework: 8-phase roadmap, project state, agent sync rules |
| 2026-07-24 | AntiGravity | Feature audit — VirusTotal replacing WHOIS, `confidence_pct`, baseline comparison, `suspicious_tld_flag`, human-readable mapping, in-memory caching. Removed backend URL re-fetching and the options page |
| 2026-07-24 | AntiGravity | Full skeleton scaffolded across backend, extension, ml, shared, tests, docker |
| 2026-08-02 | Cursor | Phase 2 ML: URL feature extractor, `generate_features.py`, 20k-row `features.csv`, XGBoost training, `shap_analysis.py` with `explain_prediction()`, unit tests |
| 2026-08-02 | AntiGravity | Code review: 5 fixes (gitignore, SHAP thresholds → 0.70/0.40, formatter return type, `has_ip_address` naming, logging). Next.js dashboard initialised |
| 2026-08-06 | Codex | Redirect counting restricted to top-level navigations (`frameId === 0`); manual network-monitor test plan |
| 2026-08-09 | Hammad (collaborator) | Alembic setup + `create_scans_table` migration; extension icons; `webNavigation` permission; extension setup guide; tracker subdomain matching |
| **2026-08-09** | **Claude** | **Merged `origin/main` (13 commits).** Kept: Alembic (Sprint 0.3), icons (0.4.2), `webNavigation` (fixes D6), `extension/README.md`, and tracker subdomain matching — reimplemented to walk parent domains rather than spreading the 500-entry Set per request, and to dedupe onto the base domain. Kept ours for `analyze.py` (incoming imports the removed `ml.features.url_features`, drops the VT call and `HttpUrl` validation), `ROADMAP.md` (incoming is an older copy), `shared/tracker_domains.json` (500 vs 20 entries), and the manual test plan. Dropped `extension/shared/` — a duplicate copy of the human-readable template map that would silently violate ADR-010 on drift. |
| **2026-08-09** | **Claude** | **Full audit against the working tree; roadmap and project state rewritten.** Found 8 defects, 3 of them viva-critical: dataset separability artifact (D1), multi-signal fusion never wired into the model (D2), VT features constant and label-circular (D3). Replaced the 8-phase/12-week plan with Sprint 0 + 4 weekly sprints to 2026-09-06, ordered by grade impact. Added ADR-013 (VT as corroboration), ADR-014 (log-odds fusion), ADR-015 (risk vs confidence, superseding ADR-009), ADR-016 (fail loudly). Consolidated four contradictory planning docs into `ROADMAP.md` + `PROJECT_STATE.md`, with `README.md` (thesis-facing) and `CLAUDE.md` (agent-facing). Added evaluation rigour to the plan: leakage audit, temporal split, unseen-domain holdout, calibration, SHAP faithfulness, deep-URL false-positive set. **No code changed in this pass.** |
| 2026-08-10 | Claude | Found and fixed a NumPy 2.x/1.x ABI break (`shap==0.45.0` needs `numpy<2`, now pinned in `backend/pyproject.toml[ml]`) and a broken `AsyncMock` in `test_virustotal_client.py` that made `.json()` return an unawaited coroutine. `pytest` was 23/24 before, 24/24 after. Environment note: system Python is 3.14, too new for the pinned ML deps (no wheels); `.venv` now built against a separate Python 3.11.15 install. |
| 2026-08-10 | Claude | Ponytail pass across `backend/`, `ml/`, `extension/`, `dashboard/`: added a one-line comment above every function per the new `CLAUDE.md` convention, removed a dead demo block in `shap_analysis.py` already covered by `test_shap.py`, and switched `generate_features.py` from `print()` to `logging` to match its sibling scripts. Left known, already-tracked defects alone (unknown-key silent drop in `explain_prediction()`, missing `ESA_ALLOW_FALLBACK` gate, `popup.js:75`'s `100 - confidence`) since each is a scoped Sprint 0–2 task, not cleanup. |
| **2026-08-10** | **Claude** | **Fixed the root npm workspace (0.5.2).** Root `node_modules` had no hoisted deps and `dashboard/` had grown its own fully independent `npm install` — two lockfiles, two copies of Next/React, which is what looked like "two dashboards." Removed `extension` from `workspaces` (it has no `package.json`), fixed `"next dev --workspace=dashboard"` → `"npm run dev --workspace=dashboard"` (the former passed an npm flag straight to the `next` CLI and would have failed), deleted both `node_modules` trees and reinstalled once from root. Also added `*.egg-info/` to `.gitignore` — `backend/fyp_backend.egg-info/` was untracked but not ignored. Updated `CLAUDE.md`/`README.md` to install from the repo root, not `cd dashboard && npm install`. |
| **2026-08-12** | **Claude** | **Closed out the rest of Sprint 0 (0.1, 0.2, 0.3.2, 0.5.1), each verified executed, not just written.** (1) `backend/pyproject.toml`: added `alembic`/`python-dotenv`/`greenlet`, moved `pandas`/`joblib` into base deps, wired `load_dotenv()` into `main.py` ahead of the env-reading imports. (2) `ml/shap_analysis.py`: `_load_model()` now raises on a `model.n_features_in_`/`feature_columns` mismatch (closes D4's guard); `explain_prediction()` raises `ModelUnavailableError` instead of silently falling back, unless `ESA_ALLOW_FALLBACK=1` (closes D5); added `get_model_status()` for `/health`. `backend/routers/analyze.py` maps `ModelUnavailableError` to a 503. Added `check_db_reachable()` to `database.py`. `GET /health` now returns `model_loaded`, `feature_count`, `model_sha256`, `vt_key_configured`, `db_reachable` — verified live both with and without a running Postgres. `tests/conftest.py` sets `ESA_ALLOW_FALLBACK=1` by default (no `.pkl` is committed, so the test suite needs the fallback) and a new test covers the unset/raising path. (3) `backend/Dockerfile` now installs `.[ml]`; `docker/docker-compose.yml`'s model mount fixed to `/app/ml/models`. Started Postgres + built/ran the backend image via `docker compose up -d --build` — confirmed clean startup log and `db_reachable: true` from inside the compose network (the build itself was slow only because of a ~450MB `[ml]` wheel download over a throttled connection, xgboost's wheel alone being 297MB — not a bug). (4) Ran `alembic upgrade head` against that live Postgres and confirmed via `\d scans` that every JSONB column exists, closing 0.3.2. (5) Added `.github/workflows/ci.yml` (backend: ruff + pytest; dashboard: tsc) and a new root `ruff.toml` (none existed) with two narrowly-scoped `E402` ignores for genuinely load-order-dependent imports; fixed one real unused import ruff caught in `test_url_features.py`. All three CI-equivalent checks verified green locally before wiring them in. `pytest` now 25/25. **Not yet done:** 0.4's real-browser load (needs a human at a GUI) and 0.5.1's "CI green on `main`" (needs a push, which wasn't done in this pass — changes are local only). |
| **2026-08-13** | **Claude + Hammad** | **First real CI run failed backend (`pytest` exit 2, `ModuleNotFoundError: No module named 'backend'/'ml'`); root cause found and fixed.** All of this session's local verification had used `python -m pytest`, which adds the CWD to `sys.path`; the CI workflow (correctly) used the bare `pytest` console-script entry point, which does not — and the `fyp-backend` editable install doesn't make `backend`/`ml` importable on its own (confirmed via its finder: `MAPPING = {}`). Production was never actually exposed to this bug because `uvicorn`'s string-import loader (`backend.main:app`) does its own CWD-based path insertion. Fix: added a root `pytest.ini` with `pythonpath = .` — reproduced the exact CI failure locally with `pytest.exe` (bare), confirmed the fix resolves it, confirmed `ruff` unaffected. Pushed; **both `backend` and `dashboard` CI jobs green on `main` at `8378be5`**, closing 0.5.1's acceptance. Then Hammad loaded the extension in real Chrome (0.4): zero manifest errors, zero service-worker exceptions, `chrome.storage.local` showed `tracker_count: 11` on `edition.cnn.com` — the only console line was `explain_prediction` returning 503 (ADR-016 working as intended, no `.pkl` committed). Set `ESA_ALLOW_FALLBACK: "1"` on the `backend` service in `docker/docker-compose.yml` so the local dev stack shows a full popup verdict instead of the 503 (compose is dev, not the Sprint 3 production deploy, so ADR-016 permits this). **Sprint 0 is now fully done.** |
| 2026-08-13 | Hammad | Popup verified end-to-end against the fallback (`✓ Page Looks Safe, 95% confident`), which surfaced two already-tracked-but-now-visible issues in one look: `popup.js:79`'s `100 - confidence` display (ADR-015/Sprint 2.5) and the fallback's low discriminating power pre-Sprint-1. Requested a phishing-tier blocking interstitial (full-page blur + warning card) instead of the passive toolbar popup. Added to `ROADMAP.md` as **Sprint 3.2** (renumbered: Deployment → 3.3, E2E → 3.4, Stretch → 3.5), gated to `risk_score > 0.70` with a dismissible "continue anyway" and explicitly held back from going live until Sprint 1's real model replaces the heuristic fallback, to avoid false-positive page blocks. |
| **2026-08-13** | **Claude** | **Sprint 1 (ML core rebuild) completed in full, all five sub-tasks executed and measured, not just written.** (1) `ml/scripts/audit_dataset.py` built and run against the original corpus: confirmed D1 numerically (`url_entropy` 0.9001 AUC, benign 0.0% vs phishing 65.2% path presence). (2) Corpus rebuild: PhiUSIIL was evaluated as the planned benign source and **rejected** after auditing it directly — its "legitimate" class is 0.0% path presence, the same artefact as bare Tranco domains under a different name. Built `ml/scripts/fetch_deep_benign_urls.py` instead — crawls real Tranco-ranked domain homepages for genuine internal links, using `asyncio` with a hard 8s per-domain deadline. A Common Crawl index-based approach was tried first and abandoned after a threaded retry loop against it hung for 50 minutes with zero progress; the direct-crawl replacement collected 9,000 training + 1,500 holdout deep-path URLs in under 9 minutes total. Rebuilt corpus passes the audit (13.6-point path-presence gap, no feature above 0.90 AUC) after an additional fix: the crawled benign class was initially 100% path-bearing (an artefact in the *opposite* direction from D1), corrected by measuring the phishing class's own 65.2% path-presence rate and mixing matching bare-homepage rows into the benign class to match it, rather than assuming either extreme. (3) `features.csv` regenerated with `brand_impersonation` restored (closes D4's 12-vs-8 drift) and VT columns excluded from the trained set (ADR-013); parity test added. (4) `backend/services/risk_fusion.py` implements ADR-014's log-odds fusion; `explain_prediction()` now raises on unrecognised feature keys instead of silently dropping them (closes D2) and routes both the SHAP path and the heuristic-fallback path through the same fusion+ranking step, so claim C2 holds even before a model existed for this session. `ml/reports/fusion_weights.md` documents all six weights. (5) Retrained: F1 0.8188, AUC 0.9017 — down from the leaky ~0.97, the expected and correct direction, recorded in `ml/reports/training_log.md` along with an honest miss (the roadmap's own named acceptance URL scores 0.564 "suspicious" not <0.40, driven by `url_entropy`; aggregate check against the 1,488-URL holdout shows an 8.8% phishing-band false-positive rate) — investigated and reported rather than tuned away, since fitting to this holdout would repeat the exact error the corpus rebuild had just corrected. |
| **2026-08-13** | **Claude** | **Sprint 2.1–2.6 completed.** (1) `ml/scripts/evaluate_baselines.py`: temporal split (phishing by real `submission_time`; benign randomly, stated explicitly since it has no timestamp) and unseen-registrable-domain split, both leakage-guarded by `tests/unit/test_evaluate_baselines.py`. Four baselines at a uniform 0.5 threshold (an XGBoost-at-0.70-vs-others-at-0.5 comparison was caught and fixed before being reported) — blocklist recall is exactly 0.0% on both splits by construction, directly evidencing claim C1. No fabricated "B5 fused" row: no offline corpus carries real browser telemetry, stated explicitly rather than relabelling B4. (2) `ml/scripts/calibration.py`: ECE 0.082 (temporal split), Platt scaling fit on a train-side validation split (never test) barely moved it (→0.080) and slightly worsened Brier score — reported as measured. Reliability diagram embedded in `evaluation_report.md`. (3) `ml/scripts/faithfulness.py`: top-3 SHAP ablation, both shifts in log-odds; **87.5% directional agreement, short of the 90% target** — reported honestly rather than adjusted. Along the way, found and fixed a real faithfulness bug in `explainer_formatter.py`: continuous-feature sentences ("randomness score is high") were rendered from a fixed template regardless of the SHAP contribution's actual sign, so a feature that *lowered* risk could be described as alarming — now branches on `sign(shap_impact)`, with a regression test. (4) ADR-015 (`risk_pct`/`confidence_pct` split) propagated through the model, both routers, dashboard types, `ConfidenceBadge` (its confidence-based colour fallback was fixed too — meaningless once confidence is always ≥50), and `popup.js` (no more `100 - confidence`); Alembic migration `33be02683ae4` applied and verified against live Postgres. (5) D7/D8 fixed: `extension/modules/permission_monitor.js` now runs in the MAIN world (`"world": "MAIN"`) where it can actually see the page's own `Notification`/`getUserMedia`/`getCurrentPosition` calls, relayed via `CustomEvent` to the isolated-world `content_script.js`; `background.js` re-runs analysis when a genuinely new permission flag arrives after the initial analysis already completed, rather than delaying every analysis for a signal window that usually produces nothing. New automated test (`tests/unit/permission_monitor_test.js`) exercises the full cross-world relay via two linked VM contexts; manual test plan + two fixture pages written for the real-browser verification step, not yet performed. Also: root `package.json`'s `test` script and CI never actually ran the extension JS tests at all — fixed, both `network_monitor_test.js` and the new `permission_monitor_test.js` now run in `dashboard`'s CI job. Docker rebuild time was a recurring cost across this work (every source change forced a full `[ml]` wheel re-download); fixed by adding a BuildKit pip cache mount to `backend/Dockerfile`. **Remaining in Sprint 2:** 2.7 (latency benchmark). |
| **2026-08-13** | **Hammad** | Requested both dashboard and extension support light/dark theming with a toggle, and that the UI/UX not read as "typical common AI design" — the existing scaffold (navy background, indigo accents, Inter font, glassmorphism, rounded-2xl cards) was exactly that generic look. Applied as an ongoing design instruction to all subsequent UI work, and retrofitted to the existing dashboard shell (Navbar, badges, overview page) as part of Sprint 3.1. |
| **2026-08-13** | **Claude** | **Sprint 2 finished: 2.7 (latency) and 2.8 (brand matching, added mid-sprint).** Latency benchmark (`ml/scripts/bench_latency.py`) against the live Docker container: cold p50=1.148s/p95=1.593s, warm p50=0.063s/p95=0.078s — both comfortably inside NFR-01's 10s/1s budgets; cold pass paced under VirusTotal's 4/min free-tier limit rather than measuring a rate-limited burst. Brand impersonation (`url_features.py`) gained homoglyph normalisation (Cyrillic/Greek confusables, leetspeak digits) plus bounded Levenshtein distance against hostname tokens — catches `pаypal.com` (Cyrillic а) and `paypa1-login.tk`, which exact substring matching missed entirely. FP cost measured *before* committing to the change, old vs new logic on `fp_holdout.csv`: one new false positive across 1,488 URLs (`mail.google.com`, `"mail"` at edit-distance 1 from brand `"gmail"` — accepted as a real, understandable edge case rather than special-cased). Regenerated `features.csv`, retrained, and re-ran the entire Sprint 2 evaluation suite (baselines, calibration, faithfulness, FP holdout — now `ml/scripts/evaluate_fp_holdout.py`, formalising what had been an ad hoc check) so `evaluation_report.md` stays consistent with the committed model; all deltas versus the pre-L1 run were <0.002 on F1/AUC, as expected for a near-zero-signal feature (`ml/reports/training_log.md`, Run 2). **Sprint 0, 1 and 2 are now all complete.** Moving to Sprint 3 (dashboard, interstitial, deployment, end-to-end validation). |
| **2026-08-13** | **Claude** | **Sprint 3.1 complete: dashboard pages, charts, and a full visual redesign of both dashboard and extension.** Installed `recharts`/`date-fns` (first attempt landed in the wrong `package.json` — root instead of `dashboard/`, caught and corrected). Built `RiskDistributionChart`, `ShapWaterfallChart` (browser-signal and SHAP attributions render identically per ADR-014 — no special-casing needed in the chart itself), `RiskSparkline`, `app/history/page.tsx` (sortable, paginated), `app/scan/[id]/page.tsx` (verdict, risk bar, network/permission/VT cards, both charts). Redesigned the whole visual language per Hammad's request above: warm neutral palette (not navy/slate), single teal accent kept separate from the red/amber/green verdict colours, sharp 3px corners, hairline borders, Space Grotesk + JetBrains Mono. `ThemeToggle` went through two real, caught-not-guessed bugs: a React-state version produced a genuine hydration mismatch (conditionally-rendered SVG children — `suppressHydrationWarning` on the parent button doesn't cover structurally different children), fixed by rendering both icons always and letting CSS alone decide visibility from the `data-theme` attribute; and the no-flash theme script as raw JSX `<script>` triggered a Next.js App Router warning ("scripts inside React components are never executed") and didn't reliably block before paint — fixed with `next/script strategy="beforeInteractive"`. ESLint's newer `react-hooks/static-components` and `react-hooks/set-state-in-effect` rules (not previously enforced) caught both issues' root causes directly: `HistoryTable`'s `Th` was a component defined inside another component's render (recreates on every render, resets its own state), fixed by hoisting to module scope. Verified in both themes via headless Chrome screenshots against the live backend with 200+ real accumulated scans from this session's own testing, and via a clean `next build` production build. Extension popup got the same palette; used `localStorage` + a separate blocking `theme_init.js` file rather than an inline script, since manifest.json's CSP (`script-src 'self'`) blocks inline script content outright — a constraint the dashboard's `next/script` fix doesn't share, caught before it could ship as a silently-broken theme toggle. |
