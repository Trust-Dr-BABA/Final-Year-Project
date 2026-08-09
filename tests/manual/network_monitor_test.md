# Manual Test Plan — Network Monitor Module (Task 3.1)

> **Purpose:** Verify that `extension/modules/network_monitor.js` correctly collects
> tracker count, mixed-content flag, and redirect chain length for real web pages.

## Prerequisites

1. Chrome extension loaded in developer mode (`chrome://extensions` → "Load unpacked" → `extension/`)
2. Service worker console open (`chrome://extensions` → "Service Worker" link)
3. DevTools console open for the page being tested

## Test Cases

### Test 1: CNN.com — High Tracker Count

| Field                                | Value                                         |
| ------------------------------------ | --------------------------------------------- |
| **URL**                              | `https://www.cnn.com`                         |
| **Expected `tracker_count`**         | ≥ 5                                           |
| **Expected `has_mixed_content`**     | `false` (CNN serves all resources over HTTPS) |
| **Expected `redirect_chain_length`** | 0–2 (minor redirects for A/B testing)         |
| **Expected `third_party_domains`**   | Non-empty array of tracker hostnames          |

**Steps:**

1. Navigate to `https://www.cnn.com`
2. Wait for the page to fully load (spinner stops)
3. Open the service worker console
4. Look for the log: `[ESA] Network signals for tab <id>:`
5. Verify `tracker_count` ≥ 5

**Pass Criteria:** `tracker_count` ≥ 5, `has_mixed_content` is `false`.

---

### Test 2: example.com — Zero Trackers

| Field                                | Value                 |
| ------------------------------------ | --------------------- |
| **URL**                              | `https://example.com` |
| **Expected `tracker_count`**         | 0                     |
| **Expected `has_mixed_content`**     | `false`               |
| **Expected `redirect_chain_length`** | 0                     |
| **Expected `third_party_domains`**   | `[]` (empty array)    |

**Steps:**

1. Navigate to `https://example.com`
2. Wait for the page to fully load
3. Check the service worker console for the network signals log
4. Verify `tracker_count` is 0

**Pass Criteria:** `tracker_count` = 0, `third_party_domains` is empty.

---

### Test 3: PhishTank URL — Redirect Chain

| Field                                | Value                                                                   |
| ------------------------------------ | ----------------------------------------------------------------------- |
| **URL**                              | A known PhishTank phishing URL (e.g., from `ml/data/raw/phishtank.csv`) |
| **Expected `redirect_chain_length`** | ≥ 1 (phishing pages often chain redirects)                              |
| **Expected `tracker_count`**         | May be 0 or low (phishing pages are minimal)                            |
| **Expected `has_mixed_content`**     | May be `true` (phishing pages often serve HTTP resources)               |

**Steps:**

1. Pick a phishing URL from `ml/data/raw/phishtank.csv`
2. Navigate to it in Chrome
3. Check the service worker console for the network signals log
4. Verify `redirect_chain_length` ≥ 1

**Pass Criteria:** `redirect_chain_length` ≥ 1, signals are logged.

---

### Test 4: Mixed Content Detection

| Field                            | Value                                             |
| -------------------------------- | ------------------------------------------------- |
| **URL**                          | A page that loads HTTP resources on an HTTPS page |
| **Expected `has_mixed_content`** | `true`                                            |

**Steps:**

1. Navigate to a page known to serve mixed content (e.g., a test page with `<img src="http://...">`)
2. Check the service worker console for the network signals log
3. Verify `has_mixed_content` is `true`

**Pass Criteria:** `has_mixed_content` = `true`.

---

## Verification Checklist

- [ ] `networkSignals` is logged to the service worker console on every page navigation
- [ ] `tracker_count` is correct for CNN.com (≥ 5)
- [ ] `tracker_count` is 0 for example.com
- [ ] `redirect_chain_length` only counts top-level navigation redirects (frameId === 0)
- [ ] `has_mixed_content` is correctly flagged on a known HTTP-resource page
- [ ] `third_party_domains` array contains the correct tracker hostnames
