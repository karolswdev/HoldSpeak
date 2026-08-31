import { readFileSync, readdirSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const source = join(root, "src");
const files = [];
const walk = (directory) => {
  for (const name of readdirSync(directory)) {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) walk(path);
    else files.push(path);
  }
};
walk(source);

const failures = [];
const directFetchAllowlist = new Set([
  // Static, same-origin sound assets are decoded as ArrayBuffers; this is not
  // an application API request and therefore does not belong in apiFetch.
  "src/lib/sfx.ts",
]);
const isTestSource = (name) =>
  /(?:^|\/)__tests__\//.test(name) || /\.(?:test|spec)\.[cm]?[jt]sx?$/.test(name);
const packageJson = JSON.parse(
  readFileSync(join(root, "package.json"), "utf8"),
);
for (const dependency of ["astro", "@astrojs/react", "alpinejs"]) {
  if (
    packageJson.dependencies?.[dependency] ||
    packageJson.devDependencies?.[dependency]
  )
    failures.push(`forbidden dependency: ${dependency}`);
}
for (const file of files) {
  const name = relative(root, file);
  if (extname(file) === ".astro") failures.push(`Astro source: ${name}`);
  if (
    ![".ts", ".tsx", ".css", ".d.ts"].some((extension) =>
      file.endsWith(extension),
    )
  )
    continue;
  const text = readFileSync(file, "utf8");
  if (/\bAlpine\b|x-(?:data|init|show|text)|client:(?:only|load)/i.test(text))
    failures.push(`legacy directive/runtime marker: ${name}`);
  if (/\.innerHTML\s*=|\.outerHTML\s*=|insertAdjacentHTML\s*\(/.test(text))
    failures.push(`runtime HTML injection: ${name}`);
  if (
    !isTestSource(name) &&
    /document\.(?:querySelector|querySelectorAll)\s*\(/.test(text)
  )
    failures.push(`global selector bootstrap: ${name}`);
  if (
    /\bfetch\s*\(/.test(text) &&
    name !== "src/lib/api.ts" &&
    !directFetchAllowlist.has(name)
  )
    failures.push(`request bypasses typed API client: ${name}`);
}

/* ── HS-156-03 surface library fence ── */

const baselinePath = join(root, "fence-baseline.json");
let baseline;
try {
  baseline = JSON.parse(readFileSync(baselinePath, "utf8"));
} catch {
  baseline = { "private-imports": [], "library-css-outside": [], "roving-reimpl": [] };
}
const baselinePrivate = new Set(baseline["private-imports"] || []);
const baselineCss = new Set(baseline["library-css-outside"] || []);
const baselineRoving = new Set(baseline["roving-reimpl"] || []);

const PRIVATE_IMPORT_RE =
  /from\s*["'][^"']*\/surface\/(Surface|gadgets|roving|Material|SurfaceFooter|wings|citations|format|foot|title|sparse|LedgerFilter|patterns|controls|graph)["']/;
const LIBRARY_CSS_RE =
  /surface-state-chip|surface-action-notice|surface-disclosure|surface-progress-plan|surface-choice-card|surface-popover|surface-provenance|surface-topology/;
const ROVING_REIMPL_RE = /Arrow(?:Up|Down)/;

for (const file of files) {
  const name = relative(root, file);
  if (![".ts", ".tsx"].some((ext) => file.endsWith(ext))) continue;
  if (isTestSource(name)) continue;
  if (name.startsWith("src/desk/surface/")) continue;
  if (!name.startsWith("src/desk/")) continue;

  const text = readFileSync(file, "utf8");

  // Rule 1: barrel-only imports
  if (PRIVATE_IMPORT_RE.test(text) && !baselinePrivate.has(name))
    failures.push(`surface fence: private-import: ${name}`);

  // Rule 3: roving reimplementation
  if (
    ROVING_REIMPL_RE.test(text) &&
    /ArrowUp/.test(text) &&
    /ArrowDown/.test(text) &&
    !baselineRoving.has(name)
  )
    failures.push(`surface fence: roving-reimpl: ${name}`);
}

// Rule 2: library CSS outside surface (scans CSS too)
for (const file of files) {
  const name = relative(root, file);
  if (![".css", ".ts", ".tsx"].some((ext) => file.endsWith(ext))) continue;
  if (isTestSource(name)) continue;
  if (name.startsWith("src/desk/surface/")) continue;

  const text = readFileSync(file, "utf8");
  if (LIBRARY_CSS_RE.test(text) && !baselineCss.has(name))
    failures.push(`surface fence: library-css-outside: ${name}`);
}

if (failures.length) {
  console.error(
    `React architecture guard failed:\n${failures.map((failure) => `- ${failure}`).join("\n")}`,
  );
  process.exit(1);
}
console.log(
  `React architecture guard passed (${files.length} source files; zero framework residue).`,
);
