/**
 * permission_monitor.js — MAIN-world permission heuristics (fixes D7).
 *
 * Must run in the page's own JavaScript context, declared via "world": "MAIN" in manifest.json.
 * A content script in the default isolated world shares the DOM with the page but not its script
 * environment — patching Notification.requestPermission there creates a new function in the
 * isolated world that the page never calls, so the interception silently observes nothing. This
 * script patches the *page's* actual Notification, getUserMedia and getCurrentPosition, which is
 * the only place those calls can be observed at all.
 *
 * The main world has no access to chrome.* APIs, so results can't be sent to the service worker
 * directly. Each triggered heuristic is instead dispatched as a CustomEvent on `document`, which
 * content_script.js (isolated world, same DOM) listens for and relays via chrome.runtime.sendMessage.
 */

(function () {
  "use strict";

  const EVENT_NAME = "esa:permission-signal";
  const PAGE_LOAD_TIME = Date.now();
  let userHasInteracted = false;

  document.addEventListener("scroll", () => { userHasInteracted = true; }, { once: true, passive: true });
  document.addEventListener("click", () => { userHasInteracted = true; }, { once: true });

  // Dispatch one observed permission call to the isolated-world relay.
  function emit(permission, ruleFlag) {
    document.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: { permission, ruleFlag } }));
  }

  // ── Heuristic: Notification permission requested within 3 seconds of load ─
  const _originalNotificationRequest = Notification.requestPermission.bind(Notification);
  Notification.requestPermission = function (...args) {
    const elapsedMs = Date.now() - PAGE_LOAD_TIME;
    emit("notifications", elapsedMs < 3000 ? "notification_prompt_on_load" : null);
    return _originalNotificationRequest(...args);
  };

  // ── Heuristic: Camera/microphone requested before any user interaction ────
  const _originalGetUserMedia = navigator.mediaDevices?.getUserMedia?.bind(navigator.mediaDevices);
  if (_originalGetUserMedia) {
    navigator.mediaDevices.getUserMedia = function (constraints) {
      if (constraints?.video) emit("camera", !userHasInteracted ? "cam_mic_on_first_visit" : null);
      if (constraints?.audio) emit("microphone", !userHasInteracted ? "cam_mic_on_first_visit" : null);
      return _originalGetUserMedia(constraints);
    };
  }

  // ── Heuristic: Geolocation requested within 3 seconds of load ──────────────
  const _originalGetPosition = navigator.geolocation?.getCurrentPosition?.bind(navigator.geolocation);
  if (_originalGetPosition) {
    navigator.geolocation.getCurrentPosition = function (...args) {
      const elapsedMs = Date.now() - PAGE_LOAD_TIME;
      emit("geolocation", elapsedMs < 3000 ? "location_on_load" : null);
      return _originalGetPosition(...args);
    };
  }
})();
