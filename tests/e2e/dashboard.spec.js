const { test, expect } = require("@playwright/test");
const fs = require("node:fs");
const path = require("node:path");

test.describe("API data readiness", () => {
  test("health reports backend and database are available", async ({ request }) => {
    const response = await request.get("/api/health");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.api).toBe("running");
    expect(body.database.connected).toBe(true);
  });

  test("core dashboard endpoints return populated datasets", async ({ request }) => {
    const cases = [
      { path: "/api/production", key: "data", min: 20 },
      { path: "/api/export/overview", key: "data", min: 20 },
      { path: "/api/export/countries?limit=9", key: "countries", min: 5 },
      { path: "/api/prices/recent?days=7", key: "provinces", min: 4 },
      { path: "/api/weather/province/DakLak?aggregate=recent12", key: "data", min: 12 },
    ];

    for (const item of cases) {
      const response = await request.get(item.path);
      expect(response.ok(), item.path).toBeTruthy();

      const body = await response.json();
      expect(Array.isArray(body[item.key]), item.path).toBeTruthy();
      expect(body[item.key].length, item.path).toBeGreaterThanOrEqual(item.min);
    }
  });
});

test.describe("Dashboard UI", () => {
  test("renders live data and charts without page errors", async ({ page }) => {
    const pageErrors = [];
    const consoleErrors = [];

    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") {
        consoleErrors.push(message.text());
      }
    });

    await page.goto("/");
    await expect(page).toHaveTitle(/Vietnam Coffee Data Portal/);
    await expect(page.getByText("Backend and database are available.")).toBeVisible();

    await expect(page.locator("#kpiProduction")).not.toHaveText("--");
    await expect(page.locator("#kpiExportValue")).not.toHaveText("--");
    await expect(page.locator("#kpiWorldPrice")).not.toHaveText("--");
    await expect(page.locator("#kpiProvincePrice")).not.toHaveText("--");
    await expect(page.locator("#countryList .country-row")).toHaveCount(9);

    for (const canvasId of ["marketChart", "exportChart", "priceChart", "weatherChart"]) {
      const canvas = page.locator(`#${canvasId}`);
      await expect(canvas).toBeVisible();
      const box = await canvas.boundingBox();
      expect(box?.width, canvasId).toBeGreaterThan(100);
      expect(box?.height, canvasId).toBeGreaterThan(100);
    }

    expect(pageErrors).toEqual([]);
    expect(consoleErrors.filter((text) => !text.includes("favicon"))).toEqual([]);
  });

  test("is usable on a mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Coffee Intelligence Dashboard" })).toBeVisible();
    await expect(page.locator(".kpi-card")).toHaveCount(4);
    await expect(page.locator("#marketChart")).toBeVisible();
  });
});

test.describe("Legacy template quality gate", () => {
  test("legacy Flask template must not contain unresolved merge conflicts", async () => {
    const html = fs.readFileSync(path.join(process.cwd(), "web/templates/index.html"), "utf8");
    expect(html).not.toMatch(/^(<<<<<<<|=======|>>>>>>>) /m);
  });
});
