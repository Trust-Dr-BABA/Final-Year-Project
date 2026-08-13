// permission_monitor_test.js — Tests the MAIN-world/isolated-world contract between
// modules/permission_monitor.js (interception) and content_script.js (relay to the service
// worker). D7 was that this interception ran in the wrong JS context and observed nothing; this
// test exercises both scripts together through the CustomEvent bridge that connects them, the
// same mechanism real Chrome uses to cross the world boundary.

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

// A single fake `document` shared by both VM contexts, standing in for the real DOM both an
// isolated-world and a MAIN-world content script actually share in Chrome.
function makeSharedDocument() {
  const listeners = {};
  return {
    addEventListener: (type, fn) => {
      (listeners[type] = listeners[type] || []).push(fn);
    },
    dispatchEvent: (event) => {
      (listeners[event.type] || []).forEach((fn) => fn(event));
      return true;
    },
  };
}

async function run() {
  const sharedDocument = makeSharedDocument();

  // ── MAIN-world script: the actual interception ──────────────────────────
  let getUserMediaCalls = 0;
  const mainWorldGlobals = {
    document: sharedDocument,
    CustomEvent,
    console,
    Notification: {
      requestPermission: () => Promise.resolve("granted"),
    },
    navigator: {
      mediaDevices: {
        getUserMedia: (constraints) => {
          getUserMediaCalls += 1;
          return Promise.resolve("stream");
        },
      },
      geolocation: {
        getCurrentPosition: (cb) => cb({ coords: {} }),
      },
    },
  };
  vm.createContext(mainWorldGlobals);
  vm.runInContext(
    fs.readFileSync("extension/modules/permission_monitor.js", "utf8"),
    mainWorldGlobals,
  );

  // ── Isolated-world script: relay to the service worker ──────────────────
  const sentMessages = [];
  const isolatedWorldGlobals = {
    document: sharedDocument,
    console,
    chrome: {
      runtime: {
        sendMessage: (msg) => sentMessages.push(msg),
      },
    },
  };
  vm.createContext(isolatedWorldGlobals);
  vm.runInContext(fs.readFileSync("extension/content_script.js", "utf8"), isolatedWorldGlobals);

  // ── Test: camera call before interaction is flagged and relayed ─────────
  await mainWorldGlobals.navigator.mediaDevices.getUserMedia({ video: true });
  assert.equal(getUserMediaCalls, 1, "the page's real getUserMedia must still be called");
  assert.equal(sentMessages.length, 1, "content_script.js must relay the signal immediately");
  // JSON round-trip strips the vm context's realm-specific Array/Object prototypes, which
  // otherwise fail a structural deepEqual even when the content is identical.
  assert.deepEqual(JSON.parse(JSON.stringify(sentMessages.at(-1).payload)), {
    permissions_requested: ["camera"],
    rule_flags: ["cam_mic_on_first_visit"],
  });

  // ── Test: notification request within the 3s window is flagged ──────────
  await mainWorldGlobals.Notification.requestPermission();
  const latest = JSON.parse(JSON.stringify(sentMessages.at(-1).payload));
  assert.ok(latest.permissions_requested.includes("notifications"));
  assert.ok(latest.rule_flags.includes("notification_prompt_on_load"));

  // ── Test: signals accumulate rather than overwrite ───────────────────────
  assert.ok(latest.rule_flags.includes("cam_mic_on_first_visit"), "earlier signals must persist");

  // ── Test: geolocation within the window is flagged ───────────────────────
  mainWorldGlobals.navigator.geolocation.getCurrentPosition(() => {});
  const final = JSON.parse(JSON.stringify(sentMessages.at(-1).payload));
  assert.ok(final.rule_flags.includes("location_on_load"));
}

run().then(() => console.log("permission monitor check passed"));
