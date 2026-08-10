/**
 * network_monitor.js — Browser-level network signal collector
 * Listens to webRequest events for the current tab to extract:
 * - Tracker domain count
 * - Mixed content flag
 * - Redirect chain length
 *
 * Tracker rules are bundled with the extension so they are available offline.
 */

// ── Tracker domain list (populated in Phase 3) ────────────────────────────
let TRACKER_DOMAINS = new Set();

// Load the bundled EasyPrivacy list once when the service worker starts.
(async function loadTrackerDomains() {
  try {
    const response = await fetch(chrome.runtime.getURL("tracker_domains.json"));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    TRACKER_DOMAINS = new Set(await response.json());
    console.info(`[ESA] Loaded ${TRACKER_DOMAINS.size} tracker domains.`);
  } catch (err) {
    console.error("[ESA] Could not load tracker domains:", err);
  }
})();

/**
 * Resolve a request hostname to the tracker base domain it belongs to.
 * EasyPrivacy `||domain^` rules match subdomains too, so `ssl.google-analytics.com`
 * must match the `google-analytics.com` entry. Walks parent domains rather than
 * scanning the whole list, keeping this O(labels) on a per-request hot path.
 * @param {string} hostname
 * @returns {string|null} the matched base domain, or null if not a tracker
 */
function matchTrackerDomain(hostname) {
  let candidate = hostname;
  while (candidate) {
    if (TRACKER_DOMAINS.has(candidate)) return candidate;
    const dot = candidate.indexOf(".");
    if (dot === -1) return null;
    candidate = candidate.slice(dot + 1);
  }
  return null;
}

// Per-tab signal accumulators
const tabSignals = {};

// Reset the per-tab signal accumulator at the start of a new top-level navigation.
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

// Start a fresh signal accumulator whenever the top-level frame begins navigating.
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
  if (details.frameId !== 0) return; // Top-level frame only
  initTabSignals(details.tabId);
  tabSignals[details.tabId].top_level_url = details.url;
});

// ── Listen: redirect events ────────────────────────────────────────────────
// Count only top-level redirects (frameId === 0); sub-frame redirects would inflate the count.
chrome.webRequest.onBeforeRedirect.addListener(
  (details) => {
    if (details.tabId < 0) return;
    if (details.frameId !== 0) return; // Top-level frame only
    if (!tabSignals[details.tabId]) initTabSignals(details.tabId);
    tabSignals[details.tabId].redirect_chain_length += 1;
  },
  { urls: ["<all_urls>"] },
);

// ── Listen: completed requests ─────────────────────────────────────────────
// Tally tracker domains and mixed-content requests as they complete.
chrome.webRequest.onCompleted.addListener(
  (details) => {
    if (details.tabId < 0) return;
    if (!tabSignals[details.tabId]) return;

    const signals = tabSignals[details.tabId];
    let requestHostname;
    try {
      requestHostname = new URL(details.url).hostname;
    } catch {
      return;
    }

    // Count unique tracker *base* domains, so ssl.google-analytics.com and
    // www.google-analytics.com count once, not twice.
    const trackerDomain = matchTrackerDomain(requestHostname);
    if (trackerDomain) {
      signals.tracker_domains_seen.add(trackerDomain);
      signals.tracker_count = signals.tracker_domains_seen.size;
    }

    // Mixed content detection (Task 3.1.4)
    const topUrl = signals.top_level_url;
    if (
      topUrl &&
      topUrl.startsWith("https://") &&
      details.url.startsWith("http://")
    ) {
      signals.has_mixed_content = true;
    }
  },
  { urls: ["<all_urls>"] },
);

// ── Listen: tab navigation complete → freeze signals ──────────────────────

// Freeze the accumulated network signals to chrome.storage.local once the tab finishes loading.
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
});
