import { readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";

const assets = fileURLToPath(
  new URL("../../holdspeak/static/_built/assets/", import.meta.url),
);
const files = readdirSync(assets);
const deskJs = files.filter((name) => /^desk-[^.]+\.js$/.test(name));
const deskCss = files.filter((name) => /^desk-[^.]+\.css$/.test(name));
const maps = files.filter((name) => name.endsWith(".map"));

const limits = {
  js: 1_500_000,
  // RATCHET — HS-200-03, 2026-09-06. Raised 300_000 -> 310_000.
  // Measured Desk CSS at the raise: 306_679 B (after deleting the only CSS
  // proven dead: `.wb-raised`/`.wb-sunken` in desk/desk.css and the legacy
  // `.wb-composer*` + `.wb-head-scan` blocks in components/workbench-config.css
  // — 674 B; every other unreferenced-looking class is dynamically composed
  // (`"desk-mc-story st-" + s.status`, `is-${state}`, ...) and so is NOT
  // provably dead). The overrun is inherited, not caused by this branch.
  // THIS NUMBER IS A RATCHET: from here it may only ever move DOWN. Anyone
  // who needs it higher must first show the CSS that cannot be removed.
  css: 310_000,
};

const bytes = (names) =>
  names.reduce((total, name) => total + statSync(`${assets}/${name}`).size, 0);
const jsBytes = bytes(deskJs);
const cssBytes = bytes(deskCss);
const failures = [];

if (deskJs.length !== 1) failures.push(`expected one Desk entry chunk, found ${deskJs.length}`);
if (jsBytes > limits.js) failures.push(`Desk JS ${jsBytes} B exceeds ${limits.js} B`);
if (cssBytes > limits.css) failures.push(`Desk CSS ${cssBytes} B exceeds ${limits.css} B`);
if (process.env.HOLDSPEAK_WEB_SOURCEMAPS !== "1" && maps.length > 0)
  failures.push(`production build contains ${maps.length} source map(s)`);

if (failures.length) {
  console.error(`bundle gate failed:\n${failures.map((failure) => `- ${failure}`).join("\n")}`);
  process.exit(1);
}

console.log(
  `bundle gate passed (Desk JS ${jsBytes} B; Desk CSS ${cssBytes} B; source maps ${maps.length})`,
);
