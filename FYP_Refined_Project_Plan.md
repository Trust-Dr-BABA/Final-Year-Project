# AI-Powered Explainable Security & Privacy Analyst
### Refined Project Plan & Technical Documentation
**Revision of:** "AI-Powered Explainable Autonomous Security Analyst" (original FYP proposal, rated Weak)
**Scope added:** Chrome extension for real-time phishing/scam detection + browser-level network/privacy monitoring

---

## 1. Multi-Lens Review (why this scope, and where the lines are)

Before locking the plan, running it through three lenses to catch problems early rather than mid-build:

**Security engineering lens**
A browser extension operates inside a sandbox. It can see and act on:
- Requests made by tabs it has permission for (`webRequest`, `declarativeNetRequest`)
- Page-level permission prompts (camera, mic, geolocation, notifications)
- Cookies, storage access, and script origins on a page

It **cannot** see:
- OS-level or other-application network traffic (no packet capture)
- Encrypted payload contents of HTTPS requests (only metadata: destination, headers, timing, size)

→ **Framing decision:** call this module "Browser-Level Network & Privacy Monitoring," not "network log analysis" or "intrusion detection." This is more defensible in a viva and, frankly, more impressive — it shows you understand the actual threat surface instead of overclaiming.

**ML engineering lens**
Adding network/privacy signals doesn't require a second model. Feed them as *additional features* into the same tree-ensemble classifier (XGBoost) that scores phishing risk — a page with a spoofed-brand login form AND excessive third-party trackers AND a camera permission request is a stronger phishing/scam signal than any one alone. One model, richer feature set. Avoid the temptation to build a separate "network anomaly model" — that doubles your ML surface area for a 3-month timeline with limited payoff.

**Product/resume lens**
With <3 months, treat this as MVP + stretch goals, not one flat feature list. Section 4 below marks each feature as MVP (must ship) or Stretch (cut first if behind schedule).

---

## 2. Expanded Feature Set

| Category | What it checks | Signal type |
|---|---|---|
| URL/domain analysis (existing) | Lexical features, domain age (WHOIS), SSL validity, redirect chains, brand-impersonation patterns | ML features |
| Network request monitoring | Excessive third-party/tracker domains, mixed content (HTTP resources on HTTPS pages), abnormal redirect chains, large outbound POST requests to unfamiliar domains (possible exfiltration pattern) | ML features + heuristic rules |
| Permissions monitoring | Page requests for camera/mic/location/notifications, especially on first visit or from low-reputation domains | Heuristic rules (rule-based flag, not ML — keeps it fast and explainable) |
| Privacy exposure | Known tracker/fingerprinting script domains (matched against a public blocklist like EasyPrivacy) | Heuristic/lookup, feeds into ML as a feature count |

**Why heuristics for permissions/privacy, ML for phishing scoring:** permission abuse is a near-binary, well-defined signal (a page asking for your camera before you've interacted with it is inherently suspicious) — a rule catches it faster and more explainably than training a model to learn it. Reserve ML for the genuinely fuzzy problem (is this URL/page a scam), and feed the heuristic flags in as extra input features. This also keeps your SHAP explanations cleaner: "flagged because of 3 tracker domains + camera permission request + 2-day-old domain" reads better than a black-box score.

---

## 3. Revised Architecture

```
┌─────────────────────────────┐
│   Chrome Extension (MV3)     │
│  - content script: page scan │
│  - webRequest listener       │
│  - permissions listener      │
└──────────────┬────────────────┘
               │ POST /analyze (URL, request metadata, permission events)
               ▼
┌─────────────────────────────┐
│   FastAPI Backend             │
│  - feature extraction layer   │
│  - heuristic rules engine     │
│  - XGBoost classifier         │
│  - SHAP explainer              │
└──────────────┬────────────────┘
               │ writes scan + verdict
               ▼
┌─────────────────────────────┐
│   PostgreSQL                 │
└──────────────┬────────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Next.js Dashboard          │
│  - scan history                │
│  - risk breakdown               │
│  - explanation view             │
└─────────────────────────────┘
```

---

## 4. MVP vs. Stretch (critical given <3-month timeline)

**MVP — must ship for the defense**
- URL/domain phishing classifier (XGBoost + SHAP)
- Extension popup showing risk score + top 3 reasons
- Basic network monitoring: tracker count, mixed content, redirect chain length
- Permission-request flagging (camera/mic/location/notifications) — rule-based
- Dashboard with scan history + risk distribution
- Deployed backend + live demo

**Stretch — add only if MVP is done with time to spare**
- Exfiltration-pattern detection (large POST to unfamiliar domain)
- Published (even unlisted) Chrome Web Store listing
- Rate-limiting/caching layer
- User-reporting feature (flag a false positive)

If week 8 arrives and you're behind, cut from the bottom of the stretch list first — never cut the SHAP explainability piece, since that's your key differentiator from a plain blocklist extension.

---

## 5. Revised 12-Week Timeline

| Weeks | Focus | Deliverable |
|---|---|---|
| 1-2 | Extension skeleton (MV3), dataset collection (PhishTank + Tranco), scope finalization | Working extension shell, cleaned dataset |
| 3-4 | Feature engineering (URL/domain) + XGBoost training + SHAP wiring | Trained model with evaluated precision/recall |
| 5 | Network monitoring module (`webRequest` listener: trackers, mixed content, redirects) | Feature extractor for network signals |
| 6 | Permissions monitoring module (rule-based flagging) | Feature extractor for permission events |
| 7-8 | FastAPI backend: merge all feature streams → single model call → SHAP explanation response; deploy | Live `/analyze` endpoint |
| 9 | Extension ↔ backend integration, popup UI with plain-English explanation | End-to-end working extension |
| 10 | Dashboard (Next.js): history, risk chart, explanation drill-down | Live dashboard |
| 11 | Evaluation (confusion matrix, precision/recall/F1), stretch goals if time allows | Eval report |
| 12 | Documentation, demo recording, defense prep | Final write-up + live links |

---

## 6. Risks & Honest Limitations (state these in the final proposal — examiners respect this)

- Browser-level network monitoring is **not** equivalent to enterprise network/endpoint security — scope is explicitly the browser sandbox.
- Model trained on public datasets; real-world generalization to novel scam patterns is limited and should be stated as a known limitation, not hidden.
- No real-time enterprise-scale deployment — this remains a research/portfolio-scale system, same honest framing as the original proposal's scope section.

---

## 7. What Changed vs. Original Proposal

| Original | Refined |
|---|---|
| Static dataset only, no live component | Live Chrome extension + deployed API |
| SHAP as an afterthought module | SHAP explanation is the core UX (popup + dashboard) |
| Vague "monitoring dashboard" | Concrete Next.js dashboard with scan history |
| Compared directly to CrowdStrike/Darktrace | Reframed as lightweight, explainable browser-level alternative to blocklist extensions |
| Single-signal detection (URL only) | Multi-signal: URL + network behavior + permissions, fused into one explainable model |
