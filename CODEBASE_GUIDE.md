# CODEBASE GUIDE — AI-Powered Explainable Security & Privacy Analyst
> **Purpose:** Your daily reference. Read this to understand what every file does, why it exists, and how it connects to everything else. Both AntiGravity and Cursor must update the [Session Log](#session-log) at the end of every session.

---

## Table of Contents

1. [How the System Works (Big Picture)](#1-how-the-system-works-big-picture)
2. [Root-Level Files](#2-root-level-files)
3. [Extension — `extension/`](#3-extension--extension)
4. [Backend — `backend/`](#4-backend--backend)
5. [Machine Learning — `ml/`](#5-machine-learning--ml)
6. [Shared Assets — `shared/`](#6-shared-assets--shared)
7. [Tests — `tests/`](#7-tests--tests)
8. [Docker — `docker/`](#8-docker--docker)
9. [Cursor Rules — `.cursor/`](#9-cursor-rules--cursor)
10. [Key Concepts Explained Simply](#10-key-concepts-explained-simply)
11. [How the Data Flows (End to End)](#11-how-the-data-flows-end-to-end)
12. [Session Log](#12-session-log)

---

## 1. How the System Works (Big Picture)

You are building a **browser security tool** that tells users, in plain English, whether a webpage they are visiting is likely a phishing/scam site — and *why* it thinks so.

Here is the entire system in one paragraph:

> A **Chrome Extension** watches every page you visit. It collects signals about the page (suspicious URL patterns, how many trackers are loaded, whether the page asked for your camera without you doing anything). It sends those signals to a **FastAPI backend** running on a cloud server. The backend feeds everything into an **XGBoost machine learning model** that was trained on thousands of phishing and legitimate URLs. The model outputs a probability (e.g., 92% likely phishing). A **SHAP explainer** then figures out *which signals caused that score* and returns the top 3 reasons in human-readable English. The extension popup shows the result instantly. A **Next.js dashboard** lets you browse your full scan history and see detailed explanations.

### The Four Components

```
┌─────────────────────┐      POST /analyze       ┌──────────────────────┐
│  Chrome Extension   │ ──────────────────────►  │  FastAPI Backend     │
│  (extension/)       │                           │  (backend/)          │
│                     │ ◄──────────────────────   │                      │
│  Collects signals,  │   verdict + confidence +  │  ML model + SHAP +   │
│  shows popup result │   plain-English reasons   │  PostgreSQL writes   │
└─────────────────────┘                           └──────────┬───────────┘
                                                             │
                                                    writes scan record
                                                             │
                                                  ┌──────────▼───────────┐
                                                  │   PostgreSQL DB       │
                                                  └──────────┬───────────┘
                                                             │
                                                    reads history/stats
                                                             │
                                                  ┌──────────▼───────────┐
                                                  │  Next.js Dashboard   │
                                                  │  (dashboard/)        │
                                                  └──────────────────────┘
```

---

## 2. Root-Level Files

### `.gitignore`
**What it does:** Tells Git which files to ignore and never commit to the repository.

**Why it exists:** Prevents you from accidentally committing:
- Secret keys (your VirusTotal API key)
- The trained ML model `.pkl` file (too large for Git)
- Raw CSV datasets (hundreds of MB)
- Compiled Python bytecode, Node modules, etc.

**Key entries to know:**
- `ml/models/*.pkl` → The trained model binary. Never commit this; it's rebuilt by running the training script.
- `ml/data/raw/*.csv` → Raw datasets. Too large; download them fresh when needed.
- `.env` → Your local secrets file. `.env.example` IS committed (it's a template with no real values).

---

### `.env.example`
**What it does:** A template of all environment variables the system needs, with placeholder values.

**Why it exists:** You copy this to `.env` and fill in your real values. The `.env` file is never committed. Anyone setting up the project from scratch copies this template and knows exactly what to fill in.

**Variables you need to fill:**
| Variable | What to put |
|---|---|
| `DATABASE_URL` | Postgres connection string — already filled for local Docker |
| `VIRUSTOTAL_API_KEY` | Get a free key at virustotal.com/gui/sign-in |
| `BACKEND_URL` | `http://localhost:8000` locally; your Render/Railway URL after deploying |
| `NEXT_PUBLIC_BACKEND_URL` | Same as BACKEND_URL but for the Next.js dashboard |

---

### `ROADMAP.md`
**What it does:** The master task list for the entire project. Every feature, broken into phases and individual checkboxes.

**Why it exists:** This is the single source of truth for "what needs to be built." Cursor reads it to know what task to work on. AntiGravity updates it when the plan changes. You read it to see progress.

**How to read it:** Phases go from 1 to 8. Inside each phase, tasks are numbered (e.g., `1.1.3`). Each task has an Acceptance Criteria section — these are the tests that prove the task is truly done, not just written.

---

### `PROJECT_STATE.md`
**What it does:** Real-time dashboard of the project's current state. What's being worked on right now, what decisions have been made, and a log of all agent activity.

**Why it exists:** This is the handoff document between AntiGravity (planner) and Cursor (coder). Cursor reads this first every session. It answers: "Where was I? What do I do next? Have any architectural decisions changed?"

**Key sections:**
- **Current Status table** → The one task Cursor should be working on right now
- **ADRs (Architectural Decision Records)** → Every major design choice recorded with its rationale. If you ever wonder "why did we do it this way?", this is where you look
- **Directory Structure** → Which files are ready (✅) vs. still need to be built (🔲)
- **Agent Activity Log** → What was done in each session, by which agent

---

### `CODEBASE_GUIDE.md` (this file)
**What it does:** Plain-English explanation of every file and concept in the project.

**Why it exists:** So you can review what's being built daily and understand the reasoning behind each piece, even if you weren't present for that coding session. Both agents update the Session Log at the end of every session.

---

## 3. Extension — `extension/`

The Chrome Extension is the user-facing part that runs inside the browser. It has no visible window — it works silently in the background and shows a popup when you click its icon.

---

### `extension/manifest.json`
**What it does:** The "ID card" of the Chrome Extension. Chrome reads this file to understand what the extension is, what permissions it needs, and which scripts to run.

**Why these permissions:**
| Permission | Why it's needed |
|---|---|
| `activeTab` | To read the URL of the current tab |
| `storage` | To save scan results per-tab so the popup can read them |
| `webRequest` | To listen to all network requests made by pages (for tracker counting) |
| `tabs` | To update the badge (red "!" for phishing) and detect navigation |
| `host_permissions: <all_urls>` | To observe requests on any website, not just a fixed list |

**MV3 (Manifest Version 3):** Chrome's new standard. The old version (MV2) is deprecated. The biggest change: background scripts are now "service workers" that can be shut down by Chrome when idle (they wake up on events). This is why state must be stored in `chrome.storage.local` rather than in memory variables.

---

### `extension/background.js`
**What it does:** The brain of the extension. It's a service worker (runs in the background, not attached to any visible page). It coordinates everything.

**Responsibilities:**
1. Listens for tab navigation events (`chrome.tabs.onUpdated`)
2. When a page finishes loading, it collects the network and permission signals
3. Calls the backend API via `api_client.js`
4. Stores the result in `chrome.storage.local` keyed by tab ID
5. Updates the browser badge (red "!" for phishing, amber "?" for suspicious, blank for safe)

**Why tab ID is used as the key:** Each browser tab has a unique integer ID. Storing results by tab ID means the popup always shows the result for the *currently open tab*, not some previous scan.

**Why results are stored in `chrome.storage.local`:** In MV3, the popup and background script are separate processes. They can't share variables. `chrome.storage.local` is the shared memory between them.

---

### `extension/content_script.js`
**What it does:** A JavaScript file that gets injected into every webpage you visit. It runs *inside* the page context, so it can see what JavaScript the page is running.

**Why it exists:** The background service worker can't see what JavaScript a page is executing. The content script acts as a spy inside the page. It watches for:
- Camera/microphone permission requests (`getUserMedia`)
- Notification permission requests (`Notification.requestPermission`)
- Geolocation requests (`navigator.geolocation.getCurrentPosition`)

**How it detects these:** It uses a technique called "method interception" — it replaces the browser's built-in functions with its own wrapper. When the page calls `Notification.requestPermission()`, it actually calls our wrapper first, which records the event, then calls the real function.

**Why heuristics here and not ML:** Permission abuse is a near-binary signal. A page asking for your camera before you've done anything is inherently suspicious. A simple rule catches it faster and more explainably than a machine learning model. The rule flags get sent to the backend and appear in the SHAP explanation.

---

### `extension/config.js`
**What it does:** A single file with two URL constants — the backend URL and the dashboard URL.

**Why it exists:** If these URLs were scattered across multiple files, you'd have to update 5 different places after deploying. With `config.js`, you update once and all other files import from here.

**After deploying:** Change `BACKEND_URL` to your Render/Railway URL and `DASHBOARD_URL` to your Vercel URL.

---

### `extension/modules/network_monitor.js`
**What it does:** Listens to all network requests made by the current tab and extracts security signals.

**Three signals it collects:**

| Signal | How it's detected | Why it matters |
|---|---|---|
| `tracker_count` | Checks each request's hostname against `shared/tracker_domains.json` | High tracker counts mean the page is data-hungry — a minor phishing signal but a major privacy signal |
| `has_mixed_content` | Flags if an `http://` resource loads on an `https://` page | Legitimate HTTPS sites never do this; it indicates a poorly maintained or suspicious page |
| `redirect_chain_length` | Counts `onBeforeRedirect` events | Phishing pages often chain redirects to hide the true destination |

**Why signals come from the extension and NOT the backend:** The original plan included fetching the URL from the backend server to count redirects. This was removed because: (1) fetching a live phishing URL from your server is a security risk, (2) it adds 5+ seconds of latency, (3) the extension already has this data for free. The extension sends the count, the backend trusts it.

**Status:** Skeleton is in place. The tracker lookup (Task 3.1.2) is stubbed with a TODO — to be implemented in Phase 3.

---

### `extension/services/api_client.js`
**What it does:** The only file in the extension that talks to the backend. It has one function: `analyzePage(url, networkSignals, permissionSignals)`.

**Why it's isolated in its own file:** Separation of concerns. If the backend API changes (e.g., endpoint path, authentication header), you only change one file, not everywhere a `fetch()` call might exist.

**How it handles timeouts:** It uses `AbortController` — a browser API that lets you cancel a `fetch()` request after a set time. If the backend doesn't respond in 15 seconds, the request is cancelled and the popup shows an error state.

---

### `extension/popup/popup.html`
**What it does:** The HTML structure of the popup window that appears when you click the extension icon.

**Four states (all in the HTML, only one visible at a time):**
1. **Scanning** — spinner + "Analyzing page..." (shown while backend call is in flight)
2. **Safe** — green shield + confidence % (e.g., "96% confident this page is safe")
3. **Suspicious** — amber warning + confidence % + top 3 reasons
4. **Phishing** — red X + confidence % + top 3 reasons + "View Full Report" button
5. **Error** — grey icon + error message + "Retry" button

**Why 5 states, not 3:** The loading and error states are critical UX. Without them, the popup would appear blank while scanning, or give no feedback if the backend is down.

---

### `extension/popup/popup.css`
**What it does:** All the visual styling for the popup — colors, fonts, layout, animations.

**Design decisions:**
- **Dark theme** — matches developer aesthetic; consistent with the dashboard; easier on the eyes when used frequently
- **Color coding** — safe=green (`#22c55e`), suspicious=amber (`#f59e0b`), phishing=red (`#ef4444`). These are not arbitrary — they match standard traffic-light security conventions
- **Design tokens in `:root`** — colors are defined once as CSS variables (`--safe`, `--phishing`, etc.) and referenced everywhere. If the color scheme changes, you update one line

---

### `extension/popup/popup.js`
**What it does:** The controller that reads the scan result from storage and renders the correct popup state.

**How it works:**
1. Gets the current tab ID from Chrome
2. Reads `chrome.storage.local[tabId]` to get the cached result
3. Looks at `result.status`: `"scanning"` → show spinner, `"done"` → show verdict, `"error"` → show error
4. Fills in the confidence % and renders SHAP reason bullets from `result.top_reasons[].human_readable`

**Why `human_readable` and not the raw feature name:** Raw feature names are snake_case internal identifiers like `domain_age_days`. Users should never see these. The backend translates every feature name into a plain-English sentence using the template system before the result even reaches the extension.

---

## 4. Backend — `backend/`

The backend is a Python web server. It receives signals from the extension, runs the ML model, and returns a verdict with explanations.

---

### `backend/main.py`
**What it does:** The entry point of the FastAPI application. Creates the `app` object, attaches middleware, and registers all the route groups (called "routers").

**CORS middleware:** This is required to allow the Chrome Extension and the Next.js dashboard (which run on different origins/ports) to call the backend API. Without it, browsers block the requests.

**Two routers registered:**
- `analyze.router` → handles `POST /analyze` and is the core of the system
- `history.router` → handles `GET /history`, `GET /stats`, `GET /scan/{id}`

---

### `backend/database.py`
**What it does:** Sets up the database connection. Creates the async engine, the session factory, and the `get_db` dependency.

**Why async:** FastAPI is an async framework. Using an async database driver (`asyncpg`) means database queries don't block the server — it can handle multiple requests simultaneously. For an ML inference endpoint that's already slow (5–10 seconds), this matters.

**`get_db` dependency:** This is a FastAPI pattern. Rather than creating a database session inside each endpoint function, you declare `db: AsyncSession = Depends(get_db)` as a parameter. FastAPI handles creating and closing the session automatically.

---

### `backend/models/scan.py`
**What it does:** Defines the `Scan` database table as a Python class using SQLAlchemy ORM.

**Why ORM instead of raw SQL:** You write Python, SQLAlchemy generates the SQL. You get type safety, easy migrations, and no SQL injection vulnerabilities.

**Key columns:**
| Column | Type | Purpose |
|---|---|---|
| `id` | UUID | Unique identifier for each scan (links popup "View Full Report" to dashboard) |
| `verdict` | String | "phishing" / "suspicious" / "legitimate" |
| `risk_score` | Float | Raw model probability, e.g., 0.92 |
| `confidence_pct` | Integer | `round(risk_score * 100)` = 92 — displayed in popup/dashboard |
| `shap_values` | JSONB | The full SHAP explanation array stored as JSON |
| `network_signals` | JSONB | What the extension's network monitor observed |
| `permission_signals` | JSONB | What permission requests were detected |

**Why JSONB for SHAP values:** SHAP values are a variable-length list of objects. Storing them in PostgreSQL's JSONB format means you don't need a separate table or schema changes when you add new features. JSONB also lets you query inside the JSON if needed.

---

### `backend/routers/analyze.py`
**What it does:** Implements the `POST /analyze` endpoint — the most important file in the entire backend.

**The pipeline inside this endpoint (Phase 4 will implement this fully):**
```
Incoming request
    │
    ▼
1. Validate with Pydantic (AnalyzeRequest)
    │
    ▼
2. Extract URL features (url_features.py + VT client)
    │
    ▼
3. Run heuristics engine (network + permission signals → rule flags)
    │
    ▼
4. Merge all features into one vector
    │
    ▼
5. XGBoost predict_proba() → risk_score (e.g., 0.92)
    │
    ▼
6. SHAP explainer → which features drove the score
    │
    ▼
7. Format SHAP features as human-readable strings
    │
    ▼
8. Write Scan record to PostgreSQL
    │
    ▼
9. Return AnalyzeResponse with confidence_pct, verdict, top_reasons
```

**`AnalyzeResponse` includes `confidence_pct`:** This is `round(risk_score * 100)`. It's an integer (e.g., 92) rather than a float (0.92) because the popup and dashboard display it as "92% confident this is phishing". Both representations are returned so consumers can use whichever they need.

**Current state:** The endpoint is a stub that returns a hardcoded "legitimate" response. This is intentional — it lets the extension load and the backend run during Phase 1 before the ML model exists.

---

### `backend/routers/history.py`
**What it does:** Three read-only endpoints for the dashboard:
- `GET /history` — paginated list of all scans
- `GET /stats` — aggregate counts (total, phishing, legitimate, suspicious, average confidence)
- `GET /scan/{id}` — full detail for one scan including raw SHAP data

**`avg_confidence_pct` in stats:** This was added as an improvement — the dashboard Overview page shows this as a stat card. It tells you the average confidence level across all scans, giving a sense of how decisive the model has been.

**Current state:** All three are stubs. Implemented in Phase 4.3.

---

### `backend/feature_extractor/url_features.py`
**What it does:** Extracts a flat dictionary of numerical features from any URL string. This dictionary is what goes into the XGBoost model.

**Every feature, explained:**

| Feature | What it measures | Why it's a phishing signal |
|---|---|---|
| `url_length` | Character count of the full URL | Phishing URLs tend to be long (lots of path segments to look legitimate) |
| `num_digits` | How many digit characters are in the URL | Phishers often use digits to create lookalike domains (paypa1.com) |
| `num_special_chars` | Count of `-`, `_`, `@`, `?`, `=`, `%`, `&` | High count often indicates encoded obfuscation |
| `subdomain_depth` | Number of dots in hostname - 1 | `login.paypal.com` = 1 level. `paypal.com.evil.xyz` = 3 levels — a common trick |
| `has_https` | Boolean: does URL start with `https://`? | Note: HTTPS doesn't guarantee safety, but HTTP is a red flag |
| `url_entropy` | Shannon entropy of the URL string | Randomly-generated phishing domains have high entropy |
| `has_ip_in_hostname` | Is the hostname a raw IP address? | Legitimate sites use domain names, not raw IPs |
| `suspicious_tld_flag` | Is the TLD in a known-abused list? | `.xyz`, `.tk`, `.ml`, `.ga`, `.cf` are statistically over-represented in phishing |
| `brand_impersonation` | Does a brand name appear outside the main domain? | `paypal-login.net` has "paypal" but it's not `paypal.com` |
| `domain_age_days` | Days since domain was registered (via VirusTotal) | New domains (< 30 days) are a very strong phishing signal |
| `vt_malicious_votes` | How many VT security vendors flagged it | Direct threat intelligence from 70+ security companies |
| `vt_harmless_votes` | How many VT vendors say it's safe | Provides context for the malicious vote count |

**Why VirusTotal instead of WHOIS:** The original plan used `python-whois` for domain age. WHOIS lookups are: (1) slow (3–12 seconds), (2) frequently rate-limited, (3) return inconsistent date formats. VirusTotal gives domain age AND malicious vote counts in one fast API call with a reliable format. The free tier (4 requests/minute) is enough for a research demo.

---

### `backend/services/heuristics_engine.py`
**What it does:** Evaluates the network and permission signals from the extension using hard-coded rules. Returns a list of triggered rule names and numerical features to add to the XGBoost feature vector.

**Why rules instead of ML for this part:** Network and permission signals like "page asked for camera on first visit" are near-binary — they're either happening or they're not. There's no "sort of" — this is inherently suspicious behavior. A hard rule fires faster, uses no compute, and produces an explanation that's cleaner for SHAP: "camera permission requested immediately" is a single boolean feature the model can use.

**Rules currently implemented:**
- `excessive_trackers` → tracker_count > 10
- `has_mixed_content` → page loads HTTP resources on HTTPS
- `long_redirect_chain` → more than 3 redirects
- `cam_mic_on_first_visit` → camera/mic before user interaction
- `notification_prompt_on_load` → notification permission within 3 seconds
- `location_on_load` → geolocation within 3 seconds

---

### `backend/services/explainer_formatter.py`
**What it does:** Translates raw SHAP feature names (snake_case) into human-readable English sentences.

**Why this exists:** The XGBoost model works with feature names like `domain_age_days`, `vt_malicious_votes`. These mean nothing to a user. `explainer_formatter.py` loads the template map from `shared/feature_name_to_human_readable.json` and substitutes the actual value. Example: `domain_age_days = 2` → `"Domain was registered only 2 days ago"`.

**This is enforced as an ADR (ADR-010):** No raw feature name should ever reach the popup or dashboard. If you see snake_case in the UI, this step was bypassed — that's a bug.

---

## 5. Machine Learning — `ml/`

The ML directory is separate from the backend because training is an **offline process** — you run it once (or a few times), produce a `model.pkl` file, and then the backend loads that file for inference. You never train the model in real-time.

---

### `ml/scripts/prepare_dataset.py`
**What it does:** Merges the PhishTank phishing URLs and Tranco legitimate URLs into one clean training dataset.

**Output:** `ml/data/processed/dataset.csv` with two columns: `url` (the URL string) and `label` (1 = phishing, 0 = legitimate).

**Why balance matters:** If you have 10,000 phishing URLs and 100 legitimate ones, the model will learn to always say "phishing" and be 99% accurate — but useless. You need roughly equal amounts of each class. The script warns if balance falls outside 40–60%.

---

### `ml/scripts/train_model.py`
**What it does:** Loads the feature-extracted dataset (`features.csv`), trains an XGBoost classifier, evaluates it, and saves the model.

**Key decisions in this script:**
- `scale_pos_weight` — automatically calculated from the data ratio. This is XGBoost's built-in way to handle class imbalance. It tells the model to penalize mistakes on the minority class more heavily.
- `n_estimators=200, max_depth=6, learning_rate=0.1` — sensible defaults for a tabular phishing dataset. These can be tuned later.
- Saves `feature_columns.json` alongside the model — critical. This JSON file records the exact order of features the model was trained on. At inference time, you must build the feature vector in the same order, or the model's predictions are garbage.

**Targets:** F1-score ≥ 0.85, ROC-AUC ≥ 0.90. The script warns if either is below threshold.

---

### `ml/shap_analysis.py`
**What it does:** Wraps the trained model with a SHAP TreeExplainer to produce per-prediction feature attributions.

**What SHAP does:** SHAP (SHapley Additive exPlanations) answers the question "how much did each feature contribute to this specific prediction?" For example: for URL `paypal-login.xyz`, SHAP might say: `domain_age_days` contributed +0.45 (strong positive push toward phishing), `suspicious_tld_flag` contributed +0.30, `brand_impersonation` contributed +0.28. We take the top 3 and show them in the popup.

**Why TreeExplainer specifically:** There are multiple SHAP explainer types. `TreeExplainer` is designed for tree-based models (XGBoost is a tree ensemble). It's faster and more accurate than the generic `KernelExplainer` for this model type.

**Status:** Skeleton with TODO — `explain_prediction()` is stubbed and will be implemented in Phase 2.4.

---

### `ml/data/raw/DATASET_SOURCES.md`
**What it does:** A provenance record — documents where the training data came from, when it was downloaded, and how many rows.

**Why this matters academically:** In your FYP defense, examiners will ask "where did your data come from?" This file is the citation. It also documents the dataset's known limitations (e.g., PhishTank reflects phishing patterns at download time — novel scams after that date won't be in the training set).

---

## 6. Shared Assets — `shared/`

Files used by more than one component — both the backend Python code and the extension JavaScript reference these.

---

### `shared/brand_list.txt`
**What it does:** A list of 50 well-known brand names (one per line, lowercase).

**How it's used:** `url_features.py` loads this list and checks: does any brand name appear in the URL but NOT as the main domain? `paypal` appearing in `paypal-login.xyz` is suspicious. `paypal` appearing in `paypal.com` is fine.

**Current brands:** PayPal, Google, Amazon, Microsoft, Apple, Facebook, Instagram, Twitter, Netflix, major banks (Chase, Wells Fargo, BoA, Citi), crypto exchanges (Coinbase, Binance), shipping companies (DHL, FedEx, UPS, USPS), and 20+ more.

---

### `shared/tracker_domains.json`
**What it does:** A JSON array of known third-party tracking domain hostnames.

**Status:** Currently an empty array `[]`. To be populated in Phase 3.1.3 by extracting domain entries from the EasyPrivacy blocklist.

**How it's used:** `network_monitor.js` (extension) checks every network request against this list. If a request goes to `doubleclick.net` (a Google ad tracker), `tracker_count` increments.

---

### `shared/feature_name_to_human_readable.json`
**What it does:** A mapping from every snake_case feature name to a plain-English template string.

**How templates work:** Templates use `{value}` as a placeholder. The `explainer_formatter.py` substitutes the actual value. Example:
```
"domain_age_days": "Domain was registered only {value} days ago"
→ with value=2 → "Domain was registered only 2 days ago"
```

**All features covered:** Every feature that can appear in SHAP output has a template. If a feature has no template, `explainer_formatter.py` falls back to `"Suspicious signal detected (feature_name)"` — not ideal, which is why all features must be in this file.

---

## 7. Tests — `tests/`

### `tests/unit/test_url_features.py`
**What it does:** Automated tests for the URL feature extraction function.

**Why mock the VT client:** Unit tests must not make real network calls — they'd be slow, unreliable, and use up your API quota. `unittest.mock.patch` replaces the VT client with a fake that returns predefined data instantly.

**Test structure:**
- `TestSuspiciousTldFlag` — verifies `.xyz` and `.tk` are flagged, `.com` and `.org` are not
- `TestIpInHostname` — verifies raw IP addresses are detected
- `TestHttpsFlag` — verifies http vs https detection
- `TestVirusTotalFeatures` — verifies VT data is merged correctly and defaults to -1 when missing
- `TestAllFeaturesPresent` — verifies the output dict always has all expected keys (prevents silent feature dropping)

### `tests/manual/` (created in Phase 3)
Manual test plans — documented step-by-step instructions for testing things that are hard to automate, like "load CNN.com and verify tracker count ≥ 5".

### `tests/integration/` (created in Phase 4)
Integration tests that test the full `/analyze` endpoint end-to-end, with the ML model and database mocked.

### `tests/e2e/` (created in Phase 7)
End-to-end test plan — 10 real URLs tested through the complete system (extension → backend → database → dashboard).

---

## 8. Docker — `docker/`

### `docker/docker-compose.yml`
**What it does:** Defines three services that run together locally: `postgres`, `backend`, `dashboard`. One command (`docker-compose up`) starts all of them.

**Service details:**
| Service | Image | Port | Purpose |
|---|---|---|---|
| `postgres` | `postgres:15-alpine` | 5432 | The database |
| `backend` | Built from `backend/Dockerfile` | 8000 | FastAPI server |
| `dashboard` | `node:20-alpine` | 3000 | Next.js dev server |

**Health check on postgres:** The backend waits for postgres to be "healthy" before starting. Without this, the backend would crash on startup because the database isn't ready yet.

**Volume for ML models:** The backend container gets read-only access to `../ml/models/` as a mounted volume. This means when you retrain the model on your host machine, the container picks up the new model without rebuilding.

---

## 9. Cursor Rules — `.cursor/`

### `.cursor/rules/agent-sync.mdc`
**What it does:** Instructions that Cursor reads at the start of every session, telling it exactly how to behave on this project.

**Key rules enforced:**
- Always read `PROJECT_STATE.md` first
- Work on one task at a time
- Mark tasks `[x]` and update the state file after completion
- Never expose snake_case feature names in the UI
- Never change architectural decisions without AntiGravity approval
- Update `CODEBASE_GUIDE.md` Session Log at the end of every session

---

## 10. Key Concepts Explained Simply

### XGBoost
A machine learning algorithm that builds many small decision trees and combines them. It works very well on tabular data (rows and columns) like our URL features. Think of it as: "many weak learners combined into one strong learner."

### SHAP (SHapley Additive exPlanations)
A method to explain *why* a model made a specific prediction. It calculates how much each input feature "pushed" the prediction up or down. The name comes from game theory (Shapley values). For us, it answers: "The model said 92% phishing — why? Because the domain was 2 days old (+0.45 impact), the TLD is .xyz (+0.30), and it impersonates PayPal (+0.28)."

### Confidence Percentage
We convert the model's raw probability (e.g., 0.92) to a percentage (92%). This is purely for display — "92% confident this is phishing" is more legible than "risk_score: 0.92". Both values are stored and returned by the backend.

### Verdict Thresholds
- **Phishing:** risk_score > 0.70 (very likely phishing)
- **Suspicious:** risk_score 0.40–0.70 (uncertain, proceed carefully)
- **Legitimate:** risk_score < 0.40 (likely safe)

These are from ADR in `PROJECT_STATE.md`. Do not change them without documenting a new ADR.

### Why Not a Neural Network?
Neural networks need more data, more compute, and are harder to explain. Our feature set is deliberately tabular (a small number of well-defined numerical features), which is exactly what XGBoost excels at. Most importantly: SHAP's `TreeExplainer` works natively and efficiently with XGBoost. For neural networks, SHAP is much slower. Our explainability-first design makes XGBoost the right choice.

### Why Not a Blocklist?
A blocklist can only block URLs it already knows about. It will always miss brand-new phishing domains (which are often created and discarded within hours). Our model generalizes from *patterns* — it can flag a phishing URL it has never seen before because the URL is 3 days old, uses `.xyz`, and contains "paypal". The evaluation (Phase 7) will prove this with a side-by-side comparison.

---

## 11. How the Data Flows (End to End)

Here is a complete walkthrough of what happens when you visit a suspicious page:

```
1. You navigate to http://paypal-login.xyz

2. extension/content_script.js injects into the page
   → Starts monitoring for permission requests

3. extension/modules/network_monitor.js fires on every network request
   → Checks: is doubleclick.net in tracker_domains.json? Yes → tracker_count++
   → Checks: is this http:// on an https:// page? → has_mixed_content flag

4. The page finishes loading (chrome.tabs.onUpdated fires with status="complete")

5. extension/background.js wakes up
   → Reads network_signals from chrome.storage.local
   → Reads permission_signals sent by content_script.js
   → Calls api_client.js → analyzePage(url, networkSignals, permissionSignals)

6. api_client.js sends POST /analyze to backend:
   {
     "url": "http://paypal-login.xyz",
     "network_signals": {"tracker_count": 2, "has_mixed_content": false, "redirect_chain_length": 1},
     "permission_signals": {"permissions_requested": [], "rule_flags": []}
   }

7. backend/routers/analyze.py receives the request
   → feature_extractor/url_features.py extracts URL features:
      url_length=25, suspicious_tld_flag=1, brand_impersonation=1, has_https=0...
   → Calls VirusTotal API for domain_age_days=2, vt_malicious_votes=8
   → services/heuristics_engine.py evaluates network + permission signals
   → All features merged into one vector of ~18 numbers
   → XGBoost.predict_proba() → 0.94 (94% phishing probability)
   → SHAP TreeExplainer computes: brand_impersonation=+0.42, domain_age_days=+0.38, suspicious_tld_flag=+0.28
   → services/explainer_formatter.py translates each:
      "URL contains a well-known brand name in a suspicious position"
      "Domain was registered only 2 days ago"
      "Domain uses a high-risk top-level domain extension"
   → Scan record written to PostgreSQL
   → Returns AnalyzeResponse:
      {verdict:"phishing", risk_score:0.94, confidence_pct:94, top_reasons:[...], scan_id:"abc-123"}

8. extension/background.js receives the response
   → Stores in chrome.storage.local["tabId"] = {status:"done", result:{...}}
   → Updates badge: red "!" on the extension icon

9. You click the extension icon → popup.html opens
   popup.js reads chrome.storage.local[tabId]
   → Sees verdict:"phishing", confidence_pct:94
   → Renders: red shield, "Phishing Detected", "94% confident this is phishing"
   → Shows 3 bullets with the human-readable SHAP reasons

10. You click "View Full Report"
    → Opens dashboard /scan/abc-123 in a new tab
    → dashboard fetches GET /scan/abc-123 from backend
    → Renders: SHAP waterfall chart, network signals, permission flags
```

---

## 12. Session Log

> **Both AntiGravity and Cursor must add an entry here at the end of every session.**  
> Format: `| Date | Agent | Files Changed | What Was Done & Why |`

| Date | Agent | Files Changed | What Was Done & Why |
|---|---|---|---|
| 2026-07-24 | AntiGravity | `ROADMAP.md`, `PROJECT_STATE.md`, `.cursor/rules/agent-sync.mdc` | **Initial planning session.** Analysed `FYP_Refined_Project_Plan.md`. Generated 8-phase ROADMAP with granular tasks and acceptance criteria. Set up two-agent workflow protocol. Created Cursor sync rules. |
| 2026-07-24 | AntiGravity | `ROADMAP.md` (rewrite), all skeleton files | **Feature audit + skeleton scaffold.** Applied improvements: replaced WHOIS with VirusTotal API (faster, richer), removed live URL re-fetch from backend (security risk + latency), added `suspicious_tld_flag` (zero-cost high-signal feature), added `confidence_pct` throughout all schemas (better UX), added `feature_name_to_human_readable.json` (prevents raw feature names in UI), added baseline comparison task to evaluation (answers "why not just a blocklist?" for viva), added in-memory caching for VT client, removed Options Page (complexity with zero academic value). Created full project skeleton: 30+ files across backend, extension, ml, shared, tests, docker directories. Project is ready to start Phase 1 execution. |
| 2026-07-24 | AntiGravity | `CODEBASE_GUIDE.md`, `.cursor/rules/agent-sync.mdc` | **Documentation & Rulebook creation.** Created `CODEBASE_GUIDE.md` explaining all files, architecture, data flows, and rationale for daily review. Updated `.cursor/rules/agent-sync.mdc` to mandate updating `CODEBASE_GUIDE.md` session log after every task and session. |
