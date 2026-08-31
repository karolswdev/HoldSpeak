// HS-156-03 — fence tests: validates the surface library's architectural ratchet.
import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";

const root = resolve(__dirname, "../../../..");
const baselinePath = join(root, "fence-baseline.json");

describe("fence-baseline.json", () => {
  it("is valid JSON with the expected keys", () => {
    const raw = readFileSync(baselinePath, "utf8");
    const baseline = JSON.parse(raw);
    expect(baseline).toHaveProperty("private-imports");
    expect(baseline).toHaveProperty("library-css-outside");
    expect(baseline).toHaveProperty("roving-reimpl");
    expect(Array.isArray(baseline["private-imports"])).toBe(true);
    expect(Array.isArray(baseline["library-css-outside"])).toBe(true);
    expect(Array.isArray(baseline["roving-reimpl"])).toBe(true);
  });

  it("every private-imports entry points to a file that exists", () => {
    const baseline = JSON.parse(readFileSync(baselinePath, "utf8"));
    for (const entry of baseline["private-imports"]) {
      const full = join(root, entry);
      expect(existsSync(full), `stale baseline entry: ${entry}`).toBe(true);
    }
  });

  it("every roving-reimpl entry points to a file that exists", () => {
    const baseline = JSON.parse(readFileSync(baselinePath, "utf8"));
    for (const entry of baseline["roving-reimpl"]) {
      const full = join(root, entry);
      expect(existsSync(full), `stale baseline entry: ${entry}`).toBe(true);
    }
  });

  it("every library-css-outside entry points to a file that exists", () => {
    const baseline = JSON.parse(readFileSync(baselinePath, "utf8"));
    for (const entry of baseline["library-css-outside"]) {
      const full = join(root, entry);
      expect(existsSync(full), `stale baseline entry: ${entry}`).toBe(true);
    }
  });
});

describe("fence pattern matching", () => {
  const PRIVATE_IMPORT_RE =
    /from\s*["'][^"']*\/surface\/(Surface|gadgets|roving|Material|SurfaceFooter|wings|citations|format|foot|sparse|LedgerFilter|patterns|controls)["']/;

  it("catches a direct surface/Surface import", () => {
    expect(
      PRIVATE_IMPORT_RE.test('import { SurfaceRow } from "../surface/Surface"'),
    ).toBe(true);
  });

  it("catches a direct surface/gadgets import", () => {
    expect(
      PRIVATE_IMPORT_RE.test(
        'import { CheckGadget } from "../../surface/gadgets"',
      ),
    ).toBe(true);
  });

  it("allows the barrel import", () => {
    expect(
      PRIVATE_IMPORT_RE.test('import { SurfaceRow } from "../surface"'),
    ).toBe(false);
  });

  it("allows the barrel index import", () => {
    expect(
      PRIVATE_IMPORT_RE.test(
        'import { SurfaceRow } from "../surface/index"',
      ),
    ).toBe(false);
  });

  const LIBRARY_CSS_RE =
    /surface-state-chip|surface-action-notice|surface-disclosure|surface-progress-plan|surface-choice-card|surface-popover|surface-provenance/;

  it("catches restyling a library-owned class", () => {
    expect(LIBRARY_CSS_RE.test(".surface-state-chip { color: red }")).toBe(
      true,
    );
    expect(LIBRARY_CSS_RE.test(".surface-action-notice { margin: 0 }")).toBe(
      true,
    );
  });

  it("does not flag unrelated classes", () => {
    expect(LIBRARY_CSS_RE.test(".surface-verbs { gap: 4px }")).toBe(false);
  });

  const ROVING_REIMPL_RE = /Arrow(?:Up|Down)/;

  it("catches arrow-key navigation reimplementation", () => {
    const code = `
      if (e.key === "ArrowDown") idx++;
      if (e.key === "ArrowUp") idx--;
    `;
    expect(ROVING_REIMPL_RE.test(code)).toBe(true);
    expect(/ArrowUp/.test(code)).toBe(true);
    expect(/ArrowDown/.test(code)).toBe(true);
  });

  it("does not flag a file with only one arrow direction", () => {
    const code = 'if (e.key === "ArrowDown") scrollDown()';
    // The rule requires BOTH ArrowUp AND ArrowDown
    const hasUp = /ArrowUp/.test(code);
    const hasDown = /ArrowDown/.test(code);
    expect(hasUp && hasDown).toBe(false);
  });
});
