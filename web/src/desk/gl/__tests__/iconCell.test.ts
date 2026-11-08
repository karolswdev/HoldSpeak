/** HS-105-01 — the icon-cell guard: real state images on disk for EVERY
 * pool sprite, and objects at a neutral rest state. The WebGL scene-model
 * cases are parked with the scene model (2026-11-08, no entry reaches it). */
import { describe, expect, it } from "vitest";
import { cpSync, existsSync, mkdtempSync, renameSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { objMotion } from "../../world";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { VARIANTS, allSpriteNames, agentSpriteName } from "../../sprites";

const SPRITES_DIR = join(
  dirname(fileURLToPath(import.meta.url)),
  "../../../../public/desk/sprites",
);

// PHILO-14 A0c: both drawn sizes, the 64 px icon set (root) and the 32 px
// list set (`32/`), and Icons D's 20 px glyph set (`20/`) carry every base
// name in all three states.
function requiredFiles(): string[] {
  return ["", "32/", "20/"].flatMap((dir) =>
    allSpriteNames().flatMap((name) =>
      ["", "_sel", "_stale"].map((suffix) => `${dir}${name}${suffix}.png`),
    ),
  );
}

function missingStateFiles(dir: string): string[] {
  return requiredFiles().filter((file) => !existsSync(join(dir, file)));
}

describe("the cell contract (HS-105-01)", () => {
  it("keeps every object at a neutral rest state", () => {
    const m = objMotion({ kind: "note", id: "x", title: "x", ref: {} as any });
    expect(m.phase).toBe(0);
    expect(m.tilt).toBe(0);
    expect(m.scale).toBe(1);
  });

  it("has a real state-image set on disk for every sprite the picker can return", () => {
    // PHILO-14 A0b round 2: the pools AND the helper-selected agent
    // sprites (agent-codex is not in any pool).
    const names = allSpriteNames();
    expect(names).toContain(agentSpriteName("codex"));
    expect(names).toContain(agentSpriteName("claude"));
    expect(names.length).toBeGreaterThan(10);
    expect(missingStateFiles(SPRITES_DIR)).toEqual([]);
  });

  it("the guard fails when any one required file is withheld", () => {
    const required = requiredFiles();
    expect(required).toContain("agent-codex_sel.png");
    expect(required).toContain("32/agent-codex_sel.png");
    expect(required).toContain("32/memory_stale.png");
    const dir = mkdtempSync(join(tmpdir(), "hs-sprite-guard-"));
    try {
      cpSync(SPRITES_DIR, dir, { recursive: true });
      expect(missingStateFiles(dir)).toEqual([]);
      for (const file of required) {
        renameSync(join(dir, file), join(dir, `${file}.withheld`));
        expect(missingStateFiles(dir), `withholding ${file}`).toEqual([file]);
        renameSync(join(dir, `${file}.withheld`), join(dir, file));
      }
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("a directory is a drawer, never paper", () => {
    // Icons D (2026-10-24): a zone folder; its hue picks the front colour.
    expect((VARIANTS as Record<string, string[]>).directory).toEqual([
      "zone-drawer",
    ]);
  });

  it("one kind = one silhouette (PHILO-14 A0b, the D1 mold)", () => {
    for (const [kind, pool] of Object.entries(
      VARIANTS as Record<string, string[]>,
    ))
      expect(pool.length, `${kind} pool`).toBe(1);
  });
});
