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
| **O4** | Train a URL classifier on an audited corpus | **Partially met.** The audit instrument is built and the corpus rebuild is specified; the training run against the rebuilt corpus is outstanding. | §5.4, §5.9 |
| **O5** | Fuse browser signals with the model on one additive scale | **Designed and specified; implementation outstanding.** The mathematics, the algorithm and the attribution shape are fixed; the fusion module is the remaining work. | §3.2.3, §4.3.5 |
| **O6** | Render every contribution in plain English | **Met.** Single shared template map; 21 templates; the popup renders `human_readable` and never inspects the identifier, so the guarantee is structural. | §3.2.1, §5.5 TC-U-16 |
| **O7** | Evaluate under protocols that reflect deployment | **Instrumented; measurements outstanding.** Temporal and unseen-domain protocols, five baselines, calibration, faithfulness ablation and sensitivity analysis are all specified with acceptance criteria. | Chapter 5, Table 5.1 |

Four objectives are fully met, one partially, and two are specified with their instruments built but
their measurements not yet taken. Section 6.6 discusses why the work arrived at this distribution.

## 6.3 Assessment of the claims

### C1 — Detection generalises beyond a blocklist

**Not yet established.** The comparison that would establish it is specified in Section 5.10, with
the decisive test being recall on URLs absent from the blocklist, where the blocklist scores zero by
construction. The instrument exists; the measurement does not.

What *is* established is that the earlier apparent evidence for C1 was worthless. The original
corpus produced a strong score by separating classes on path presence, and any claim of
generalisation resting on it would have been false. Removing a false basis for a claim is progress,
though it is progress that leaves the claim unproven.

### C2 — Detection is genuinely multi-signal

**Partially established.** Browser signals are measured correctly, transmitted, and reach the
reasoning layer — TC-S-07 confirms this empirically, since rule flags derived from those signals
appeared in a live response. They influence the displayed rule flags today. They do not yet influence
the score, because the fusion module is the outstanding item in O5.

The honest position is that C2 is currently true of the explanation and not yet true of the
computation. That distinction matters, and it is precisely the distinction the defect in Section
4.7.2 obscured for weeks: signals that are *shown* look identical, from outside, to signals that are
*used*.

### C3 — Explanations are faithful rather than decorative

**Not yet established.** The ablation procedure is specified in Section 5.12 with a ≥ 90%
directional-agreement criterion, and it requires a trained model to run against.

One structural property does support faithfulness independently of the measurement. `TreeExplainer`
is exact for tree ensembles rather than approximate, so the attributions are not estimates of
contributions but the contributions themselves, and they sum to the prediction. The fusion
attributions are exact by construction, since each is computed from the same expression that applies
it to the score. Faithfulness is therefore expected on theoretical grounds — but expectation is not
measurement, and the project's own integrity rule (NFR-14) forbids reporting it as though it were.

## 6.4 Limitations

Stated without softening. Several of these are structural rather than incidental, and an honest
account is more useful than a defensive one.

**The permission signal family does not work.** Two independent defects, D7 and D8, each sufficient
alone. Interception runs in the isolated world and therefore cannot observe the page's own calls, and
the signals are posted after the assessment has already been requested. One of the three advertised
signal families is currently inert, and the system's multi-signal claim rests on two families rather
than three.

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

**Brand impersonation matching is literal.** Substring matching against a fifty-brand list catches
`paypal.secure-login.tk` and misses `paypa1`, `pаypal` with a Cyrillic character, and every
edit-distance variant. Homoglyph and typosquat detection are well-understood techniques that are
simply not implemented here.

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

## 6.5 Future work

**Complete the outstanding measurements.** Everything in Table 5.1. This is not future work in the
usual sense of "an interesting extension" — it is the remaining path to establishing C1 and C3, and
it is the highest-value work available.

**Repair the permission family.** Move interception to the main world through a manifest entry
declaring `"world": "MAIN"`, and resolve the ordering race by awaiting the signals with a bounded
timeout before assessing, or by re-assessing when they arrive. Doing so restores the third signal
family and, with it, the full multi-signal claim.

**Learn the fusion weights.** The honest route is a small labelled corpus collected through the
extension itself, with user consent, recording browser signals alongside a ground-truth label. With
even a few thousand rows, the weights become a fitted logistic layer over the URL model's log-odds —
which keeps the additive structure, and therefore the explainability, entirely intact. This is the
most direct path from a documented judgement to an empirical result.

**Add content signals.** Form-field analysis, a visual similarity check against known brand login
pages, and DOM structural features would address the largest coverage gap in Section 6.4. Each brings
a false-positive cost that must be measured before adoption, not assumed away.

**Strengthen brand matching.** Homoglyph normalisation and bounded edit-distance matching, evaluated
against the popular-site holdout so that the false-positive cost is quantified rather than traded
blind.

**Establish a retraining cadence.** Scheduled retraining on a rolling window, with the leakage audit
as an automatic gate and a held-out comparison against the incumbent model before any promotion.

**Report intervals, not points.** Repeated splits with confidence intervals on every headline metric.

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

The project is not finished. Two of its three claims are instrumented but unmeasured, and one signal
family is inoperative. What it does have is an accurate account of which parts are established and
which are not — and after the experience of D1 and D2, I would rather submit a system whose gaps are
documented than one whose gaps are merely undiscovered.
