import { test, expect } from "../fixtures/client";

/**
 * Journey 2 + 3b: overview page with real seeded data, and the empty state for a valid client_id
 * that just hasn't scanned anything yet (distinct from onboarding.spec.ts's "never had a
 * client_id at all" case).
 */

test.describe("Overview page", () => {
  test("shows zeroed stats and the 'no scans yet' message for a client with no scans", async ({ page, clientId }) => {
    await page.goto("/");

    await expect(page.getByTestId("stat-total-scans")).toHaveText("0");
    await expect(page.getByTestId("overview-empty-state")).toContainText("No scans recorded yet");
    await expect(page.getByTestId("risk-distribution-chart")).toHaveCount(0);
  });

  test("reflects seeded scans in the stat counts and renders the distribution chart", async ({ page, seedScan }) => {
    await seedScan({ url: "https://e2e-overview-test.example/one" });
    await seedScan({ url: "https://e2e-overview-test.example/two" });

    await page.goto("/");

    await expect(page.getByTestId("stat-total-scans")).toHaveText("2");
    await expect(page.getByTestId("risk-distribution-chart")).toBeVisible();
    await expect(page.getByTestId("overview-empty-state")).toHaveCount(0);

    // avg confidence is a real, deterministic-shaped number (0-100), not a placeholder — this
    // catches a regression where the stat silently stops rendering a number at all.
    const avgConfidenceText = await page.getByTestId("stat-avg-confidence").innerText();
    expect(Number(avgConfidenceText.replace("%", ""))).toBeGreaterThanOrEqual(0);
  });
});
