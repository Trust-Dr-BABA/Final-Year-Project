/**
 * popup.js — Extension popup controller
 * Reads the cached analysis result for the current tab and renders
 * the correct state: scanning / safe / suspicious / phishing / error.
 */

import ESA_CONFIG from "../config.js";

// ── DOM helpers ────────────────────────────────────────────────────────────

// Hide every popup state panel except the one matching stateId.
function showState(stateId) {
  document.querySelectorAll(".state").forEach((el) => el.classList.add("hidden"));
  document.getElementById(stateId)?.classList.remove("hidden");
}

// Set an element's text content by id, no-op if the element isn't found.
function setTextById(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// Render the SHAP/heuristic top_reasons list as <li> items under listId.
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

// Flip data-theme on <html> and persist the choice. theme_init.js applies it on next open.
function initThemeToggle() {
  document.getElementById("btn-theme-toggle")?.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("esa-theme", next);
  });
}

// ── Main render ────────────────────────────────────────────────────────────

// Load the current tab's cached scan result from storage and render the matching popup state.
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

  // Status is "done". risk_pct and confidence_pct are separate quantities (ADR-015): risk_pct is
  // how phishing-like the page is, confidence_pct is how decisive the model is either way. Both
  // are read directly from the response — no arithmetic here, which is exactly what ADR-015 was
  // written to make possible (this popup used to compute `100 - confidence` for the safe case).
  const result = entry.result;
  const riskPct = result.risk_pct ?? Math.round((result.risk_score ?? 0) * 100);
  const confidencePct = result.confidence_pct ?? Math.max(riskPct, 100 - riskPct);
  const reasons = result.top_reasons || [];

  if (result.verdict === "phishing") {
    showState("state-phishing");
    setTextById("phishing-confidence", `${confidencePct}% confident this is phishing`);
    renderReasons("phishing-reasons", reasons);

  } else if (result.verdict === "suspicious") {
    showState("state-suspicious");
    setTextById("suspicious-confidence", `${riskPct}% risk score`);
    renderReasons("suspicious-reasons", reasons);

  } else {
    // legitimate
    showState("state-safe");
    setTextById("safe-confidence", `${confidencePct}% confident this page is safe`);
  }

  // Dashboard link (always visible in footer)
  document.getElementById("btn-dashboard")?.addEventListener("click", () => {
    chrome.tabs.create({ url: ESA_CONFIG.DASHBOARD_URL });
  });
}

// Run on popup open
initThemeToggle();
render();
