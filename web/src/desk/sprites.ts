import { dockSprite48 } from "./systemSprites";

const M64 = 1n << 64n;
const HALF = 1n << 63n;

export function stableHash(value: string): bigint {
  let hash = 5381n;
  for (const byte of new TextEncoder().encode(String(value)))
    hash = (hash * 33n + BigInt(byte)) % M64;
  const signed = hash >= HALF ? hash - M64 : hash;
  return signed < 0n ? -signed : signed;
}

// PHILO-14 A0b (ruling 2026-10-07, docs/internal/philo/phase-14/icons/
// README.md): the D1 "Workbench+" mold. One kind = one silhouette — every
// pool has length 1, so the per-id variety of the old mold is retired (the
// old pools are parked in public/desk/sprites/_parked-2026-10-07/). The
// variantIndex hash stays for any future pool.
//
// Honest gaps: kb and roadmap wear `artifact` and story wears `note` until
// they get their own icon. The capability kinds (model, recipe, chain,
// workflow, workbench, intelligence) wear the old `cartridge`, carried
// forward un-parked. memory stays the chip until it is redrawn.
export const VARIANTS: Record<string, string[]> = {
  meeting: ["meeting"],
  // Calls (2026-10-28): a desk telephone, the blue handset on its cradle.
  call: ["call"],
  // Programs (2026-10-28): three stacked cards, the front one lit with the
  // station track (canvases/programs-2026-10-28.html).
  program: ["program"],
  // PG-REQ: a Shot requirement's image window wears its Program's object.
  "program-shot": ["program"],
  note: ["note"],
  decision: ["decision"],
  artifact: ["artifact"],
  people: ["people-ledger"],
  person: ["person"],
  project: ["project-drawer"],
  // HS-105-01: a directory is a DRAWER (the Workbench silhouette rule).
  // Icons D (2026-10-24): a zone is a folder whose front wears the zone's
  // colour (`ZONE_HUES`, read by `zoneSpriteName`); a Project keeps its
  // own flagged folder.
  directory: ["zone-drawer"],
  repository: ["repository"],
  kb: ["artifact"],
  roadmap: ["artifact"],
  story: ["note"],
  thread: ["thread"],
  memory: ["memory"],
  // The coder and agent kinds pick by agent name (agentSpriteName); the
  // pool is the fallback when no agent name rides along.
  coder: ["agent-claude-code"],
  agent: ["agent-claude-code"],
  // New kinds for the A1/A2 lanes: action items, pull requests, drawers.
  action: ["action-item"],
  pr: ["pull-request"],
  smart: ["smart-drawer"],
  conductor: ["conductor-drawer"],
  parked: ["parked-drawer"],
  // Capability kinds: one neutral object until they get their own icon.
  model: ["cartridge"],
  recipe: ["cartridge"],
  chain: ["cartridge"],
  workflow: ["cartridge"],
  workbench: ["cartridge"],
  intelligence: ["cartridge"],
};

/** The sprites `agentSpriteName` can return. They sit outside the pools. */
export const AGENT_SPRITES = ["agent-claude-code", "agent-codex", "agent-pi"] as const;

/** The agent sprite for an agent name: Codex wears `agent-codex`, pi wears
 * `agent-pi` (pi spike #1020); Claude Code and any unknown agent wear
 * `agent-claude-code`. */
export function agentSpriteName(
  agent: string | null | undefined,
): (typeof AGENT_SPRITES)[number] {
  const name = String(agent ?? "");
  if (/codex/i.test(name)) return "agent-codex";
  if (/^pi(?:$|[:\-])/i.test(name)) return "agent-pi";
  return "agent-claude-code";
}

/** Icons D (owner pick 2026-10-24): the zone folder colours. A front is
 * blue unless the zone carries another hue. */
export type ZoneHue = "blue" | "teal" | "violet" | "amber";
export const ZONE_SPRITES: Record<ZoneHue, string> = {
  blue: "zone-drawer",
  teal: "zone-drawer-teal",
  violet: "zone-drawer-violet",
  amber: "zone-drawer-amber",
};
/** The zone colour data. Directories carry no paint on the hub (a zone's
 * paint is per-surface layout, `DirectoryRecord`), so the packaged zones
 * (holdspeak/seeds/fresh-desk.yaml) carry their hue here, keyed by their
 * stable seed id, never by the name: renaming Work keeps it teal. Every
 * other zone, and every Project, is blue. */
export const ZONE_HUES: Readonly<Record<string, ZoneHue>> = {
  "hs-seed-inbox": "blue",
  "hs-seed-work": "teal",
  "hs-seed-personal": "violet",
  "hs-seed-reference": "amber",
};
export function zoneSpriteName(id: string): string {
  return ZONE_SPRITES[ZONE_HUES[id] ?? "blue"];
}

/** Every base sprite name `spriteName` can return: the pools plus the
 * helper-selected agent and zone sprites. The state-file guard walks this list. */
export function allSpriteNames(): string[] {
  const names = new Set<string>([...AGENT_SPRITES, ...Object.values(ZONE_SPRITES)]);
  for (const pool of Object.values(VARIANTS)) for (const n of pool) names.add(n);
  return [...names].sort();
}
export const SPRITE_BASE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/`;
export function variantIndex(id: string, poolLength: number): number {
  return poolLength <= 1 ? 0 : Number(stableHash(id) % BigInt(poolLength));
}
export function spriteName(
  kind: string,
  id: string,
  agent?: string | null,
): string {
  if ((kind === "coder" || kind === "agent") && agent)
    return agentSpriteName(agent);
  if (kind === "directory") return zoneSpriteName(id);
  const pool = VARIANTS[kind] ?? VARIANTS.note;
  return pool[variantIndex(id, pool.length)];
}
/** HS-105-01 — sprite STATES are real second images on disk (derived by
 * web/scripts/gen-sprite-states.py), never runtime filters: the Workbench
 * dual-image rule. `rest` is the base file. */
export type SpriteState = "rest" | "sel" | "stale";
/** PHILO-14 A0c: the two drawn sizes. 64 is the icon on the screen and in a
 * drawer; 32 is the list row (ObjectList, Needs you, the confirm line, the
 * badge). The 32 set is drawn at 32, not scaled: it lives in `32/` beside
 * the 64 set, one file per base name and state. */
export type SpriteSize = 64 | 32 | 20;
/** Icons D (2026-10-24): 20 is the dense row and the title-bar glyph, drawn
 * at 20 (no bevel, heavier outline) in `20/`. */
export const SPRITE_SIZES: readonly SpriteSize[] = [64, 32, 20];
function sizeDir(size: SpriteSize): string {
  return size === 64 ? "" : `${size}/`;
}
export function spriteUrl(
  kind: string,
  id: string,
  state: SpriteState = "rest",
  /** The agent name of a coder/agent object ("claude", "codex", "pi"). */
  agent?: string | null,
  size: SpriteSize = 64,
): string {
  const suffix = state === "rest" ? "" : `_${state}`;
  return `${SPRITE_BASE}${sizeDir(size)}${spriteName(kind, id, agent)}${suffix}.png`;
}

const WORLD_FILE = /^([a-z0-9-]+?)(_sel|_stale)?\.png$/;
/** The 32 px sibling of a 64 px world-sprite URL. A list species gets its
 * sprite as a URL (the row's `sprite`, minted for the icon view), so it
 * maps the URL here instead of every caller minting two. Any other URL
 * (a system glyph, an outside image, a 32 px URL) comes back unchanged. */
export function listSprite(url: string): string {
  if (!url.startsWith(SPRITE_BASE)) return url;
  const file = url.slice(SPRITE_BASE.length);
  const m = WORLD_FILE.exec(file);
  if (!m || !allSpriteNames().includes(m[1])) return url;
  return `${SPRITE_BASE}32/${file}`;
}

const SIZED_FILE = /^(?:(?:32|20)\/)?([a-z0-9-]+?)(_sel|_stale)?\.png$/;
const SYSTEM_FILE = /^system\/(?:20\/)?([a-z0-9-]+)\.png$/;
/** Icons D (2026-10-24): the 20 px sibling of a sprite URL, for a dense
 * row or a title-bar glyph. A world sprite (64 or 32, any state) maps to
 * `20/`, a system sprite to `system/20/`; any other URL comes back
 * unchanged. */
/** The floating dock (2026-10-26): the picture a seated window wears on its
 * 48 px dock tile. A system sprite maps to its `system/48/` drawing, a world
 * sprite (any size or state) to its 64 px drawing, drawn down to 48. Any
 * other URL comes back unchanged (the tile scales it, smooth). */
export function seatSprite(url: string): string {
  if (!url.startsWith(SPRITE_BASE)) return url;
  const file = url.slice(SPRITE_BASE.length);
  if (SYSTEM_FILE.exec(file)) return dockSprite48(url);
  const m = SIZED_FILE.exec(file);
  if (!m || !allSpriteNames().includes(m[1])) return url;
  return `${SPRITE_BASE}${m[1]}${m[2] ?? ""}.png`;
}

export function glyphSprite(url: string): string {
  if (!url.startsWith(SPRITE_BASE)) return url;
  const file = url.slice(SPRITE_BASE.length);
  const sys = SYSTEM_FILE.exec(file);
  if (sys) return `${SPRITE_BASE}system/20/${sys[1]}.png`;
  const m = SIZED_FILE.exec(file);
  if (!m || !allSpriteNames().includes(m[1])) return url;
  return `${SPRITE_BASE}20/${m[1]}${m[2] ?? ""}.png`;
}

/** The agent name a world object's ref carries, if any. */
export function refAgent(ref: unknown): string | undefined {
  const agent = (ref as { agent?: unknown } | null | undefined)?.agent;
  return typeof agent === "string" ? agent : undefined;
}
