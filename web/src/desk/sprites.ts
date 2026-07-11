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
const avatars = Array.from({ length: 16 }, (_, index) => `agent_o${index}`);
export const VARIANTS: Record<string, string[]> = {
  meeting: numbered("cassette", 17),
  note: numbered("note", 16),
  kb: numbered("crystal", 16),
  model: ["cartridge"],
  agent: avatars,
  recipe: avatars,
  coder: avatars,
  artifact: ["paper"],
  chain: ["cartridge"],
  workflow: ["cartridge"],
  directory: ["paper"],
};
export const SPRITE_BASE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/`;
export function variantIndex(id: string, poolLength: number): number {
  return poolLength <= 1 ? 0 : Number(stableHash(id) % BigInt(poolLength));
}
export function spriteName(kind: string, id: string): string {
  const pool = VARIANTS[kind] ?? VARIANTS.note;
  return pool[variantIndex(id, pool.length)];
}
export function spriteUrl(kind: string, id: string): string {
  return `${SPRITE_BASE}${spriteName(kind, id)}.png`;
}
