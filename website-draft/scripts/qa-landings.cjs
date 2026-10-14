const { chromium } = require("playwright");
const AxeBuilder = require("@axe-core/playwright").default;
const fs = require("fs");
const assert = require("node:assert/strict");
const copy = require("../content/landing-copy.json");
(async () => {
  fs.mkdirSync("qa-artifacts/landings", { recursive: true });
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const errors = [];
  const results = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const base = "http://127.0.0.1:3001";
  for (const s of copy) {
    const r = await page.goto(`${base}/soluciones/${s.slug}/`);
    assert.equal(r.status(), 200);
    await page.locator("h1").waitFor();
    assert.equal(await page.locator("h1").textContent(), s.headline);
    assert.ok(
      await page
        .locator(".service-hero img")
        .evaluate((img) => img.complete && img.naturalWidth > 0),
    );
    assert.equal(await page.locator(".capability-card").count(), 4);
    assert.equal(
      await page.locator("select[name=service]").inputValue(),
      s.slug,
    );
    await page.locator(".service-faq summary").first().click();
    assert.ok(
      (await page
        .locator(".service-faq details")
        .first()
        .getAttribute("open")) !== null,
    );
    const axe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();
    if (axe.violations.length)
      console.log(
        s.slug,
        axe.violations.map((v) => ({
          id: v.id,
          nodes: v.nodes.map((n) => n.target),
        })),
      );
    assert.equal(axe.violations.length, 0);
    await page.screenshot({
      path: `qa-artifacts/landings/${s.slug}-desktop.png`,
    });
    for (const width of [390, 320]) {
      await page.setViewportSize({ width, height: 844 });
      assert.ok(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        `Overflow ${s.slug} ${width}`,
      );
    }
    if (["protect-recover", "optidesk", "itsm"].includes(s.slug))
      await page.screenshot({
        path: `qa-artifacts/landings/${s.slug}-mobile.png`,
        fullPage: true,
      });
    await page.setViewportSize({ width: 1440, height: 1000 });
    results.push(
      `${s.slug}: route, hero image, content, FAQ, selected service, axe, mobile widths`,
    );
  }
  await page.goto(`${base}/home-v2/`);
  assert.equal(await page.locator("#servicios .service-card").count(), 9);
  await page.screenshot({ path: "qa-artifacts/landings/home-desktop.png" });
  await page.locator('#servicios a[href="/soluciones/optidesk/"]').click();
  await page.waitForURL("**/soluciones/optidesk/");
  await page.getByLabel("Nombre completo").fill("Persona de prueba");
  await page.getByLabel("Empresa", { exact: true }).fill("Empresa de prueba");
  await page.getByLabel("Correo de contacto").fill("prueba@example.com");
  await page.getByLabel("¿Qué necesita resolver?").fill("Prueba del borrador");
  await page.locator("form button[type=submit]").click();
  await page.getByRole("status").waitFor();
  assert.match(
    await page.getByRole("status").textContent(),
    /No se ha enviado/,
  );
  results.push(
    "Home directory connects to Optidesk; demo form gives honest status",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${base}/home-v2/`);
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await page.screenshot({ path: "qa-artifacts/landings/home-mobile.png" });
  await page.getByRole("button", { name: "Menú", exact: true }).click();
  await page.locator(".solutions-dropdown>summary").click();
  await page
    .locator('.solutions-dropdown a[href="/soluciones/cleanshield/"]')
    .click();
  await page.waitForURL("**/soluciones/cleanshield/");
  results.push("Mobile home, menu and service dropdown");
  assert.equal(errors.length, 0);
  await context.close();
  const auto = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    reducedMotion: "no-preference",
  });
  const ap = await auto.newPage();
  await ap.clock.install();
  await ap.goto(`${base}/home-v2/`);
  await ap.getByText("Recorrido automático · 10 s", { exact: true }).waitFor();
  const active = () =>
    ap
      .locator(".solution-selector [role=tab][aria-selected=true]")
      .textContent();
  const first = await active();
  await ap.clock.runFor(10100);
  assert.notEqual(await active(), first);
  await ap.locator(".visual-copy h1").click();
  const stopped = await active();
  await ap.clock.runFor(20100);
  assert.equal(await active(), stopped);
  results.push("10 second carousel and persistent pause on reading click");
  await browser.close();
  fs.writeFileSync(
    "qa-artifacts/landings/report.json",
    JSON.stringify({ results, errors }, null, 2),
  );
  console.log(
    "PASS",
    results.length,
    "checks; 9 routes; no axe A/AA violations",
  );
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
