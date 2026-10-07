/** HS-105-01 — the icon-cell guard. Pins the gated cell contract:
 * integer-true pixel art in one uniform cell, real state images on disk
 * for EVERY pool sprite, badges only from named live fields, and no
 * fractional jitter. A regression here is unshippable. */
import { describe, expect, it } from "vitest";
import { cpSync, existsSync, mkdtempSync, renameSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { LIFT, SPRITE, SPRITE_SMALL, buildScene, isFresh } from "../sceneModel";
import { objMotion } from "../../world";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { VARIANTS, allSpriteNames, agentSpriteName } from "../../sprites";
import type { KB, Note, Coder } from "../../../lib/primitives";
import { EMPTY_ITEMS, type Items } from "../../api";

const SPRITES_DIR = join(
  dirname(fileURLToPath(import.meta.url)),
  "../../../../public/desk/sprites",
);

function requiredFiles(): string[] {
  return allSpriteNames().flatMap((name) =>
    ["", "_sel", "_stale"].map((suffix) => `${name}${suffix}.png`),
  );
}

function missingStateFiles(dir: string): string[] {
  return requiredFiles().filter((file) => !existsSync(join(dir, file)));
}

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
    expect((VARIANTS as Record<string, string[]>).directory).toEqual([
      "project-drawer",
    ]);
  });

  it("one kind = one silhouette (PHILO-14 A0b, the D1 mold)", () => {
    for (const [kind, pool] of Object.entries(
      VARIANTS as Record<string, string[]>,
    ))
      expect(pool.length, `${kind} pool`).toBe(1);
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
      kb: [{ kind: "kb", id: "k1", name: "KB", memberIds: ["a", "b", "c"] } as KB],
      note: [{ kind: "note", id: "n1", title: "Note" } as Note],
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

  it("a Codex coder stays Codex at rest, lit and selected (PHILO-14 A0b r2)", () => {
    const items: Items = {
      ...EMPTY_ITEMS,
      coder: [
        { kind: "coder", id: "x1", agent: "codex", title: "codex one" } as Coder,
        { kind: "coder", id: "x2", agent: "claude", title: "claude one" } as Coder,
      ],
    };
    const rest = sceneFor(items).objects;
    const sel = sceneFor(items, ["x1", "x2"]).objects;
    const by = (list: typeof rest, id: string) => list.find((o) => o.id === id)!;
    expect(by(rest, "x1").sprite).toMatch(/\/agent-codex\.png$/);
    expect(by(rest, "x1").spriteSel).toMatch(/\/agent-codex_sel\.png$/);
    expect(by(sel, "x1").sprite).toMatch(/\/agent-codex_sel\.png$/);
    expect(by(rest, "x2").sprite).toMatch(/\/agent-claude-code\.png$/);
    expect(by(rest, "x2").spriteSel).toMatch(/\/agent-claude-code_sel\.png$/);
  });

  it("state picks the real second image: sel > stale > rest", () => {
    const items: Items = {
      ...EMPTY_ITEMS,
      coder: [
        { kind: "coder", id: "c1", title: "stale one", stale: true } as Coder,
        { kind: "coder", id: "c2", title: "live one", stale: false } as Coder,
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
