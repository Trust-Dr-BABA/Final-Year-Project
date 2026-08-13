# Manual Test Plan — Phishing Interstitial (Sprint 3.2)

> **Purpose.** Verify the full-page warning overlay triggers correctly, only on the phishing tier,
> renders the actual attributed reasons, and that dismissal doesn't persist across navigation.
> Like D7/D8, this is DOM-injection behaviour that needs a real browser to verify — it isn't
> meaningfully testable in a Node sandbox the way `network_monitor.js`'s pure logic is.

## Prerequisites

1. Extension loaded in developer mode, `manifest.json` includes `modules/interstitial.js` in the
   default-world content script entry (verify: `chrome://extensions` → no manifest errors).
2. Backend running with the trained model loaded (`GET /health` → `model_loaded: true`) — the
   overlay is deliberately not meaningful to test against the heuristic fallback (Sprint 3.2.3).
3. Service worker console open.

## Test 1 — Overlay appears on a phishing verdict

**Steps:**

1. Navigate to a URL known to score above 0.70 (a live PhishTank URL, or any URL whose lexical
   structure clearly matches the training distribution — e.g. a raw-IP host with a suspicious TLD
   and brand token, per `ml/reports/training_log.md`'s sanity checks).
2. Observe the page immediately after the analysis completes (badge turns red `!`).

**Pass criteria:** the page blurs, a centered card appears reading "Phishing Detected" with a
confidence percentage, the assessed URL, and up to three reasons matching what the popup would
show for the same scan (open the popup to cross-check `top_reasons`).

## Test 2 — Never triggers on suspicious or legitimate

**Steps:**

1. Navigate to a URL that scores in the suspicious band (0.40–0.70) — check via the popup first if
   unsure which band a candidate URL lands in.
2. Navigate to an ordinary legitimate site.

**Pass criteria:** no overlay in either case, even though the suspicious case still shows an amber
badge and reasons in the popup. The gate is exactly `verdict === "phishing"` (score > 0.70), never
`suspicious` — confirms 3.2.1's acceptance criterion.

## Test 3 — "Leave this page" closes the tab

**Steps:**

1. Trigger the overlay (Test 1).
2. Click **Leave this page**.

**Pass criteria:** the tab closes. In the service worker console, confirm an `INTERSTITIAL_LEAVE`
message was handled (no error logged).

## Test 4 — "Continue" dismisses without persisting

**Steps:**

1. Trigger the overlay (Test 1).
2. Click **I understand the risks, continue**.
3. Confirm the overlay disappears and the underlying page is usable.
4. Reload the same tab (or re-navigate to the identical URL).

**Pass criteria:** the overlay reappears on step 4. Nothing about the dismissal in step 2 is
persisted anywhere (no `chrome.storage` write, no cookie, no in-memory flag surviving navigation)
— a remembered bypass would be a durable attack surface, so this is a correctness requirement, not
a nice-to-have.

## Test 5 — Shadow DOM isolation

**Steps:**

1. Trigger the overlay.
2. In DevTools, inspect the page. Confirm `#esa-interstitial-host` has `shadowRoot` set to `null`
   in the Elements panel (closed shadow root — not inspectable from the page's own script either).
3. In the page's own console (not the extension's), run `document.getElementById("esa-interstitial-host").shadowRoot` and confirm it returns `null`.

**Pass criteria:** the page itself cannot query into the warning's DOM or styles — the closed
shadow root is doing its job. This matters because the page under assessment is, by definition,
untrusted; it should not be able to inspect or manipulate the warning shown about it.

## Verification checklist

- [ ] Test 1: overlay appears with correct confidence and reasons on a phishing verdict
- [ ] Test 2: no overlay on suspicious or legitimate verdicts
- [ ] Test 3: "Leave this page" closes the tab
- [ ] Test 4: "Continue" dismisses locally; a fresh navigation re-warns
- [ ] Test 5: closed shadow root confirmed isolated from the host page
