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
| FR-05 | UC-08 | §4.4.3 | — | **Open (D7, D8)** |
| FR-06 | UC-08 | §4.4.1 | TC-S-07 | Verified |
| FR-07 | UC-01 | §3.1.2 | TC-SEC-05 | Verified |
| FR-08 | UC-01 | §4.3.1, §4.3.2 | TC-U-01…TC-U-09 | Verified |
| FR-09 | UC-01 | §4.3.4 | TC-S-07 | Verified |
| FR-10 | UC-01 | §4.1 | TC-I-01 | Verified |
| FR-11 | UC-01 | §4.3.5 | TC-I-06 | **Pending fusion** |
| FR-12 | UC-01 | §4.3.6 | TC-I-01 | Verified |
| FR-13 | UC-09 | §4.5.2 | TC-U-10…TC-U-13, TC-I-04 | Verified |
| FR-14 | UC-01 | §3.2.5 | TC-U-17, TC-I-05, TC-S-08 | Verified |
| FR-15 | UC-01 | §4.3.6 | TC-U-22 | **Pending fusion** |
| FR-16 | UC-10 | §3.2.3 | TC-I-01 | Verified |
| FR-17 | UC-10 | §4.3.6 | TC-I-01 | Verified |
| FR-18 | UC-10 | §3.2.1 | TC-U-14…TC-U-16 | Verified |
| FR-19 | UC-10 | §3.2.3 | TC-I-06 | **Pending fusion** |
| FR-20 | UC-01 | §4.4 | TC-S-06 | Verified |
| FR-21 | UC-02 | §3.7.1 | TC-S-09 | Verified |
| FR-22 | UC-04 | §3.7.2 | TC-S-10, TC-S-11 | **Pending model** |
| FR-23 | UC-03 | §3.7.1 | TC-S-08 | Verified |
| FR-24 | UC-01 | §3.4 | TC-I-10 | Verified |
| FR-25 | UC-05 | §3.6.1 | TC-I-09 | Verified |
| FR-26 | UC-06 | §3.7.3 | TC-I-07, TC-I-08 | Verified |
| FR-27 | UC-07 | §3.6.1 | TC-I-01 | Verified |
| FR-28 | UC-13 | §4.5.3 | TC-S-02…TC-S-04 | Verified |
| FR-29 | UC-12 | §5.4.1 | ⟨M-01⟩…⟨M-04⟩ | **Pending run** |
| FR-30 | UC-11 | §4.7.4 | TC-U-23 | Verified |
| FR-31 | UC-11 | §5.9 | ⟨M-07⟩, ⟨M-08⟩ | **Pending run** |
| NFR-01 | — | §4.5.2 | ⟨M-16⟩ | **Pending run** |
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

*[Complete from `ml/data/raw/DATASET_SOURCES.md` after the corpus rebuild. Every row is required for
the provenance citation in Chapter 5.]*

| Source | Class | Rows | Retrieved | Licence | Notes |
|---|---|---|---|---|---|
| PhishTank verified feed | Phishing | ⟨M-05⟩ | *[date]* | *[terms]* | Filtered to `verified == yes`; `submission_time` retained for the temporal split |
| *[path-bearing benign corpus]* | Benign | ⟨M-05⟩ | *[date]* | *[terms]* | Selected for realistic URL structure; see §4.7.1 |
| Tranco top-1000, deep paths | Holdout | ⟨M-11⟩ | *[date]* | Open | Never used for training; false-positive evaluation only |

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

*[Complete from `ml/reports/fusion_weights.md` once the fusion layer is implemented.]*

Each row states the signal, its normalising transform $g_j$, its weight $w_j$, and the reasoning
behind the value. Recall from §4.3.5 that a signal's attribution is exactly $w_j g_j(v_j)$, so this
table fully determines the browser-signal half of every explanation the system produces.

| Signal | Transform $g_j$ | Weight $w_j$ | Justification |
|---|---|---|---|
| `tracker_count` | Saturating in the count | *[value]* | Diminishing returns: the fortieth tracker is weaker evidence than the fifth |
| `has_mixed_content` | Identity (binary) | *[value]* | Insecure resources in a secure document indicate poor or hostile construction |
| `redirect_chain_length` | Saturating above 1 | *[value]* | Long top-level chains conceal the final destination |
| `cam_mic_on_first_visit` | Identity (binary) | *[value]* | Device capture requested before interaction is rarely legitimate |
| `notification_prompt_on_load` | Identity (binary) | *[value]* | Common on low-quality and hostile pages alike; weighted modestly |
| `location_on_load` | Identity (binary) | *[value]* | Precise location requested before interaction |

Weights are quoted in log-odds. As a reference point, a weight of 0.69 doubles the odds and a weight
of 2.20 multiplies them by nine.

---

## Appendix D — End-to-end result detail

*[Complete after executing the 30-URL protocol of §5.15.]*

| # | URL | Expected | Observed | Risk % | Principal reason | Outcome |
|---|---|---|---|---|---|---|
| 1–15 | *[live phishing URLs]* | phishing | ⟨M-17⟩ | ⟨M-17⟩ | ⟨M-17⟩ | ⟨M-17⟩ |
| 16–30 | *[legitimate URLs, ≥ 10 deep-path]* | legitimate | ⟨M-17⟩ | ⟨M-17⟩ | ⟨M-17⟩ | ⟨M-17⟩ |

Record the URL exactly as assessed. Phishing URLs expire quickly, so note the retrieval timestamp
against each; a URL that has been taken down between selection and assessment must be replaced rather
than counted as a miss.

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
