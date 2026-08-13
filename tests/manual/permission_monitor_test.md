# Manual Test Plan — Permission Monitor Module (Sprint 2.6)

> **Purpose.** Verify the D7/D8 fix: permission interception now runs in the page's MAIN world
> (`extension/modules/permission_monitor.js`) rather than the isolated world, where it previously
> observed nothing, and `background.js` re-runs analysis when a permission signal arrives after
> the initial analysis already completed, rather than requiring the popup to be reopened to see it.

## Prerequisites

1. Extension loaded in developer mode (`chrome://extensions` → Developer mode → "Load unpacked" → `extension/`)
2. Service worker console open (`chrome://extensions` → the extension card → "service worker")
3. Backend running and reachable (`docker compose up -d` from `docker/`, or `uvicorn backend.main:app --reload`)

## Test 1 — Main-world interception actually fires (D7)

| Field | Value |
|---|---|
| **URL** | `file:///<repo-path>/tests/manual/fixtures/camera_on_load.html` |
| **Expected** | The page's own permission prompt appears (camera) |
| **Expected storage** | `perm_<tabId>` contains `permissions_requested: ["camera"]`, `rule_flags: ["cam_mic_on_first_visit"]` |

**Steps:**

1. Open the fixture file directly in Chrome (`file://` URL, or serve it locally).
2. Chrome's native camera permission prompt should appear almost immediately — click **Block** (the extension observes the call, not the outcome, so the decision doesn't matter).
3. In the service worker console, run:
   ```js
   chrome.storage.local.get(null, console.log)
   ```
4. Find the `perm_<tabId>` entry for this tab.

**Pass criteria:** `rule_flags` contains `cam_mic_on_first_visit`. Before the fix, this array was always empty — the isolated-world patch in the old `content_script.js` never saw the page's real `getUserMedia` call.

## Test 2 — Notification prompt inside the 3-second window

| Field | Value |
|---|---|
| **URL** | `tests/manual/fixtures/notification_on_load.html` |
| **Expected storage** | `rule_flags` contains `notification_prompt_on_load` |

Same procedure as Test 1. The fixture calls `Notification.requestPermission()` 1 second after
load, inside the 3-second window.

## Test 3 — No false flags on an ordinary site (D7 regression guard)

| Field | Value |
|---|---|
| **URL** | `https://google.com` |
| **Expected storage** | `perm_<tabId>` is either absent or has empty `rule_flags` |

Google's homepage does not request camera, microphone, geolocation, or notifications on load.
Confirms the interception isn't flagging pages that never call these APIs.

## Test 4 — Re-analysis when a signal arrives late (D8)

This is the ordering-race fix. Permission calls routinely fire seconds after `tabs.onUpdated`
reports `"complete"`, well after the initial `/analyze` call has already returned and cached a
result.

**Steps:**

1. Navigate to `tests/manual/fixtures/camera_on_load.html`.
2. Immediately open the popup and note the verdict shown (this reflects the *first* analysis,
   before the permission signal has necessarily arrived — it may already include it if the
   `getUserMedia` call and the analysis race the other way, so don't assume either order).
3. Watch the service worker console. Once `permission_monitor.js`'s main-world call fires,
   `content_script.js` relays it, and `background.js`'s message handler should log a second
   `/analyze` request (visible via `console.error`/network activity, or by checking `chrome.storage.local.get([String(tabId)])` for an updated `timestamp`).
4. Reopen the popup.

**Pass criteria:** the second, updated result includes `cam_mic_on_first_visit` among
`flagged_rules` / `top_reasons`, even though the popup was potentially opened before that signal
arrived. The cached entry's `timestamp` should have advanced between steps 2 and 4, confirming a
second analysis actually ran rather than the popup just re-displaying stale data.

## Known limitation (documented, not fixed by this change)

MAIN-world content scripts are subject to the *page's own* Content-Security-Policy, unlike
isolated-world scripts. A page with an unusually strict CSP could in principle block the script
injection itself. This is a Chrome platform constraint rather than a defect in this extension, and
is recorded in the thesis limitations section rather than silently assumed away.

## Verification checklist

- [ ] Test 1: `cam_mic_on_first_visit` set after the camera fixture
- [ ] Test 2: `notification_prompt_on_load` set after the notification fixture
- [ ] Test 3: no rule flags on `google.com`
- [ ] Test 4: a second analysis runs and updates the cached result after a late permission signal
