# ROADMAP — AI-Powered Explainable Security & Privacy Analyst
> **Last Updated:** 2026-07-24  
> **Current Phase:** Phase 1 — Project Skeleton & Dataset  
> **Agent Maintaining This File:** AntiGravity (updates) / Cursor (checkbox ticks)

---

## How to Read This Roadmap

- Each phase maps to roughly 1–2 weeks of work.
- Tasks are **vertical slices**: each one produces a running, testable artifact.
- Complete tasks top-to-bottom, in order. Do not skip ahead.
- After finishing a task, mark it `[x]` and update `PROJECT_STATE.md`.
- Mark a task `[/]` (in-progress) when you start it.

---

## Phase 1 — Project Skeleton & Dataset Collection (Weeks 1–2)

**Objective:** Bootstrap the entire project scaffold (all four components) and collect + clean the ML training dataset. Every piece of infrastructure is in place before any feature code is written.

### 1.1 — Monorepo & Tooling Bootstrap

- [ ] **1.1.1** The top-level directory structure is already scaffolded (skeleton files committed). Verify all directories exist: `backend/`, `extension/`, `dashboard/`, `ml/`, `shared/`, `tests/`, `docker/`
- [ ] **1.1.2** Initialize a single root `package.json` with workspaces pointing to `extension/` and `dashboard/`
- [ ] **1.1.3** Verify `backend/pyproject.toml` has all pinned deps: `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `asyncpg`, `xgboost`, `shap`, `pandas`, `scikit-learn`, `python-dotenv`, `alembic`, `httpx`, `tldextract`
- [ ] **1.1.4** Copy `.env.example` to `.env` and fill in: `DATABASE_URL`, `VIRUSTOTAL_API_KEY` (get free key at https://www.virustotal.com/gui/sign-in), `MODEL_PATH`, `BACKEND_URL`
- [ ] **1.1.5** Run `docker-compose up` from `docker/` — verify all three services start cleanly
- [ ] **1.1.6** Verify `GET http://localhost:8000/health` returns `{"status": "ok"}`

**Acceptance Criteria:**
- `docker-compose up` starts postgres + backend + dashboard with no errors
- `GET http://localhost:8000/health` → `{"status": "ok"}`
- `GET http://localhost:3000` renders Next.js default page

---

### 1.2 — Chrome Extension Skeleton (MV3)

- [ ] **1.2.1** Load the unpacked extension in Chrome: open `chrome://extensions` → enable Developer mode → "Load unpacked" → select `extension/` folder
- [ ] **1.2.2** Verify popup appears when clicking the extension icon and shows "Extension Active"
- [ ] **1.2.3** Open the service worker console (chrome://extensions → "Service Worker" link) and verify "Extension loaded" is logged
- [ ] **1.2.4** Navigate to any page and verify "Content script injected: [url]" appears in the page's DevTools console
- [ ] **1.2.5** Add real 16x16, 48x48, 128x128 PNG icons to `extension/icons/` (use any placeholder security/shield icon; the skeleton has text placeholders)

**Acceptance Criteria:**
- Extension loads in Chrome with zero manifest errors
- Popup renders the "Extension Active" badge
- Service worker logs on startup; content script logs on every page

---

### 1.3 — Dataset Collection & Cleaning

- [ ] **1.3.1** Download PhishTank verified phishing URLs CSV from `http://data.phishtank.com/data/online-valid.csv` — save to `ml/data/raw/phishtank.csv`. Target: 5,000–10,000 rows. **Record the download date in `ml/data/raw/DATASET_SOURCES.md`**
- [ ] **1.3.2** Download Tranco Top-1M CSV from `https://tranco-list.eu/download/AAAA/full` — save to `ml/data/raw/tranco.csv`. Sample 5,000–10,000 rows. Record the list date in `DATASET_SOURCES.md`
- [ ] **1.3.3** Create `ml/data/raw/DATASET_SOURCES.md` — document: source URLs, download dates, row counts. This becomes the citation in your evaluation report
- [ ] **1.3.4** Run `python ml/scripts/prepare_dataset.py` — merges CSVs, assigns labels, deduplicates, shuffles, saves to `ml/data/processed/dataset.csv`
- [ ] **1.3.5** Open `ml/notebooks/01_data_exploration.ipynb` — run all cells, verify class distribution bar chart renders and shows ≥ 40% of each class
- [ ] **1.3.6** Verify class balance: if imbalanced, set `SCALE_POS_WEIGHT` env var note in `ml/scripts/train_model.py`

**Acceptance Criteria:**
- `ml/data/processed/dataset.csv` exists with columns: `url`, `label`
- Minimum 8,000 total rows; ≥ 40% of each class
- `ml/data/raw/DATASET_SOURCES.md` is filled with accurate download dates
- Notebook 01 runs top-to-bottom without errors

---

## Phase 2 — ML Pipeline: Feature Engineering & Model Training (Weeks 3–4)

**Objective:** Build and validate the core XGBoost phishing classifier. Replace slow WHOIS with VirusTotal API. Produce `model.pkl`, wire SHAP, and create the human-readable feature name mapper.

### 2.1 — URL Feature Extraction

- [ ] **2.1.1** Open `ml/features/url_features.py` — the skeleton is already present. Review the `extract_url_features(url: str) -> dict` function signature
- [ ] **2.1.2** Implement all lexical features in `url_features.py`:
  - URL length, number of digits, number of special chars (`-`, `_`, `@`, `?`, `=`, `%`)
  - Presence of IP address in hostname (regex: `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}`)
  - Subdomain depth (count of `.` in hostname minus 1)
  - TLD extracted via `tldextract` library
  - `has_https`: True/False
  - URL entropy (Shannon entropy of the full URL string)
  - **`suspicious_tld_flag`**: True if TLD is in `[".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".gq", ".pw", ".cc", ".su"]` — pure string check, zero latency
- [ ] **2.1.3** Implement VirusTotal domain reputation feature (replaces WHOIS):
  - Create `ml/features/virustotal_client.py` — async `get_domain_info(domain: str) -> dict` using `httpx.AsyncClient`
  - Endpoint: `GET https://www.virustotal.com/api/v3/domains/{domain}` with `x-apikey` header
  - Extract: `domain_age_days` (from `creation_date` attribute), `vt_malicious_votes` (count of malicious vendor detections), `vt_harmless_votes`
  - Return `{"domain_age_days": int, "vt_malicious_votes": int, "vt_harmless_votes": int}` — return all `-1` on any error/timeout (5s timeout)
  - **Rate limit:** 4 req/min on free tier. Cache results in memory with `functools.lru_cache` (TTL via `cachetools.TTLCache`, 1 hour)
- [ ] **2.1.4** Implement brand-impersonation feature: load `shared/brand_list.txt` (top 50 brand names); check if any brand name appears in the URL but is NOT the registrable domain (e.g., `paypal-login.net` → True)
- [ ] **2.1.5** Write unit tests in `tests/unit/test_url_features.py`:
  - Test each feature against 3 known phishing URLs and 3 legitimate URLs
  - Mock the VirusTotal client using `unittest.mock.patch` — do NOT make real API calls in tests

**Acceptance Criteria:**
- `extract_url_features("http://paypal-secure-login.xyz")` returns a dict with all expected keys
- `suspicious_tld_flag` is True for `.xyz` domain, False for `google.com`
- `pytest tests/unit/test_url_features.py` passes with 0 failures (VT client mocked)
- No real network calls are made during unit tests

---

### 2.2 — Feature Name → Human-Readable Mapper

- [ ] **2.2.1** Populate `shared/feature_name_to_human_readable.json` — the skeleton has the structure. Add a plain-English template for every feature:
  ```json
  {
    "url_length": "URL is unusually long ({value} characters)",
    "domain_age_days": "Domain was registered only {value} days ago",
    "vt_malicious_votes": "{value} security vendors flagged this domain as malicious",
    "suspicious_tld_flag": "Domain uses a high-risk top-level domain extension",
    "has_https": "Page does not use a secure HTTPS connection",
    "brand_impersonation": "URL contains a known brand name in a suspicious position",
    "tracker_count": "{value} third-party tracking domains loaded on this page",
    "has_mixed_content": "Page loads insecure resources over HTTP",
    "redirect_chain_length": "URL went through {value} redirects before reaching the page",
    "cam_mic_on_first_visit": "Page requested camera or microphone access immediately",
    "notification_prompt_on_load": "Page requested notification permission within 3 seconds of loading"
  }
  ```
- [ ] **2.2.2** Create `backend/services/explainer_formatter.py` — `format_reason(feature_name: str, value: any, shap_impact: float) -> str` function that looks up the template and substitutes `{value}` with the actual value
- [ ] **2.2.3** Write unit test in `tests/unit/test_explainer_formatter.py` — test that `format_reason("domain_age_days", 2, 0.45)` returns `"Domain was registered only 2 days ago"`

**Acceptance Criteria:**
- All features in `url_features.py` have a corresponding entry in `feature_name_to_human_readable.json`
- `format_reason()` correctly substitutes values for all templates
- No raw feature names (snake_case) are ever exposed to the popup or dashboard UI

---

### 2.3 — Model Training Pipeline

- [ ] **2.3.1** Open `ml/notebooks/02_feature_engineering.ipynb` — apply `extract_url_features` to every row of `dataset.csv`; use `pd.DataFrame.apply` with a progress bar (`tqdm`); save as `ml/data/processed/features.csv`
- [ ] **2.3.2** Run `python ml/scripts/train_model.py` — loads `features.csv`, splits 80/20 (stratified), trains `XGBClassifier` (`n_estimators=200`, `max_depth=6`, `learning_rate=0.1`, `eval_metric="logloss"`)
- [ ] **2.3.3** Verify model saves: `ml/models/xgboost_phishing.pkl` and `ml/models/feature_columns.json` both exist after training
- [ ] **2.3.4** Open `ml/notebooks/03_model_evaluation.ipynb` — run all cells; verify confusion matrix, classification report (precision/recall/F1), and ROC-AUC curve render correctly
- [ ] **2.3.5** *(Optional — only if F1 looks suspicious)* Add 5-fold `StratifiedKFold` cross-validation to `train_model.py` and log mean ± std F1

**Acceptance Criteria:**
- `python ml/scripts/train_model.py` completes without errors
- `ml/models/xgboost_phishing.pkl` exists and loads with `joblib.load`
- Test set **F1-score ≥ 0.85** and **ROC-AUC ≥ 0.90**
- Confusion matrix shows in Notebook 03

---

### 2.4 — SHAP Explainability Wiring

- [ ] **2.4.1** Open `ml/shap_analysis.py` — review the skeleton. Instantiate `shap.TreeExplainer(model)` and compute SHAP values for the test set
- [ ] **2.4.2** Open `ml/notebooks/04_shap_analysis.ipynb` — run all cells: verify beeswarm summary plot and waterfall plot for 3 phishing examples render
- [ ] **2.4.3** Implement `explain_prediction(url: str) -> dict` in `ml/shap_analysis.py`:
  - Extract features for the URL
  - Call `model.predict_proba()` — use the phishing probability as `risk_score`
  - Compute SHAP values for just this one sample
  - Return:
    ```json
    {
      "score": 0.92,
      "confidence_pct": 92,
      "label": "phishing",
      "top_reasons": [
        {"feature": "domain_age_days", "value": 2, "shap_impact": 0.45, "human_readable": "Domain was registered only 2 days ago"}
      ]
    }
    ```
  - `confidence_pct` = `round(score * 100)` — exposes the raw probability as a percentage
  - `human_readable` is populated by calling `format_reason()` from task 2.2.2
- [ ] **2.4.4** Write unit test in `tests/unit/test_shap.py` — mock feature extraction, assert `confidence_pct` is an integer between 0–100, `top_reasons` has 3 items, `human_readable` strings contain no snake_case

**Acceptance Criteria:**
- `explain_prediction(...)` returns `confidence_pct` as an integer
- `human_readable` strings pass a check: `assert "_" not in reason["human_readable"]`
- Notebook 04 renders both plots without errors

---

## Phase 3 — Browser Signal Extractors (Weeks 5–6)

**Objective:** Build the two browser signal extractors. Network signals are already collected by the extension's `webRequest` listener — the backend does NOT re-fetch the URL. Permission signals use rule-based heuristics.

### 3.1 — Network Monitoring Module (Week 5)

- [ ] **3.1.1** Open `extension/modules/network_monitor.js` — review the existing skeleton structure
- [ ] **3.1.2** Implement tracker counting: load `shared/tracker_domains.json` (EasyPrivacy-sourced list). For every `chrome.webRequest.onCompleted` event on the current tab, check if the request hostname is in the tracker list. Count unique tracker domains per page load
- [ ] **3.1.3** Populate `shared/tracker_domains.json` with ~500 known tracker hostnames. Source: paste the `[Adblock Plus 2.0]` domain list from `https://easylist.to/easylist/easyprivacy.txt` — extract all `||domain^` lines. Save as a JSON array of strings
- [ ] **3.1.4** Implement mixed-content detection: flag if any `http://` resource request is made on a tab whose top-level URL starts with `https://` (compare `details.initiator` scheme vs `details.url` scheme)
- [ ] **3.1.5** Redirect chain count comes from `chrome.webRequest.onBeforeRedirect` — count events per top-level navigation. **Do NOT re-fetch the URL in the backend** — trust the extension's count
- [ ] **3.1.6** On tab `onUpdated` (status `complete`), freeze the `networkSignals` object: `{ tracker_count: int, has_mixed_content: bool, redirect_chain_length: int, third_party_domains: string[] }` and store in `chrome.storage.local` keyed by tab ID
- [ ] **3.1.7** Write manual test plan in `tests/manual/network_monitor_test.md` — document expected results for: CNN.com (high tracker count), example.com (zero trackers), a PhishTank URL

**Acceptance Criteria:**
- Loading `https://cnn.com` → `tracker_count` ≥ 5
- Loading `https://example.com` → `tracker_count` = 0
- `networkSignals` is logged to the service worker console on every page navigation
- `mixed_content` is correctly flagged on a known HTTP-resource page

---

### 3.2 — Permissions Monitoring Module (Week 6)

- [ ] **3.2.1** Open `extension/modules/permission_monitor.js` — review skeleton
- [ ] **3.2.2** Inject via content script: detect `navigator.permissions.query` and `getUserMedia` calls using a MutationObserver on permission prompts and JS API intercepts
- [ ] **3.2.3** Implement heuristic rules:
  - `cam_mic_on_first_visit`: camera or mic requested before the user has scrolled or clicked (track via `document.addEventListener("scroll"/"click")` in content script)
  - `notification_prompt_on_load`: `Notification.requestPermission()` called within 3 seconds of `DOMContentLoaded`
  - `location_on_load`: `geolocation.getCurrentPosition()` called within 3 seconds of page load
- [ ] **3.2.4** Pass rule flags from content script → background service worker via `chrome.runtime.sendMessage`
- [ ] **3.2.5** Aggregate into `permissionSignals`: `{ permissions_requested: string[], rule_flags: string[] }` — store in `chrome.storage.local` with the `networkSignals` on tab complete
- [ ] **3.2.6** Write manual test plan in `tests/manual/permission_monitor_test.md`

**Acceptance Criteria:**
- `rule_flags` is correctly populated for a page that requests camera access immediately
- `permissionSignals` is included in `chrome.storage.local` after page load
- No false flags on `https://google.com`

---

## Phase 4 — FastAPI Backend: Full Integration (Weeks 7–8)

**Objective:** Build the production-ready backend that merges all signal streams from the extension, calls XGBoost, runs SHAP, returns a confidence-scored, human-readable response. Deploy live.

### 4.1 — Database Schema & Migrations

- [ ] **4.1.1** Open `backend/models/scan.py` — review the `Scan` SQLAlchemy model skeleton
- [ ] **4.1.2** Run `alembic init alembic` inside `backend/` and configure `alembic.ini` to point to `DATABASE_URL` from env
- [ ] **4.1.3** Generate initial migration: `alembic revision --autogenerate -m "create_scans_table"`
- [ ] **4.1.4** Apply migration: `alembic upgrade head`
- [ ] **4.1.5** Verify `scans` table in psql: `\d scans` — confirm all columns including `confidence_pct` (integer)

**Acceptance Criteria:**
- `alembic upgrade head` applies with 0 errors
- `scans` table has correct schema including `confidence_pct` column
- `backend/database.py` async session factory works (import without error)

---

### 4.2 — FastAPI `/analyze` Endpoint

- [ ] **4.2.1** Open `backend/main.py` — verify FastAPI app has CORS middleware, health check, and router includes
- [ ] **4.2.2** Open `backend/routers/analyze.py` — implement `POST /analyze` endpoint fully:
  1. Validate `AnalyzeRequest` (url, network_signals, permission_signals)
  2. Extract URL features via `feature_extractor/url_features.py` (calls VT client)
  3. Merge network signals sent from extension (trust them — do NOT re-fetch)
  4. Run `heuristics_engine.py` on permission signals → get `rule_flags`
  5. Combine all features → load `model.pkl` → `predict_proba()` → `risk_score`
  6. Run SHAP → `top_reasons` (human-readable via `explainer_formatter.py`)
  7. Determine verdict: `> 0.7` → phishing, `0.4–0.7` → suspicious, `< 0.4` → legitimate
  8. Write `Scan` record to PostgreSQL
  9. Return `AnalyzeResponse`
- [ ] **4.2.3** `AnalyzeResponse` schema must include `confidence_pct: int` (e.g., `87`) alongside `risk_score: float` (e.g., `0.87`)
- [ ] **4.2.4** Add `functools.lru_cache` wrapper on VT client calls (use `cachetools.TTLCache` with 1-hour TTL) — prevents re-querying the same domain repeatedly and avoids free-tier rate limits
- [ ] **4.2.5** Add 5-second timeout on all external HTTP calls (VT API). On timeout, set VT features to `-1` and continue — never let a VT timeout crash the endpoint
- [ ] **4.2.6** Write integration test `tests/integration/test_analyze_endpoint.py` — mock the VT client and model; assert response schema is valid

**Acceptance Criteria:**
- `POST /analyze {"url": "http://paypal-secure-login.xyz"}` returns `verdict: "phishing"`, `confidence_pct: > 70`, `top_reasons` with 3 human-readable strings (no snake_case)
- `POST /analyze {"url": "https://google.com"}` returns `verdict: "legitimate"`
- Response time < 10 seconds even on first call (WHOIS removed; VT has 5s timeout with fallback)
- Integration test passes: `pytest tests/integration/test_analyze_endpoint.py`

---

### 4.3 — History, Stats & Detail Endpoints

- [ ] **4.3.1** Open `backend/routers/history.py` — implement `GET /history?limit=50&offset=0` returning paginated scan records
- [ ] **4.3.2** Add `GET /stats` endpoint — returns `{ total_scans, phishing_count, legitimate_count, suspicious_count }`
- [ ] **4.3.3** Add `GET /scan/{scan_id}` endpoint — returns full scan detail including `shap_values`, `confidence_pct`, and all signal data
- [ ] **4.3.4** Seed 10 test scans via a `python backend/scripts/seed_db.py` script — verify `/stats` returns correct counts

**Acceptance Criteria:**
- All 3 endpoints return 200 with correct schemas
- Swagger UI at `http://localhost:8000/docs` shows all endpoints with correct request/response schemas
- `GET /stats` returns accurate counts after seeding

---

### 4.4 — Backend Deployment

- [ ] **4.4.1** Open `backend/Dockerfile` — review multi-stage build
- [ ] **4.4.2** Deploy to Railway or Render (free tier) — set all env vars from `.env.example` in the platform dashboard
- [ ] **4.4.3** Provision PostgreSQL on the same platform; run `alembic upgrade head` via the deploy shell
- [ ] **4.4.4** Verify: `curl https://<your-deploy-url>/health` → `{"status": "ok"}`
- [ ] **4.4.5** Update `PROJECT_STATE.md` Live Endpoints table with the deployed backend URL

**Acceptance Criteria:**
- Live backend health check responds within 3 seconds
- `POST https://<live-url>/analyze` returns a valid phishing verdict for a known phishing URL
- Database persists scan records across deploys

---

## Phase 5 — Extension ↔ Backend Integration & Popup UI (Week 9)

**Objective:** Wire the extension to the live backend and build the popup UI with confidence score display and SHAP-powered plain-English explanations.

### 5.1 — Extension API Integration

- [ ] **5.1.1** Open `extension/services/api_client.js` — implement `analyzePage(url, networkSignals, permissionSignals)` that POSTs to `BACKEND_URL/analyze`
- [ ] **5.1.2** Update `extension/background.js` — on `chrome.tabs.onUpdated` (status `complete`):
  1. Read `networkSignals` + `permissionSignals` from `chrome.storage.local`
  2. Call `analyzePage()` 
  3. Store the full response in `chrome.storage.local[tabId]`
  4. Update the extension badge: red badge "!" for phishing, no badge for safe
- [ ] **5.1.3** Handle loading state: store `{ status: "scanning" }` before the call, `{ status: "done", result: {...} }` after, `{ status: "error" }` on failure
- [ ] **5.1.4** On error/offline: set `status: "error"` and store `{ error_message: "Could not reach analysis server. Check your connection." }` — popup will show a Retry button

**Acceptance Criteria:**
- Navigating to `https://google.com` → `chrome.storage.local` contains result within 15 seconds
- Extension badge shows red "!" on a known phishing URL
- Console shows no unhandled promise rejections

---

### 5.2 — Popup UI

- [ ] **5.2.1** Build `extension/popup/popup.html` — 4-state UI:
  - **Scanning**: spinner + "Analyzing page..."
  - **Safe**: green shield, "Page Looks Safe", confidence badge (e.g., "96% confident")
  - **Suspicious**: amber shield, "Proceed with Caution", confidence %, top 3 reasons
  - **Phishing**: red shield, "⚠ Phishing Detected", confidence %, top 3 SHAP reasons, "View Full Report" button
  - **Error**: grey icon, error message, "Retry" button
- [ ] **5.2.2** Update `extension/popup/popup.css` — dark theme, color tokens: safe=`#22c55e`, suspicious=`#f59e0b`, phishing=`#ef4444`, background=`#0f0f1a`, card=`#1a1a2e`
- [ ] **5.2.3** Implement `extension/popup/popup.js`:
  - Read result from `chrome.storage.local` for the current tab
  - Render the correct state
  - Display `confidence_pct` as "XX% confident" — e.g., "92% confident this is phishing"
  - Display SHAP `top_reasons[].human_readable` as bullet points — these are already plain English
  - "View Full Report" → opens dashboard `/scan/<scan_id>` in a new tab
- [ ] **5.2.4** Retry button: re-triggers the scan by sending a message to the background service worker

**Acceptance Criteria:**
- Popup correctly shows all 4 states
- Confidence percentage is visible and correct on phishing/suspicious/safe verdicts
- SHAP reason bullets contain no snake_case text
- "View Full Report" opens the correct dashboard URL

---

## Phase 6 — Next.js Dashboard (Week 10)

**Objective:** Build a polished Next.js dashboard with scan history, risk distribution, confidence scores, and full SHAP explanation drill-downs including a risk-score-over-time sparkline.

### 6.1 — Dashboard Setup & Layout

- [ ] **6.1.1** Initialize Next.js 14 in `dashboard/`: `npx create-next-app@latest . --typescript --tailwind --app --no-git`
- [ ] **6.1.2** Install dependencies: `npm install recharts date-fns`
- [ ] **6.1.3** Create `dashboard/lib/api.ts` — typed API client: `getHistory()`, `getStats()`, `getScan(id: string)`
- [ ] **6.1.4** Create `dashboard/lib/types.ts` — TypeScript interfaces: `Scan`, `Stats`, `ShapReason` — all fields typed, no `any`
- [ ] **6.1.5** Create `dashboard/components/layout/` — `Navbar.tsx`, `PageWrapper.tsx`
- [ ] **6.1.6** Configure dark theme in `dashboard/app/globals.css` — matching extension color palette

**Acceptance Criteria:**
- `npm run dev` starts with no TypeScript or runtime errors
- Dark-theme navbar renders on all pages
- `npx tsc --noEmit` passes

---

### 6.2 — Dashboard Pages

- [ ] **6.2.1** Build `dashboard/app/page.tsx` (Overview):
  - 4 stat cards: Total Scans, Phishing Detected, Suspicious, Legitimate
  - `RiskDistributionChart` — Recharts PieChart with verdict breakdown
  - Average confidence score card (mean `confidence_pct` across all scans)
- [ ] **6.2.2** Build `dashboard/app/history/page.tsx`:
  - Sortable, paginated table: URL (truncated), verdict badge, **confidence %**, risk score, timestamp
  - Clicking a row navigates to `/scan/[id]`
- [ ] **6.2.3** Build `dashboard/app/scan/[id]/page.tsx` (full detail):
  - URL + verdict banner with confidence % (e.g., "Phishing — 92% confident")
  - Risk score progress bar (0–100%)
  - **SHAP Waterfall Chart** — horizontal bars, top 5 features, red = increases risk, green = decreases risk, bars labeled with `human_readable` strings
  - Network signals card: tracker count, mixed content badge, redirect count
  - Permission flags card: list of triggered rules with plain-English descriptions
  - **Risk History Sparkline**: if this URL has been scanned before, show a line chart of `confidence_pct` over time
- [ ] **6.2.4** Create `dashboard/components/charts/ShapWaterfallChart.tsx` — Recharts horizontal bar chart; bars colored by SHAP sign; tooltips show raw feature value
- [ ] **6.2.5** Create `dashboard/components/charts/RiskSparkline.tsx` — Recharts LineChart showing `confidence_pct` over time for repeat scans of the same URL
- [ ] **6.2.6** Create `dashboard/components/VerdictBadge.tsx` — colored pill (Phishing=red, Suspicious=amber, Legitimate=green)
- [ ] **6.2.7** Create `dashboard/components/ConfidenceBadge.tsx` — shows `XX%` with color gradient (red at 90%+, amber at 50–70%, green at <40% phishing confidence)

**Acceptance Criteria:**
- Overview shows correct stats + average confidence from `/stats`
- History table shows confidence % column
- Scan detail shows SHAP waterfall with human-readable labels (no snake_case visible to user)
- Confidence % on scan detail page matches value from backend
- Risk sparkline renders correctly for a URL scanned more than once
- `npx tsc --noEmit` passes with 0 errors

---

### 6.3 — Dashboard Deployment

- [ ] **6.3.1** Deploy `dashboard/` to Vercel: connect GitHub repo or `npx vercel --prod`
- [ ] **6.3.2** Set `NEXT_PUBLIC_BACKEND_URL` in Vercel environment variables
- [ ] **6.3.3** Update `PROJECT_STATE.md` Live Endpoints table with Vercel URL
- [ ] **6.3.4** Update `extension/config.js` dashboard URL constant to the live Vercel URL

**Acceptance Criteria:**
- Live dashboard URL loads within 3 seconds
- Dashboard correctly fetches and displays live scan data from deployed backend

---

## Phase 7 — Evaluation & Academic Reporting (Week 11)

**Objective:** Produce rigorous academic evaluation artifacts. Include a baseline comparison to directly answer the "why not just use a blocklist?" examiner question.

### 7.1 — Model Evaluation Report

- [ ] **7.1.1** Create `ml/notebooks/05_final_evaluation.ipynb` — run all cells:
  - Confusion matrix (annotated TP/FP/TN/FN counts)
  - Classification report (precision, recall, F1-score)
  - ROC-AUC curve with AUC value annotated
  - SHAP beeswarm summary plot (global feature importance)
  - Top 10 features ranked by mean |SHAP value|
- [ ] **7.1.2** **Baseline Comparison** — add a section to Notebook 05:
  - Implement a simple URL blocklist baseline: check if the URL is in the PhishTank dataset (a pure lookup, no ML)
  - Compute F1/precision/recall for the baseline on the test set
  - Create a side-by-side table: **Baseline vs. XGBoost + Multi-signal**
  - This directly answers the examiner question "why not just use a blocklist?" with data — your model catches URLs not in the training blocklist
- [ ] **7.1.3** Create `ml/reports/evaluation_report.md` — write-up including:
  - Dataset sources and download dates (from `DATASET_SOURCES.md`)
  - Model performance numbers (actual values, not fabricated)
  - Baseline comparison results
  - Known limitations (dataset freshness, novel scam patterns, browser-sandbox scope)

**Acceptance Criteria:**
- F1-score ≥ 0.85, ROC-AUC ≥ 0.90 (document actual values)
- Baseline comparison table shows XGBoost outperforming simple blocklist, especially on novel URLs
- `DATASET_SOURCES.md` is cited in the report
- All notebook cells run without errors

---

### 7.2 — End-to-End System Test

- [ ] **7.2.1** Create `tests/e2e/system_test.md` — manual E2E test plan: 10 URLs (5 phishing from PhishTank, 5 legitimate top-1M sites)
- [ ] **7.2.2** Execute the test plan; document: URL, expected verdict, actual verdict, confidence %, pass/fail
- [ ] **7.2.3** Fix any bugs surfaced during E2E testing
- [ ] **7.2.4** Record a 2-minute demo video (Loom or OBS): extension popup scan → phishing warning with confidence % → "View Full Report" → dashboard SHAP waterfall → history table

**Acceptance Criteria:**
- ≥ 8/10 URLs correctly classified
- Demo video shows confidence % in popup and dashboard
- Demo video link is stored in `PROJECT_STATE.md`

---

### 7.3 — Stretch Goals (only if ≥ 1 week remains after 7.2)

- [ ] **7.3.1** [STRETCH] Exfiltration-pattern detection: flag POST requests > 10KB body to a domain not in `shared/tracker_domains.json` (heuristic, extension-side)
- [ ] **7.3.2** [STRETCH] User false-positive reporting: "Mark as Safe" button in popup → `POST /report` endpoint → stores in a `reports` table
- [ ] **7.3.3** [STRETCH] Chrome Web Store submission (unlisted listing) — requires extension ZIP and privacy policy page

---

## Phase 8 — Documentation & Defense Prep (Week 12)

**Objective:** Polish all documentation, finalize for submission, prep for viva.

### 8.1 — Documentation

- [ ] **8.1.1** Write final `README.md` — project overview, architecture diagram (ASCII or Mermaid), Docker setup instructions, live demo links (backend URL + dashboard URL)
- [ ] **8.1.2** Write `LIMITATIONS.md` — honest scope statement: browser sandbox only, dataset generalization, research-scale deployment, VirusTotal API rate limits in production
- [ ] **8.1.3** Finalize inline code comments in: `backend/routers/analyze.py`, `ml/features/url_features.py`, `ml/shap_analysis.py`
- [ ] **8.1.4** Verify `backend/docs` (Swagger at `/docs`) is accessible on the live deployment

### 8.2 — Defense Preparation

- [ ] **8.2.1** Prepare 5-slide technical summary: architecture → ML pipeline → SHAP + confidence score → evaluation (baseline comparison) → limitations + future work
- [ ] **8.2.2** Prepare answers for these 4 anticipated examiner questions:
  1. "Why XGBoost over a neural network?" → Tabular features, no GPU needed, SHAP TreeExplainer native support, interpretable
  2. "Why heuristics for permissions and not ML?" → Permission abuse is near-binary; rule is faster, more explainable, keeps SHAP output clean
  3. "What are the limitations of browser-sandbox monitoring?" → Cannot see OS-level traffic, HTTPS payloads, or other applications
  4. **"Why not just use a blocklist?"** → See baseline comparison: our model catches URLs not in any blocklist by generalizing from features
- [ ] **8.2.3** Confirm all live URLs (backend, dashboard) respond within 3 seconds on defense day

**Acceptance Criteria:**
- `README.md` Docker setup successfully reproduced from fresh clone
- All live URLs accessible
- Demo video link in `PROJECT_STATE.md` is shareable

---

## Summary Checklist

| Phase | Weeks | Status |
|---|---|---|
| Phase 1: Skeleton & Dataset | 1–2 | 🔲 Not Started |
| Phase 2: ML Pipeline, SHAP & Confidence | 3–4 | 🔲 Not Started |
| Phase 3: Browser Signal Extractors | 5–6 | 🔲 Not Started |
| Phase 4: FastAPI Backend (Full Integration) | 7–8 | 🔲 Not Started |
| Phase 5: Extension ↔ Backend + Popup UI | 9 | 🔲 Not Started |
| Phase 6: Next.js Dashboard | 10 | 🔲 Not Started |
| Phase 7: Evaluation + Baseline Comparison | 11 | 🔲 Not Started |
| Phase 8: Documentation & Defense | 12 | 🔲 Not Started |
