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

/** HS-201-06 (Constitution tenet 4, ASD-STE100: one word, one meaning).
 *  A state word is not a counted noun, so the default plural must not
 *  invent one: `7 WAITING`, never `7 WAITINGS` (the Models face, audit
 *  row 6). Matched on the LAST word of the token, case-insensitively;
 *  an explicit `plural` always wins over this list. */
const STATE_WORDS = new Set([
  "waiting", "failed", "queued", "running", "pending", "blocked",
  "skipped", "done", "ready", "kept", "saved", "sent", "set", "left",
  "missing", "open", "new", "late", "cancelled", "canceled",
  "succeeded", "accepted", "dismissed", "approved", "rejected",
  "revoked", "expired", "unavailable", "offline",
]);

/** True when the token ends in a state word and must not take an S. */
function isStateWord(token: string): boolean {
  const last = token.trim().split(/\s+/).pop() ?? "";
  return STATE_WORDS.has(last.toLowerCase());
}

export function countToken(
  count: number | null | undefined,
  singular: string,
  plural?: string,
): string | null {
  const n = typeof count === "number" && Number.isFinite(count) ? Math.trunc(count) : 0;
  if (n <= 0) return null;
  const many = plural ?? (isStateWord(singular) ? singular : `${singular}S`);
  const noun = n === 1 ? singular : many;
  return `${n} ${noun}`;
}

/** countLabel — the same rule for section captions that carry a count:
 *  `NEEDS YOU 3` at n>0, `NEEDS YOU` at zero (never `NEEDS YOU 0`). */
export function countLabel(label: string, count: number | null | undefined): string {
  const n = typeof count === "number" && Number.isFinite(count) ? Math.trunc(count) : 0;
  return n > 0 ? `${label} ${n}` : label;
}
