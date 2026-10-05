import { chromium } from "../frontend/node_modules/playwright/index.mjs";
import fs from "node:fs";
import assert from "node:assert/strict";
const browser = await chromium.launch({ headless: true, channel: "msedge" });
const page = await browser.newPage({
  viewport: { width: 1440, height: 1000 },
  reducedMotion: "reduce",
});
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
fs.mkdirSync("artifacts", { recursive: true });
try {
  await page.goto(process.env.TIMBLE_TEST_URL || "http://127.0.0.1:15173/");
  await page.getByLabel("Username").fill("browser-test");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.TIMBLE_TEST_PASSWORD);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("heading", { name: "Overview", exact: true }).waitFor();
  await page.getByRole("button", { name: "Data Import", exact: true }).click();
  await page
    .getByLabel("Choose a dataset ZIP", { exact: false })
    .setInputFiles("datasets/demo-datasets.zip");
  await page.getByRole("button", { name: "Validate package" }).click();
  await page.getByRole("heading", { name: "Validation passed" }).waitFor();
  const beforeImport = await page.evaluate(
    async () => (await (await fetch("/api/programs/")).json()).length,
  );
  assert.equal(beforeImport, 0, "ZIP preview must retain no rows");
  assert.equal(
    await page.getByRole("cell", { name: "Passed", exact: true }).count(),
    10,
  );
  await page.getByRole("button", { name: "Import all datasets" }).click();
  await page.getByRole("heading", { name: "Import complete" }).waitFor();
  await page.screenshot({ path: "artifacts/bulk-bundle.png", fullPage: true });
  const afterImport = await page.evaluate(
    async () => (await (await fetch("/api/programs/")).json()).length,
  );
  assert.equal(afterImport, 1, "ZIP commit imports the bundled program");
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.getByRole("heading", { name: "Overview", exact: true }).waitFor();
  await page
    .locator(".stats article")
    .first()
    .getByText("1", { exact: true })
    .waitFor();
  await page.screenshot({ path: "artifacts/dashboard.png", fullPage: true });
  await page
    .getByRole("button", { name: "Collapse navigation", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Expand navigation", exact: true })
    .click();
  await page
    .getByRole("button", { name: "DATA MANAGEMENT", exact: true })
    .click();
  assert.equal(
    await page
      .getByRole("button", { name: "Data Entry", exact: true })
      .isVisible(),
    false,
  );
  await page
    .getByRole("button", { name: "DATA MANAGEMENT", exact: true })
    .click();
  await page.getByRole("button", { name: "Data Entry", exact: true }).click();
  await page.getByRole("button", { name: "Subjects", exact: true }).click();
  await page.getByRole("heading", { name: "Subjects", exact: true }).waitFor();
  await page.getByRole("button", { name: "Programs", exact: true }).click();
  await page.getByRole("button", { name: "Add record", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Program Code").fill("BROWSER");
  await dialog.getByLabel("Program Name").fill("Browser verified");
  await dialog.getByLabel("Max Year Level").fill("4");
  await dialog.getByRole("button", { name: "Save record" }).click();
  await page.getByRole("cell", { name: "BROWSER", exact: true }).waitFor();
  await page.screenshot({ path: "artifacts/data-entry.png", fullPage: true });
  await page
    .getByRole("button", { name: "Forecast Generation", exact: true })
    .click();
  await page.getByLabel("Program scope").selectOption({ label: "DEMO-CS" });
  await page.getByRole("button", { name: "Generate", exact: true }).click();
  await page
    .getByRole("button", { name: "Finalize & create offerings" })
    .waitFor();
  await page
    .getByRole("button", { name: "Inspect", exact: true })
    .last()
    .click();
  await page.getByRole("dialog").getByText("95", { exact: true }).count();
  await page.screenshot({
    path: "artifacts/forecast-computation.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Finalize & create offerings" })
    .click();
  await page.getByRole("heading", { name: /Course offerings/ }).waitFor();
  await page
    .getByRole("button", { name: "Generate Timetable", exact: true })
    .click();
  await page.getByLabel("Finalized forecast").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Generate schedule" }).click();
  await page.getByText("OPTIMAL", { exact: true }).waitFor({ timeout: 90000 });
  assert.equal(
    await page.getByRole("button", { name: "Explain", exact: true }).count(),
    12,
  );
  await page.screenshot({ path: "artifacts/timetable.png", fullPage: true });
  await page
    .getByRole("button", { name: "Explain", exact: true })
    .first()
    .click();
  await page
    .getByRole("heading", { name: "Why this assignment is valid" })
    .waitFor();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Optimization computation", exact: true })
    .click();
  await page
    .getByText("All hard constraints satisfied", { exact: true })
    .waitFor();
  await page
    .getByRole("button", { name: "Demonstrate a hypothetical collision" })
    .click();
  await page
    .getByText(
      "2 > 1: the faculty collision constraint rejects this assignment.",
    )
    .waitFor();
  await page.screenshot({ path: "artifacts/optimization.png", fullPage: true });
  await page
    .getByRole("button", { name: "Solver progress", exact: true })
    .click();
  await page.getByRole("heading", { name: "Solver measurements" }).waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "artifacts/mobile.png", fullPage: true });
  await page.getByRole("button", { name: "Toggle navigation" }).click();
  await page.getByRole("button", { name: "Data Entry", exact: true }).click();
  await page
    .getByRole("heading", { name: "Data Entry", exact: true })
    .waitFor();
  await page.getByRole("button", { name: "Rooms", exact: true }).click();
  await page.getByRole("heading", { name: "Rooms", exact: true }).waitFor();
  await page.getByRole("cell", { name: "DEMO-L30", exact: true }).waitFor();
  await page.screenshot({
    path: "artifacts/mobile-data-entry.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Toggle navigation" }).click();
  await page.keyboard.press("Escape");
  assert.equal(
    await page
      .getByRole("button", { name: "Data Import", exact: true })
      .isVisible(),
    false,
  );
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > innerWidth,
  );
  assert.equal(overflow, false, "Mobile layout must not overflow horizontally");
  assert.deepEqual(errors, []);
  const run = await page.evaluate(async () => {
    const all = await (await fetch("/api/schedules/")).json();
    return await (await fetch("/api/schedules/" + all[0].id + "/")).json();
  });
  fs.writeFileSync(
    "artifacts/verified-demo-run.json",
    JSON.stringify(run, null, 2),
  );
  console.log(
    JSON.stringify({
      browser: "Edge headless",
      checks:
        "login, ZIP preview rollback, ten-file ZIP commit, CRUD, forecast, finalization, asynchronous solve, timetable, explanation, all matrices, hypothetical conflict, solver metrics, mobile width",
      assignments: run.assignments.length,
      status: run.status,
      objective: run.objective_value,
      violations: run.validation.violations.length,
      pageErrors: errors,
    }),
  );
} finally {
  await browser.close();
}
