import { defineConfig, devices } from "@playwright/test";

/**
 * playwright.config.ts — E2E config for the dashboard (the browser-facing surface of this app).
 *
 * The Chrome extension itself is deliberately NOT driven through this suite — see
 * e2e/README.md's "What this suite does not cover" section for why. The backend + Postgres are
 * treated as an already-running external dependency (globalSetup health-checks it) rather than
 * something Playwright spins up itself, matching how this project already runs its stack
 * (`docker compose up` or a host-run `uvicorn` process) — duplicating that inside test config
 * would be a second, divergent way to start the same services.
 */

const DASHBOARD_PORT = 3100; // deliberately not 3000, so this suite never collides with a dev server you already have running
const BASE_URL = process.env.E2E_BASE_URL || `http://localhost:${DASHBOARD_PORT}`;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI, // a stray .only must fail CI, not silently skip the rest of the suite
  retries: process.env.CI ? 2 : 0, // local failures should be investigated immediately, not retried away
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [["github"], ["html", { open: "never" }]]
    : [["list"], ["html", { open: "never" }]],
  globalSetup: require.resolve("./support/global-setup.ts"),
  globalTeardown: require.resolve("./support/global-teardown.ts"),

  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry", // full trace only when a test actually failed once — cheap on the happy path, informative on failure
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  // Chromium only, deliberately: the product itself (the browser extension) is Chrome/Chromium-only
  // by construction (chrome.* APIs), so cross-browser coverage of the dashboard wouldn't reflect how
  // any real user actually reaches it — the extension's "Open Dashboard" link always opens Chromium.
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Playwright starts and owns the dashboard's dev server for the duration of the run — this is
  // the one service cheap and fast enough to manage as test infra rather than an external
  // dependency. `reuseExistingServer` locally means a `npm run dev:dashboard` you already have
  // running is left alone; CI always starts fresh.
  webServer: {
    command: `npx next dev -p ${DASHBOARD_PORT}`,
    cwd: "../dashboard",
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: {
      NEXT_PUBLIC_BACKEND_URL: process.env.E2E_BACKEND_URL || "http://localhost:8000",
    },
  },
});
