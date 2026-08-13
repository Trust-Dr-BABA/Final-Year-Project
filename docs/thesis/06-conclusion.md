# Chapter 6 — Conclusion

## 6.1 Summary

This project set out to build a browser-resident phishing and privacy analyser that judges a page on
more than its URL and that says, in language a non-specialist can read, exactly why it reached the
judgement it did.

The delivered system comprises four components. A Chrome extension observes each page as it loads,
counting distinct third-party tracker domains, detecting insecure resources inside secure documents,
measuring top-level redirect depth, and recording permission requests made before the user has
interacted with anything. A FastAPI service extracts lexical features from the URL, scores them with
a gradient-boosted classifier, attributes that score across the features with SHAP, and adds the
browser-observed signals as documented weights in log-odds space. Because SHAP values and fusion
weights are the same kind of object — additive contributions to the log-odds — both families of
evidence rank in one list, render through one formatter, store in one representation, and draw on
one chart. A PostgreSQL database keeps the full attribution for every assessment, and a Next.js
dashboard presents history, aggregates and per-assessment detail.

The technical core of the work is that last property. Multi-signal detection and explainability are
each well-studied in isolation; combining them usually forces a choice, because a hand-set signal
weight and a learned attribution are not normally comparable quantities and cannot be shown side by
side without inventing a common scale. Recognising that log-odds already *is* the common scale
removed that obstacle, and it did so without a single schema change downstream of the fusion
function.

## 6.2 Achievement against objectives

**Table 6.1 — Objectives**

| # | Objective | Outcome | Evidence |
|---|---|---|---|
| **O1** | Specify requirements and model them as use cases with contracts | **Met.** 31 functional and 14 non-functional requirements, 13 use cases, 7 operation contracts, traced to test cases. | Chapter 2 |
| **O2** | Design an architecture preserving attribution end to end | **Met.** Five layers across four components, with the attribution invariant stated and structurally enforced at the presentation boundary. | Chapter 3 |
| **O3** | Implement browser instrumentation without re-fetching the page | **Met and verified in a real browser.** 11 distinct tracker domains and a redirect depth of 5 measured on a live commercial site; no server-side fetch of any assessed URL. | §5.7 TC-S-06, TC-SEC-05 |
| **O4** | Train a URL classifier on an audited corpus | **Met.** Audit built and run before and after the rebuild (`url_entropy` 0.9001 → 0.7339 AUC alone); trained model measured under three split protocols. | §5.4, §5.9 |
| **O5** | Fuse browser signals with the model on one additive scale | **Met.** `risk_fusion.py` implemented per ADR-014; TC-I-06 confirms adverse signals strictly raise the fused score by exactly the documented weight; sensitivity analysis quantifies dependence on the hand-set values. | §4.3.5, §5.6, §5.12.2 |
| **O6** | Render every contribution in plain English | **Met.** Single shared template map; 21 templates; the popup renders `human_readable` and never inspects the identifier, so the guarantee is structural. | §3.2.1, §5.5 TC-U-16 |
| **O7** | Evaluate under protocols that reflect deployment | **Met.** Temporal and unseen-domain protocols, four measured baselines (a fifth is explicitly not fabricated — see §5.10), calibration, faithfulness ablation, sensitivity analysis and a 30-URL live run are all executed and reported, including where they fell short of their target. | Chapter 5 |

All seven objectives are met. Three of the results (faithfulness, the deep-path false-positive
rate, and the 30-URL live run) fall short of the acceptance criterion originally set for them; they
are counted as met at the level of the objective — evaluate rigorously and report honestly — while
the underlying shortfalls are carried forward as limitations in §6.4 rather than hidden inside a
green checkmark. Section 6.6 discusses this distinction.

## 6.3 Assessment of the claims

### C1 — Detection generalises beyond a blocklist

**Established, on the metric that actually answers the question.** Section 5.10's decisive test is
recall on URLs absent from the blocklist, where the blocklist scores exactly 0.0% by construction.
The trained classifier recovers 62.1% recall on that same temporal-split test set (Table 5.14) —
generalisation a blocklist structurally cannot provide, whatever its precision on URLs it has
already seen.

What underwrites this claim is not the headline number alone but the audit that preceded it. The
original corpus produced a stronger-looking score (F1 ≈ 0.97) by separating classes on path
presence rather than phishing, and any claim of generalisation resting on it would have been false.
The rebuilt corpus's lower, harder-won F1 (0.726 under the temporal split, Table 5.12) is the honest
number, and it is the one C1 is assessed against.

### C2 — Detection is genuinely multi-signal

**Established for the architecture and the live pipeline; not established as an offline accuracy
number, and that gap is stated rather than papered over.** Browser signals are measured, transmitted,
reach the reasoning layer, and — since the fusion layer landed — measurably move the score: TC-I-06
confirms the fused probability strictly increases under adverse signals, by exactly the weight
documented in Appendix C, and the sensitivity analysis (§5.12.2) shows that movement is not an
artefact of one arbitrary weight choice. The 30-URL live run in §5.15 exercises the complete fused
pipeline against real requests, not a mock.

What remains genuinely unestablished is an offline accuracy figure for the fused system — there is
no "B5" row in Table 5.14, because no corpus, including this project's own, pairs a phishing label
with real per-URL browser telemetry. Fabricating that pairing to produce a B5 number would be the
same category of error C1's own history warns against. C2 is therefore established as "the signals
are real, reach the score, and move it correctly" rather than as "the fused system is measurably
more accurate than the URL-only model" — a narrower but honest claim.

### C3 — Explanations are faithful rather than decorative

**Partially established, with the shortfall reported rather than concealed.** The ablation procedure
in §5.12.1 measured 87.0% directional agreement against a 90% target — not met. The gap is small in
absolute terms and is explained, not merely noted: XGBoost at `max_depth=6` permits real
three-way feature interactions that a simultaneous three-feature ablation does not fully respect,
and several strong features (`url_entropy`, `num_digits`) are mutually correlated, so removing the
top three together displaces more combined signal than the sum of their individual attributions
predicts.

The structural argument still holds independently of this number: `TreeExplainer` is exact for tree
ensembles rather than approximate, so the model's own attributions are not estimates of
contributions but the contributions themselves, and the fusion attributions are exact by
construction. What the measurement adds is the honest qualifier — exact local attribution does not
guarantee that a simultaneous multi-feature intervention behaves as the sum of those attributions
predicts, and 87.0% is how close it comes on this classifier, not 100%.

## 6.4 Limitations

Stated without softening. Several of these are structural rather than incidental, and an honest
account is more useful than a defensive one.

**The permission signal family's real-browser behaviour is unconfirmed.** D7 and D8 are fixed in
code — interception now runs in the main world via a manifest `"world": "MAIN"` entry, relayed to
the isolated world by a `CustomEvent` bridge, and `background.js` re-runs the assessment when a
genuinely new permission flag arrives late — and a cross-realm automated test exercises the relay
mechanism. What has not been done is watching a real Chrome instance intercept an actual page's own
`Notification.requestPermission` call end to end; `tests/manual/permission_monitor_test.md` records
the procedure, and, like the interstitial's own pending confirmation (TC-S-10/11, §5.7), it is
recorded as outstanding rather than assumed to follow from the automated coverage.

**Fusion weights are hand-set, not learned.** ADR-014 explains why — no labelled corpus carries
per-URL tracker counts — but the consequence stands: those weights encode the author's judgement
about how much a tracker count should matter. The sensitivity analysis bounds how much the
conclusions depend on them; it does not make them empirical.

**The service trusts the counts it receives.** Signals are collected client-side and submitted
without attestation. Within the intended deployment this is acceptable, since a user tampering with
their own extension only misleads themselves. It would not survive a model in which the service
accepted submissions from arbitrary clients, and it means the counts are not evidence in any
adversarial sense.

**Assessment is URL-and-behaviour only.** No page content is examined: not the rendered text, not the
form structure, not the visual similarity to a legitimate brand. A pixel-perfect clone of a bank's
login page hosted on an unremarkable URL with ordinary network behaviour is invisible to this system.
That is a substantial category of attack, and content analysis is the single largest gap in coverage.

**Lexical URL features are brittle in ways a raw count cannot fix.** The 30-URL live run (§5.15)
found a false positive on `docs.python.org/3/library/asyncio.html` driven almost entirely by
`num_digits = 1` — a single incidental digit (the Python version `3` in the path) contributing +0.87
log-odds because the feature counts digits rather than measuring their density. The same run's
misses on live phishing hosted on trusted free platforms (`vercel.app`, `typedream.app`) show the
same brittleness from the other direction, via `url_length`'s negative learned weight. This is
consistent with the 8.5% false-positive rate on the deep-path holdout (§5.11.1) and the 87.0%
faithfulness result (§5.12.1) — three independent measurements pointing at the same underlying
limitation rather than three unrelated problems. A length-normalised digit *ratio* in place of a raw
count is the most direct, currently-unimplemented fix, deliberately not applied mid-evaluation
against an n = 30 sample for the reasons given in §5.15.

**Brand impersonation matching now catches typosquats, at a small measured cost.** The original
literal substring match caught `paypal.secure-login.tk` but missed `paypa1`, `pаypal` with a
Cyrillic character, and every edit-distance variant. Homoglyph normalisation plus bounded
Levenshtein matching against hostname tokens closes that gap (`ml/reports/training_log.md`, Run 2)
— at the cost of one new false positive across the 1,488-URL holdout (`mail.google.com`, whose
`"mail"` token sits at edit-distance 1 from the brand `"gmail"`), accepted rather than special-cased
since excluding it would be the same kind of fitting-to-the-holdout error rejected throughout this
project. The technique is no longer purely literal, but it is not free of false positives either.

**The corpus is a snapshot.** Phishing campaigns evolve continuously. A model trained on one period's
feed degrades against later campaigns, and this project measures that degradation once, through the
temporal split, rather than tracking it. No retraining cadence is established.

**Reputation data is subject to a free-tier allowance.** Four requests per minute and five hundred per
day. The one-hour cache makes ordinary browsing viable, but heavy use exhausts the allowance, at
which point corroboration silently becomes unavailable. By design this cannot alter a verdict, but
it does degrade what the user is shown.

**The URL itself is transmitted.** The privacy analysis in TC-SEC-04 confirms that no page content
leaves the browser, but a URL *is* browsing history, and the service records it durably. A design
that hashed URLs, or performed assessment locally, would be more private. This one does not.

**Desktop Chromium only.** Mobile browsers do not support the extension APIs this design depends on,
which excludes the platform where a large share of phishing is actually opened.

**The evaluation is single-run.** No cross-validation over repeated seeds and no confidence intervals
on the reported metrics. Point estimates from one split are weaker evidence than an interval, and the
distinction should be kept in mind when reading Chapter 5.

**Live deployment was not completed within this submission.** The backend and dashboard were built
and evaluated against the local Docker stack — the same image the deployment target would run — but
were not deployed to the hosting platforms named in §4.2. The 30-URL end-to-end run in §5.15
therefore exercises the correct code path and a real trained model, but not the actual network
topology, TLS termination, or cross-origin configuration a live deployment would introduce, any of
which could surface its own defects in the way §4.7's earlier ones were surfaced only once a real
environment was exercised.

## 6.5 Future work

**Normalise `num_digits` to a length-relative ratio.** The single most direct fix identified by this
work's own evaluation (§5.15, §6.4): a digit *ratio* rather than a raw count would stop one
incidental character from dominating a 46-character URL's score, and is a well-precedented technique
in the lexical-phishing-detection literature. Deliberately not applied against the 30-URL sample
that surfaced it, for the reasons given in §5.15 — the correct next step is to implement it and
re-run the full evaluation suite, not to hand-tune the existing model against that one sample.

**Complete live deployment and re-run the end-to-end validation against it.** The backend and
dashboard are built and evaluated locally; deploying to the platforms named in §4.2 and repeating
§5.15's 30-URL run against the live stack would close the one gap §6.4 identifies between "verified
against the shipped image" and "verified in the actual target environment."

**Confirm the permission signal family and the interstitial in a real browser.** Both are code-complete
with automated coverage of their non-DOM logic; `tests/manual/permission_monitor_test.md` and
`tests/manual/interstitial_test.md` specify the remaining manual sessions.

**Learn the fusion weights.** The honest route is a small labelled corpus collected through the
extension itself, with user consent, recording browser signals alongside a ground-truth label. With
even a few thousand rows, the weights become a fitted logistic layer over the URL model's log-odds —
which keeps the additive structure, and therefore the explainability, entirely intact. This remains
the most direct path from a documented judgement (§4.3.5, Appendix C) to an empirical one; the
sensitivity analysis in §5.12.2 bounds the risk of the current judgement without removing it.

**Add content signals.** Form-field analysis, a visual similarity check against known brand login
pages, and DOM structural features would address the largest coverage gap in Section 6.4: a
pixel-perfect clone hosted on an unremarkable URL with ordinary network behaviour is invisible to
this system. Each brings a false-positive cost that must be measured before adoption, following the
same discipline §5.11 and the L1 brand-matching change (§6.4) already applied.

**Establish a retraining cadence.** Scheduled retraining on a rolling window, with the leakage audit
as an automatic gate and a held-out comparison against the incumbent model before any promotion —
the corpus is a snapshot (§6.4) and this project measures degradation once rather than tracking it.

**Report intervals, not points.** Repeated splits with confidence intervals on every headline metric,
rather than the single-run point estimates in Chapter 5.

**Investigate client attestation.** If the service were ever opened to third-party clients, signal
integrity would need addressing — a signed submission, or server-side corroboration of a sample of
claims.

## 6.6 Reflection

Three things about how this project actually went are worth recording, because they were not
anticipated at the start and they are the parts I would carry into the next piece of work.

**The most damaging defects produced no symptom.** D2 discarded every browser signal at one line of
dictionary comprehension, and the system continued returning well-formed responses with sensible
verdicts and correct-looking explanations. D5 let four separate failure paths return a confident
verdict with the model absent. In both cases the test suite passed, the interface looked right, and a
demonstration would have appeared entirely successful. What found them was reading code against the
claims it was supposed to support, not running it.

This changed how I think about failure handling. A `try`/`except` that falls back to a plausible
default is not defensive programming; it is a decision to prefer a wrong answer over an obvious one.
The design rule that emerged — fail loudly, and make the fallback an explicit, configured choice
rather than an automatic one — is the single most transferable thing I take from the project.

**Finding my own dataset flaw was the most valuable hour spent.** The first model scored around 0.97
and I nearly accepted it. The reason I did not is that the number was better than the published
literature on comparable feature sets, and a result that good on a task that hard is more likely to
be an artefact than a breakthrough. Writing the audit script to *quantify* the flaw rather than
simply removing it turned a private embarrassment into the strongest methodological evidence in the
report. The before-and-after comparison demonstrates something no clean result can: that the
evaluation is capable of detecting its own failure.

**Sequencing by consequence rather than by enthusiasm.** The natural order of work on a project like
this is to build the visible parts first, because they are satisfying. The order that turned out to
matter was the opposite: make the system report its own state honestly, then fix the data, then
measure, then build the surface. Every hour spent on the dashboard before the corpus was sound would
have been an hour spent making a misleading result look more convincing.

**Knowing when to stop measuring and report the number.** The 30-URL live run (§5.15) surfaced a
false positive traceable to a single incidental digit, and the instinctive response was to fix it
immediately — change the feature, retrain, re-run. The reason that instinct was wrong here is the
same reason D1 was a defect in the first place: a change justified by one observed failure on the
exact sample used to measure it is not a fix, it is overfitting to the report. The discipline that
D1 forced onto the corpus had to be applied a second time, under time pressure, to a single test
result — and holding to it meant submitting a genuine, unresolved shortfall (§6.4) rather than a
number quietly nudged until it passed.

The system deployed to a local stack rather than to the live hosting platforms named in §4.2, a
scope decision made deliberately rather than by running out of time — the evaluation that matters
academically (does the detector generalise, is it calibrated, are its explanations faithful) does
not depend on where the container happens to run, and spending the remaining time on a genuine model
limitation was judged more valuable than spending it on infrastructure that would not have changed
a single number in Chapter 5.

The project is complete against its own stated scope, and it is not finished in the sense that no
real system ever is. Every claim in §1.5 is now measured rather than asserted, including the two
that did not clear their target — faithfulness at 87.0% against a 90% goal, and 20 of 30 correct on
the live end-to-end run against a 26-of-30 bar. What it has, consistently with the discipline D1 and
D2 established early on, is an accurate account of which parts are established, which are
established with a caveat, and which are not — and I would still rather submit a system whose gaps
are documented than one whose gaps are merely undiscovered.
