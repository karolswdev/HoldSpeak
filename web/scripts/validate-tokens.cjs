#!/usr/bin/env node
/**
 * HS-96-02 — the token gate, adapted from the vendored design-system
 * skill's validate-tokens.cjs for this repo: component CSS must reference
 * tokens, never raw values. Scope (the honest v1): color literals (hex,
 * rgb/rgba), z-index literals, and ms durations in `web/src/**` CSS.
 * `tokens.css` is the one allowed raw-value home; deliberate exceptions
 * live in web/token-allowlist.json, each with a reason.
 *
 * Usage: node scripts/validate-tokens.cjs
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "src");
const ALLOWLIST = path.join(ROOT, "token-allowlist.json");

const PATTERNS = [
  {
    kind: "hex color",
    regex: /#[0-9A-Fa-f]{3,8}\b/g,
    hint: "use a semantic/component color token",
  },
  {
    kind: "rgb color",
    regex: /rgba?\([^)]*\)/g,
    hint: "use a color token (or add a primitive with a doc string)",
  },
  {
    kind: "z-index literal",
    regex: /z-index:\s*-?\d+/g,
    hint: "use a --desk-z-* / --z-* ladder token",
  },
  {
    kind: "ms duration",
    regex: /\b\d+ms\b/g,
    hint: "use a --duration-* token",
  },
];

function cssFiles(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) cssFiles(full, out);
    else if (entry.name.endsWith(".css") && entry.name !== "tokens.css")
      out.push(full);
  }
  return out;
}

function main() {
  const allow = JSON.parse(fs.readFileSync(ALLOWLIST, "utf-8"));
  const allowed = new Map(
    allow.entries.map((entry) => [`${entry.file}::${entry.match}`, entry]),
  );
  const used = new Set();
  const violations = [];

  for (const file of cssFiles(SRC)) {
    const rel = path.relative(ROOT, file);
    const text = fs.readFileSync(file, "utf-8");
    const lines = text.split("\n");
    lines.forEach((line, index) => {
      const noComment = line.replace(/\/\*.*?\*\//g, "");
      if (noComment.includes("var(--")) {
        // A declaration may mix a var() with a literal fallback — still
        // scan the remainder after removing var() bodies.
      }
      const scannable = noComment.replace(/var\(--[^)]*\)/g, "");
      for (const pattern of PATTERNS) {
        for (const match of scannable.match(pattern.regex) || []) {
          const key = `${rel}::${match}`;
          if (allowed.has(key)) {
            used.add(key);
            continue;
          }
          violations.push(
            `${rel}:${index + 1}: ${pattern.kind} \`${match}\` — ${pattern.hint}`,
          );
        }
      }
    });
  }

  const stale = allow.entries.filter(
    (entry) => !used.has(`${entry.file}::${entry.match}`),
  );

  if (violations.length) {
    console.error(`token gate: ${violations.length} raw value(s) in component CSS\n`);
    for (const v of violations.slice(0, 40)) console.error("  " + v);
    if (violations.length > 40)
      console.error(`  … and ${violations.length - 40} more`);
    process.exit(1);
  }
  if (stale.length) {
    console.error("token gate: stale allow-list entries (remove them):");
    for (const entry of stale) console.error(`  ${entry.file} :: ${entry.match}`);
    process.exit(1);
  }
  console.log(
    `token gate: clean (${allow.entries.length} allow-listed exceptions, all in use)`,
  );
}

main();
