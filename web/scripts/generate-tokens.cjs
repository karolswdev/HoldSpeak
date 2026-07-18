#!/usr/bin/env node
/**
 * HS-96-01 — generate src/styles/tokens.css from design-tokens.json.
 *
 * Adapted from the vendored design-system skill's generate-tokens.cjs:
 * same {primitive.path.ref} reference syntax, purpose-built emitter for
 * this repo (plain CSS, three labeled layers, the reduced-motion block,
 * no Tailwind output). The JSON is the source of truth; the CSS is a
 * build artifact kept in-tree so `git pull` needs no npm step.
 *
 * Usage:
 *   node scripts/generate-tokens.cjs            # write tokens.css
 *   node scripts/generate-tokens.cjs --check    # fail if CSS drifted
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const CONFIG = path.join(ROOT, "design-tokens.json");
const OUTPUT = path.join(ROOT, "src", "styles", "tokens.css");

function resolveReference(value, tokens) {
  if (typeof value !== "string" || !value.startsWith("{") || !value.endsWith("}")) {
    return value;
  }
  const segments = value.slice(1, -1).split(".");
  let node = tokens;
  for (const key of segments) {
    node = node?.[key];
    if (node === undefined) {
      throw new Error(`unresolved token reference: ${value}`);
    }
  }
  if (typeof node === "object" && node !== null && "value" in node) {
    return node.value;
  }
  if (typeof node !== "string") {
    throw new Error(`reference does not resolve to a value: ${value}`);
  }
  return node;
}

function emitPrimitives(tokens) {
  const lines = [];
  const walk = (prefix, node) => {
    for (const [key, entry] of Object.entries(node)) {
      if (key.startsWith("$")) continue;
      if (entry && typeof entry === "object" && "value" in entry) {
        const name = `--${prefix}-${key}`.replace(/\./g, "-");
        const doc = entry.doc ? ` /* ${entry.doc} */` : "";
        lines.push(`  ${name}: ${entry.value};${doc}`);
      } else if (entry && typeof entry === "object") {
        walk(`${prefix}-${key}`, entry);
      }
    }
  };
  walk("p-color", tokens.primitive.color);
  walk("p-font", tokens.primitive.font);
  return lines;
}

function emitGroups(groups, tokens) {
  return groups.map((entry) => {
    const value = resolveReference(entry.value, tokens);
    const doc = entry.doc ? ` /* ${entry.doc} */` : "";
    return `  ${entry.name}: ${value};${doc}`;
  });
}

function generate(tokens) {
  const out = [];
  out.push("/*");
  out.push(" * HoldSpeak design tokens — \"Signal\" (HS-30-03; three-layer since HS-96-01).");
  out.push(" *");
  out.push(" * GENERATED FILE — do not edit. The source of truth is");
  out.push(" * web/design-tokens.json; regenerate with:");
  out.push(" *");
  out.push(" *   node scripts/generate-tokens.cjs");
  out.push(" *");
  out.push(" * Layers (the vendored design-system skill's architecture):");
  out.push(" *   1. PRIMITIVE  (--p-*)  raw values; never referenced by components.");
  out.push(" *   2. SEMANTIC             the canonical Signal vocabulary components use");
  out.push(" *                           (names and computed values preserved verbatim");
  out.push(" *                           from the HS-30-03 hand-written file).");
  out.push(" *   3. COMPONENT            the Desk OS chrome (HS-95 values, codified).");
  out.push(" *");
  out.push(" * Dark-only by design (design-language-signal.md, 2026-06-01); the");
  out.push(" * semantic layer is where a future light theme would attach.");
  out.push(" */");
  out.push("");
  out.push('@import "open-props/style";');
  out.push("");
  out.push(":root {");
  out.push("  color-scheme: dark;");
  out.push("");
  out.push("  /* ============================================================");
  out.push("   * 1. PRIMITIVE TOKENS (raw values — components never use these)");
  out.push("   * ============================================================ */");
  out.push("");
  out.push(...emitPrimitives(tokens));
  out.push("");
  out.push("  /* ============================================================");
  out.push("   * 2. SEMANTIC TOKENS (the canonical Signal vocabulary)");
  out.push("   * ============================================================ */");
  out.push("");
  out.push(...emitGroups(tokens.semantic.groups, tokens));
  out.push("");
  out.push("  /* ============================================================");
  out.push("   * 3. COMPONENT TOKENS (the Desk OS chrome — HS-95 values)");
  out.push("   * ============================================================ */");
  out.push("");
  out.push(...emitGroups(tokens.component.groups, tokens));
  out.push("}");
  out.push("");
  out.push("@media (prefers-reduced-motion: reduce) {");
  out.push("  :root {");
  out.push("    --duration-short: 0ms;");
  out.push("    --duration-medium: 0ms;");
  out.push("    --duration-long: 0ms;");
  out.push("  }");
  out.push("");
  out.push("  *,");
  out.push("  *::before,");
  out.push("  *::after {");
  out.push("    animation-duration: 0ms !important;");
  out.push("    animation-iteration-count: 1 !important;");
  out.push("    transition-duration: 0ms !important;");
  out.push("    scroll-behavior: auto !important;");
  out.push("  }");
  out.push("}");
  out.push("");
  return out.join("\n");
}

function main() {
  const check = process.argv.includes("--check");
  const tokens = JSON.parse(fs.readFileSync(CONFIG, "utf-8"));
  const css = generate(tokens);
  if (check) {
    const current = fs.existsSync(OUTPUT) ? fs.readFileSync(OUTPUT, "utf-8") : "";
    if (current !== css) {
      console.error(
        "tokens.css drifted from design-tokens.json — run: node scripts/generate-tokens.cjs",
      );
      process.exit(1);
    }
    console.log("tokens.css matches design-tokens.json");
    return;
  }
  fs.writeFileSync(OUTPUT, css);
  console.log(`wrote ${path.relative(ROOT, OUTPUT)} (${css.split("\n").length} lines)`);
}

main();
