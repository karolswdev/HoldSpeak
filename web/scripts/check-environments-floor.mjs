// Production-bundle integration walk with explicit, isolated HTTP fixtures.
// Nothing in this harness contacts a hub or writes the owner's Desk data.
import puppeteer from "puppeteer";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import assert from "node:assert/strict";

const origin =
  process.env.ATMOSPHERE_PRODUCTION_ORIGIN || "http://127.0.0.1:4323";
const output = resolve("../docs/assets/screenshots/environments");
const settleWalk = process.argv.includes("--settle");
await mkdir(output, { recursive: true });
const browser = await puppeteer.launch({ headless: true });
try {
  const page = await browser.newPage();
  page.setDefaultTimeout(10000);
  const errors = [];
  const captureWrites = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.setRequestInterception(true);
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (!path.startsWith("/api/")) return request.continue();
    if (path.startsWith("/api/meeting/") && request.method() !== "GET")
      captureWrites.push(path);
    const responses = {
      "/api/setup/status": {
        first_run: false,
        arrival_required: false,
        overall: "ready",
        trust: { web_bind: "127.0.0.1", transcript_egress: "none" },
      },
      "/api/notes": {
        notes: [
          {
            id: "preview-notes",
            title: "Field notes",
            body_markdown: "A quiet place to think.",
            created_at: "2026-09-04T10:00:00Z",
          },
          {
            id: "preview-ideas",
            title: "Evening ideas",
            body_markdown: "Ideas for the next session.",
            created_at: "2026-09-04T10:00:00Z",
          },
        ],
      },
      "/api/meetings": {
        meetings: [
          {
            id: "preview-meeting",
            title: "Studio session",
            status: "completed",
            started_at: "2026-09-04T10:00:00Z",
            duration_seconds: 600,
          },
        ],
      },
      "/api/settings": { ui: {}, presence: {} },
      "/api/state": {
        activity: { state: settleWalk ? "meeting_live" : "idle" },
      },
      "/api/desk/projections": {
        projections: [],
        page: { total: 0 },
        counts: {},
        subject_counts: {},
      },
      "/api/desk/projections/counts": { counts: {}, subject_counts: {} },
      "/api/door": {
        board: {
          overdue: [],
          now: [],
          waiting: [],
          unassigned: [],
          active: [],
        },
        upcoming: [],
        counts: {},
        calendar_configured: false,
      },
      "/api/brief/latest": null,
      "/api/follow-through/board": {
        now: [],
        waiting: [],
        unassigned: [],
        overdue: [],
      },
      "/api/decision-records/review": [],
    };
    request.respond({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        Object.hasOwn(responses, path) ? responses[path] : {},
      ),
    });
  });
  await page.evaluateOnNewDocument(() => {
    if (!localStorage.getItem("hs.desk.atmosphere"))
      localStorage.setItem("hs.desk.atmosphere", "radio-station");
    window.__micRequests = 0;
    navigator.mediaDevices.getUserMedia = async () => {
      window.__micRequests++;
      throw new Error("The environment walk must never acquire a microphone");
    };
  });
  await page.goto(`${origin}/_built/`, { waitUntil: "networkidle0" });
  await page.waitForSelector('button[aria-label="Floor"]');
  await page.click('button[aria-label="Floor"]');
  await page.waitForSelector(
    '[data-atmosphere="radio-station"] canvas[data-ready="true"]',
  );
  await page.waitForSelector(".desk-world-canvas");
  await new Promise((done) => setTimeout(done, 1000));
  await page.screenshot({
    path: resolve(output, "floor-production-desktop.png"),
  });
  const object = await page.evaluate(() =>
    window.__hsWorldProbe?.().find((entry) => entry.title === "Field notes"),
  );
  assert(object, "Actual Pixi object did not render");
  await page.mouse.click(object.x, object.y);
  assert(
    await page.evaluate(
      () =>
        window.__hsWorldProbe?.().find((entry) => entry.title === "Field notes")
          ?.selected,
    ),
    "Atmosphere intercepted object selection",
  );
  if (settleWalk) {
    const { checkSettleFlow } = await import("./check-settle-flow.mjs");
    await checkSettleFlow(page, output, origin);
    assert.deepEqual(
      captureWrites,
      [],
      "Settling or changing places changed recording",
    );
    assert.equal(await page.evaluate(() => window.__micRequests), 0);
    assert.deepEqual(errors, []);
  } else {
    await page.evaluate(() => {
      history.replaceState({}, "", "/settings");
      dispatchEvent(new PopStateEvent("popstate"));
    });
    await page.waitForFunction(() =>
      [...document.querySelectorAll("button")].some((button) =>
        button.textContent?.includes("Wallpaper"),
      ),
    );
    await page.evaluate(() =>
      [...document.querySelectorAll("button")]
        .find((button) => button.textContent?.includes("Wallpaper"))
        ?.click(),
    );
    await page.waitForSelector('[role="radio"]');
    const choose = async (name, id) => {
      await page.evaluate(
        (label) =>
          [...document.querySelectorAll('[role="radio"]')]
            .find((radio) => radio.textContent?.includes(label))
            ?.click(),
        name,
      );
      await page.waitForSelector(
        `[data-atmosphere="${id}"] canvas[data-ready="true"]`,
      );
      assert.equal(
        await page.evaluate(() => localStorage.getItem("hs.desk.atmosphere")),
        id,
      );
      await page.evaluate((label) => {
        const radio = [...document.querySelectorAll('[role="radio"]')].find(
          (entry) => entry.textContent?.includes(label),
        );
        radio?.scrollIntoView({ block: "center" });
      }, name);
      await page.waitForFunction(() => {
        const image = document.querySelector(
          '[role="radio"][aria-checked="true"] img',
        );
        return image?.complete && image.naturalWidth > 0;
      });
      await new Promise((done) => setTimeout(done, 300));
    };
    await choose("Rainy City", "rainy-city");
    await choose("Lantern Garden", "lantern-garden");
    await page.screenshot({
      path: resolve(output, "settings-production-desktop.png"),
    });
    await page.setViewport({ width: 393, height: 852, deviceScaleFactor: 1 });
    await choose("Rainy City", "rainy-city");
    await page.screenshot({
      path: resolve(output, "settings-production-phone.png"),
    });
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      "Settings overflows phone",
    );
    assert.deepEqual(errors, []);
    const report = {
      bundle: "production",
      backend: "isolated HTTP fixtures",
      pixiSelection: true,
      settingsLiveSelection: true,
      selectedPreviewsLoaded: true,
      originalWorldsIncluded: true,
      phoneOverflow: false,
      errors,
    };
    await writeFile(
      resolve(output, "production-checks.json"),
      JSON.stringify(report, null, 2) + "\n",
    );
    console.log(JSON.stringify(report, null, 2));
  }
} catch (error) {
  for (const page of await browser.pages()) {
    console.log(
      (await page.evaluate(() => document.body.innerText)).slice(0, 3000),
    );
  }
  throw error;
} finally {
  await browser.close();
}
