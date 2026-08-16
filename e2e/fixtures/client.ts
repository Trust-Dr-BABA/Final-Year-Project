import { test as base, expect } from "@playwright/test";
import crypto from "node:crypto";
import { CLIENT_ID_COOKIE } from "../../dashboard/lib/clientId";

/**
 * fixtures/client.ts — This app has no login (see e2e/README.md), so there is no session to fixture
 * around in the traditional sense. The closest real analog is `client_id`: a per-browser-install
 * identifier the extension generates once and the dashboard binds to a cookie via a redirect
 * (dashboard/proxy.ts) — every dashboard view is scoped to it. This fixture is that adaptation:
 * it establishes a known client_id's cookie directly (skipping the redirect flow, which has its
 * own dedicated test) so every other test doesn't have to repeat it, and gives each test a
 * `seedScan()` helper to create real data for that identity via the actual /analyze endpoint —
 * not a hand-inserted DB row, so tests exercise the same code path a real scan goes through.
 *
 * Every test gets its own client_id (`e2e-<worker>-<random>`), so tests never see each other's
 * data even when run in parallel — no shared fixture state, no cleanup-ordering dependency.
 */

const BACKEND_URL = process.env.E2E_BACKEND_URL || "http://localhost:8000";

export interface SeedScanOptions {
  url?: string;
  network_signals?: Record<string, unknown>;
  permission_signals?: Record<string, unknown>;
  scam_content_signals?: Record<string, unknown>;
}

export interface SeededScan {
  scan_id: string;
  verdict: string;
  risk_pct: number;
  confidence_pct: number;
}

type ClientFixtures = {
  clientId: string;
  seedScan: (options?: SeedScanOptions) => Promise<SeededScan>;
};

export const test = base.extend<ClientFixtures>({
  clientId: async ({ context }, use, testInfo) => {
    const clientId = `e2e-${testInfo.workerIndex}-${crypto.randomUUID()}`;
    const baseURL = new URL(testInfo.project.use.baseURL as string);
    await context.addCookies([
      {
        name: CLIENT_ID_COOKIE,
        value: clientId,
        domain: baseURL.hostname,
        path: "/",
      },
    ]);
    await use(clientId);
  },

  seedScan: async ({ clientId, request }, use) => {
    const seed = async (options: SeedScanOptions = {}): Promise<SeededScan> => {
      const response = await request.post(`${BACKEND_URL}/analyze`, {
        data: {
          url: options.url ?? `https://e2e-test.example/${crypto.randomUUID()}`,
          client_id: clientId,
          network_signals: options.network_signals,
          permission_signals: options.permission_signals,
          scam_content_signals: options.scam_content_signals,
        },
      });
      expect(response.ok(), `seedScan: POST /analyze failed with ${response.status()}`).toBeTruthy();
      return response.json();
    };
    await use(seed);
  },
});

export { expect };
