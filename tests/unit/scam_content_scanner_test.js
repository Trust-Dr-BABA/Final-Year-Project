// scam_content_scanner_test.js — Tests modules/scam_content_scanner.js's phrase matching and its
// message contract with background.js (SCAM_CONTENT_SIGNALS).

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

// Runs the content script against a fake page body (and optionally a list of fake <input>
// attribute sets), returns the single message it sent.
function scanPage(bodyText, inputs = []) {
  const sentMessages = [];
  const globals = {
    document: {
      body: { innerText: bodyText },
      querySelectorAll: (selector) => {
        if (selector !== "input") return [];
        return inputs;
      },
    },
    console,
    chrome: {
      runtime: {
        sendMessage: (msg) => sentMessages.push(msg),
      },
    },
    // The real script delays its scan behind setTimeout to let SPA content render; the test runs
    // it immediately rather than waiting on the real 2s delay.
    setTimeout: (fn) => fn(),
  };
  vm.createContext(globals);
  vm.runInContext(
    fs.readFileSync("extension/modules/scam_content_scanner.js", "utf8"),
    globals,
  );
  return sentMessages.at(-1);
}

async function run() {
  // ── Ordinary page: no scam phrases, no false positives from single risky-sounding words ──
  const clean = scanPage(
    "Welcome to our store. Enter your password to log in. We accept all major payment methods.",
  );
  assert.equal(
    clean.type,
    "SCAM_CONTENT_SIGNALS",
    "must send the SCAM_CONTENT_SIGNALS message type",
  );
  // "password" and "payment" alone appear on almost any commercial site — only full phrase
  // matches should count, and this text doesn't contain any of the listed multi-word phrases.
  assert.equal(clean.payload.scam_keyword_hits, 0);
  // JSON round-trip strips the vm context's realm-specific Array prototype, which otherwise fails
  // a structural deepEqual even when the content is identical (same fix as permission_monitor_test.js).
  assert.deepEqual(JSON.parse(JSON.stringify(clean.payload.matched_phrases)), []);

  // ── Scam page: multiple distinct phrase matches ──────────────────────────────────────────
  const scammy = scanPage(
    "WARNING: your account has been suspended. Verify your identity immediately and " +
      "confirm your card number to restore access. Act now or your account will be deleted.",
  );
  assert.ok(scammy.payload.scam_keyword_hits >= 3, "expected at least 3 distinct phrase matches");
  assert.ok(scammy.payload.matched_phrases.includes("your account has been suspended"));
  assert.ok(scammy.payload.matched_phrases.includes("verify your identity immediately"));
  assert.ok(scammy.payload.matched_phrases.includes("confirm your card number"));

  // ── Case-insensitivity ────────────────────────────────────────────────────────────────────
  const shouting = scanPage("YOUR ACCOUNT WILL BE SUSPENDED unless you act now.");
  assert.ok(shouting.payload.matched_phrases.includes("your account will be suspended"));

  // ── A phrase repeated many times still counts once (distinct phrases, not raw occurrences) ──
  const repeated = scanPage(
    "gift card codes gift card codes gift card codes gift card codes gift card codes",
  );
  assert.equal(repeated.payload.scam_keyword_hits, 1);

  // ── Sensitive fields: an ordinary login page (password only) is not itself a signal ──────────
  const login = scanPage("Sign in to your account.", [{ type: "password", name: "pwd" }]);
  assert.equal(login.payload.sensitive_field_count, 1);
  assert.deepEqual(JSON.parse(JSON.stringify(login.payload.sensitive_field_categories)), ["password"]);

  // ── Sensitive fields: multiple high-value categories together is the real signal ─────────────
  const harvester = scanPage("Verify your details to continue.", [
    { type: "password", name: "pwd" },
    { type: "text", name: "cc-number", autocomplete: "cc-number" },
    { type: "text", name: "cvv" },
    { type: "text", name: "ssn_field" },
  ]);
  assert.equal(harvester.payload.sensitive_field_count, 4);
  const categories = JSON.parse(JSON.stringify(harvester.payload.sensitive_field_categories));
  assert.ok(categories.includes("password"));
  assert.ok(categories.includes("card_number"));
  assert.ok(categories.includes("cvv"));
  assert.ok(categories.includes("ssn"));

  // ── Sensitive fields: repeated fields of the same category count once (distinct, not raw) ────
  const repeatedFields = scanPage("", [
    { type: "password", name: "pwd" },
    { type: "password", name: "pwd_confirm" },
  ]);
  assert.equal(repeatedFields.payload.sensitive_field_count, 1);

  // ── No input fields at all ────────────────────────────────────────────────────────────────────
  const noFields = scanPage("Just an article page with no forms.");
  assert.equal(noFields.payload.sensitive_field_count, 0);
}

run().then(() => console.log("scam content scanner check passed"));
