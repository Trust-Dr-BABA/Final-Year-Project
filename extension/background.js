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
    const stored = await chrome.storage.local.get([`net_${tabId}`, `perm_${tabId}`]);
    const networkSignals = stored[`net_${tabId}`] || null;
    const permissionSignals = stored[`perm_${tabId}`] || null;

    const result = await analyzePage(url, networkSignals, permissionSignals);

    await chrome.storage.local.set({
      [tabId]: { status: "done", url, result, timestamp: Date.now() },
    });

    if (result.verdict === "phishing") {
      chrome.action.setBadgeText({ text: "!", tabId });
      chrome.action.setBadgeBackgroundColor({ color: "#ef4444", tabId });
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

// When a tab finishes loading, mark it as scanning and fire the initial analysis.
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !tab.url || tab.url.startsWith("chrome://")) {
    return;
  }

  await chrome.storage.local.set({
    [tabId]: { status: "scanning", url: tab.url, timestamp: Date.now() },
  });

  await runAnalysis(tabId, tab.url);
});

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

        const cached = (await chrome.storage.local.get([String(tabId)]))[String(tabId)];
        if (cached?.status !== "done") return; // still scanning, or errored — the next run will pick this up

        const tab = await chrome.tabs.get(tabId).catch(() => null);
        if (tab && tab.url === cached.url) {
          await runAnalysis(tabId, tab.url);
        }
      })();
    }
  }

  if (message.type === "RETRY_SCAN") {
    const { tabId, url } = message.payload;
    chrome.tabs.get(tabId, (tab) => {
      if (tab) chrome.tabs.reload(tabId);
    });
  }

  // Always return false — nothing here sends a response.
  return false;
});
