# Network Monitor Manual Test Plan

## Test 1 – CNN.com

URL:
https://cnn.com

Expected:

- tracker_count >= 5
- has_mixed_content = false
- redirect_chain_length >= 0
- third_party_domains contains Google Analytics, DoubleClick, etc.

Result:

[ ]

---

## Test 2 – Example.com

URL:
https://example.com

Expected:

- tracker_count = 0
- has_mixed_content = false
- redirect_chain_length = 0
- third_party_domains = []

Result:

[ ]

---

## Test 3 – PhishTank URL

URL:
(any active PhishTank sample)

Expected:

- redirect_chain_length >= 0
- tracker_count depends on page
- networkSignals logged in Service Worker console

Result:

[ ]