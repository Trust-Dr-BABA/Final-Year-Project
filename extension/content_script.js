/**
 * content_script.js — Isolated-world relay for permission signals.
 * The actual interception happens in modules/permission_monitor.js, which runs in the page's
 * MAIN world (D7 fix — see that file for why). This script shares the DOM with the page but not
 * its script environment, which is exactly why it can't intercept anything itself, but it *can*
 * see DOM events the main-world script dispatches, and only it has access to chrome.runtime.
 */

(function () {
  "use strict";

  const EVENT_NAME = "esa:permission-signal";

  const permissionSignals = {
    permissions_requested: [],
    rule_flags: [],
  };

  // Forward the accumulated signals to the service worker. Sent on every new signal rather than
  // once after a fixed delay (D8 fix) — background.js re-runs analysis if a message arrives after
  // the initial one already completed, so there is no need to withhold signals until some
  // arbitrary deadline has passed.
  function send() {
    chrome.runtime.sendMessage({ type: "PERMISSION_SIGNALS", payload: permissionSignals });
  }

  document.addEventListener(EVENT_NAME, (event) => {
    const { permission, ruleFlag } = event.detail || {};
    if (permission && !permissionSignals.permissions_requested.includes(permission)) {
      permissionSignals.permissions_requested.push(permission);
    }
    if (ruleFlag && !permissionSignals.rule_flags.includes(ruleFlag)) {
      permissionSignals.rule_flags.push(ruleFlag);
    }
    send();
  });
})();
