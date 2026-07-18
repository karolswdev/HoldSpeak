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
const TS_OUTPUT = path.join(ROOT, "src", "lib", "tokens.gen.ts");

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

function componentValue(tokens, name) {
  const row = tokens.component.groups.find((entry) => entry.name === name);
  if (!row) throw new Error(`missing component token ${name}`);
  return resolveReference(row.value, tokens);
}

function px(value) {
  return Number(String(value).replace(/px$/, ""));
}

function generateTs(tokens) {
  const out = [];
  out.push("// GENERATED FILE — do not edit (HS-96-02). Source of truth:");
  out.push("// web/design-tokens.json → node scripts/generate-tokens.cjs.");
  out.push("// The TS mirror of the Desk OS component tokens, so the window");
  out.push("// physics and the GL world can never drift from the CSS ladder.");
  out.push("");
  out.push("export const DESK_Z = {");
  out.push(`  canvas: ${componentValue(tokens, "--desk-z-canvas")},`);
  out.push(`  worldOverlay: ${componentValue(tokens, "--desk-z-world-overlay")},`);
  out.push(`  chrome: ${componentValue(tokens, "--desk-z-chrome")},`);
  out.push(`  windowBase: ${componentValue(tokens, "--desk-z-window-base")},`);
  out.push(`  dock: ${componentValue(tokens, "--desk-z-dock")},`);
  out.push(`  transient: ${componentValue(tokens, "--desk-z-transient")},`);
  out.push("} as const;");
  out.push("");
  out.push("export const DESK_WINDOW = {");
  out.push(`  margin: ${px(componentValue(tokens, "--desk-window-margin"))},`);
  out.push(`  grab: ${px(componentValue(tokens, "--desk-window-grab"))},`);
  out.push(`  cascade: ${px(componentValue(tokens, "--desk-window-cascade"))},`);
  out.push(`  snapTop: ${px(componentValue(tokens, "--desk-snap-top"))},`);
  out.push(`  snapBottom: ${px(componentValue(tokens, "--desk-snap-bottom"))},`);
  out.push("} as const;");
  out.push("");
  const glow = (kind) => componentValue(tokens, `--glow-${kind}`);
  out.push("export const GLOW_POOL: Record<string, string> = {");
  out.push(`  meeting: "${glow("meeting")}",`);
  out.push(`  note: "${glow("note")}",`);
  out.push(`  kb: "${glow("kb")}",`);
  out.push(`  recipe: "${glow("recipe")}",`);
  out.push(`  artifact: "${glow("artifact")}",`);
  out.push(`  chain: "${glow("chain")}",`);
  out.push(`  workflow: "${glow("meeting")}",`);
  out.push(`  directory: "${glow("directory")}",`);
  out.push(`  coder: "${glow("recipe")}",`);
  out.push("};");
  out.push("");
  const tint = (n) => componentValue(tokens, `--zone-tint-${n}`);
  out.push("export const ZONE_TINT_POOL = [");
  for (let i = 1; i <= 6; i++) out.push(`  "${tint(i)}",`);
  out.push("] as const;");
  out.push("");
  return out.join("\n");
}

function main() {
  const check = process.argv.includes("--check");
  const tokens = JSON.parse(fs.readFileSync(CONFIG, "utf-8"));
  const css = generate(tokens);
  const ts = generateTs(tokens);
  if (check) {
    const current = fs.existsSync(OUTPUT) ? fs.readFileSync(OUTPUT, "utf-8") : "";
    const currentTs = fs.existsSync(TS_OUTPUT) ? fs.readFileSync(TS_OUTPUT, "utf-8") : "";
    if (current !== css || currentTs !== ts) {
      console.error(
        "tokens drifted from design-tokens.json — run: node scripts/generate-tokens.cjs",
      );
      process.exit(1);
    }
    console.log("tokens.css and tokens.gen.ts match design-tokens.json");
    return;
  }
  fs.writeFileSync(OUTPUT, css);
  fs.writeFileSync(TS_OUTPUT, ts);
  console.log(`wrote ${path.relative(ROOT, OUTPUT)} and ${path.relative(ROOT, TS_OUTPUT)}`);
}

main();
