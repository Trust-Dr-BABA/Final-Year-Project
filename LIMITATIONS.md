# Limitations

Full discussion and evidence: `docs/thesis/06-conclusion.md` §6.4. Summarised here for a reader who
won't open the thesis.

**Lexical URL features are brittle in ways a raw count doesn't fix.** The 30-URL live run
(`ml/reports/e2e_validation.md`) found a false positive on `docs.python.org/3/library/asyncio.html`
driven almost entirely by `num_digits = 1` — a single incidental digit (the Python version `3` in
the path) carrying outsized weight because the feature counts digits rather than measuring their
density relative to URL length. Consistent with the 8.5% false-positive rate on the deep-path
holdout (`ml/reports/evaluation_report.md`) and the 87.0% faithfulness result (vs. a 90% target) —
three independent measurements of the same underlying limitation. A length-normalised digit ratio
is the identified, currently-unimplemented fix; deliberately not applied against the 30-URL sample
that surfaced it, since that would be fitting to the measurement instrument rather than the problem.

**Fusion weights are hand-set, not learned** (ADR-014). No labelled corpus pairs a phishing label
with real per-URL browser telemetry, so there is nothing to fit a coefficient against.
`ml/reports/evaluation_report.md`'s sensitivity analysis bounds how much conclusions depend on the
exact values — real sensitivity exists at extreme perturbations (43.9% verdict churn at 2x weights)
but stays modest near the shipped magnitude — without making the weights empirical.

**Permission signal family and phishing interstitial: code-complete, real-browser confirmation
pending.** Both defects that made permission signals non-functional (D7 isolated-world interception,
D8 the arrival-order race) are fixed and covered by automated tests, but watching a real Chrome
instance intercept an actual page's own permission prompt has not been done —
`tests/manual/permission_monitor_test.md` and `tests/manual/interstitial_test.md` specify the
remaining manual sessions.

**Live deployment was not completed within this submission.** The backend and dashboard are built
and evaluated against the local Docker stack (the same image a deployment would run), not against
the hosting platforms named in the system design — deployment requires external accounts that were
deferred to a later stage.

**Assessment is URL-and-behaviour only.** No page content is examined — not rendered text, form
structure, or visual similarity to a legitimate brand. A pixel-perfect clone hosted on an
unremarkable URL with ordinary network behaviour is invisible to this system.

**The service trusts the counts it receives** — signals are collected client-side without
attestation. Acceptable within the intended single-user deployment; would not survive a model
accepting submissions from arbitrary clients.

**The corpus is a snapshot.** Phishing campaigns evolve continuously; this project measures
degradation once, via the temporal split, rather than tracking it with a retraining cadence.

**Reputation data is subject to a free-tier allowance** (4 requests/minute, 500/day). Corroboration
silently becomes unavailable under heavy use — by design this cannot alter a verdict, but it
degrades what the user is shown.

**The URL itself is transmitted and persisted** — it is browsing history. No page content, form
values or cookies leave the browser, but a design that hashed URLs or assessed locally would be more
private than this one.

**Desktop Chromium only** — mobile browsers do not support the extension APIs this design depends
on.

**The evaluation is single-run** — no cross-validation over repeated seeds, no confidence intervals
on reported metrics.
