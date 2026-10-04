const { chromium } = require(process.argv[2] || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const base = process.env.QA_URL || "http://127.0.0.1:3000";
const output = path.join(__dirname, "../qa-artifacts");
fs.mkdirSync(output, { recursive: true });
(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.platform === "win32" ? { channel: "msedge" } : {}),
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const requests = [];
  page.on("requestfailed", (r) => requests.push(r.url()));
  const checks = [];
  const check = (name) => {
    checks.push(name);
    console.log("PASS " + name);
  };
  await page.clock.install();
  await page.goto(base + "/home-v2/");
  await page
    .getByText("Recorrido automático · 15 s", { exact: true })
    .waitFor();
  await page.evaluate(() => document.fonts.ready);
  const selected = () =>
    page.locator('.solution-selector [aria-selected="true"]').innerText();
  assert.match(await selected(), /Protect & Recover/);
  await page.clock.runFor(15100);
  assert.match(await selected(), /Cloud/);
  check("Autoplay advances after 15 seconds");
  await page.getByRole("tab", { name: "03 OptiNOC", exact: true }).click();
  await page.mouse.move(0, 0);
  await page.clock.runFor(31000);
  assert.match(await selected(), /OptiNOC/);
  check("Manual selection cancels autoplay");
  await page
    .getByRole("tab", { name: "02 Nuestra propuesta", exact: true })
    .click();
  assert.ok(
    await page
      .getByRole("heading", { name: "Conversar con OPTI", exact: true })
      .isVisible(),
  );
  await page
    .getByRole("tab", { name: "02 Nuestra propuesta", exact: true })
    .press("ArrowRight");
  assert.equal(
    await page
      .getByRole("tab", { name: "03 Nuestra experiencia", exact: true })
      .getAttribute("aria-selected"),
    "true",
  );
  check("Story stages and arrow-key navigation");
  await page
    .getByRole("button", { name: "Reanudar recorrido", exact: true })
    .click();
  await page.mouse.move(0, 0);
  await page.clock.runFor(15100);
  assert.match(await selected(), /Infrastructure/);
  check("Resume starts a new 15 second cycle");
  await page.locator(".solution-top h3").hover();
  const current = await selected();
  await page.clock.runFor(20000);
  assert.equal(await selected(), current);
  check("Hover pauses countdown");
  await page.mouse.move(0, 0);
  await page.clock.runFor(15100);
  assert.match(await selected(), /ITSM/);
  check("Hover exit preserves and resumes countdown");
  await page.getByRole("tab", { name: "05 ITSM", exact: true }).focus();
  await page.getByRole("tab", { name: "05 ITSM", exact: true }).press("End");
  assert.match(await selected(), /Managed Services/);
  check("Home/End solution navigation");
  await page
    .getByRole("button", { name: "Reanudar recorrido", exact: true })
    .click();
  await page.mouse.move(0, 0);
  await page.clock.runFor(15100);
  assert.match(await selected(), /Protect/);
  check("Last solution wraps to first");
  await page
    .getByRole("tab", { name: "01 Protect & Recover", exact: true })
    .click();
  await page
    .getByRole("button", {
      name: "Evalúa tu estrategia de recuperación",
      exact: true,
    })
    .click();
  assert.ok(await page.getByRole("dialog").isVisible());
  await page.keyboard.press("Escape");
  assert.equal(await page.getByRole("dialog").count(), 0);
  check("Draft CTA opens accessible non-submitting dialog");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.mouse.move(0, 0);
  await page.screenshot({
    path: path.join(output, "home-desktop.png"),
    fullPage: true,
  });
  for (const slug of [
    "protect-recover",
    "cloud",
    "optinoc",
    "infrastructure",
    "itsm",
    "managed-services",
  ]) {
    const response = await page.goto(base + "/soluciones/" + slug + "/");
    assert.equal(response.status(), 200);
    assert.equal(await page.locator("h1").count(), 1);
    assert.equal(await page.locator(".detail-stories>section").count(), 4);
    assert.match(
      await page.locator('meta[name="robots"]').getAttribute("content"),
      /noindex/,
    );
    assert.equal(
      await page.locator('link[rel="canonical"]').getAttribute("href"),
      "https://www.optimizeit.co/soluciones/" + slug + "/",
    );
    assert.ok(
      await page.locator('meta[property="og:title"]').getAttribute("content"),
    );
    const data = JSON.parse(
      await page.locator('script[type="application/ld+json"]').innerText(),
    );
    assert.equal(data["@type"], "Service");
  }
  check(
    "Six static solution routes with four sections, SEO, OpenGraph, canonical and structured data",
  );
  await page.goto(base + "/home-v2/");
  await page
    .getByRole("tab", { name: "01 Protect & Recover", exact: true })
    .click();
  for (const size of [
    { width: 768, height: 1024 },
    { width: 390, height: 844 },
    { width: 320, height: 740 },
  ]) {
    await page.setViewportSize(size);
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      "Horizontal overflow at " + size.width,
    );
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({
      path: path.join(output, "home-" + size.width + ".png"),
      fullPage: true,
    });
  }
  check("No horizontal overflow at tablet, mobile and 320px");
  await page.getByRole("button", { name: "Menú", exact: true }).click();
  assert.ok(await page.locator("#main-nav").isVisible());
  await page.locator("#main-nav a").first().click();
  assert.equal(
    await page
      .getByRole("button", { name: "Menú", exact: true })
      .getAttribute("aria-expanded"),
    "false",
  );
  check("Mobile navigation opens and closes");
  const frame = page.locator(".solution-frame");
  await frame.dispatchEvent("touchstart", {
    touches: [{ identifier: 1, clientX: 280, clientY: 300 }],
  });
  await frame.dispatchEvent("touchend", {
    changedTouches: [{ identifier: 1, clientX: 100, clientY: 310 }],
  });
  assert.match(await selected(), /Cloud/);
  check("Horizontal swipe changes solution");
  const reduced = await browser.newPage({
    viewport: { width: 390, height: 844 },
    reducedMotion: "reduce",
  });
  await reduced.clock.install();
  await reduced.goto(base + "/home-v2/");
  await reduced.getByText("Exploración manual", { exact: true }).waitFor();
  await reduced.clock.runFor(40000);
  assert.match(
    await reduced
      .locator('.solution-selector [aria-selected="true"]')
      .innerText(),
    /Protect/,
  );
  check("Reduced motion disables autoplay");
  const AxeBuilder = require("@axe-core/playwright").default;
  const accessibility = [];
  for (const slug of [
    "home-v2",
    "soluciones/protect-recover",
    "soluciones/optinoc",
  ]) {
    await page.goto(base + "/" + slug + "/");
    const audit = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    accessibility.push({
      route: slug,
      violations: audit.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        nodes: v.nodes.map((n) => n.target),
      })),
    });
  }
  fs.writeFileSync(
    path.join(output, "accessibility.json"),
    JSON.stringify(accessibility, null, 2),
  );
  assert.equal(
    accessibility.flatMap((a) => a.violations).length,
    0,
    "Accessibility issues: see qa-artifacts/accessibility.json",
  );
  check("WCAG automated accessibility checks");
  assert.deepEqual(errors, []);
  check("No browser runtime errors");
  const report = { checks, errors, failedRequests: requests };
  fs.writeFileSync(
    path.join(output, "report.json"),
    JSON.stringify(report, null, 2),
  );
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
