import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const puppeteer = require("../../../../web/node_modules/puppeteer");

const root = "http://127.0.0.1:4399/";
const visualRoot = dirname(fileURLToPath(import.meta.url));
const assetRoot = resolve(visualRoot, "assets");
const states = [
  "desk-spatial", "desk-list", "desk-context", "desk-drawer", "windows-two", "windows-expose",
  "speak-ready", "speak-progress", "meeting-review", "thread", "agents", "settings", "info",
  "drop-valid", "drop-refusal", "command", "shade", "high-contrast", "pseudo",
];
const manifestPath = resolve(visualRoot, "artboards.json");
const artboards = JSON.parse(readFileSync(manifestPath, "utf8"));
const artboardRequirements = Object.fromEntries(artboards.map(({ id, requirement }) => [id, requirement]));
const requirementsPath = resolve(visualRoot, "../data/requirements.json");
const requirements = JSON.parse(readFileSync(requirementsPath, "utf8")).requirements;
const requirementIds = new Set(requirements.map(({ id }) => id));
const missingManifestFields = artboards.filter(({ id, label, group, tone, requirement }) => !id || !label || !group || !tone || !requirement);
if (missingManifestFields.length > 0) {
  throw new Error(`Incomplete artboard manifest entries in ${manifestPath}: ${JSON.stringify(missingManifestFields)}`);
}
const unknownRequirementIds = Object.entries(artboardRequirements)
  .filter(([, requirement]) => !requirementIds.has(requirement));
if (unknownRequirementIds.length > 0) {
  throw new Error(`Unknown artboard requirement IDs in ${requirementsPath}: ${JSON.stringify(unknownRequirementIds)}`);
}
const unmappedStates = states.filter((id) => !Object.hasOwn(artboardRequirements, id));
if (unmappedStates.length > 0) {
  throw new Error(`Artboard capture state has no requirement mapping: ${unmappedStates.join(", ")}`);
}
const manifestIds = artboards.map(({ id }) => id);
if (JSON.stringify(manifestIds) !== JSON.stringify(states)) {
  throw new Error(`Capture states do not match gallery manifest ${manifestPath}`);
}
const primary = new Set([
  "desk-spatial", "desk-list", "desk-context", "speak-ready", "speak-progress", "meeting-review", "thread", "agents",
]);
const manifestPrimary = new Set(artboards.filter(({ primary: isPrimary }) => isPrimary).map(({ id }) => id));
if (JSON.stringify([...manifestPrimary].sort()) !== JSON.stringify([...primary].sort())) {
  throw new Error(`Capture compact set does not match gallery manifest ${manifestPath}`);
}

const browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox"] });
const reports = [];
const failures = [];
for (const id of states) {
  for (const compact of primary.has(id) ? [false, true] : [false]) {
    const width = compact ? 393 : 1440;
    const height = compact ? 844 : 900;
    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 1 });
    const errors = [];
    page.on("console", (message) => {
      if (message.type() === "error" && !message.text().includes("favicon")) errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(error.stack));
    await page.goto(`${root}?artboard=${id}&bare=1&shot=3`, { waitUntil: "networkidle0" });
    await new Promise((resolve) => setTimeout(resolve, 900));
    const report = await page.evaluate(() => ({
      bodyWidth: document.body.scrollWidth,
      innerWidth,
      bodyHeight: document.body.scrollHeight,
      windowRects: [...document.querySelectorAll(".desk-window")].map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height),
          scroll: element.scrollHeight, client: element.clientHeight,
        };
      }),
      overflow: [...document.querySelectorAll("*")]
        .filter((element) => {
          const rect = element.getBoundingClientRect();
          return rect.right > innerWidth + 1 || rect.left < -1;
        })
        .slice(0, 5)
        .map((element) => element.className),
    }));
    const suffix = compact ? "compact" : "wide";
    await page.screenshot({ path: `${assetRoot}/${id}-${suffix}.png` });
    reports.push({ id, suffix, errors, ...report });
    if (errors.length > 0 || report.bodyWidth > report.innerWidth || report.overflow.length > 0) {
      failures.push({
        id,
        suffix,
        errors,
        horizontalOverflow: report.bodyWidth > report.innerWidth || report.overflow.length > 0,
        bodyWidth: report.bodyWidth,
        innerWidth: report.innerWidth,
        overflow: report.overflow,
      });
    }
    await page.close();
  }
}
await browser.close();
console.log(JSON.stringify(reports, null, 2));
if (failures.length > 0) {
  console.error(`Capture validation failed for ${failures.length} face(s):`);
  console.error(JSON.stringify(failures, null, 2));
  process.exitCode = 1;
}
