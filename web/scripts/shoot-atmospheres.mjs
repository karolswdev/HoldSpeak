// Capture the actual lazy scene modules. Uses an isolated browser page: no hub,
// microphone or owner preferences. Start Vite first (npm run dev -- --port 4322).
import puppeteer from "puppeteer";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

const base = process.env.ATMOSPHERE_ORIGIN || "http://127.0.0.1:4322";
const output = resolve(
  process.env.ATMOSPHERE_SHOTS || "../docs/assets/screenshots/environments",
);
const requested = process.argv.slice(2);
const thumbnails = resolve("public/desk/atmospheres");
await mkdir(output, { recursive: true });
await mkdir(thumbnails, { recursive: true });
const browser = await puppeteer.launch({ headless: true });
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.setRequestInterception(true);
  page.on("request", (request) => {
    if (request.isNavigationRequest())
      request.respond({
        status: 200,
        contentType: "text/html",
        body: '<html><head></head><body style="margin:0"><div id="root"></div></body></html>',
      });
    else request.continue();
  });
  await page.goto(`${base}/_built/`);
  await page.evaluate(async () => {
    const { default: RefreshRuntime } = await import("/_built/@react-refresh");
    RefreshRuntime.injectIntoGlobalHook(window);
    window.$RefreshReg$ = () => {};
    window.$RefreshSig$ = () => (type) => type;
    window.__vite_plugin_react_preamble_installed__ = true;
    await import("/_built/src/styles/tokens.css");
    await import("/_built/src/desk/desk.css");
    const { default: React } =
      await import("/_built/node_modules/.vite/deps/react.js");
    const { createRoot } = (
      await import("/_built/node_modules/.vite/deps/react-dom_client.js")
    ).default;
    const { Atmosphere } = await import("/_built/src/desk/gl/Atmosphere.tsx");
    const root = createRoot(document.querySelector("#root"));
    window.renderAtmosphere = (id) =>
      root.render(
        React.createElement(
          "main",
          { className: "desk-next" },
          React.createElement(Atmosphere, { id }),
        ),
      );
  });
  const collectionIds = await page.evaluate(async () => {
    const { SCENIC_ATMOSPHERES } =
      await import("/_built/src/desk/gl/atmosphereRegistry.ts");
    return SCENIC_ATMOSPHERES.map((entry) => entry.id);
  });
  const ids = requested.length ? requested : collectionIds;
  for (const id of ids) {
    if (!collectionIds.includes(id))
      throw new Error(`Unknown scenic atmosphere: ${id}`);
    await page.evaluate((next) => window.renderAtmosphere(next), id);
    await page.waitForSelector(
      `[data-atmosphere="${id}"] canvas[data-ready="true"]`,
    );
    await new Promise((done) => setTimeout(done, 1800));
    await page.screenshot({ path: resolve(output, `${id}.png`) });
    await page.screenshot({
      path: resolve(thumbnails, `${id}.webp`),
      type: "webp",
      quality: 82,
    });
    console.log(`${id}: ${output}/${id}.png`);
  }
  if (errors.length) throw new Error(errors.join("\n"));
} finally {
  await browser.close();
}
