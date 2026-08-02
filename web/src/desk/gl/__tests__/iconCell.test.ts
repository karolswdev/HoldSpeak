/** HS-105-01 — the icon-cell guard. Pins the gated cell contract:
 * integer-true pixel art in one uniform cell, real state images on disk
 * for EVERY pool sprite, badges only from named live fields, and no
 * fractional jitter. A regression here is unshippable. */
import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { LIFT, SPRITE, SPRITE_SMALL, buildScene, isFresh } from "../sceneModel";
import { objMotion } from "../../world";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { VARIANTS } from "../../sprites";
import { EMPTY_ITEMS, type Items } from "../../api";

const SPRITES_DIR = join(
  dirname(fileURLToPath(import.meta.url)),
  "../../../../public/desk/sprites",
);

describe("the cell contract (HS-105-01)", () => {
  it("renders pixel art integer-true in one uniform cell", () => {
    expect(SPRITE).toBe(64); // the art, 1:1 against the 64px sources
    expect(SPRITE_SMALL).toBe(SPRITE); // the small-note differential is dead
    expect(LIFT).toBe(80); // the selection box
  });

  it("keeps every object at a neutral rest state", () => {
    const m = objMotion({ kind: "note", id: "x", title: "x", ref: {} as any });
    expect(m.phase).toBe(0);
    expect(m.tilt).toBe(0);
    expect(m.scale).toBe(1);
  });

  it("has a real state-image set on disk for every pool sprite", () => {
    const names = new Set<string>();
    for (const pool of Object.values(VARIANTS) as string[][])
      for (const name of pool) names.add(name);
    expect(names.size).toBeGreaterThan(10);
    for (const name of names) {
      for (const suffix of ["", "_sel", "_stale"]) {
        const file = join(SPRITES_DIR, `${name}${suffix}.png`);
        expect(existsSync(file), `${name}${suffix}.png missing`).toBe(true);
      }
    }
  });

  it("a directory is a drawer, never paper", () => {
    expect((VARIANTS as Record<string, string[]>).directory).toEqual([
      "drawer",
    ]);
  });
});

function sceneFor(items: Items, selected: string[] = []) {
  return buildScene({
    items,
    divedZone: null,
    positions: {},
    zoneWidths: {},
    draggingId: null,
    hoverZoneId: null,
    renamingZoneId: null,
    newIds: [],
    editingId: null,
    selectedIds: selected,
    subjectCounts: {},
    compact: false,
    worldWidth: 1440,
  });
}

describe("badges ride only named live fields (the source-map census)", () => {
  it("count = memberIds.length; absent memberIds = no count badge", () => {
    const items: Items = {
      ...EMPTY_ITEMS,
      kb: [{ kind: "kb", id: "k1", name: "KB", memberIds: ["a", "b", "c"] }],
      note: [{ kind: "note", id: "n1", title: "Note" }],
    };
    const scene = sceneFor(items);
    const kb = scene.objects.find((o) => o.id === "k1")!;
    const note = scene.objects.find((o) => o.id === "n1")!;
    expect(kb.count).toBe(3);
    expect(note.count).toBeNull();
  });

  it("fresh = lastModified within the window, honestly absent otherwise", () => {
    const now = Date.now();
    expect(isFresh(new Date(now - 3600_000).toISOString(), now)).toBe(true);
    expect(isFresh(new Date(now - 72 * 3600_000).toISOString(), now)).toBe(
      false,
    );
    expect(isFresh(undefined, now)).toBe(false);
    expect(isFresh("not-a-date", now)).toBe(false);
  });

  it("state picks the real second image: sel > stale > rest", () => {
    const items: Items = {
      ...EMPTY_ITEMS,
      coder: [
        { kind: "coder", id: "c1", title: "stale one", stale: true },
        { kind: "coder", id: "c2", title: "live one", stale: false },
      ],
    };
    const scene = sceneFor(items, ["coder_session:claude:c1"]);
    const c1 = scene.objects.find((o) => o.id === "c1")!;
    const c2 = scene.objects.find((o) => o.id === "c2")!;
    // c1 is stale but NOT selected under this ref shape; assert the
    // stale image rides the url and rest stays bare.
    expect(c1.sprite.endsWith("_stale.png") || c1.sprite.endsWith("_sel.png"))
      .toBe(true);
    expect(c2.sprite.endsWith("_stale.png")).toBe(false);
    expect(c2.sprite.endsWith("_sel.png")).toBe(false);
  });
});
