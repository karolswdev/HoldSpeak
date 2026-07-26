const M64 = 1n << 64n;
const HALF = 1n << 63n;

export function stableHash(value: string): bigint {
  let hash = 5381n;
  for (const byte of new TextEncoder().encode(String(value)))
    hash = (hash * 33n + BigInt(byte)) % M64;
  const signed = hash >= HALF ? hash - M64 : hash;
  return signed < 0n ? -signed : signed;
}

function numbered(base: string, count: number): string[] {
  return Array.from({ length: count }, (_, index) =>
    index ? `${base}${index + 1}` : base,
  );
}
// HS-104-08 (the owner's sitting rider): the family reforged in one
// Workbench-2.0-modern language. The crystal is gone — knowledge is a
// bound TOME. The avatar bitmoji is gone — an agent is a mechanical
// AUTOMATON head, a machine handle, not a mascot. Pool sizes are the
// candidate picks that survived ICON-DISCIPLINE review.
const automatons = numbered("automaton", 14);
export const VARIANTS: Record<string, string[]> = {
  meeting: numbered("cassette", 16),
  note: numbered("note", 12),
  kb: numbered("tome", 13),
  model: ["cartridge"],
  agent: automatons,
  recipe: automatons,
  coder: automatons,
  artifact: ["paper"],
  chain: ["cartridge"],
  workflow: ["cartridge"],
  // HS-105-01: a directory is a DRAWER (the Workbench silhouette rule) —
  // never paper. The owner's diagnosis: "no real idea of directories".
  directory: ["drawer"],
};
export const SPRITE_BASE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/`;
export function variantIndex(id: string, poolLength: number): number {
  return poolLength <= 1 ? 0 : Number(stableHash(id) % BigInt(poolLength));
}
export function spriteName(kind: string, id: string): string {
  const pool = VARIANTS[kind] ?? VARIANTS.note;
  return pool[variantIndex(id, pool.length)];
}
/** HS-105-01 — sprite STATES are real second images on disk (derived by
 * web/scripts/gen-sprite-states.py), never runtime filters: the Workbench
 * dual-image rule. `rest` is the base file. */
export type SpriteState = "rest" | "sel" | "stale";
export function spriteUrl(
  kind: string,
  id: string,
  state: SpriteState = "rest",
): string {
  const suffix = state === "rest" ? "" : `_${state}`;
  return `${SPRITE_BASE}${spriteName(kind, id)}${suffix}.png`;
}
