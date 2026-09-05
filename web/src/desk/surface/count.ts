/**
 * countToken — the ONE way a face says "N things" (UX-CANON A8: no counters
 * of zero). Returns null at zero so the caller renders nothing (or its own
 * one true line); otherwise `N NOUN` with the plural chosen by count.
 *
 *   {countToken(open, "OPEN PR")}          → "3 OPEN PRS" | null
 *   {countToken(n, "MEETING", "MEETINGS")} → "1 MEETING" | "4 MEETINGS" | null
 *
 * `plural` defaults to `${singular}S`. Case is the caller's (tokens are
 * uppercase mono by convention; pass lowercase nouns for secondary text).
 */
export function countToken(
  count: number | null | undefined,
  singular: string,
  plural?: string,
): string | null {
  const n = typeof count === "number" && Number.isFinite(count) ? Math.trunc(count) : 0;
  if (n <= 0) return null;
  const noun = n === 1 ? singular : (plural ?? `${singular}S`);
  return `${n} ${noun}`;
}

/** countLabel — the same rule for section captions that carry a count:
 *  `NEEDS YOU 3` at n>0, `NEEDS YOU` at zero (never `NEEDS YOU 0`). */
export function countLabel(label: string, count: number | null | undefined): string {
  const n = typeof count === "number" && Number.isFinite(count) ? Math.trunc(count) : 0;
  return n > 0 ? `${label} ${n}` : label;
}
