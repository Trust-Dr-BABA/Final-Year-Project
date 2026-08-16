import { test, expect } from "@playwright/test";

/** Journey 9: light/dark theme toggle persists via localStorage. */

test.describe("Theme toggle", () => {
  test("switches the data-theme attribute and persists across reload", async ({ page }) => {
    await page.goto("/");

    const html = page.locator("html");
    const initialTheme = await html.getAttribute("data-theme");

    const toggle = page.getByRole("button", { name: "Toggle light/dark theme" });
    await toggle.click();

    const toggledTheme = await html.getAttribute("data-theme");
    expect(toggledTheme).not.toBe(initialTheme);

    await page.reload();
    await expect(html).toHaveAttribute("data-theme", toggledTheme ?? "");
  });
});
