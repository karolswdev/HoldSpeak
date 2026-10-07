// PHILO-14 A0c — the 32 px world set, drawn at 32. The list species read
// the 32 px file; the icon on the screen and in a drawer reads the 64.
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  SPRITE_BASE,
  VARIANTS,
  allSpriteNames,
  listSprite,
  spriteUrl,
} from "../sprites";
import { objectSprite } from "../surface/objects/kinds";

const SPRITES_DIR = join(dirname(fileURLToPath(import.meta.url)), "../../../public/desk/sprites");

/** Width and height from a PNG's IHDR chunk. */
function pngSize(file: string): [number, number] {
  const buf = readFileSync(file);
  return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
}

describe("spriteUrl by size", () => {
  it("64 is the default and keeps every existing call", () => {
    expect(spriteUrl("meeting", "m1")).toBe(`${SPRITE_BASE}meeting.png`);
    expect(spriteUrl("meeting", "m1", "sel")).toBe(`${SPRITE_BASE}meeting_sel.png`);
    expect(spriteUrl("coder", "c1", "stale", "codex")).toBe(`${SPRITE_BASE}agent-codex_stale.png`);
  });

  it("32 reads the drawn 32 px file in `32/`", () => {
    expect(spriteUrl("meeting", "m1", "rest", undefined, 32)).toBe(`${SPRITE_BASE}32/meeting.png`);
    expect(spriteUrl("pr", "p1", "sel", undefined, 32)).toBe(`${SPRITE_BASE}32/pull-request_sel.png`);
    expect(spriteUrl("coder", "c1", "rest", "codex", 32)).toBe(`${SPRITE_BASE}32/agent-codex.png`);
    expect(spriteUrl("coder", "c1", "rest", "claude", 32)).toBe(`${SPRITE_BASE}32/agent-claude-code.png`);
  });
});

describe("listSprite", () => {
  it("maps every 64 px world sprite in every state to its 32 px sibling", () => {
    for (const name of allSpriteNames())
      for (const suffix of ["", "_sel", "_stale"])
        expect(listSprite(`${SPRITE_BASE}${name}${suffix}.png`)).toBe(`${SPRITE_BASE}32/${name}${suffix}.png`);
  });

  it("leaves any other URL alone", () => {
    expect(listSprite("/badge.png")).toBe("/badge.png");
    expect(listSprite(`${SPRITE_BASE}system/mic.png`)).toBe(`${SPRITE_BASE}system/mic.png`);
    expect(listSprite(`${SPRITE_BASE}32/meeting.png`)).toBe(`${SPRITE_BASE}32/meeting.png`);
    expect(listSprite(`${SPRITE_BASE}not-a-kind.png`)).toBe(`${SPRITE_BASE}not-a-kind.png`);
  });
});

describe("objectSprite resolves every kind at both sizes", () => {
  it("the object kinds wear their own D1 icon", () => {
    expect(objectSprite("action", "a")).toBe(`${SPRITE_BASE}action-item.png`);
    expect(objectSprite("pr", "p")).toBe(`${SPRITE_BASE}pull-request.png`);
    expect(objectSprite("person", "x")).toBe(`${SPRITE_BASE}person.png`);
    expect(objectSprite("agent", "x")).toBe(`${SPRITE_BASE}agent-claude-code.png`);
    expect(objectSprite("parked", "x", "sel", 32)).toBe(`${SPRITE_BASE}32/parked-drawer_sel.png`);
  });

  it("every VARIANTS kind resolves to a file on disk at 64 and 32", () => {
    for (const kind of Object.keys(VARIANTS))
      for (const size of [64, 32] as const)
        for (const state of ["rest", "sel", "stale"] as const) {
          const url = spriteUrl(kind, "id", state, undefined, size);
          const file = join(SPRITES_DIR, url.slice(SPRITE_BASE.length));
          expect(pngSize(file), `${kind} ${size} ${state}`).toEqual([size, size]);
        }
  });

  it("the 32 px files are drawn at 32, not copies of the 64", () => {
    for (const name of allSpriteNames()) {
      expect(pngSize(join(SPRITES_DIR, "32", `${name}.png`)), name).toEqual([32, 32]);
      expect(pngSize(join(SPRITES_DIR, `${name}.png`)), name).toEqual([64, 64]);
    }
  });
});
