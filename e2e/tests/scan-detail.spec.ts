import { test, expect } from "../fixtures/client";
import { randomUUID } from "node:crypto";
import { CLIENT_ID_COOKIE } from "../../dashboard/lib/clientId";

/**
 * Journeys 5-8: the full scan report, the ownership boundary (this app's closest analog to an
 * "expired session" — see the journey list this suite was approved from), a malformed id, and
 * degraded/sparse data (no browser signals recorded, VT unavailable).
 */

test.describe("Scan detail page", () => {
  test("renders the full report for a scan with data in every signal category", async ({ page, seedScan }) => {
    const scan = await seedScan({
      url: "https://e2e-scan-detail-test.example/full-report",
      network_signals: { tracker_count: 5, has_mixed_content: true, redirect_chain_length: 2 },
      permission_signals: { rule_flags: ["cam_mic_on_first_visit"] },
      scam_content_signals: {
        scam_keyword_hits: 2,
        matched_phrases: ["verify your password", "confirm your billing details immediately"],
        sensitive_field_count: 2,
        sensitive_field_categories: ["password", "card_number"],
      },
    });

    await page.goto(`/scan/${scan.scan_id}`);

    await expect(page.getByTestId("verdict-badge")).toBeVisible();
    await expect(page.getByTestId("confidence-badge")).toBeVisible();
    await expect(page.getByTestId("risk-bar")).toBeVisible();
    await expect(page.getByTestId("risk-pct")).toHaveText(`${scan.risk_pct}%`);
    await expect(page.getByTestId("shap-waterfall-chart")).toBeVisible();

    await expect(page.getByRole("heading", { name: "Network signals" })).toBeVisible();
    await expect(page.getByText("5", { exact: true })).toBeVisible(); // tracker_count Field value
    await expect(page.getByRole("heading", { name: "Permission signals" })).toBeVisible();
    await expect(page.getByText(/cam mic on first visit/)).toBeVisible();
    await expect(page.getByRole("heading", { name: "Page content signals" })).toBeVisible();
    await expect(page.getByText("verify your password")).toBeVisible();
    await expect(page.getByText(/card number/)).toBeVisible();
    await expect(page.getByRole("heading", { name: "VirusTotal corroboration" })).toBeVisible();
  });

  test("degrades gracefully with no browser signals recorded at all", async ({ page, seedScan }) => {
    const scan = await seedScan({ url: "https://e2e-scan-detail-test.example/sparse" });

    await page.goto(`/scan/${scan.scan_id}`);

    await expect(page.getByText("No network signals recorded.")).toBeVisible();
    await expect(page.getByText("No permission signals flagged.")).toBeVisible();
    await expect(page.getByText("No scam-indicator phrases detected on this page.")).toBeVisible();
    await expect(page.getByText("No sensitive form-field categories detected on this page.")).toBeVisible();
  });

  test("shows VirusTotal as unavailable for an unrecognised test domain", async ({ page, seedScan }) => {
    const scan = await seedScan({ url: `https://e2e-vt-unknown-${randomUUID()}.invalid/` });

    await page.goto(`/scan/${scan.scan_id}`);

    await expect(
      page.getByText(/Unavailable for this scan — no API key configured, VirusTotal timed out/)
    ).toBeVisible();
  });

  test("404s when the scan exists but belongs to a different client_id", async ({ page, seedScan, context }, testInfo) => {
    const scan = await seedScan({ url: "https://e2e-scan-detail-test.example/not-yours" });

    // Switch identity mid-test — same pattern as another browser/install trying the same link.
    const baseURL = new URL(testInfo.project.use.baseURL as string);
    await context.clearCookies();
    await context.addCookies([
      {
        name: CLIENT_ID_COOKIE,
        value: `e2e-intruder-${randomUUID()}`,
        domain: baseURL.hostname,
        path: "/",
      },
    ]);

    const response = await page.goto(`/scan/${scan.scan_id}`);
    expect(response?.status()).toBe(404);
    // The status code is the load-bearing assertion here — Next's default not-found markup isn't
    // a stable contract to assert against, so this only checks the page didn't crash into
    // something unrelated (e.g. an unhandled-exception page) while still being on this URL.
    await expect(page).toHaveURL(new RegExp(`/scan/${scan.scan_id}$`));
  });

  test("404s for a well-formed but nonexistent scan id", async ({ page }) => {
    const response = await page.goto(`/scan/${randomUUID()}`);
    expect(response?.status()).toBe(404);
  });

  test("404s for a malformed scan id rather than erroring", async ({ page }) => {
    const response = await page.goto("/scan/not-a-valid-uuid");
    expect(response?.status()).toBe(404);
  });
});
