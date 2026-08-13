# Fusion weights — ADR-014

> Implements `backend/services/risk_fusion.py`. Each browser signal's attribution is **exactly**
> `weight × transform(value)` — not an estimate of its contribution, the contribution itself,
> computed from the same expression that applies it to the score (Algorithm 4.5). This table is
> the full, auditable specification of the browser-signal half of every explanation the system
> produces.

## Why weights are hand-set rather than learned

No labelled corpus carries per-URL tracker counts, mixed-content flags, redirect depths, or
permission-prompt timings — PhishTank and every public phishing corpus label the *URL*, not the
browsing session that visited it. There is nothing to fit a coefficient against. Fabricating such
labels to enable a learned weight would be worse than not having one: it would produce a number
that looks empirical and isn't.

The alternative adopted here works because of a property of the attribution method already in use.
For a tree ensemble scored through a logistic link, SHAP values are additive contributions in
**log-odds space** — they sum, together with the base rate, to the model's log-odds output
(Lundberg & Lee, 2017). A hand-set weight added in that same space is the same *kind* of quantity.
That is what makes it valid to rank a SHAP value and a fusion weight in one list: they are both
already log-odds contributions, just produced by different means.

## The transform functions

Two shapes are used, chosen per signal by whether "more" should keep mattering linearly or not.

**Saturating** — `1 − e^(−value / scale)`. Used for counts where the *presence* of the behaviour
matters more than its exact magnitude past a point: the fortieth tracker is weaker evidence than
the fifth, because by the fortieth the page has already established itself as heavily instrumented.
Reaches ~63% of its way to the ceiling at `value == scale`, and asymptotes towards 1 beyond it.

**Identity** — passes a 0/1 flag through unchanged. Used for the binary signals, where there is no
"more" to diminish.

## The table

| Signal | Transform | Scale | Weight (log-odds) | Odds multiplier at saturation | Justification |
|---|---|---|---|---|---|
| `tracker_count` | saturating | 10 | **1.5** | ×4.48 | Scale matches `heuristics_engine.py`'s own `excessive_trackers` threshold (>10), so the signal saturates roughly where the rule layer already calls it "excessive". A single tracker is weak evidence — most legitimate commercial sites carry a few — so the transform must let low counts through with a small contribution. |
| `has_mixed_content` | identity | — | **1.0** | ×2.72 | Loading insecure resources into a secure document is a real construction-quality signal, but it is common enough on legitimate sites (stale third-party widgets, old CDN links) that it should not dominate the score on its own. |
| `redirect_chain_length` | saturating | 3 | **1.2** | ×3.32 | Scale matches the `long_redirect_chain` rule threshold (>3). A single redirect is unremarkable — most auth flows and short-link services produce one — so the transform is deliberately gentle below the threshold. |
| `cam_mic_on_first_visit` | identity | — | **2.0** | ×7.39 | The strongest weight in the table. A page requesting camera or microphone access before any user interaction has essentially no legitimate justification — this is the signal with the least plausible innocent explanation. |
| `notification_prompt_on_load` | identity | — | **0.8** | ×2.23 | The weakest weight. Immediate notification prompts are poor UX practice but extremely widespread on ordinary commercial and content sites — weighting this heavily would produce false positives on a large fraction of the legitimate web. |
| `location_on_load` | identity | — | **1.5** | ×4.48 | Between the two extremes: precise location on load is unusual outside a narrow set of legitimate use cases (maps, delivery, weather), so it carries real signal, but those legitimate cases exist and are common enough to withhold the maximum weight. |

*"Odds multiplier at saturation" is `e^weight` — how much the signal alone can multiply the odds of
phishing by, at its transform's ceiling. Quoted so the relative strength of the six weights is
readable without doing the exponentiation by hand.*

## What these numbers are, and what they are not

They are a documented, internally-consistent, ranked judgement about relative signal strength,
calibrated against the same thresholds the rule-flag layer already uses so the two layers agree
about what counts as "excessive." They are not fitted to data, and no claim in this project rests
on them being optimal.

**Cost, stated plainly.** A different, equally reasonable person could set these weights
differently. That is the nature of a hand-set parameter. Two things bound the risk this poses to
the project's conclusions:

1. Section 5.9's sensitivity analysis perturbs every weight (halved, doubled, and individually
   zeroed) and reports how much the headline classification metrics move. If conclusions were
   fragile to the exact values in this table, that analysis would show it.
2. Section 6.5 (future work) identifies the honest fix: a small extension-collected, consented
   corpus pairing browser signals with outcomes would let these weights be fitted as a logistic
   layer over the URL model's log-odds — keeping the additive structure, and therefore the
   explainability, completely intact.
