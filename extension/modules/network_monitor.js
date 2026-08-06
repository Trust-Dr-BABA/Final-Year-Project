/**
 * network_monitor.js — Browser-level network signal collector
 * Listens to webRequest events for the current tab to extract:
 * - Tracker domain count
 * - Mixed content flag
 * - Redirect chain length
 *
 * TODO (Phase 3, Task 3.1.2): Load tracker_domains.json and implement full counting logic.
 */

// ── Tracker domain list (populated in Phase 3) ────────────────────────────
// Will be loaded from shared/tracker_domains.json
let TRACKER_DOMAINS = new Set();
// Load tracker domains once when the extension starts
(async function loadTrackerDomains() {
    try {
        const url = chrome.runtime.getURL("shared/tracker_domains.json");
        console.log("[ESA] Loading tracker list from:", url);

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const domains = await response.json();
        TRACKER_DOMAINS = new Set(domains);

        console.log(`[ESA] Loaded ${TRACKER_DOMAINS.size} tracker domains.`);
    } catch (err) {
        console.error("[ESA] Failed to load tracker domains:", err);
    }
})();

// Per-tab signal accumulators
const tabSignals = {};

/**
 * Initialize signal tracking for a new tab navigation.
 * @param {number} tabId
 */

function initTabSignals(tabId) {
  tabSignals[tabId] = {
    tracker_count: 0,
    tracker_domains_seen: new Set(),
    has_mixed_content: false,
    redirect_chain_length: 0,
    top_level_url: null,
  };
}

// ── Listen: tab navigation start ──────────────────────────────────────────

chrome.webNavigation.onBeforeNavigate.addListener((details) => {
  if (details.frameId !== 0) return; // Top-level frame only
  initTabSignals(details.tabId);
  tabSignals[details.tabId].top_level_url = details.url;
});

// ── Listen: redirect events ────────────────────────────────────────────────

chrome.webRequest.onBeforeRedirect.addListener(
  (details) => {
    if (details.tabId < 0) return;
    if (!tabSignals[details.tabId]) initTabSignals(details.tabId);
    tabSignals[details.tabId].redirect_chain_length += 1;
  },
  { urls: ["<all_urls>"] }
);

// ── Listen: completed requests ─────────────────────────────────────────────

chrome.webRequest.onCompleted.addListener(
  (details) => {
    if (details.tabId < 0) return;
    if (!tabSignals[details.tabId]) return;

    const signals = tabSignals[details.tabId];
    const requestHostname = new URL(details.url).hostname;
    // Check if request belongs to a known tracker
const isTracker = [...TRACKER_DOMAINS].some(domain =>
    requestHostname === domain ||
    requestHostname.endsWith("." + domain)
);

if (isTracker) {
    signals.tracker_domains_seen.add(requestHostname);
    signals.tracker_count = signals.tracker_domains_seen.size;
}

    // TODO (Task 3.1.2): Check if requestHostname is in TRACKER_DOMAINS
    // if (TRACKER_DOMAINS.has(requestHostname)) {
    //   signals.tracker_domains_seen.add(requestHostname);
    //   signals.tracker_count = signals.tracker_domains_seen.size;
    // }

    // Mixed content detection (Task 3.1.4)
    const topUrl = signals.top_level_url;
    if (topUrl && topUrl.startsWith("https://") && details.url.startsWith("http://")) {
      signals.has_mixed_content = true;
    }
  },
  { urls: ["<all_urls>"] }
);

// ── Listen: tab navigation complete → freeze signals ──────────────────────

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
  if (changeInfo.status !== "complete") return;
  if (!tabSignals[tabId]) return;

  const signals = tabSignals[tabId];
  const networkSignals = {
    tracker_count: signals.tracker_count,
    has_mixed_content: signals.has_mixed_content,
    redirect_chain_length: signals.redirect_chain_length,
    third_party_domains: [...signals.tracker_domains_seen],
  };

  // Store for background.js to pick up
  await chrome.storage.local.set({ [`net_${tabId}`]: networkSignals });
  console.log(`[ESA] Network signals for tab ${tabId}:`, networkSignals);
});
