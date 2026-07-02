/** The world's tiny stable 0..1 hash for per-object layout jitter + float
 * phase — the exact FNV-1a variant the Alpine desk used (`_oh`), kept
 * bit-identical so hand-arranged desks look the same on the island. */
export function oh(s: string): number {
  let h = 2166136261;
  const str = String(s || "");
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10000) / 10000;
}
