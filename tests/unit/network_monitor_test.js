const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

async function run() {
  const listeners = {};
  let stored;
  const chrome = {
    runtime: { getURL: () => "tracker_domains.json" },
    webNavigation: {
      onBeforeNavigate: { addListener: (fn) => (listeners.navigate = fn) },
    },
    webRequest: {
      onBeforeRedirect: { addListener: (fn) => (listeners.redirect = fn) },
      onCompleted: { addListener: (fn) => (listeners.completed = fn) },
    },
    tabs: { onUpdated: { addListener: (fn) => (listeners.updated = fn) } },
    storage: { local: { set: async (value) => (stored = value) } },
  };
  const source = fs.readFileSync(
    "extension/modules/network_monitor.js",
    "utf8",
  );
  vm.runInNewContext(source, {
    chrome,
    console,
    URL,
    fetch: async () => ({ ok: true, json: async () => ["tracker.example"] }),
  });
  await new Promise(setImmediate);

  listeners.navigate({ tabId: 7, frameId: 0, url: "https://example.com" });
  listeners.completed({ tabId: 7, url: "https://tracker.example/pixel" });
  listeners.completed({ tabId: 7, url: "https://tracker.example/second" });
  // Subdomains of a listed tracker must match too (EasyPrivacy ||domain^ rules)
  // and must collapse onto the same base domain rather than counting twice.
  listeners.completed({ tabId: 7, url: "https://ssl.tracker.example/beacon" });
  // A domain that merely ends with the same text is not a match
  listeners.completed({ tabId: 7, url: "https://nottracker.example/x" });
  await listeners.updated(7, { status: "complete" });

  assert.deepEqual(JSON.parse(JSON.stringify(stored.net_7)), {
    tracker_count: 1,
    has_mixed_content: false,
    redirect_chain_length: 0,
    third_party_domains: ["tracker.example"],
  });

  // ── Test 3.1.5: redirect counting only counts top-level navigations ──
  // Reset for a new tab
  listeners.navigate({ tabId: 8, frameId: 0, url: "https://example.com" });

  // Top-level redirect (frameId === 0) — should be counted
  listeners.redirect({
    tabId: 8,
    frameId: 0,
    url: "https://example.com/redirect1",
  });
  // Sub-frame redirect (frameId !== 0) — should NOT be counted
  listeners.redirect({
    tabId: 8,
    frameId: 1,
    url: "https://example.com/iframe-redirect",
  });
  // Another top-level redirect — should be counted
  listeners.redirect({
    tabId: 8,
    frameId: 0,
    url: "https://example.com/redirect2",
  });

  await listeners.updated(8, { status: "complete" });

  assert.equal(
    stored.net_8.redirect_chain_length,
    2,
    "Should count only top-level redirects",
  );
}

run().then(() => console.log("network monitor check passed"));
