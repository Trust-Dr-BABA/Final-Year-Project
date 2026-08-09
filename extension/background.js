/**
 * background.js — MV3 Service Worker
 * Orchestrates all scanning: collects network/permission signals per tab,
 * calls the backend API, caches results, and updates the extension badge.
 */

import { analyzePage } from "./services/api_client.js";
import "./modules/network_monitor.js";
// import "./modules/permission_monitor.js";  // Sprint 2.6.3

// ── Extension lifecycle ────────────────────────────────────────────────────

// ── Tab navigation tracking ────────────────────────────────────────────────

/**
 * When a tab finishes loading, collect all cached signals and fire an analysis.
 */
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !tab.url || tab.url.startsWith("chrome://")) {
    return;
  }

  // Mark tab as "scanning"
  await chrome.storage.local.set({
    [tabId]: { status: "scanning", url: tab.url, timestamp: Date.now() },
  });

  // Update badge to indicate scanning
  chrome.action.setBadgeText({ text: "…", tabId });
  chrome.action.setBadgeBackgroundColor({ color: "#6b7280", tabId });

  try {
    // Retrieve network + permission signals collected during page load
    const stored = await chrome.storage.local.get([
      `net_${tabId}`,
      `perm_${tabId}`,
    ]);
    const networkSignals = stored[`net_${tabId}`] || null;
    const permissionSignals = stored[`perm_${tabId}`] || null;

    const result = await analyzePage(tab.url, networkSignals, permissionSignals);

    // Cache the full result
    await chrome.storage.local.set({
      [tabId]: { status: "done", url: tab.url, result, timestamp: Date.now() },
    });

    // Update badge based on verdict
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
        url: tab.url,
        error_message: "Could not reach analysis server. Check your connection.",
        timestamp: Date.now(),
      },
    });
    chrome.action.setBadgeText({ text: "✕", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#6b7280", tabId });
  }
});

// ── Message handler (from content_script and popup) ────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "PERMISSION_SIGNALS") {
    const tabId = sender.tab?.id;
    if (tabId) {
      chrome.storage.local.set({ [`perm_${tabId}`]: message.payload });
    }
  }

  if (message.type === "RETRY_SCAN") {
    const { tabId, url } = message.payload;
    chrome.tabs.get(tabId, (tab) => {
      if (tab) chrome.tabs.reload(tabId);
    });
  }

  // Always return false for non-async handlers
  return false;
});
