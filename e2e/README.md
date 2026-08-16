# End-to-end tests (Playwright)

Tests the Next.js dashboard against a real running backend + Postgres. Does not drive the Chrome
extension itself — see "What this suite does not cover" below.

## One-time setup

```bash
npm install                                    # from repo root — installs all workspaces, including e2e
npx playwright install --with-deps chromium --with-deps  # from e2e/, or: npm run test:e2e -- (see below)
```

## Running

The backend + Postgres must already be running — this suite does not start them (see
`playwright.config.ts` for why). Either:

```bash
docker compose -f docker/docker-compose.yml up -d      # from repo root
# or the host-run uvicorn command in the root README.md
```

Then, from the repo root:

```bash
npm run test:e2e        # headless, local settings (no retries, single worker default)
npm run test:e2e:ui     # Playwright's UI mode — step through tests, inspect the DOM live
npm run test:e2e:ci     # CI settings (2 retries, GitHub + HTML reporters) — what the CI workflow runs
```

The dashboard itself is started automatically by Playwright on port 3100 (not 3000, so it never
collides with a dev server you already have running) and torn down after the run.

### Environment overrides

Copy `e2e/.env.example` to `e2e/.env` if your backend isn't on `localhost:8000`, or if you want
`global-teardown`'s cleanup query to run against a non-default `DATABASE_URL`. See that file for
the three variables involved.

### Viewing a failure

```bash
npx playwright show-report    # from e2e/ — opens the HTML report for the last run
```

Every failed test gets a trace (`trace: on-first-retry`) and a screenshot attached to its report
entry — open the trace via the report's "View trace" link for a full timeline, network log, and
DOM snapshot at the point of failure, not just a stack trace.

## What this suite does not cover, and why

**The Chrome extension itself (popup, content scripts, background service worker, phishing
interstitial) is not driven through Playwright.** Reasons, concretely:

- MV3 service workers are not reliably observable through Playwright across versions the way a
  normal page is; the extension's own `background.js` orchestrates scanning through a service
  worker, which is exactly the layer this would need to drive.
- The popup lives at `chrome-extension://<dynamic-id>/popup/popup.html` — the id is assigned at
  load time unless pinned via a `key` in `manifest.json`, which this project doesn't currently do.
- This project has already tried and documented this exact class of problem: real-browser
  verification of the permission/interstitial flows was attempted via a different browser
  automation tool earlier in this project and was blocked outright (`chrome://extensions` and
  `file://` fixture URLs are both categorically inaccessible to that tooling) — see
  `LIMITATIONS.md` and `PROJECT_STATE.md`'s 2026-08-15 entries.
- The extension already has a deliberate, working test strategy for its own logic: a Node-based
  unit harness (`npm test` at the repo root — `network_monitor_test.js`,
  `permission_monitor_test.js`, `scam_content_scanner_test.js`) that loads each content script
  into a `vm` context and exercises it directly. That's the right tool for that layer; Playwright
  driving a real loaded extension would be solving the same problem again, less reliably.

If real end-to-end extension coverage is wanted later, the concrete next step is pinning the
extension's id (a `key` in `manifest.json`) and using
`browserType.launchPersistentContext` with `--load-extension`/`--disable-extensions-except` — this
is a real, larger scope decision, not a same-pass addition.

**The backend's own correctness (SQLi, IDOR, validation, etc.) is not re-tested here.** It already
has a `pytest` integration suite (`tests/integration/`) that's the right layer for that — this
suite only seeds through `/analyze` as a means of getting real data onto the dashboard, and asserts
on what the dashboard does with it.
