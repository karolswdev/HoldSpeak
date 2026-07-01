// HS-71-02: the web sprite picker — the port of the iPad `DeskSprites` /
// `SpriteStore` (apple/App/SpriteStore.swift). A primitive's pixel-art object is
// chosen deterministically from its kind's variety pool by a STABLE hash of its
// id, so a given object always wears the same sprite (across reloads) and, for
// the numbered kinds, the SAME sprite the iPad would pick.
//
// The art lives in web/public/desk/sprites/ (copied from apple/App/*.png).

// djb2, 64-bit two's-complement, matching Swift's `h = h &* 33 &+ byte` in Int
// followed by `abs(...)`. BigInt so the wrap is exact (JS Number loses precision
// past 2^53). Returns a non-negative BigInt.
const M64 = 1n << 64n;
const HALF = 1n << 63n;
export function stableHash(s) {
  let h = 5381n;
  for (const b of new TextEncoder().encode(String(s))) {
    h = (h * 33n + BigInt(b)) % M64; // wrap to unsigned 64-bit
  }
  const signed = h >= HALF ? h - M64 : h; // reinterpret as signed 64-bit
  return signed < 0n ? -signed : signed; // abs
}

function numbered(base, count) {
  const a = [base];
  for (let i = 2; i <= count; i++) a.push(base + i);
  return a;
}

// Pools mirror `DeskSprites.variants` (meeting/note/kb/model) plus web-side art
// for the kinds the iPad draws with SF Symbols (agent/coder get avatars; the
// capability/organization kinds get a sensible object until they gain their own).
export const VARIANTS = {
  meeting: numbered("cassette", 17),
  note: numbered("note", 16),
  kb: numbered("crystal", 16),
  model: ["cartridge"],
  agent: Array.from({ length: 16 }, (_, i) => "agent_o" + i),
  coder: Array.from({ length: 16 }, (_, i) => "agent_o" + i),
  artifact: ["paper"],
  chain: ["cartridge"],
  workflow: ["cartridge"],
  directory: ["paper"],
};

// Astro serves web/public/ under its configured base ("/_built/"); use BASE_URL
// so this is not hardcoded (matches how /_built/qlippy/* is referenced).
export const SPRITE_BASE =
  (import.meta.env && import.meta.env.BASE_URL ? import.meta.env.BASE_URL : "/_built/") +
  "desk/sprites/";

/** The variant index for `id` within a pool of `poolLen` (stable). */
export function variantIndex(id, poolLen) {
  if (poolLen <= 1) return 0;
  return Number(stableHash(id) % BigInt(poolLen));
}

/** The sprite base name a primitive should wear. */
export function spriteName(kind, id) {
  const pool = VARIANTS[kind] || VARIANTS.note;
  if (pool.length <= 1) return pool[0];
  return pool[variantIndex(id, pool.length)];
}

/** The full URL of a primitive's sprite PNG. */
export function spriteUrl(kind, id) {
  return SPRITE_BASE + spriteName(kind, id) + ".png";
}
