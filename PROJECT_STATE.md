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
| **Current sprint** | Sprint 0 — Make it run, and make it fail loudly |
| **Current task** | `0.1.1` — Add missing runtime deps to `backend/pyproject.toml` |
| **Recently merged** | `origin/main` (13 commits) on 2026-08-09 — Alembic migration, extension icons, `webNavigation` fix |
| **Status** | 🔲 Not started |
| **Blocked?** | No |
| **Last full audit** | 2026-08-09 |

### Live endpoints

| Service | URL | Status |
|---|---|---|
| Backend API | _(not deployed — Sprint 3.2.1)_ | ⏳ Pending |
| Dashboard | _(not deployed — Sprint 3.2.2)_ | ⏳ Pending |
| PostgreSQL | `localhost:5432` (Docker) | 🔲 Migration not yet applied (Sprint 0.3) |
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
| **D1** | Dataset trivially separable — benign class is bare Tranco domains, phishing class is full URLs with paths | 1 |
| **D2** | Browser-signal features silently dropped by `explain_prediction()`; multi-signal fusion not actually wired in | 1 |
| **D3** | VT features constant `-1` across all training rows, and would be label-circular if populated | 1 |
| **D4** | `feature_columns.json` (12 cols) ≠ `features.csv` (8 cols); nothing asserts lockstep | 0 |
| **D5** | Every failure path silently falls back to a heuristic verdict; Docker omits `[ml]` extras; model volume mounted to the wrong path | 0 |
| ~~D6~~ | ~~`manifest.json` missing `webNavigation`~~ — **fixed**, merged from `origin/main` 2026-08-09 | ✅ |
| **D7** | Permission interception runs in the isolated world → cannot observe the page's real calls; signal family non-functional | 2 |
| **D8** | Permission signals arrive ~3.5s after analysis has already fired | 2 |

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

## Directory structure (verified 2026-08-09)

```
fyp/
├── backend/
│   ├── main.py                          ✅ FastAPI app, CORS, /health
│   ├── database.py                      ✅ Async engine + get_db
│   ├── Dockerfile                       ⚠️  Installs base deps only — misses [ml] extras (D5)
│   ├── pyproject.toml                   ⚠️  Missing alembic, python-dotenv, greenlet
│   ├── models/scan.py                   ✅ Scan ORM
│   ├── alembic/                         ✅ Async env.py + create_scans_table migration
│   ├── alembic.ini                      ✅ Reads DATABASE_URL from env
│   ├── routers/
│   │   ├── analyze.py                   ✅ POST /analyze — full pipeline
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
│   │   ├── feature_columns.json         ⚠️  12 columns; no model to match them (D4)
│   │   └── xgboost_phishing.pkl         🔲 Does not exist
│   ├── scripts/
│   │   ├── prepare_dataset.py           ⚠️  Discards PhishTank metadata; bare-domain negatives (D1)
│   │   ├── generate_features.py         ⚠️  Never passes vt_data (D3)
│   │   ├── train_model.py               ✅ Correct; writes .pkl + columns together
│   │   └── audit_dataset.py             🔲 Sprint 1.1.1
│   ├── reports/                         🔲 Sprint 1–4
│   └── shap_analysis.py                 ⚠️  Silently drops unknown features (D2); silent fallback (D5)
│
├── shared/
│   ├── brand_list.txt                   ✅ 50 brands
│   ├── tracker_domains.json             ✅ 500 EasyPrivacy domains
│   ├── TRACKER_DOMAINS_SOURCE.md        ✅ Provenance
│   └── feature_name_to_human_readable.json ✅ 21 templates
│
├── tests/
│   ├── conftest.py                      ✅ Env defaults
│   ├── unit/                            ✅ 4 Python + 1 JS test module
│   ├── integration/                     ✅ test_analyze_endpoint.py
│   ├── manual/                          ✅ network_monitor_test.md
│   └── e2e/                             🔲 Sprint 3.3.1
│
├── docker/docker-compose.yml            ⚠️  Model volume mounted to wrong path (D5)
├── .github/workflows/ci.yml             🔲 Sprint 0.5.1
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
