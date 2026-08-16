/**
 * background.js — MV3 Service Worker
 * Orchestrates all scanning: collects network/permission signals per tab,
 * calls the backend API, caches results, and updates the extension badge.
 */

import { analyzePage } from "./services/api_client.js";
import "./modules/network_monitor.js";

// ── Analysis ─────────────────────────────────────────────────────────────────

// Run (or re-run) analysis for a tab using whatever network/permission signals are stored now,
// cache the result, and update the badge. Shared by the initial load-complete trigger and the
// permission-signal-arrived re-trigger (D8 fix) so both paths behave identically.
async function runAnalysis(tabId, url) {
  chrome.action.setBadgeText({ text: "…", tabId });
  chrome.action.setBadgeBackgroundColor({ color: "#6b7280", tabId });

  try {
    const stored = await chrome.storage.local.get([`net_${tabId}`, `perm_${tabId}`, `scam_${tabId}`]);
    const networkSignals = stored[`net_${tabId}`] || null;
    const permissionSignals = stored[`perm_${tabId}`] || null;
    const scamContentSignals = stored[`scam_${tabId}`] || null;

    const result = await analyzePage(url, networkSignals, permissionSignals, scamContentSignals);

    await chrome.storage.local.set({
      [tabId]: { status: "done", url, result, timestamp: Date.now() },
    });

    if (result.verdict === "phishing") {
      chrome.action.setBadgeText({ text: "!", tabId });
      chrome.action.setBadgeBackgroundColor({ color: "#ef4444", tabId });
      // Gated to the phishing tier only (score > 0.70), never suspicious (Sprint 3.2) — the
      // threshold lives once, in the backend's verdict label, rather than being duplicated here.
      chrome.tabs.sendMessage(tabId, {
        type: "SHOW_INTERSTITIAL",
        payload: { url, confidencePct: result.confidence_pct, reasons: result.top_reasons },
      }).catch(() => {}); // the content script may not be injectable on this page (e.g. chrome://); non-fatal
    } else if (result.verdict === "suspicious") {
      chrome.action.setBadgeText({ text: "?", tabId });
      chrome.action.setBadgeBackgroundColor({ color: "#f59e0b", tabId });
    } else {
      chrome.action.setBadgeText({ text: "", tabId });
    }
  } catch (err) {
    console.error("[ESA] Analysis failed:", err.message);
    await chrome.storage.local.set({
      [tabId]: {
        status: "error",
        url,
        error_message: "Could not reach analysis server. Check your connection.",
        timestamp: Date.now(),
      },
    });
    chrome.action.setBadgeText({ text: "✕", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#6b7280", tabId });
  }
}

// ── Tab navigation tracking ────────────────────────────────────────────────

// True for localhost and RFC1918/link-local addresses — no public phishing/legitimate corpus
// contains these, so the model has zero training signal for them and a verdict would be
// meaningless. Flagged as its own distinct state rather than silently skipped, since an
// unexpected navigation to a local address is itself worth the user noticing.
function isLocalOrPrivateHost(hostname) {
  if (!hostname) return false;
  const host = hostname.toLowerCase();
  if (host === "localhost" || host.endsWith(".localhost")) return true;
  if (host === "127.0.0.1" || host.startsWith("127.")) return true;
  if (host === "::1" || host === "[::1]") return true;
  if (/^10\./.test(host)) return true;
  if (/^172\.(1[6-9]|2\d|3[01])\./.test(host)) return true;
  if (/^192\.168\./.test(host)) return true;
  if (/^169\.254\./.test(host)) return true; // link-local
  return false;
}

// Chrome can fire status:"complete" more than once for a single real navigation — observed
// directly as pairs of duplicate scan records for the same tab+URL less than ~2s apart. A short
// recency window (not an unconditional same-URL check) tells that apart from a genuine revisit or
// refresh of the same URL later on, which must still be re-analyzed rather than silently skipped.
const DUPLICATE_COMPLETE_WINDOW_MS = 3000;

// When a tab finishes loading, mark it as scanning and fire the initial analysis — unless it's a
// local/private address, which skips the model entirely and shows a dedicated notice instead.
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !tab.url || tab.url.startsWith("chrome://")) {
    return;
  }

  const existing = (await chrome.storage.local.get([String(tabId)]))[String(tabId)];
  if (
    existing &&
    existing.url === tab.url &&
    Date.now() - existing.timestamp < DUPLICATE_COMPLETE_WINDOW_MS
  ) {
    return;
  }

  let hostname = "";
  try {
    hostname = new URL(tab.url).hostname;
  } catch {
    // malformed URL — fall through to the normal analysis path, which will surface its own error
  }

  if (isLocalOrPrivateHost(hostname)) {
    await chrome.storage.local.set({
      [tabId]: { status: "local", url: tab.url, timestamp: Date.now() },
    });
    chrome.action.setBadgeText({ text: "L", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#a3540c", tabId });
    return;
  }

  await chrome.storage.local.set({
    [tabId]: { status: "scanning", url: tab.url, timestamp: Date.now() },
  });

  await runAnalysis(tabId, tab.url);
});

// Re-run analysis for a tab if its most recent scan is done and it's still on the same URL —
// shared tail for both re-trigger paths below (permission signals, scam content signals), which
// differ only in what decides whether a re-trigger is warranted at all; that decision is made by
// the caller before this runs.
async function maybeRetriggerAnalysis(tabId) {
  const cached = (await chrome.storage.local.get([String(tabId)]))[String(tabId)];
  if (cached?.status !== "done") return; // still scanning, or errored — the next run will pick this up

  const tab = await chrome.tabs.get(tabId).catch(() => null);
  if (tab && tab.url === cached.url) {
    await runAnalysis(tabId, tab.url);
  }
}

// ── Message handler (from content_script and popup) ────────────────────────

// Route messages from content_script.js (permission signals) and the popup (retry requests).
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "PERMISSION_SIGNALS") {
    const tabId = sender.tab?.id;
    if (tabId) {
      // Permission signals routinely arrive after the initial analysis has already completed —
      // notification/geolocation/camera calls can fire seconds into a page's life, well after
      // tabs.onUpdated reports "complete" (D8). Rather than delaying every analysis to wait for
      // signals that usually never come, re-run analysis only when a genuinely new flag appears.
      (async () => {
        const key = `perm_${tabId}`;
        const previous = (await chrome.storage.local.get([key]))[key];
        const previousFlags = new Set(previous?.rule_flags || []);
        const newFlags = message.payload.rule_flags || [];
        const hasNewFlag = newFlags.some((flag) => !previousFlags.has(flag));

        await chrome.storage.local.set({ [key]: message.payload });

        if (!hasNewFlag) return;
        await maybeRetriggerAnalysis(tabId);
      })();
    }
  }

  if (message.type === "SCAM_CONTENT_SIGNALS") {
    const tabId = sender.tab?.id;
    if (tabId) {
      // Sent exactly once per page, 2s after document_idle (scam_content_scanner.js). Unlike the
      // permission-signal path, there's no "previous" state to diff against — but re-triggering
      // unconditionally meant *every* page got analyzed twice, since the scanner sends this
      // message even when it found nothing (the overwhelming majority of pages). Only worth a
      // second analysis when something was actually found — the whole point of the re-trigger is
      // to let a newly-discovered signal reach the score, not to re-run an identical analysis.
      (async () => {
        await chrome.storage.local.set({ [`scam_${tabId}`]: message.payload });

        const hasSignal =
          (message.payload.scam_keyword_hits || 0) > 0 ||
          (message.payload.sensitive_field_count || 0) > 0;
        if (!hasSignal) return;
        await maybeRetriggerAnalysis(tabId);
      })();
    }
  }

  if (message.type === "RETRY_SCAN") {
    const { tabId, url } = message.payload;
    chrome.tabs.get(tabId, (tab) => {
      if (tab) chrome.tabs.reload(tabId);
    });
  }

  if (message.type === "INTERSTITIAL_LEAVE") {
    const tabId = sender.tab?.id;
    if (tabId) chrome.tabs.remove(tabId);
  }

  // Always return false — nothing here sends a response.
  return false;
});
