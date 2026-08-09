/**
 * popup.js — Extension popup controller
 * Reads the cached analysis result for the current tab and renders
 * the correct state: scanning / safe / suspicious / phishing / error.
 */

import ESA_CONFIG from "../config.js";

// ── DOM helpers ────────────────────────────────────────────────────────────

function showState(stateId) {
  document.querySelectorAll(".state").forEach((el) => el.classList.add("hidden"));
  document.getElementById(stateId)?.classList.remove("hidden");
}

function setTextById(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function renderReasons(listId, reasons) {
  const list = document.getElementById(listId);
  if (!list) return;
  list.innerHTML = "";
  (reasons || []).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = r.human_readable || r.feature;
    list.appendChild(li);
  });
}

// ── Main render ────────────────────────────────────────────────────────────

async function render() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  const stored = await chrome.storage.local.get([String(tab.id)]);
  const entry = stored[String(tab.id)];

  if (!entry || entry.status === "scanning") {
    showState("state-scanning");
    return;
  }

  if (entry.status === "error") {
    showState("state-error");
    setTextById("error-message", entry.error_message || "Unknown error occurred.");

    document.getElementById("btn-retry")?.addEventListener("click", () => {
      chrome.runtime.sendMessage({ type: "RETRY_SCAN", payload: { tabId: tab.id, url: tab.url } });
      showState("state-scanning");
    });
    return;
  }

  // Status is "done"
  const result = entry.result;
  const confidence = result.confidence_pct ?? Math.round((result.risk_score ?? 0) * 100);
  const reasons = result.top_reasons || [];

  if (result.verdict === "phishing") {
    showState("state-phishing");
    setTextById("phishing-confidence", `${confidence}% confident this is phishing`);
    renderReasons("phishing-reasons", reasons);

  } else if (result.verdict === "suspicious") {
    showState("state-suspicious");
    setTextById("suspicious-confidence", `${confidence}% risk score`);
    renderReasons("suspicious-reasons", reasons);

  } else {
    // legitimate
    showState("state-safe");
    setTextById("safe-confidence", `${100 - confidence}% confident this page is safe`);
  }

  // Dashboard link (always visible in footer)
  document.getElementById("btn-dashboard")?.addEventListener("click", () => {
    chrome.tabs.create({ url: ESA_CONFIG.DASHBOARD_URL });
  });
}

// Run on popup open
render();
