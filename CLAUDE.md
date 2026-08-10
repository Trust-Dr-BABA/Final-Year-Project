# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session start

Read `PROJECT_STATE.md` (current sprint, current task, ADRs, open defects), then find that task in
`ROADMAP.md` and read its **acceptance criterion**. A task is done when the criterion has been
*executed and observed*, not when the code is written.

`ROADMAP.md` and `PROJECT_STATE.md` are the only planning docs. Keep them in sync: tick the box in
the roadmap, advance **Current task** in the state file, add an activity-log row.

## Commands

```bash
# Environment (backend + ml + dev in one editable install)
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e "./backend[ml,dev]"

# Full stack (Postgres + backend + dashboard)
cd docker && docker compose up --build

# Backend alone — note the module path is backend.main, run from repo root
uvicorn backend.main:app --reload

# Tests
pytest tests/ -q
pytest tests/unit/test_url_features.py -q                       # single file
pytest tests/unit/test_url_features.py::TestSuspiciousTldFlag   # single class/test
node tests/unit/network_monitor_test.js                         # extension JS tests

# ML pipeline, in order — each step consumes the previous step's output
python ml/scripts/prepare_dataset.py      # raw CSVs        → data/processed/dataset.csv
python ml/scripts/audit_dataset.py        # leakage / separability audit → ml/reports/
python ml/scripts/generate_features.py    # dataset.csv     → data/processed/features.csv
python ml/scripts/train_model.py          # features.csv    → model.pkl + feature_columns.json

# Dashboard — install from repo root (npm workspace); do not run `npm install` inside dashboard/,
# it creates a second, independent node_modules that drifts from the root lockfile.
npm install
npm run dev:dashboard        # or: cd dashboard && npm run dev
cd dashboard && npx tsc --noEmit

# Database
alembic -c backend/alembic.ini upgrade head
```

Extension: `chrome://extensions` → Developer mode → Load unpacked → select `extension/`.

## Architecture

Four components, one request path. The thing that is not obvious from any single file is that
**attribution is preserved end to end** — every number the user sees traces back to a named,
additive contribution.

```
extension → POST /analyze → FastAPI → XGBoost + fusion → SHAP → Postgres → dashboard
```

**Signals are collected in the browser, never re-fetched server-side.** `network_monitor.js`
counts trackers, mixed content and top-level redirects via `webRequest`/`webNavigation`;
`content_script.js` intercepts permission APIs. The backend *trusts* these counts. Re-fetching a
live phishing URL from the server would be both a security risk and a latency cost.

**The scoring pipeline** (`backend/routers/analyze.py`) is: extract lexical features →
`heuristics_engine.evaluate()` turns browser signals into rule flags + numeric features →
XGBoost yields `p_url` → `risk_fusion.py` adds documented browser-signal weights **in log-odds
space** → SHAP `TreeExplainer` attributes the model portion → `explainer_formatter.format_reason()`
renders every contribution as an English sentence.

**Why log-odds fusion matters** (ADR-014): SHAP values *are* additive log-odds contributions, so a
hand-set browser-signal weight and a SHAP value live on the same scale. They can be ranked in one
`top_reasons` list and drawn by the same waterfall chart, with no schema change downstream. Browser
signals are not trained features because no labelled corpus carries per-URL tracker counts.

**VirusTotal is display-only** (ADR-013). VT ingests PhishTank, so training on VT verdicts would be
circular — the model would learn the label. `virustotal_client.py` is called live, shown as
corroboration, persisted on the scan record, and excluded from `feature_columns.json`. A VT
timeout degrades display and can never change a verdict.

**Training is strictly offline.** `ml/` produces `xgboost_phishing.pkl`; the backend only loads it.
`ml/shap_analysis.py` is imported by the backend at request time, so `pandas` and `joblib` are
runtime dependencies, not optional extras.

## Invariants

Breaking any of these is a bug, not a style choice.

1. **No snake_case feature name may reach the popup or dashboard** (ADR-010). Everything passes
   through `format_reason()` and `shared/feature_name_to_human_readable.json`. A new feature
   without a template is an incomplete feature.
2. **`feature_columns.json` and `xgboost_phishing.pkl` are written by the same training run and
   never hand-edited.** Hand-editing the JSON already caused a 12-vs-8 column mismatch. Model load
   asserts `model.n_features_in_ == len(feature_columns)`.
3. **Never silently drop features.** `explain_prediction()` previously filtered the feature vector
   against `feature_columns` and discarded browser signals without a word — that defeated the
   project's core multi-signal claim for weeks. Unknown keys must raise.
4. **No silent fallback in a serving deployment** (ADR-016). `_simple_rule_prediction()` is gated
   behind `ESA_ALLOW_FALLBACK=1`. `/health` reports `model_loaded`, `feature_count`, `model_sha256`,
   `vt_key_configured`, `db_reachable`.
5. **Verdict thresholds:** `> 0.70` phishing, `0.40–0.70` suspicious, `< 0.40` legitimate.
   Changing them requires a new ADR.
6. **`risk_pct` ≠ `confidence_pct`** (ADR-015). `risk_pct = round(p*100)`;
   `confidence_pct = round(max(p, 1-p)*100)`. No UI may derive one from the other.
7. **Never cut SHAP explainability** (ADR-011) — it is the project's academic contribution.
8. **Evaluation numbers are measured, never estimated** or carried over from a prior run.

## Gotchas

- **The dashboard is Next.js 16, not 14.** See `dashboard/AGENTS.md`: read
  `node_modules/next/dist/docs/` before writing App Router code rather than assuming Next 14
  conventions. Existing docs and roadmap history refer to 14 — they are stale on this point.
- **MV3 service workers are killable.** State must live in `chrome.storage.local`, keyed by tab ID,
  never in module-scope variables. `tabSignals` in `network_monitor.js` is in-memory by design but
  is frozen to storage on tab complete.
- **Content scripts run in an isolated world.** Patching `Notification.requestPermission` there
  does *not* intercept the page's own calls — main-world injection is required. This is why the
  permission signal family is currently non-functional (defect D7).
- **`unittest.mock.patch` targets the import site**, e.g.
  `backend.routers.analyze.get_domain_info`, not `backend.services.virustotal_client.get_domain_info`.
- Unit tests must never make real network calls — the VT free tier is 4 req/min, 500/day.

## Code conventions

**Every function gets exactly one single-line comment immediately above it, stating what it does.**
No multi-paragraph docstrings, no JSDoc blocks with `@param`/`@returns` tags, no comment restating
the function name. If the line can't say what the function does, the function is doing too much.

**Python** — type hints on all signatures; `black` (88); `isort`; `logging`, never `print()`.
**Extension JS** — `const`/`let`; `async`/`await` over `.then()` chains.
**Dashboard TS** — strict mode; no `any`; all API response types in `dashboard/lib/types.ts`.

**Commits:** `feat(sprint-N): …` · `fix(sprint-N): …` · `test(sprint-N): …` · `docs: …`

## Engineering posture

From `.cursor/rules/ponytail.mdc`, which applies to all work here: prefer the simplest thing that
works. Before writing code, check in order — is it needed at all; does it already exist in this
codebase; does the standard library or platform cover it; does an installed dependency solve it.
No abstractions that were not requested, no new dependency that can be avoided, deletion over
addition. Fix root causes rather than the symptom named in a report: grep every caller and fix the
shared function once.

Not lazy about: understanding the problem before choosing an approach, validation at trust
boundaries, error handling, security, and leaving one runnable check behind for non-trivial logic.
