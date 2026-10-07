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
  note: ["note"],
  decision: ["decision"],
  artifact: ["artifact"],
  people: ["people-ledger"],
  person: ["person"],
  project: ["project-drawer"],
  // HS-105-01: a directory is a DRAWER (the Workbench silhouette rule).
  directory: ["project-drawer"],
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
export const AGENT_SPRITES = ["agent-claude-code", "agent-codex"] as const;

/** The agent sprite for an agent name: Codex wears `agent-codex`; Claude
 * Code and any unknown agent wear `agent-claude-code`. */
export function agentSpriteName(
  agent: string | null | undefined,
): (typeof AGENT_SPRITES)[number] {
  return /codex/i.test(String(agent ?? "")) ? "agent-codex" : "agent-claude-code";
}

/** Every base sprite name `spriteName` can return: the pools plus the
 * helper-selected agent sprites. The state-file guard walks this list. */
export function allSpriteNames(): string[] {
  const names = new Set<string>(AGENT_SPRITES);
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
export type SpriteSize = 64 | 32;
export const SPRITE_SIZES: readonly SpriteSize[] = [64, 32];
function sizeDir(size: SpriteSize): string {
  return size === 32 ? "32/" : "";
}
export function spriteUrl(
  kind: string,
  id: string,
  state: SpriteState = "rest",
  /** The agent name of a coder/agent object ("claude", "codex"). */
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

/** The agent name a world object's ref carries, if any. */
export function refAgent(ref: unknown): string | undefined {
  const agent = (ref as { agent?: unknown } | null | undefined)?.agent;
  return typeof agent === "string" ? agent : undefined;
}
