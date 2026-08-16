import { test, expect } from "../fixtures/client";

/** Journey 4: browse, sort, paginate, and click through to a scan's detail page. */

test.describe("History page", () => {
  test("shows the empty state for a client with no scans", async ({ page }) => {
    await page.goto("/history");
    await expect(page.getByTestId("history-empty-state")).toContainText("No scans recorded yet");
  });

  test("lists seeded scans and sorts by column on click", async ({ page, seedScan }) => {
    const alpha = await seedScan({ url: "https://e2e-history-test.example/alpha" });
    const beta = await seedScan({ url: "https://e2e-history-test.example/beta" });

    await page.goto("/history");

    await expect(page.getByTestId(`history-row-${alpha.scan_id}`)).toBeVisible();
    await expect(page.getByTestId(`history-row-${beta.scan_id}`)).toBeVisible();

    // Default sort is last_scanned_at desc — beta (seeded second, so scanned later) sorts first.
    const rowsBefore = page.locator("tbody tr");
    await expect(rowsBefore.first()).toHaveAttribute("data-testid", `history-row-${beta.scan_id}`);

    // Click the URL column header to sort ascending by URL — "alpha" sorts before "beta".
    await page.getByRole("columnheader", { name: /URL/ }).click();
    const rowsAfterFirstClick = page.locator("tbody tr");
    await expect(rowsAfterFirstClick.first()).toHaveAttribute("data-testid", `history-row-${alpha.scan_id}`);

    // Clicking the same header again reverses the sort direction.
    await page.getByRole("columnheader", { name: /URL/ }).click();
    const rowsAfterSecondClick = page.locator("tbody tr");
    await expect(rowsAfterSecondClick.first()).toHaveAttribute("data-testid", `history-row-${beta.scan_id}`);
  });

  test("clicking a row navigates to that scan's detail page", async ({ page, seedScan }) => {
    const scan = await seedScan({ url: "https://e2e-history-test.example/click-through" });

    await page.goto("/history");
    await page.getByTestId(`history-row-${scan.scan_id}`).click();

    await expect(page).toHaveURL(new RegExp(`/scan/${scan.scan_id}$`));
    await expect(page.getByText("e2e-history-test.example/click-through")).toBeVisible();
  });

  test("an out-of-range page number degrades to an empty table instead of erroring", async ({ page, seedScan }) => {
    await seedScan({ url: "https://e2e-history-test.example/single-page" });

    await page.goto("/history?page=999");

    await expect(page.getByTestId("history-empty-state")).toBeVisible();
  });
});
