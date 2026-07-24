# PROJECT_STATE.md — AI-Powered Explainable Security & Privacy Analyst
> **Protocol:** Cursor reads this file at the **start of every session**. AntiGravity updates this file when the plan changes. Cursor updates the task fields and activity log after each task.

---

## 🟢 Current Status

| Field | Value |
|---|---|
| **Active Phase** | Phase 1 — Project Skeleton & Dataset Collection |
| **Current Task** | `1.1.1` — Verify directory structure exists (skeleton already committed) |
| **Status** | 🔲 Not Started |
| **Blocked?** | No |
| **Next Task** | `1.1.2` — Initialize root package.json |

---

## 🔗 Live Endpoints (update when deployed)

| Service | URL | Status |
|---|---|---|
| Backend API | _(not deployed yet)_ | ⏳ Pending |
| Dashboard | _(not deployed yet)_ | ⏳ Pending |
| PostgreSQL | `localhost:5432` (Docker) | 🔲 Not Started |
| Demo Video | _(recorded in Phase 7)_ | ⏳ Pending |

---

## 🏗️ Key Architectural Decisions (ADRs)

| # | Decision | Rationale | Date |
|---|---|---|---|
| ADR-001 | **MV3 for Chrome Extension** | MV2 is deprecated; MV3 service workers are required for new extensions | 2026-07-24 |
| ADR-002 | **XGBoost (not neural network)** | Tabular URL/network features; SHAP TreeExplainer native support; no GPU needed | 2026-07-24 |
| ADR-003 | **Heuristics for permissions (not ML)** | Near-binary signal; faster; keeps SHAP output cleaner for viva | 2026-07-24 |
| ADR-004 | **Single unified XGBoost model** | One pipeline avoids 3-model maintenance on a 3-month timeline | 2026-07-24 |
| ADR-005 | **FastAPI (not Django/Flask)** | Async-first, auto OpenAPI docs, Pydantic validation | 2026-07-24 |
| ADR-006 | **Next.js 14 App Router** | SSR, TypeScript-first, zero-config Vercel deployment | 2026-07-24 |
| ADR-007 | **PostgreSQL with JSONB for SHAP values** | Variable-length SHAP arrays stored as JSONB; relational for scan metadata | 2026-07-24 |
| ADR-008 | **VirusTotal API (replaces WHOIS)** | VT returns domain age + malicious votes in one call; WHOIS timeouts would break live demo | 2026-07-24 |
| ADR-009 | **confidence_pct (int, 0-100) alongside risk_score (float)** | Popup and dashboard show "87% confident" — more legible than "0.87" | 2026-07-24 |
| ADR-010 | **feature_name_to_human_readable.json** | All SHAP feature names must be translated before reaching the UI — never expose snake_case | 2026-07-24 |
| ADR-011 | **NEVER cut SHAP explainability** | Core academic differentiator; examiners will specifically evaluate this | 2026-07-24 |
| ADR-012 | **Baseline comparison in evaluation** | Must show model beats a simple blocklist — directly answers "why not just use a blocklist?" | 2026-07-24 |

---

## 📁 Directory Structure (as scaffolded)

```
fyp/
├── backend/                        # FastAPI Python backend
│   ├── __init__.py
│   ├── main.py                     ✅ Skeleton ready
│   ├── database.py                 ✅ Skeleton ready
│   ├── Dockerfile                  ✅ Skeleton ready
│   ├── pyproject.toml              ✅ All deps pinned
│   ├── models/
│   │   ├── __init__.py
│   │   └── scan.py                 ✅ Skeleton ready
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analyze.py              ✅ Stub (implement Phase 4)
│   │   └── history.py              ✅ Stub (implement Phase 4)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── heuristics_engine.py    ✅ Skeleton ready
│   │   └── explainer_formatter.py  ✅ Skeleton ready
│   └── feature_extractor/
│       ├── __init__.py
│       └── url_features.py         ✅ Skeleton ready (VT TODO in Phase 2)
│
├── extension/                      # Chrome MV3 Extension
│   ├── manifest.json               ✅ Complete MV3 manifest
│   ├── background.js               ✅ Skeleton ready
│   ├── content_script.js           ✅ Permission heuristics ready
│   ├── config.js                   ✅ Config constants
│   ├── modules/
│   │   ├── network_monitor.js      ✅ Skeleton ready (tracker TODO Phase 3)
│   │   └── permission_monitor.js   🔲 Not created (Phase 3.2)
│   ├── services/
│   │   └── api_client.js           ✅ Skeleton ready
│   ├── popup/
│   │   ├── popup.html              ✅ 4-state UI complete
│   │   ├── popup.js                ✅ Skeleton ready (wire in Phase 5)
│   │   └── popup.css               ✅ Dark theme complete
│   └── icons/                      🔲 Add real PNGs (Phase 1.2.5)
│
├── dashboard/                      🔲 Initialize with create-next-app (Phase 6.1.1)
│
├── ml/                             # ML pipeline
│   ├── data/
│   │   ├── raw/
│   │   │   └── DATASET_SOURCES.md  ✅ Template ready
│   │   └── processed/              🔲 Created after running prepare_dataset.py
│   ├── features/                   🔲 Mirror url_features.py here (Phase 2)
│   ├── models/                     🔲 Created after running train_model.py
│   ├── notebooks/                  🔲 Create in Phase 2
│   ├── scripts/
│   │   ├── prepare_dataset.py      ✅ Ready
│   │   └── train_model.py          ✅ Ready
│   └── shap_analysis.py            ✅ Stub ready (implement Phase 2.4)
│
├── shared/
│   ├── brand_list.txt              ✅ 50 brand names loaded
│   ├── tracker_domains.json        ✅ Empty list (populate Phase 3.1.3)
│   └── feature_name_to_human_readable.json  ✅ All features mapped
│
├── tests/
│   ├── unit/
│   │   └── test_url_features.py    ✅ Written
│   ├── integration/                🔲 Write in Phase 4
│   ├── e2e/                        🔲 Write in Phase 7
│   └── manual/                     🔲 Write in Phase 3
│
├── docker/
│   └── docker-compose.yml          ✅ Complete
│
├── .cursor/rules/agent-sync.mdc    ✅ Cursor rules
├── .env.example                    ✅ All vars documented
├── .gitignore                      ✅ Complete
└── ROADMAP.md                      ✅ Updated (all audit improvements applied)
```

---

## 📋 Agent Activity Log

| Date | Agent | Action |
|---|---|---|
| 2026-07-24 | AntiGravity | Initial planning framework established. Generated ROADMAP.md (8 phases), PROJECT_STATE.md, agent-sync rules. |
| 2026-07-24 | AntiGravity | **Feature audit completed.** Applied: VirusTotal replacing WHOIS, confidence_pct, baseline comparison task, suspicious_tld_flag, feature_name_to_human_readable.json, in-memory caching. Removed: real-time URL fetching from backend, Options Page. |
| 2026-07-24 | AntiGravity | **Full skeleton scaffolded.** Created all directories and starter files: backend (main.py, database.py, models, routers, services, feature_extractor), extension (manifest.json, background.js, content_script.js, popup, modules, services), ml (scripts, shap_analysis.py), shared (brand_list, tracker_domains, feature templates), tests, docker. Project is ready for Phase 1 execution. |

---

## 📌 Cursor Instructions

### At the START of every session:
1. Read this file (`PROJECT_STATE.md`)
2. Note the **Current Task** field
3. Open `ROADMAP.md` and find that task
4. Read the task description AND acceptance criteria carefully
5. Begin work

### After COMPLETING a task:
1. Mark it `[x]` in `ROADMAP.md`
2. Update **Current Task** to the next unchecked item
3. Update **Status** to `🔲 Not Started`
4. Add an entry to the **Agent Activity Log**

### If BLOCKED:
1. Set **Blocked?** to `Yes — <describe blocker>`
2. Do NOT proceed to the next task
3. Tag AntiGravity

### NEVER:
- Skip tasks out of order without AntiGravity approval
- Modify ROADMAP.md phase structure or acceptance criteria
- Remove or override ADRs above
- Expose snake_case feature names in the popup or dashboard UI
