// HoldSpeak route screenshot harness (HS-30 follow-up).
//
// One command — `npm run shots` — builds the site, serves the built
// output with `astro preview`, drives a headless browser over every
// route + a couple of states/viewports, writes PNGs to a timestamped
// folder under web/.shots/, then tears the server down.
//
// Use it to eyeball the UI after any change without hand-running a
// browser. Add a route below to capture more. Output is gitignored.
//
//   cd web && npm run shots
//   open web/.shots/<latest>/
//
// Env knobs:
//   SHOTS_DIR=path   override the output directory
//   SHOTS_PORT=4321  override the preview port
//   SHOTS_BASE=/_built  override the base path (must match astro.config)

import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import puppeteer from "puppeteer";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PORT = process.env.SHOTS_PORT || "4321";
const BASE = process.env.SHOTS_BASE || "/_built";
const ORIGIN = `http://127.0.0.1:${PORT}`;

const stamp = new Date()
  .toISOString()
  .replace(/[:.]/g, "-")
  .replace("T", "_")
  .slice(0, 19);
const outDir = process.env.SHOTS_DIR || resolve(webRoot, ".shots", stamp);

// name, path (relative to BASE), width, height, fullPage
const ROUTES = [
  ["runtime", "/", 1440, 900, true],
  ["dictation", "/dictation/", 1440, 1100, true],
  ["history", "/history/", 1440, 1100, true],
  ["activity", "/activity/", 1440, 1100, true],
  ["companion", "/companion/", 1440, 1000, true],
  ["components", "/design/components/", 1440, 1200, true],
  ["settings-drawer", "/#settings", 1440, 900, false],
  ["runtime-mobile", "/", 560, 1000, false],
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitForServer(url, tries = 60) {
  for (let i = 0; i < tries; i++) {
    try {
      const res = await fetch(url);
      if (res.ok) return true;
    } catch {
      /* not up yet */
    }
    await sleep(500);
  }
  throw new Error(`preview server did not come up at ${url}`);
}

async function main() {
  mkdirSync(outDir, { recursive: true });

  // Serve the already-built output. `astro build` runs first via the
  // npm script, so preview just hosts ../holdspeak/static/_built.
  const astroBin = resolve(webRoot, "node_modules", ".bin", "astro");
  const server = spawn(astroBin, ["preview", "--port", PORT], {
    cwd: webRoot,
    stdio: "ignore",
  });

  let browser;
  try {
    await waitForServer(`${ORIGIN}${BASE}/`);
    browser = await puppeteer.launch({
      headless: "new",
      args: ["--no-sandbox", "--hide-scrollbars"],
    });
    const page = await browser.newPage();

    for (const [name, path, w, h, fullPage] of ROUTES) {
      await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
      const url = `${ORIGIN}${BASE}${path}`;
      try {
        await page.goto(url, { waitUntil: "networkidle2", timeout: 25000 });
        await sleep(1200); // let Alpine / webfonts settle
        await page.screenshot({ path: resolve(outDir, `${name}.png`), fullPage });
        console.log(`  ✓ ${name.padEnd(18)} ${path}`);
      } catch (e) {
        console.log(`  ✗ ${name.padEnd(18)} ${path} — ${e.message}`);
      }
    }
  } finally {
    if (browser) await browser.close();
    server.kill("SIGTERM");
  }

  console.log(`\nScreenshots → ${outDir}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
