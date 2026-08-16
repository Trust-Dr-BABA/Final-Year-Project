import { test as base, expect } from "@playwright/test";
import { CLIENT_ID_COOKIE } from "../../dashboard/lib/clientId";

/**
 * Journey 1 + 3a: the extension's "Open Dashboard" link binds ?client_id=... to a cookie and
 * strips it from the URL (dashboard/proxy.ts); a direct visit with no client_id at all shows the
 * "open from the extension" message rather than a crash or someone else's data.
 *
 * Doesn't use fixtures/client.ts's clientId fixture — the whole point here is to exercise the
 * real cookie-binding redirect, not skip it.
 */
const test = base;

test.describe("Dashboard onboarding", () => {
  test("binds client_id from the URL to a cookie and strips it from the URL", async ({ page, context }) => {
    const clientId = `e2e-onboarding-${Date.now()}`;

    await page.goto(`/?client_id=${clientId}`);

    // proxy.ts redirects to the clean URL — the param must not survive.
    await expect(page).toHaveURL(/^http:\/\/localhost:\d+\/$/);

    const cookies = await context.cookies();
    const clientCookie = cookies.find((c) => c.name === CLIENT_ID_COOKIE);
    expect(clientCookie?.value).toBe(clientId);
    expect(clientCookie?.httpOnly).toBe(true);
  });

  test("a repeat visit with no client_id param keeps the previously bound cookie", async ({ page, context }) => {
    const clientId = `e2e-onboarding-${Date.now()}`;
    await page.goto(`/?client_id=${clientId}`);

    // Plain revisit, no query param this time.
    await page.goto("/");
    await expect(page).toHaveURL(/^http:\/\/localhost:\d+\/$/);

    const cookies = await context.cookies();
    expect(cookies.find((c) => c.name === CLIENT_ID_COOKIE)?.value).toBe(clientId);
  });

  test("a visit with no client_id ever set shows the 'open from the extension' message, not someone else's data", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByTestId("overview-empty-state")).toContainText(
      "Open this dashboard from the extension popup's"
    );
    await expect(page.getByTestId("stat-total-scans")).toHaveText("0");
  });
});
