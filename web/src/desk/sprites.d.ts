// The sprite picker is plain ESM shared with the legacy desk (HS-71-02) — the
// React island imports the SAME module for exact parity (same djb2 BigInt
// wrap, same pools, same instance in the bundle).
declare module "../scripts/desk/sprites.js" {
  export function stableHash(s: string): bigint;
  export function variantIndex(id: string, poolLen: number): number;
  export function spriteName(kind: string, id: string): string;
  export function spriteUrl(kind: string, id: string): string;
  export const VARIANTS: Record<string, string[]>;
  export const SPRITE_BASE: string;
}
