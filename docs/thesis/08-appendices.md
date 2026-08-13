# Appendices

## Appendix A — Requirements traceability matrix

Each requirement is traced to the use case that realises it, the design section that specifies it,
and the test that verifies it. Rows whose verification is outstanding are marked.

| Req | Use case | Design | Verified by | Status |
|---|---|---|---|---|
| FR-01 | UC-08 | §4.4.1 | TC-S-06 | Verified |
| FR-02 | UC-08 | §4.3.3 | TC-U-19, TC-U-20, TC-S-06 | Verified |
| FR-03 | UC-08 | §4.4 | TC-S-06 | Verified |
| FR-04 | UC-08 | §4.4.2 | TC-S-06 | Verified |
| FR-05 | UC-08 | §4.4.3 | `permission_monitor_test.js` (cross-realm relay) | Resolved (D7, D8); real-browser confirmation pending (TC-S-10/11) |
| FR-06 | UC-08 | §4.4.1 | TC-S-07 | Verified |
| FR-07 | UC-01 | §3.1.2 | TC-SEC-05 | Verified |
| FR-08 | UC-01 | §4.3.1, §4.3.2 | TC-U-01…TC-U-09 | Verified |
| FR-09 | UC-01 | §4.3.4 | TC-S-07 | Verified |
| FR-10 | UC-01 | §4.1 | TC-I-01 | Verified |
| FR-11 | UC-01 | §4.3.5 | TC-I-06 | Verified |
| FR-12 | UC-01 | §4.3.6 | TC-I-01 | Verified |
| FR-13 | UC-09 | §4.5.2 | TC-U-10…TC-U-13, TC-I-04 | Verified |
| FR-14 | UC-01 | §3.2.5 | TC-U-17, TC-I-05, TC-S-08 | Verified |
| FR-15 | UC-01 | §4.3.6 | TC-U-22 | Verified |
| FR-16 | UC-10 | §3.2.3 | TC-I-01 | Verified |
| FR-17 | UC-10 | §4.3.6 | TC-I-01 | Verified |
| FR-18 | UC-10 | §3.2.1 | TC-U-14…TC-U-16 | Verified |
| FR-19 | UC-10 | §3.2.3 | TC-I-06 | Verified |
| FR-20 | UC-01 | §4.4 | TC-S-06 | Verified |
| FR-21 | UC-02 | §3.7.1 | TC-S-09 | Verified |
| FR-22 | UC-04 | §3.7.2 | TC-S-10, TC-S-11 | Code-complete; **pending real-browser run** |
| FR-23 | UC-03 | §3.7.1 | TC-S-08 | Verified |
| FR-24 | UC-01 | §3.4 | TC-I-10 | Verified |
| FR-25 | UC-05 | §3.6.1 | TC-I-09 | Verified |
| FR-26 | UC-06 | §3.7.3 | TC-I-07, TC-I-08 | Verified |
| FR-27 | UC-07 | §3.6.1 | TC-I-01 | Verified |
| FR-28 | UC-13 | §4.5.3 | TC-S-02…TC-S-04 | Verified |
| FR-29 | UC-12 | §5.4.1 | Tables 5.2–5.5 | Verified |
| FR-30 | UC-11 | §4.7.4 | TC-U-23 | Verified |
| FR-31 | UC-11 | §5.9 | Table 5.12 | Verified |
| NFR-01 | — | §4.5.2 | Table 5.19 | Verified |
| NFR-02 | — | §4.4.1 | TC-P-02 | Verified |
| NFR-03 | — | §3.2.2 | TC-I-04 | Verified |
| NFR-04 | — | §3.2.5 | TC-I-05, TC-S-08 | Verified |
| NFR-05 | — | §4.4.1 | TC-S-07 | Verified |
| NFR-06 | — | §3.2.1 | TC-U-16 | Verified |
| NFR-07 | — | §3.7.1 | TC-S-09 | Verified |
| NFR-08 | — | §4.4 | TC-SEC-01 | Verified |
| NFR-09 | — | §4.5.1 | TC-SEC-02 | Verified |
| NFR-10 | — | §4.2 | TC-SEC-03 | Verified |
| NFR-11 | — | §3.1.2 | TC-SEC-04 | Verified |
| NFR-12 | — | §4.8 | TC-M-01 | Verified |
| NFR-13 | — | §4.2 | TC-S-01 | Verified |
| NFR-14 | — | §5.2 | Table 5.1 | Ongoing |

---

## Appendix B — Dataset provenance

Reproduced from `ml/data/raw/DATASET_SOURCES.md`, which is generated fresh on every
`prepare_dataset.py` run and so cannot drift out of sync with the data it describes.

| Source | Class | Rows | Retrieved | Licence | Notes |
|---|---|---|---|---|---|
| PhishTank verified feed (`data.phishtank.com/data/online-valid.csv`) | Phishing | 10,000 | 25 July 2026 | PhishTank open data terms | Filtered to `verified == "yes"` (10,000/10,000 passed — the feed already contains only verified entries); `url`, `submission_time`, `target`, `verified`, `online` retained |
| Live crawl of Tranco-ranked domain homepages (ranks 200–20,000), same-domain internal links with a non-trivial path | Benign | 9,000 raw → 9,685 after path-presence mixing (Appendix B note below) | 13 August 2026 | Tranco list itself CC BY-NC-SA 4.0; crawled pages under their own site terms | 5,288 distinct domains, ≤4 links per domain, 8s per-domain crawl deadline; see §4.7.1 for why a domain-ranking-derived source (Tranco bare domains, then PhiUSIIL) was tried and rejected first |
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

---

## Appendix C — Fusion weights

Reproduced from `ml/reports/fusion_weights.md`. Each row states the signal, its normalising
transform $g_j$, its weight $w_j$, and the reasoning behind the value. Recall from §4.3.5 that a
signal's attribution is exactly $w_j g_j(v_j)$, so this table fully determines the browser-signal
half of every explanation the system produces.

| Signal | Transform $g_j$ | Scale | Weight $w_j$ | Odds multiplier at saturation | Justification |
|---|---|---|---|---|---|
| `tracker_count` | Saturating, $1-e^{-v/\text{scale}}$ | 10 | **1.5** | ×4.48 | Scale matches `heuristics_engine.py`'s own `excessive_trackers` threshold (>10); a single tracker is weak evidence, since most legitimate commercial sites carry a few |
| `has_mixed_content` | Identity (binary) | — | **1.0** | ×2.72 | A real construction-quality signal, but common enough on legitimate sites (stale third-party widgets, old CDN links) that it should not dominate alone |
| `redirect_chain_length` | Saturating | 3 | **1.2** | ×3.32 | Scale matches the `long_redirect_chain` rule threshold (>3); a single redirect is unremarkable (auth flows, short-link services) |
| `cam_mic_on_first_visit` | Identity (binary) | — | **2.0** | ×7.39 | The strongest weight in the table — camera/microphone access requested before any interaction has essentially no legitimate justification |
| `notification_prompt_on_load` | Identity (binary) | — | **0.8** | ×2.23 | The weakest weight — immediate notification prompts are poor UX but extremely widespread on ordinary sites; weighting this heavily would produce false positives across a large fraction of the legitimate web |
| `location_on_load` | Identity (binary) | — | **1.5** | ×4.48 | Between the two extremes — precise location on load is unusual outside a narrow set of legitimate use cases (maps, delivery, weather), which are nonetheless common enough to withhold the maximum weight |

Weights are quoted in log-odds. As a reference point, a weight of 0.69 doubles the odds and a weight
of 2.20 multiplies them by nine ("odds multiplier at saturation" is $e^{w_j}$). §5.12.2 reports a
sensitivity analysis perturbing every weight in this table and measuring how much the resulting
verdicts move — the honest bound on how much these hand-set values matter, given that no corpus
exists to fit them as learned coefficients (§4.3.5).

---

## Appendix D — End-to-end result detail

Executed 13 August 2026 against the local Docker stack via live `POST /analyze` calls. Full method
in `tests/e2e/system_test.md`; raw output in `ml/reports/e2e_validation.md`. All 30 URLs were live at
assessment time (0 errors); OpenPhish entries are volatile and may since have been taken down.

| # | URL | Expected | Observed | Risk % | Principal reason | Outcome |
|---|---|---|---|---|---|---|
| 1 | `logowanie-facebook.vercel.app/` | phishing | suspicious | 62% | Contains a well-known brand name in a suspicious position | Miss |
| 2 | `ledger-login-web-conect-web-sso-in.typedream.app/` | phishing | legitimate | 10% | URL length (57 chars) read as unremarkable | Miss |
| 3 | `sp15ct7-gresor-biz-fantik-lurmon.pages.dev/` | phishing | phishing | 75% | Contains 3 digit characters | Hit |
| 4 | `sp15ct7-grasik-biz-forlen-haskel.pages.dev/` | phishing | phishing | 73% | Contains 3 digit characters | Hit |
| 5 | `merry-maamoul-33ac49.netlify.app/` | phishing | phishing | 88% | Contains 4 digit characters | Hit |
| 6 | `27p-sddo-up2-zcwe25-9i92.pages.dev/` | phishing | phishing | 97% | Contains 8 digit characters | Hit |
| 7 | `backupiau.direct.quickconnect.to/cgi-bin/home.ha` | phishing | legitimate | 7% | URL length (56 chars) read as unremarkable | Miss |
| 8 | `www.myxfinitycom.weebly.com/` | phishing | legitimate | 38% | No HTTPS | Miss |
| 9 | `xfinity-customer-care.weebly.com/` | phishing | suspicious | 59% | Few digit characters (0), read as typical | Miss |
| 10 | `metamask-docs-l8lvh00ol-consensys-ddffed67.vercel.app/embedded-wallets/troubleshooting` | phishing | phishing | 86% | No HTTPS | Hit |
| 11 | `bc4f19.icefactory.cl/` | phishing | phishing | 98% | No HTTPS | Hit |
| 12 | `6c0fd9.icefactory.cl/` | phishing | phishing | 98% | No HTTPS | Hit |
| 13 | `4533ff.icefactory.cl/` | phishing | phishing | 99% | No HTTPS | Hit |
| 14 | `proj002mintinglive.netlify.app/` | phishing | phishing | 81% | No HTTPS | Hit |
| 15 | `72e520.icefactory.cl/` | phishing | phishing | 99% | Contains 5 digit characters | Hit |
| 16 | `github.com/torvalds/linux/blob/master/README` (deep) | legitimate | suspicious | 56% | Randomness score high (4.4643) | Miss |
| 17 | `en.wikipedia.org/wiki/Transport_Layer_Security` (deep) | legitimate | legitimate | 17% | URL length (54 chars) read as unremarkable | Hit |
| 18 | `docs.python.org/3/library/asyncio.html` (deep) | legitimate | **phishing** | **71%** | Contains 1 digit character | **False positive** |
| 19 | `google.com/search?q=...` (deep) | legitimate | legitimate | 10% | URL length (62 chars) read as unremarkable | Hit |
| 20 | `stackoverflow.com/questions/tagged/xgboost` (deep) | legitimate | legitimate | 39% | Few digit characters (0), read as typical | Hit |
| 21 | `news.ycombinator.com/item?id=1` (deep) | legitimate | suspicious | 70% | Contains 1 digit character | Miss |
| 22 | `bbc.com/news/technology` (deep) | legitimate | legitimate | 19% | Few digit characters (0), read as typical | Hit |
| 23 | `developer.mozilla.org/.../Using_Fetch` (deep) | legitimate | legitimate | 13% | URL length (70 chars) read as unremarkable | Hit |
| 24 | `nytimes.com/section/technology` (deep) | legitimate | legitimate | 22% | Few digit characters (0), read as typical | Hit |
| 25 | `pypi.org/project/fastapi/` (deep) | legitimate | legitimate | 7% | Randomness score low (3.7953) | Hit |
| 26 | `amazon.com/gp/help/customer/display.html` (deep) | legitimate | legitimate | 38% | URL length (52 chars) read as unremarkable | Hit |
| 27 | `microsoft.com/.../what-is-phishing` (deep) | legitimate | suspicious | 46% | URL length (79 chars) read as unremarkable | Miss |
| 28 | `reddit.com/r/MachineLearning/` (deep) | legitimate | suspicious | 42% | Few digit characters (0), read as typical | Miss |
| 29 | `wikipedia.org/` | legitimate | legitimate | 20% | Randomness score low (3.7962) | Hit |
| 30 | `python.org/` | legitimate | legitimate | 18% | Randomness score low (3.5555) | Hit |

"Hit" here means the strict-correctness bar (expected == observed band); a "suspicious" result on a
legitimate URL is a miss by that bar but not a false positive in the sense §5.15 treats as the real
one — only row 18 crosses into the phishing band on a legitimate URL, and it is the row discussed at
length in §5.15.

---

## Appendix E — Service interface reference

Generated documentation is served at `/docs` (Swagger UI) and `/redoc` by the running service.

| Method | Path | Query / body | Success | Errors |
|---|---|---|---|---|
| `POST` | `/analyze` | `AnalyzeRequest` (§3.6.2) | `200 AnalyzeResponse` | `422` schema; `503` model unavailable; `500` persistence |
| `GET` | `/history` | `limit ≤ 200`, `offset ≥ 0` | `200 { scans, total, limit, offset }` | `422` |
| `GET` | `/stats` | — | `200 { total_scans, phishing_count, suspicious_count, legitimate_count, avg_confidence_pct }` | — |
| `GET` | `/scan/{id}` | UUID path parameter | `200` full record | `400` malformed; `404` unknown |
| `GET` | `/health` | — | `200` (§3.6.4) | — |

---

## Appendix F — Building and running the system

### Prerequisites

Python 3.11, Node.js 24, Docker, and Google Chrome.

### Service and database

```bash
cp .env.example .env          # then set POSTGRES_*, DATABASE_URL and VIRUSTOTAL_API_KEY
cd docker && docker compose --env-file ../.env up -d --build
alembic -c backend/alembic.ini upgrade head
curl http://localhost:8000/health
```

A correct start reports `db_reachable: true`. It reports `model_loaded: false` until a trained
artefact is present at `ml/models/xgboost_phishing.pkl`, which is the intended behaviour — see
§3.2.5.

### Development environment

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -e "./backend[ml,dev]"
pytest tests/ -q
ruff check backend ml tests
```

### Dashboard

```bash
npm install                    # from the repository root; it is an npm workspace
npm run dev:dashboard
cd dashboard && npx tsc --noEmit
```

Do not run `npm install` inside `dashboard/`. Doing so creates a second, independent `node_modules`
that drifts from the root lockfile; this happened once during development and produced two copies of
the framework.

### Extension

`chrome://extensions` → enable Developer mode → **Load unpacked** → select `extension/`.

### Offline pipeline

```bash
python ml/scripts/prepare_dataset.py      # raw corpora  → data/processed/dataset.csv
python ml/scripts/audit_dataset.py        # leakage audit → ml/reports/
python ml/scripts/generate_features.py    # dataset.csv  → data/processed/features.csv
python ml/scripts/train_model.py          # features.csv → model.pkl + feature_columns.json
```

Run in this order; each step consumes the previous step's output. The audit is a gate, not a report:
if any feature exceeds 0.90 standalone AUC, do not proceed to training.

### Rebuilding the diagrams

```bash
cd docs/thesis/diagrams
java -jar plantuml.jar -tpng -o out *.puml
```

---

## Appendix G — Repository layout

```
fyp/
├── backend/                 FastAPI service
│   ├── main.py              application entry, CORS, /health
│   ├── database.py          async engine, session factory, reachability check
│   ├── models/scan.py       Scan ORM entity
│   ├── routers/             analyze.py, history.py
│   ├── services/            heuristics_engine, explainer_formatter,
│   │                        virustotal_client, risk_fusion
│   ├── feature_extractor/   url_features.py
│   └── alembic/             migrations
├── extension/               Chrome MV3 extension
│   ├── manifest.json
│   ├── background.js        service worker, orchestration, badge
│   ├── content_script.js    permission interception
│   ├── modules/             network_monitor.js, permission_monitor.js
│   ├── services/            api_client.js
│   └── popup/               five-state popup UI
├── dashboard/               Next.js 16 dashboard
├── ml/                      offline pipeline
│   ├── scripts/             prepare_dataset, audit_dataset,
│   │                        generate_features, train_model
│   ├── models/              artefact and column manifest (git-ignored)
│   ├── reports/             audit and evaluation output
│   └── shap_analysis.py     attribution, loaded by the service at request time
├── shared/                  tracker_domains.json, brand_list.txt,
│                            feature_name_to_human_readable.json
├── tests/                   unit, integration, manual, e2e
├── docker/                  docker-compose.yml
├── docs/thesis/             this report and its diagram sources
└── .github/workflows/ci.yml lint, tests, type-check
```

Note that `ml/shap_analysis.py` sits in the machine-learning tree but is imported by the service on
the request path. This is why `pandas` and `joblib` are base dependencies rather than optional
extras — see §4.1.1, where treating them as optional produced a container that ran without a model
and said nothing about it.
