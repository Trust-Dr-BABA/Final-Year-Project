# Sprint 3.4 — End-to-End Validation (30 URLs)

Run: 2026-08-13 15:53 UTC. Local Docker stack, live `POST /analyze` calls (real VirusTotal lookups included). See `tests/e2e/system_test.md` for method and the deployment-deferral rationale.

| # | Expected | Actual | Risk % | Deep path | URL |
|---|---|---|---|---|---|
| 1 | phishing | suspicious | 62% | no | `https://logowanie-facebook.vercel.app/` |
| 2 | phishing | legitimate | 10% | no | `https://ledger-login-web-conect-web-sso-in.typedream.app/` |
| 3 | phishing | phishing | 75% | no | `https://sp15ct7-gresor-biz-fantik-lurmon.pages.dev/` |
| 4 | phishing | phishing | 73% | no | `https://sp15ct7-grasik-biz-forlen-haskel.pages.dev/` |
| 5 | phishing | phishing | 88% | no | `https://merry-maamoul-33ac49.netlify.app/` |
| 6 | phishing | phishing | 97% | no | `https://27p-sddo-up2-zcwe25-9i92.pages.dev/` |
| 7 | phishing | legitimate | 7% | no | `https://backupiau.direct.quickconnect.to/cgi-bin/home.ha` |
| 8 | phishing | legitimate | 38% | no | `http://www.myxfinitycom.weebly.com/` |
| 9 | phishing | suspicious | 59% | no | `https://xfinity-customer-care.weebly.com/` |
| 10 | phishing | phishing | 86% | no | `http://metamask-docs-l8lvh00ol-consensys-ddffed67.vercel.app/embedded-wallets/troubleshooting` |
| 11 | phishing | phishing | 98% | no | `http://bc4f19.icefactory.cl/` |
| 12 | phishing | phishing | 98% | no | `http://6c0fd9.icefactory.cl/` |
| 13 | phishing | phishing | 99% | no | `http://4533ff.icefactory.cl/` |
| 14 | phishing | phishing | 81% | no | `http://proj002mintinglive.netlify.app/` |
| 15 | phishing | phishing | 99% | no | `https://72e520.icefactory.cl/` |
| 16 | legitimate | suspicious | 56% | yes | `https://github.com/torvalds/linux/blob/master/README` |
| 17 | legitimate | legitimate | 17% | yes | `https://en.wikipedia.org/wiki/Transport_Layer_Security` |
| 18 | legitimate | phishing | 71% | yes | `https://docs.python.org/3/library/asyncio.html` |
| 19 | legitimate | legitimate | 10% | yes | `https://www.google.com/search?q=explainable+phishing+detection` |
| 20 | legitimate | legitimate | 39% | yes | `https://stackoverflow.com/questions/tagged/xgboost` |
| 21 | legitimate | suspicious | 70% | yes | `https://news.ycombinator.com/item?id=1` |
| 22 | legitimate | legitimate | 19% | yes | `https://www.bbc.com/news/technology` |
| 23 | legitimate | legitimate | 13% | yes | `https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch` |
| 24 | legitimate | legitimate | 22% | yes | `https://www.nytimes.com/section/technology` |
| 25 | legitimate | legitimate | 7% | yes | `https://pypi.org/project/fastapi/` |
| 26 | legitimate | legitimate | 38% | yes | `https://www.amazon.com/gp/help/customer/display.html` |
| 27 | legitimate | suspicious | 46% | yes | `https://www.microsoft.com/en-us/security/business/security-101/what-is-phishing` |
| 28 | legitimate | suspicious | 42% | yes | `https://www.reddit.com/r/MachineLearning/` |
| 29 | legitimate | legitimate | 20% | no | `https://www.wikipedia.org/` |
| 30 | legitimate | legitimate | 18% | no | `https://www.python.org/` |

## Confusion matrix (strict: expected == actual)

- Correct: 20/30
- Errors (URL unreachable / dead at test time): 0
- False positives among deep-path legitimate URLs: 1

| Expected \ Actual | phishing | suspicious | legitimate | error |
|---|---|---|---|---|
| phishing | 10 | 2 | 3 | 0 |
| legitimate | 1 | 4 | 10 | 0 |

**Acceptance (ROADMAP.md 3.4):** >= 26/30 correct, zero false positives among deep-path legitimate URLs. Result: 20/30 correct, 1 deep-path false positives -> FAIL.
