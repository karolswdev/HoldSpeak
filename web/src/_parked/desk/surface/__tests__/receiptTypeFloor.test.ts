// PHILO-3-04 — the receipt lines sit at or above the 12 px floor
// (docs/internal/checks/type-scale-ruling-2026-09-21.md, M7), paid in the
// LIBRARY, never as a face override. Reads the real stylesheets and resolves
// each `var(--token)` against the real generated tokens.
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const web = resolve(__dirname, "../../../..");
const read = (path: string) => readFileSync(resolve(web, path), "utf8");
const FLOOR_PX = 12;

const tokens = new Map<string, string>();
for (const match of read("src/styles/tokens.css").matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
  if (!tokens.has(match[1])) tokens.set(match[1], match[2].trim());
}

function px(value: string): number {
  const token = value.match(/^var\((--[\w-]+)\)$/);
  if (token) {
    const next = tokens.get(token[1]);
    if (!next) throw new Error(`unknown token ${token[1]}`);
    return px(next);
  }
  const rem = value.match(/^([\d.]+)rem$/);
  if (rem) return Number(rem[1]) * 16;
  const raw = value.match(/^([\d.]+)px$/);
  if (raw) return Number(raw[1]);
  throw new Error(`cannot resolve font-size ${value}`);
}

/** Every font-size declared in a rule whose selector list names `needle`. */
function sizesFor(css: string, needle: string): string[] {
  const out: string[] = [];
  const clean = css.replace(/\/\*[\s\S]*?\*\//g, "");
  for (const match of clean.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    if (!match[1].includes(needle)) continue;
    for (const size of match[2].matchAll(/font-size\s*:\s*([^;]+);/g)) out.push(size[1].trim());
  }
  return out;
}

const LIBRARY: Array<[string, string]> = [
  ["src/desk/surface/surface-footer.css", ".surface-footer-receipt-line"],
  ["src/desk/surface/surface-footer.css", ".surface-footer-egress"],
  ["src/desk/surface/surface.css", ".surface-receipt-line"],
];

describe("PHILO-3-04 receipt lines at the 12 px floor", () => {
  it.each(LIBRARY)("%s %s computes at 12 px or more", (file, selector) => {
    const sizes = sizesFor(read(file), selector);
    expect(sizes.length, `${selector} declares no font-size in ${file}`).toBeGreaterThan(0);
    for (const size of sizes) expect(px(size), `${selector} font-size ${size}`).toBeGreaterThanOrEqual(FLOOR_PX);
  });

  it("the Thought face does not re-size its receipt lines below the floor", () => {
    for (const size of sizesFor(read("src/desk/thought-workspace/thought-workspace.css"), "surface-footer-receipt")) {
      expect(px(size)).toBeGreaterThanOrEqual(FLOOR_PX);
    }
  });
});
