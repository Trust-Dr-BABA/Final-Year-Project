/**
 * interstitial.js — Full-page warning overlay for the phishing verdict tier (Sprint 3.2).
 * Isolated world (default) — this only needs chrome.runtime to receive the trigger from
 * background.js and never touches the page's own script environment, unlike permission_monitor.js.
 *
 * Rendered inside a closed Shadow DOM so a page actively trying to look legitimate (or a page
 * whose own CSS happens to collide with ours) can neither style-leak into the warning nor have
 * its own styles bleed in — the warning is meant to be unambiguously trustworthy chrome, not
 * something the page under assessment has any influence over.
 */

(function () {
  "use strict";

  const HOST_ID = "esa-interstitial-host";

  // True if the overlay is already showing for this document — never inject twice.
  function alreadyShown() {
    return !!document.getElementById(HOST_ID);
  }

  // HTML-escape attacker-influenced text (the assessed URL) before it reaches innerHTML.
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // Build the full-viewport scrim + warning card as a Shadow DOM host element.
  function buildOverlay(payload) {
    const host = document.createElement("div");
    host.id = HOST_ID;
    host.style.cssText = "position:fixed;inset:0;z-index:2147483647;";
    const shadow = host.attachShadow({ mode: "closed" });

    const style = document.createElement("style");
    style.textContent = `
      :host { all: initial; }
      .scrim {
        position: fixed; inset: 0;
        background: rgba(10, 10, 8, 0.72);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        display: flex; align-items: center; justify-content: center;
        font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
      }
      .card {
        width: 380px; max-width: 90vw;
        background: #151512; color: #f2f0ea;
        border: 1px solid #f87171; border-radius: 4px;
        padding: 24px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
      }
      .icon {
        width: 40px; height: 40px;
        border: 1px solid #f87171; color: #f87171; border-radius: 4px;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; font-weight: 700;
        margin-bottom: 14px;
      }
      h1 { font-size: 16px; font-weight: 700; margin: 0 0 6px; letter-spacing: -0.01em; }
      .risk {
        font-family: ui-monospace, "SF Mono", Consolas, monospace;
        font-size: 12px; color: #f87171; margin: 0 0 12px;
      }
      .url {
        font-family: ui-monospace, "SF Mono", Consolas, monospace;
        font-size: 11px; color: #918e83; word-break: break-all; margin: 0 0 16px;
      }
      .reasons { list-style: none; padding: 0; margin: 0 0 20px; display: flex; flex-direction: column; gap: 6px; }
      .reasons li {
        font-size: 12px; line-height: 1.4; color: #f2f0ea;
        background: #0c0c0a; border: 1px solid #2c2b26; border-radius: 3px; padding: 8px 10px;
      }
      .actions { display: flex; gap: 10px; }
      button {
        flex: 1; font-family: inherit; font-size: 12px; font-weight: 600;
        padding: 9px 12px; border-radius: 3px; cursor: pointer; border: 1px solid #2c2b26;
      }
      .btn-leave { background: #f87171; color: #1a1917; border-color: #f87171; }
      .btn-leave:hover { opacity: 0.85; }
      .btn-continue { background: transparent; color: #918e83; }
      .btn-continue:hover { color: #f2f0ea; border-color: #918e83; }
    `;

    const wrap = document.createElement("div");
    wrap.className = "scrim";
    wrap.innerHTML = `
      <div class="card">
        <div class="icon">✕</div>
        <h1>Phishing Detected</h1>
        <p class="risk">${payload.confidencePct}% confident this is phishing</p>
        <p class="url">${escapeHtml(payload.url)}</p>
        <ul class="reasons"></ul>
        <div class="actions">
          <button class="btn-leave" type="button">Leave this page</button>
          <button class="btn-continue" type="button">I understand the risks, continue</button>
        </div>
      </div>
    `;

    const list = wrap.querySelector(".reasons");
    (payload.reasons || []).slice(0, 3).forEach((reason) => {
      const li = document.createElement("li");
      li.textContent = reason.human_readable || reason.feature;
      list.appendChild(li);
    });

    wrap.querySelector(".btn-leave").addEventListener("click", () => {
      chrome.runtime.sendMessage({ type: "INTERSTITIAL_LEAVE" });
    });
    // Dismiss for this document only — nothing is persisted, so a fresh navigation to the same
    // URL re-triggers the warning. A remembered bypass would be a durable attack surface.
    wrap.querySelector(".btn-continue").addEventListener("click", () => {
      host.remove();
    });

    shadow.appendChild(style);
    shadow.appendChild(wrap);
    return host;
  }

  chrome.runtime.onMessage.addListener((message) => {
    if (message.type !== "SHOW_INTERSTITIAL") return;
    if (alreadyShown()) return;
    document.documentElement.appendChild(buildOverlay(message.payload));
  });
})();
