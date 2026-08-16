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
| **O6** | Render every contribution in plain English | **Met.** Single shared template map; 24 templates (three added this pass for the content and reputation-fusion signals); the popup renders `human_readable` and never inspects the identifier, so the guarantee is structural. | §3.2.1, §5.5 TC-U-16 |
| **O7** | Evaluate under protocols that reflect deployment | **Met.** Temporal and unseen-domain protocols, four measured baselines (a fifth is explicitly not fabricated — see §5.10), calibration, faithfulness ablation, sensitivity analysis and a 30-URL live run are all executed and reported, including where they fell short of their target — and re-executed a second time after a mid-project feature fix, with both passes reported rather than only the later, more favourable one. | Chapter 5 |

All seven objectives are met. Three of the results (faithfulness, the deep-path false-positive
rate, and the 30-URL live run) fall short of the acceptance criterion originally set for them; they
are counted as met at the level of the objective — evaluate rigorously and report honestly — while
the underlying shortfalls are carried forward as limitations in §6.4 rather than hidden inside a
green checkmark. Section 6.6 discusses this distinction.

## 6.3 Assessment of the claims

### C1 — Detection generalises beyond a blocklist

**Established, on the metric that actually answers the question.** Section 5.10's decisive test is
recall on URLs absent from the blocklist, where the blocklist scores exactly 0.0% by construction.
The trained classifier recovers 61.3% recall on that same temporal-split test set (Table 5.15) —
generalisation a blocklist structurally cannot provide, whatever its precision on URLs it has
already seen.

What underwrites this claim is not the headline number alone but the audit that preceded it. The
original corpus produced a stronger-looking score (F1 ≈ 0.97) by separating classes on path
presence rather than phishing, and any claim of generalisation resting on it would have been false.
The rebuilt corpus's lower, harder-won F1 (0.723 under the temporal split, Table 5.13) is the honest
number, and it is the one C1 is assessed against. The figure moved by two points (0.726 → 0.723)
when the corpus's `digit_ratio` fix was applied and the whole evaluation suite re-run on 16 August —
consistent with replacing one moderately informative feature with a redefinition of comparable
standalone power (§5.9), not a regression traceable to the fix.

### C2 — Detection is genuinely multi-signal

**Established for the architecture and the live pipeline; not established as an offline accuracy
number, and that gap is stated rather than papered over.** Browser and page-content signals are
measured, transmitted, reach the reasoning layer, and — since the fusion layer landed — measurably
move the score: TC-I-06 and TC-U-25–TC-U-30 confirm the fused probability moves in the documented
direction under every signal family, by exactly the weight documented in Table 4.1, and the
sensitivity analysis (§5.12.2) shows that movement is not an artefact of one arbitrary weight choice
for the signals the analysis currently exercises. Reputation data joined the same mechanism under
ADR-017 partway through the project (§3.2.6) — a deliberate widening of C2's own scope, closing a
real false positive that the URL model alone had no route to correct, subject to the same
gated-and-asymmetric safeguards the original browser-signal design established. The 30-URL live run
in §5.15 exercises the complete fused pipeline against real requests, not a mock, and the 16 August
re-check (§5.15.2) confirms the extended pipeline still behaves as documented on that same set.

What remains genuinely unestablished is an offline accuracy figure for the fused system — there is
no "B5" row in Table 5.15, because no corpus, including this project's own, pairs a phishing label
with real per-URL browser telemetry or reputation data. Fabricating that pairing to produce a B5
number would be the same category of error C1's own history warns against. C2 is therefore
established as "the signals are real, reach the score, and move it correctly" rather than as "the
fused system is measurably more accurate than the URL-only model" — a narrower but honest claim, now
covering three signal families instead of one.

### C3 — Explanations are faithful rather than decorative

**Partially established, with the shortfall reported rather than concealed — and narrowing.** The
ablation procedure in §5.12.1 measured 87.0% directional agreement against a 90% target on 13
August — not met. Re-measured on 16 August against the `digit_ratio`-fixed model, the same procedure
on the same test set reports 88.4%: a genuine 1.4-point improvement, consistent with the hypothesis
that a length-normalised feature produces smoother, more locally-linear attributions than a raw
count prone to single-value dominance. The gap that remains is explained, not merely noted: XGBoost
at `max_depth=6` permits real three-way feature interactions that a simultaneous three-feature
ablation does not fully respect, and several strong features (`url_entropy`, `digit_ratio`) are
mutually correlated, so removing the top three together displaces more combined signal than the sum
of their individual attributions predicts.

The structural argument still holds independently of this number: `TreeExplainer` is exact for tree
ensembles rather than approximate, so the model's own attributions are not estimates of
contributions but the contributions themselves, and the fusion attributions are exact by
construction. What the measurement adds is the honest qualifier — exact local attribution does not
guarantee that a simultaneous multi-feature intervention behaves as the sum of those attributions
predicts, and 88.4% is how close it comes on this classifier, not 100%.

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

**Fusion weights are hand-set, not learned, and the sensitivity analysis does not yet cover all of
them.** ADR-014 and ADR-017 explain why — no labelled corpus carries per-URL tracker counts,
page-content matches or reputation data — but the consequence stands: those weights encode the
author's judgement about how much each signal should matter. The sensitivity analysis (§5.12.2)
bounds how much the conclusions depend on the three original browser-signal weights it was designed
to test; it does not yet exercise the three signals added later (`scam_keyword_hits`,
`sensitive_field_count`, `vt_malicious_votes`) because the synthetic "typical page" profile it
perturbs against was never extended to set them, and deciding what a representative page-content and
reputation profile looks like was deliberately not done under this evaluation pass's time pressure
rather than guessed at. Section 6.5 records extending it as a specific, bounded next step.

**The service trusts the counts it receives.** Signals are collected client-side and submitted
without attestation. Within the intended deployment this is acceptable, since a user tampering with
their own extension only misleads themselves. It would not survive a model in which the service
accepted submissions from arbitrary clients, and it means the counts are not evidence in any
adversarial sense.

**Page-content examination is narrow, not absent, and the gap it leaves is still large.** Since the
content scanner landed (§4.3.7), the system does read the page's own rendered text for a fixed list
of scam-indicator phrases and its form fields for sensitive-data-category combinations — the
original blanket claim that no page content is examined at all no longer holds. What it still does
not do is anything resembling comprehension: no visual similarity check against known brand login
pages, no DOM structural analysis, no matching against page content that avoids the specific phrase
list verbatim. A pixel-perfect clone of a bank's login page, using generic field names and none of
the listed phrases, hosted on an unremarkable URL with ordinary network behaviour, is still invisible
to this system — the phrase list only catches a scam page that phrases itself in a way this project
anticipated. That remains a substantial category of attack, and closing it properly (visual
similarity, structural DOM analysis) is still the single largest gap in coverage, now narrowed rather
than untouched.

**Lexical URL features are brittle in ways one fix does not close.** The original 30-URL live run
(§5.15.1) found a false positive on `docs.python.org/3/library/asyncio.html` driven almost entirely
by `num_digits = 1` — a single incidental digit (the Python version `3` in the path) contributing
+0.87 log-odds because the feature counted digits rather than measuring their density. Replacing it
with `digit_ratio` (§4.7.1) fixed that specific case — confirmed by the 16 August re-check (§5.15.2),
where the same URL no longer crosses the interstitial threshold — without moving the aggregate
false-positive rate (8.5% → 8.7%) or faithfulness (87.0% → 88.4%, an *improvement*) outside noise.
**The same re-check surfaced a new, unrelated false positive** (`news.ycombinator.com/item?id=1`,
driven by `url_entropy`, one point over the threshold) that did not exist in the original run,
demonstrating concretely that fixing one lexical feature's brittleness does not make the class of
problem go away — it was never a `digit_ratio`-shaped problem specifically, it is a
purely-lexical-features-shaped problem, and D17 (§5.16) is carried forward as open for exactly that
reason. The original run's other pattern — misses on live phishing hosted on trusted free platforms
(`vercel.app`, `typedream.app`) via `url_length`'s negative learned weight — is unaffected by either
fix and remains open. Three-plus independent measurements now point at the same underlying
limitation rather than one.

**Brand impersonation matching now catches typosquats, at a small measured cost.** The original
literal substring match caught `paypal.secure-login.tk` but missed `paypa1`, `pаypal` with a
Cyrillic character, and every edit-distance variant. Homoglyph normalisation plus bounded
Levenshtein matching against hostname tokens closes that gap (`ml/reports/training_log.md`, Run 2)
— at the cost of one new false positive across the 1,488-URL holdout (`mail.google.com`, whose
`"mail"` token sits at edit-distance 1 from the brand `"gmail"`), accepted rather than special-cased
since excluding it would be the same kind of fitting-to-the-holdout error rejected throughout this
project. The technique is no longer purely literal, but it is not free of false positives either.

**The corpus is a snapshot, and a promotion mechanism is not the same as a cadence.** Phishing
campaigns evolve continuously. A model trained on one period's feed degrades against later
campaigns, and this project measures that degradation once, through the temporal split, rather than
tracking it. `ml/scripts/retrain_gate.py` (§4.7's algorithm notes, §6.5) now exists and has been run
once, successfully, against the current corpus — it is the leakage-audit-gated promotion logic a
cadence would need — but no schedule invokes it, and this static corpus cannot itself supply the new
labelled data a real cadence needs to have anything to retrain against. The mechanism existing
narrows this limitation; it does not close it.

**Reputation data is subject to a free-tier allowance.** Four requests per minute and five hundred per
day. The one-hour cache makes ordinary browsing viable, but heavy use exhausts the allowance, at
which point corroboration silently becomes unavailable. By design this cannot alter a verdict, but
it does degrade what the user is shown.

**The URL itself is transmitted.** The privacy analysis in TC-SEC-04 confirms that no page content
leaves the browser, but a URL *is* browsing history, and the service records it durably — the kind
of data GDPR [27] treats as personal and subject to a right of access and erasure neither `/history`
nor `/scan/{id}` currently implement for a given browsing record. A design that hashed URLs, or
performed assessment locally, would be more private. This one does not. Separately, an automated
system that gates a warning shown to a user on a probability score sits close to the kind of
consequential automated decision the EU AI Act [28] and GDPR's Article 22 both single out for
explanation requirements — the explainability this project treats as its central contribution is
also, incidentally, a compliance-relevant property for exactly that reason, though this project
makes no claim of regulatory compliance and none was assessed.

**Desktop Chromium only.** Mobile browsers do not support the extension APIs this design depends on,
which excludes the platform where a large share of phishing is actually opened.

**The evaluation is single-run for most tables, and the one place it is not reveals why that
matters.** A repeated-seed instrument (§5.9.1) was built and run for the two headline split
protocols on the B4 model: ten seeds each, with mean, standard deviation and a 95% CI reported
alongside the single-seed headline figure. It found the temporal split's F1 stable to ±0.004 across
seeds but the unseen-domain split's F1 varying by ±0.058 — more than an order of magnitude wider —
so the single previously-reported unseen-domain figure (Table 5.13) should be read as one draw from
a genuinely wide distribution, not a tight estimate. Every *other* measured table in Chapter 5 —
calibration, faithfulness, the false-positive holdout, the fusion sensitivity analysis — remains a
single-seed point estimate, because extending the same repeated-training protocol to each would
multiply the compute cost of every one of them by the repeat count, and doing that within this
evaluation pass was judged lower-value than the two headline splits it was applied to first. The
distinction between a point estimate and an interval should be kept in mind when reading the rest of
the chapter, and §6.5 lists extending coverage as a specific next step rather than a vague
aspiration.

**Live deployment was not completed within this submission.** The backend and dashboard were built
and evaluated against the local Docker stack — the same image the deployment target would run — but
were not deployed to the hosting platforms named in §4.2. The 30-URL end-to-end run in §5.15
therefore exercises the correct code path and a real trained model, but not the actual network
topology, TLS termination, or cross-origin configuration a live deployment would introduce, any of
which could surface its own defects in the way §4.7's earlier ones were surfaced only once a real
environment was exercised.

## 6.5 Future work

**Chase D17, the false positive the `digit_ratio` fix's own re-check surfaced.** §6.4 now carries
two independent lexical false-positive mechanisms (`url_length` under-scoring long legitimate URLs;
`url_entropy` over-scoring path segments with naturally high character variety) instead of one. A
single-feature fix closed the specific case that motivated it without closing the class of problem —
consistent with, not contradicting, the project's own repeated finding that lexical URL features
alone cannot reach a production-grade false-positive rate. The corrected next step is content
signals and reputation data doing more of the work (both already underway per the two items below),
not a third single-feature patch chased against another small sample.

**Re-run the live 30-URL end-to-end validation with reputation data re-enabled.** §5.15.2's re-check
was deliberately offline, so it does not reflect ADR-017's established-reputation dampening for the
well-known domains in that set. A live re-run — the same method as §5.15.1, against the current
system — would show whether that dampening actually improves the popular-domain false-positive
picture in practice, rather than leaving it as the reasoned-but-unmeasured expectation §5.15.2
states. `ml/scripts/bench_latency.py` should be re-run in the same session, since the reputation
client's timeout reduction (2.5s, §5.13) has not been measured live either.

**Extend the fusion sensitivity analysis to the three currently-uncovered weights.** §5.12.2's
coverage caveat is specific and actionable: `scam_keyword_hits`, `sensitive_field_count` and
`vt_malicious_votes` need a considered "typical page" profile value each before the same
perturbation protocol can say anything about them, and that consideration was deliberately deferred
rather than guessed at under this pass's time pressure (§6.4).

**Extend the repeated-seed protocol beyond the two headline splits.** §5.9.1 found a genuinely
useful result — the unseen-domain split is an order of magnitude more seed-sensitive than the
temporal split — by applying `cross_validate.py` to only two of Chapter 5's many measured tables.
Calibration, faithfulness and the false-positive holdout are the natural next candidates, each at
the cost of retraining ten (or more) times per table.

**Complete live deployment and re-run the end-to-end validation against it.** The backend and
dashboard are built and evaluated locally; deploying to the platforms named in §4.2 and repeating
§5.15's 30-URL run against the live stack would close the one gap §6.4 identifies between "verified
against the shipped image" and "verified in the actual target environment."

**Confirm the permission signal family and the interstitial in a real browser.** Both are code-complete
with automated coverage of their non-DOM logic; `tests/manual/permission_monitor_test.md` and
`tests/manual/interstitial_test.md` specify the remaining manual sessions.

**Learn the fusion weights.** The honest route is a small labelled corpus collected through the
extension itself, with user consent, recording browser, content and reputation signals alongside a
ground-truth label. With even a few thousand rows, the weights become a fitted logistic layer over
the URL model's log-odds — which keeps the additive structure, and therefore the explainability,
entirely intact. This remains the most direct path from a documented judgement (Table 4.1) to an
empirical one; the sensitivity analysis in §5.12.2 bounds the risk of the current judgement without
removing it.

**Extend content signals beyond phrase and field matching.** The page-content scanner added this
pass (§4.3.7) narrows, but does not close, the largest coverage gap identified in the original
submission: a pixel-perfect clone hosted on an unremarkable URL, using generic wording and ordinary
form fields, is still invisible to it. Visual similarity checking against known brand login pages
and DOM structural features are the natural next layer. Each brings a false-positive cost that must
be measured before adoption, following the same discipline §5.11 and the L1 brand-matching change
(§6.4) already applied — and the same discipline this pass applied when the content scanner's own
weights were deliberately set below the OS-level permission signals (Table 4.1) pending exactly this
kind of validation data.

**Exercise the retraining gate on a real cadence.** `ml/scripts/retrain_gate.py` (added this pass)
is the promotion *mechanism* a scheduled cadence needs — leakage audit, candidate training, and a
held-out comparison against the incumbent before any promotion — and it has been run once,
successfully, against the current corpus (`ml/reports/retrain_gate_log.md`). What it has not done is
run repeatedly against a corpus that changes over time, because this project's corpus is a static
snapshot (§6.4); the mechanism existing is not the same claim as a cadence being established, and
this item is narrower than it was before this pass specifically because of that distinction.

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

**Fixing a measured defect is not the same as closing the class of problem it belongs to, and the
evaluation that catches the fix should also be trusted to catch that.** `digit_ratio` did exactly
what it was built to do — the specific false positive that motivated it (§5.15.1) is gone (§5.15.2)
— and the same re-check that confirmed the fix also found a different URL, driven by a different
feature, that had newly crossed into the phishing band. The easy version of this project's own
discipline would have stopped at "the fix worked" and moved on; the version actually applied here
was to re-run the same 30-URL check the fix was meant to pass, on principle, rather than trust that
one confirmed case meant the whole evaluation was still clean — and it wasn't quite. Three further
defects (D13, D14, D16) turned up the same way, inside the evaluation tooling itself rather than the
system under evaluation, while re-running the pipeline this pass's other changes required: a stale
column name, a hand-written report paragraph that no longer matched its own table, a helper that
mutated the global it was only meant to read. None of the four were visible until something forced a
genuine re-execution. The lesson I take from this project, restated once more with this pass's own
evidence behind it, is that "passing" is a property of a specific run, not a durable property of the
code — which is the entire argument §5.2 makes for dating every measurement in this report rather
than just stating it once and trusting it to still be true.

The system deployed to a local stack rather than to the live hosting platforms named in §4.2, a
scope decision made deliberately rather than by running out of time — the evaluation that matters
academically (does the detector generalise, is it calibrated, are its explanations faithful) does
not depend on where the container happens to run, and spending the remaining time on a genuine model
limitation was judged more valuable than spending it on infrastructure that would not have changed
a single number in Chapter 5.

The project is complete against its own stated scope, and it is not finished in the sense that no
real system ever is. Every claim in §1.5 is now measured rather than asserted, including the ones
that did not clear their target — faithfulness at 88.4% against a 90% goal (up from 87.0% after the
`digit_ratio` fix, still short), and 20 of 30 correct on both the original and re-checked live
end-to-end runs against a 26-of-30 bar. What it has, consistently with the discipline D1 and D2
established early on and reapplied throughout this later evaluation pass, is an accurate account of
which parts are established, which are established with a caveat, and which are not — and I would
still rather submit a system whose gaps are documented than one whose gaps are merely undiscovered.
