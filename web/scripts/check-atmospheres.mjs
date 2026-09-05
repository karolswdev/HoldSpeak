import puppeteer from "puppeteer";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import assert from "node:assert/strict";

const origin = process.env.ATMOSPHERE_ORIGIN || "http://127.0.0.1:4322";
const output = resolve("../docs/assets/screenshots/environments");
await mkdir(output, { recursive: true });
const browser = await puppeteer.launch({ headless: true });
const settle = (ms) => new Promise((done) => setTimeout(done, ms));
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.goto(`${origin}/_built/atmospheres.html`, {
    waitUntil: "networkidle0",
  });
  const ready = (id) =>
    page.waitForSelector(`[data-atmosphere="${id}"] canvas[data-ready="true"]`);
  await ready("rainy-city");
  const collection = await page.evaluate(async () => {
    const { SCENIC_ATMOSPHERES } =
      await import("/_built/src/desk/gl/atmosphereRegistry.ts");
    return SCENIC_ATMOSPHERES.map(({ id, name, previewUrl }) => ({
      id,
      name,
      previewUrl,
    }));
  });
  assert.deepEqual(
    collection.map(({ id }) => id),
    [
      "rainy-city",
      "lantern-garden",
      "radio-station",
      "midnight-archive",
      "night-train",
      "deep-sea",
      "greenhouse",
      "laundromat",
    ],
  );
  assert.equal(
    await page.$$eval(
      ".atmosphere-preview-strip button",
      (buttons) => buttons.length,
    ),
    8,
  );
  await page.waitForFunction(() =>
    [...document.images].every(
      (image) => image.complete && image.naturalWidth > 0,
    ),
  );
  const choose = async (id) => {
    await page.click(`.atmosphere-preview-strip [data-scene="${id}"]`);
    await ready(id);
    await settle(400);
  };
  const assertStill = async (label) => {
    await page.mouse.move(3, 400);
    await settle(700);
    const before = await page.screenshot();
    await page.mouse.move(900, 200);
    await settle(350);
    assert(
      Buffer.from(before).equals(Buffer.from(await page.screenshot())),
      `${label} changed`,
    );
  };
  const reports = [];
  for (const { id } of collection) {
    await choose(id);
    const fps = await page.evaluate(
      () =>
        new Promise((done) => {
          let start,
            frames = 0;
          const sample = (now) => {
            if (start === undefined) start = now;
            else frames++;
            if (now - start >= 1000)
              done(Math.round(frames / ((now - start) / 1000)));
            else requestAnimationFrame(sample);
          };
          requestAnimationFrame(sample);
        }),
    );
    const before = await page.screenshot();
    await settle(250);
    assert(
      !Buffer.from(before).equals(Buffer.from(await page.screenshot())),
      `${id} did not animate`,
    );
    await page.click(".atmosphere-preview-controls button:first-child");
    await ready(id);
    await assertStill(`Paused ${id}`);
    await page.click(".atmosphere-preview-controls button:first-child");
    await ready(id);
    reports.push({ id, observedFps: fps, animated: true, pausedStable: true });
  }
  // Both original scenes are full gallery members, including numbering and wraparound.
  await choose("rainy-city");
  await page.click('[aria-label="Previous environment"]');
  await ready("laundromat");
  await page.click('[aria-label="Next environment"]');
  await ready("rainy-city");
  assert.match(
    await page.$eval(".atmosphere-preview-kicker", (node) => node.textContent),
    /01\s*\/\s*08/,
  );
  await page.screenshot({ path: resolve(output, "preview-desktop.png") });
  await choose("lantern-garden");
  await page.click(".atmosphere-preview-actions button:last-child");
  await page.reload({ waitUntil: "networkidle0" });
  await ready("lantern-garden");
  assert.equal(
    await page.evaluate(() => localStorage.getItem("hs.desk.atmosphere")),
    "lantern-garden",
  );
  await page.emulateMediaFeatures([
    { name: "prefers-reduced-motion", value: "reduce" },
  ]);
  await page.setViewport({ width: 393, height: 852, deviceScaleFactor: 1 });
  for (const id of ["rainy-city", "lantern-garden"]) {
    await choose(id);
    await assertStill(`Reduced-motion ${id}`);
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `${id} phone overflow`,
    );
    await page.screenshot({ path: resolve(output, `preview-${id}-phone.png`) });
  }
  await page.screenshot({ path: resolve(output, "preview-phone.png") });
  assert.deepEqual(errors, []);
  const report = {
    scenes: reports,
    liveSelection: true,
    wraparound: true,
    preferenceReload: true,
    reducedMotionStable: true,
    phoneOverflow: false,
    errors,
  };
  await writeFile(
    resolve(output, "browser-checks.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  console.log(JSON.stringify(report, null, 2));
  // Contact sheet uses captured scenes and registry metadata, not concept art.
  await page.setViewport({ width: 1440, height: 1130, deviceScaleFactor: 1 });
  await page.evaluate((entries) => {
    document.body.innerHTML = `<main style="padding:38px;background:#101412;color:#e6e4d8;font-family:system-ui"><div style="font-size:11px;letter-spacing:2px;color:#a5aa9b">HOLDSPEAK · THE NIGHT COLLECTION</div><h1 style="font:42px Georgia;margin:12px 0 30px">Eight places to think.</h1><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:22px">${entries.map(({ name, previewUrl }, i) => `<article><img style="display:block;width:100%;aspect-ratio:1.9;object-fit:cover" src="${previewUrl}"><p style="margin:10px 0;font-size:14px"><span style="color:#9b9f90;margin-right:12px">${String(i + 1).padStart(2, "0")}</span>${name}</p></article>`).join("")}</div></main>`;
  }, collection);
  await page.waitForFunction(() =>
    [...document.images].every((image) => image.complete && image.naturalWidth),
  );
  await page.screenshot({
    path: resolve(output, "collection.png"),
    fullPage: true,
  });
} finally {
  await browser.close();
}
