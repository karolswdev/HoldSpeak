// HS-156-03 — shot-sheet capture for the v1 library patterns gallery.
// Builds are assumed fresh; drives headless Chrome at 1440 and 393
// against the running HoldSpeak backend's /design/components gallery.
//
// Usage: HOLDSPEAK_PORT=53788 HOLDSPEAK_TOKEN=abc node scripts/shoot-gallery.mjs
//
// The token is the web_auth_token from the running backend's config.
// The SPA captures it from ?token= into tab-scoped storage on first load.
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PORT = process.env.HOLDSPEAK_PORT || "62119";
const TOKEN = process.env.HOLDSPEAK_TOKEN || "";
const ORIGIN = `http://127.0.0.1:${PORT}`;
const outDir = resolve(
  webRoot,
  "../pm/roadmap/holdspeak/phase-156-the-front-door/assets/story-03-shot-sheet",
);

mkdirSync(outDir, { recursive: true });

const WIDTHS = [1440, 393];
const HEIGHT = 1200;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function run() {
  // Verify the backend is reachable
  try {
    await fetch(`${ORIGIN}/_built/`);
  } catch {
    console.error(`Backend not reachable at ${ORIGIN}. Set HOLDSPEAK_PORT.`);
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--hide-scrollbars"],
  });

  const shots = [];

  try {
    for (const width of WIDTHS) {
      const page = await browser.newPage();
      await page.setViewport({ width, height: HEIGHT, deviceScaleFactor: 1 });

      // Load the SPA root through the real backend (with auth token).
      const tokenQs = TOKEN ? `?token=${encodeURIComponent(TOKEN)}` : "";
      const launchUrl = `${ORIGIN}/_built/${tokenQs}`;
      await page.goto(launchUrl, { waitUntil: "networkidle2", timeout: 30000 });

      // Skip onboarding if present: click "Continue later"
      const continueBtn = await page.evaluateHandle(() => {
        const btns = [...document.querySelectorAll("button")];
        return btns.find((b) => /continue.*later/i.test(b.textContent)) || null;
      });
      if (continueBtn && continueBtn.asElement()) {
        await continueBtn.asElement().click();
        await sleep(1500);
      }

      // Open the components gallery
      await page.evaluate(() => {
        window.history.replaceState({}, "", "/design/components");
        window.dispatchEvent(new PopStateEvent("popstate"));
      });
      await sleep(3000);

      // Shot 1: Full desk with the Components window visible (top)
      const topName = `gallery-top-${width}.png`;
      await page.screenshot({ path: resolve(outDir, topName) });
      shots.push({ component: "Gallery (gadgets)", state: "existing kit + buttons", width, file: topName });
      console.log(`  captured ${topName}`);

      // Scroll the Components window down to show v1 patterns.
      // The window's scrollable body is .desk-surface-body
      await page.evaluate(() => {
        const body = document.querySelector(".desk-surface-body");
        if (body) body.scrollTop = body.scrollHeight;
      });
      await sleep(500);

      // Shot 2: Scrolled to bottom showing v1 patterns
      const bottomName = `gallery-patterns-${width}.png`;
      await page.screenshot({ path: resolve(outDir, bottomName) });
      shots.push({ component: "Gallery (v1 patterns)", state: "StateChip, ActionNotice, Disclosure, ProgressPlan, ChoiceCardGroup, Popover, ProvenanceChip, Receipt", width, file: bottomName });
      console.log(`  captured ${bottomName}`);

      // Scroll to middle to get more patterns visible
      await page.evaluate(() => {
        const body = document.querySelector(".desk-surface-body");
        if (body) body.scrollTop = Math.floor(body.scrollHeight * 0.6);
      });
      await sleep(500);

      const midName = `gallery-mid-${width}.png`;
      await page.screenshot({ path: resolve(outDir, midName) });
      shots.push({ component: "Gallery (mid-scroll)", state: "ActionNotice, Disclosure, ProgressPlan", width, file: midName });
      console.log(`  captured ${midName}`);

      // Keyboard focus frame: scroll to top, then Tab through elements
      await page.evaluate(() => {
        const body = document.querySelector(".desk-surface-body");
        if (body) body.scrollTop = 0;
      });
      await sleep(300);
      for (let i = 0; i < 10; i++) {
        await page.keyboard.press("Tab");
      }
      await sleep(300);
      const focusName = `gallery-focus-${width}.png`;
      await page.screenshot({ path: resolve(outDir, focusName) });
      shots.push({ component: "Gallery (focus)", state: "keyboard focus visible", width, file: focusName });
      console.log(`  captured ${focusName}`);

      await page.close();
    }
  } finally {
    await browser.close();
  }

  // Generate index.md
  const lines = [
    "# Shot sheet: HS-156-03 The Library Patterns",
    "",
    "Gallery at /design/components with all v1 pattern states.",
    "Captured from the live backend with headless Chrome.",
    "",
    "| Component | State | Width | File | Reviewer | Verdict |",
    "| --- | --- | --- | --- | --- | --- |",
  ];
  for (const shot of shots) {
    lines.push(`| ${shot.component} | ${shot.state} | ${shot.width}px | [${shot.file}](./${shot.file}) | | |`);
  }
  lines.push("");
  writeFileSync(resolve(outDir, "index.md"), lines.join("\n"));

  console.log(`\nShot sheet written to ${outDir}`);
  console.log(`${shots.length} shots captured.`);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
