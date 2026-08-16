/**
 * scam_content_scanner.js — Isolated-world content script.
 * Scans the page's own rendered text for scam-indicator phrase combinations (urgent account,
 * payment, or credential requests) and reports a distinct-phrase count to background.js. Runs in
 * the default isolated world — unlike modules/permission_monitor.js, reading the DOM's rendered
 * text doesn't require intercepting the page's own script calls, so no MAIN-world injection is
 * needed here.
 */

(function () {
  "use strict";

  // Multi-word phrases only, never single words ("money", "password" alone appear constantly on
  // ordinary banking/e-commerce pages). Each phrase combines urgency with an account, payment, or
  // credential action — the combination is what narrows this toward scam pages specifically.
  const SCAM_PHRASES = [
    "verify your password",
    "confirm your password",
    "enter your password to continue",
    "your account has been suspended",
    "your account will be suspended",
    "your account will be locked",
    "verify your identity immediately",
    "confirm your identity immediately",
    "unusual activity detected",
    "suspicious activity detected",
    "click here to verify",
    "update your payment information",
    "confirm your card number",
    "enter your card number",
    "enter your bank details",
    "enter your social security number",
    "wire transfer required",
    "send payment via gift card",
    "gift card codes",
    "you have won",
    "claim your prize",
    "urgent payment required",
    "pay a small fee",
    "processing fee required",
    "act now or your account",
    "verify your account now",
  ];

  // Category -> regex tested against each <input>'s name/id/autocomplete attributes (password is
  // checked separately, via input.type, below). A single password field is extremely common on
  // ordinary sites (any login page has one) and is deliberately NOT a signal on its own — what's
  // unusual is a page asking for *multiple* high-value credential categories together (password +
  // card number + SSN, say), which ordinary login forms don't do and credential-harvesting scam
  // pages often do.
  const SENSITIVE_FIELD_PATTERNS = {
    card_number: /cc-?number|card-?number|cardnum|ccnum/,
    cvv: /cvv|cvc|security-?code/,
    ssn: /ssn|social-?security/,
    bank_account: /routing-?number|account-?number|iban/,
  };

  // Wait for the page's own JS (SPA frameworks etc.) to finish rendering content before scanning —
  // a scan immediately at document_idle would miss most single-page-app content entirely.
  const SCAN_DELAY_MS = 2000;

  function scanPageText() {
    const text = (document.body?.innerText || "").toLowerCase();
    const matched = SCAM_PHRASES.filter((phrase) => text.includes(phrase));

    const foundCategories = new Set();
    document.querySelectorAll("input").forEach((input) => {
      if ((input.type || "").toLowerCase() === "password") foundCategories.add("password");

      const haystack = [input.name, input.id, input.autocomplete]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      for (const [category, pattern] of Object.entries(SENSITIVE_FIELD_PATTERNS)) {
        if (pattern.test(haystack)) foundCategories.add(category);
      }
    });

    chrome.runtime.sendMessage({
      type: "SCAM_CONTENT_SIGNALS",
      payload: {
        scam_keyword_hits: matched.length,
        matched_phrases: matched,
        sensitive_field_count: foundCategories.size,
        sensitive_field_categories: [...foundCategories],
      },
    });
  }

  setTimeout(scanPageText, SCAN_DELAY_MS);
})();
