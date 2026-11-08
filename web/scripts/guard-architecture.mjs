import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, extname, join, relative } from "node:path";
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
  /from\s*["'][^"']*\/surface\/(Surface|gadgets|roving|Material|SurfaceFooter|wings|citations|format|foot|title|sparse|LedgerFilter|patterns|controls|graph|objects)["']/;
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

/* ── HS-S53 destination owner closure ──
 * The one destination form and the destination account words live in
 * src/features/channels. Their import closure (static imports, re-exports
 * and dynamic import(), type imports included) must not reach the Settings
 * screen or the stateful Send module. The surface library (src/desk/surface,
 * not its send/ sub-barrel) is the public material and a boundary: the walk
 * does not enter it, because its barrel reaches the desk store and through
 * the app registry every core. This is a lexical check of the source graph,
 * not a runtime or bundle measurement. */
const DESTINATION_OWNERS = [
  "src/features/channels/DestinationForm.tsx",
  "src/features/channels/accountChip.ts",
];
const DESTINATION_FORBIDDEN = new Set([
  "src/pages/cores/connections/ConnectionsPane.tsx",
  "src/pages/cores/connections/Destinations.tsx",
  "src/desk/surface/send/SendWell.tsx",
  "src/desk/surface/send/index.ts",
]);
const IMPORT_SPEC_RE =
  /(?:\bfrom\s*|\bimport\s*\(\s*|^\s*import\s+)["'](\.{1,2}\/[^"']+)["']/gm;
const resolveSource = (fromName, spec) => {
  const base = join(root, dirname(fromName), spec);
  for (const candidate of [base, `${base}.ts`, `${base}.tsx`, join(base, "index.ts"), join(base, "index.tsx")]) {
    if (/\.(?:tsx?|mjs|js)$/.test(candidate) && existsSync(candidate) && statSync(candidate).isFile())
      return relative(root, candidate);
  }
  return null; // CSS, JSON and assets carry no imports to follow
};
const closureFrom = (start) => {
  const via = new Map([[start, null]]);
  const queue = [start];
  while (queue.length) {
    const name = queue.shift();
    const text = readFileSync(join(root, name), "utf8");
    for (const match of text.matchAll(IMPORT_SPEC_RE)) {
      const next = resolveSource(name, match[1]);
      if (!next || via.has(next)) continue;
      via.set(next, name);
      const material = next.startsWith("src/desk/surface/") && !next.startsWith("src/desk/surface/send/");
      if (!material) queue.push(next);
    }
  }
  return via;
};
for (const owner of DESTINATION_OWNERS) {
  if (!existsSync(join(root, owner))) {
    failures.push(`destination owner missing: ${owner}`);
    continue;
  }
  const via = closureFrom(owner);
  for (const forbidden of DESTINATION_FORBIDDEN) {
    if (!via.has(forbidden)) continue;
    const path = [];
    for (let at = forbidden; at; at = via.get(at)) path.unshift(at);
    failures.push(`destination owner reaches ${forbidden}: ${path.join(" -> ")}`);
  }
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
