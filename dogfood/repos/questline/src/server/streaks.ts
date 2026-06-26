// Streak computation — timezone-aware.
//
// INVARIANT (see .hs/memory.md, QL-322): a streak may break ONLY when
// the user genuinely misses their quest window in THEIR OWN local
// timezone. All "what day is it" math must happen in the user's IANA
// timezone, never in server UTC.

/** A quest completion as we need it here: the UTC instant and the user tz. */
export interface CompletionInput {
  completedAt: Date; // stored UTC instant
  timezone: string; // IANA tz, e.g. "America/Los_Angeles"
}

export interface StreakResult {
  current: number;
  longest: number;
}

/**
 * Return the user-local calendar day (YYYY-MM-DD) for a UTC instant.
 *
 * This is the heart of QL-322: bucketing by UTC date drops or doubles a
 * day for non-UTC users and across DST, breaking streaks unfairly. We
 * resolve the local date with Intl so the day boundary is the user's.
 */
export function localDayKey(instant: Date, timezone: string): string {
  // en-CA yields ISO-ish YYYY-MM-DD parts; we read them off the formatter.
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(instant);

  const get = (t: string) => parts.find((p) => p.type === t)?.value ?? "";
  return `${get("year")}-${get("month")}-${get("day")}`;
}

/** Days between two local-day keys (calendar days, tz already applied). */
function dayGap(prevKey: string, nextKey: string): number {
  const a = Date.UTC(...keyParts(prevKey));
  const b = Date.UTC(...keyParts(nextKey));
  return Math.round((b - a) / 86_400_000);
}

function keyParts(key: string): [number, number, number] {
  const [y, m, d] = key.split("-").map(Number);
  return [y, m - 1, d];
}

/**
 * Compute the current and longest DAILY streak from completions.
 * Completions may arrive unsorted and may include same-day dupes.
 */
export function computeStreak(completions: CompletionInput[]): StreakResult {
  if (completions.length === 0) return { current: 0, longest: 0 };

  // Collapse to unique local days, sorted ascending.
  const days = [
    ...new Set(
      completions.map((c) => localDayKey(c.completedAt, c.timezone)),
    ),
  ].sort();

  let longest = 1;
  let run = 1;
  for (let i = 1; i < days.length; i++) {
    run = dayGap(days[i - 1], days[i]) === 1 ? run + 1 : 1;
    if (run > longest) longest = run;
  }

  return { current: run, longest };
}
