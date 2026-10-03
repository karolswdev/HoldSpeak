import { readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";

const assets = fileURLToPath(
  new URL("../../holdspeak/static/_built/assets/", import.meta.url),
);
const files = readdirSync(assets);
const deskJs = files.filter((name) => /^desk-[^.]+\.js$/.test(name));
const deskCss = files.filter((name) => /^desk-[^.]+\.css$/.test(name));
const maps = files.filter((name) => name.endsWith(".map"));

// No byte budgets (owner, 2026-10-03: "frig off with the ... budget on the
// bundle"). Sizes are reported, never gated. The gate keeps the two
// correctness checks: one Desk entry chunk, and no source maps in production.

const bytes = (names) =>
  names.reduce((total, name) => total + statSync(`${assets}/${name}`).size, 0);
const jsBytes = bytes(deskJs);
const cssBytes = bytes(deskCss);
const failures = [];

if (deskJs.length !== 1) failures.push(`expected one Desk entry chunk, found ${deskJs.length}`);
if (process.env.HOLDSPEAK_WEB_SOURCEMAPS !== "1" && maps.length > 0)
  failures.push(`production build contains ${maps.length} source map(s)`);

if (failures.length) {
  console.error(`bundle gate failed:\n${failures.map((failure) => `- ${failure}`).join("\n")}`);
  process.exit(1);
}

console.log(
  `bundle gate passed (Desk JS ${jsBytes} B; Desk CSS ${cssBytes} B; source maps ${maps.length})`,
);
