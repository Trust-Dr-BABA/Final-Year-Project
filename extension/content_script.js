/**
 * content_script.js — Page-level scanner
 * Runs on every page load. Detects permission abuse heuristics and
 * reports back to the background service worker via chrome.runtime.sendMessage.
 */

(function () {
  "use strict";

  const permissionSignals = {
    permissions_requested: [],
    rule_flags: [],
  };

  let userHasInteracted = false;
  const PAGE_LOAD_TIME = Date.now();

  // ── Interaction tracking ───────────────────────────────────────────────────

  document.addEventListener("scroll", () => { userHasInteracted = true; }, { once: true, passive: true });
  document.addEventListener("click",  () => { userHasInteracted = true; }, { once: true });

  // ── Heuristic: Notification permission requested within 3 seconds ──────────

  const _originalNotificationRequest = Notification.requestPermission.bind(Notification);
  Notification.requestPermission = function (...args) {
    const elapsedMs = Date.now() - PAGE_LOAD_TIME;
    permissionSignals.permissions_requested.push("notifications");
    if (elapsedMs < 3000) {
      permissionSignals.rule_flags.push("notification_prompt_on_load");
      console.warn("[ESA] Notification permission requested within 3s of load.");
    }
    return _originalNotificationRequest(...args);
  };

  // ── Heuristic: Camera/Mic requested before user interaction ───────────────

  const _originalGetUserMedia = navigator.mediaDevices?.getUserMedia?.bind(navigator.mediaDevices);
  if (_originalGetUserMedia) {
    navigator.mediaDevices.getUserMedia = function (constraints) {
      if (constraints.video) permissionSignals.permissions_requested.push("camera");
      if (constraints.audio) permissionSignals.permissions_requested.push("microphone");
      if (!userHasInteracted) {
        permissionSignals.rule_flags.push("cam_mic_on_first_visit");
        console.warn("[ESA] Camera/mic requested before user interaction.");
      }
      return _originalGetUserMedia(constraints);
    };
  }

  // ── Heuristic: Geolocation requested within 3 seconds ─────────────────────

  const _originalGetPosition = navigator.geolocation?.getCurrentPosition?.bind(navigator.geolocation);
  if (_originalGetPosition) {
    navigator.geolocation.getCurrentPosition = function (...args) {
      const elapsedMs = Date.now() - PAGE_LOAD_TIME;
      permissionSignals.permissions_requested.push("geolocation");
      if (elapsedMs < 3000) {
        permissionSignals.rule_flags.push("location_on_load");
        console.warn("[ESA] Geolocation requested within 3s of load.");
      }
      return _originalGetPosition(...args);
    };
  }

  // ── Send signals to background on page load complete ──────────────────────

  window.addEventListener("load", () => {
    // Small delay to catch anything that fires right on load
    setTimeout(() => {
      chrome.runtime.sendMessage({
        type: "PERMISSION_SIGNALS",
        payload: permissionSignals,
      });
      console.log("[ESA] Content script signals sent:", permissionSignals);
    }, 3500);
  });

  console.log("[ESA] Content script injected:", window.location.href);
})();
