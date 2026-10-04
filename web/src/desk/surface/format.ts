// HS-98-01 — honest-row formatters (DESIGN_SYSTEM.md, "The surface
// idiom" rule 4): times humanized, labels de-snaked, unknowns OMITTED —
// a surface never prints "unknown"/"none" theater.

/** The ONE parse of a wire time. Every face reads a hub time through
 * this helper; no face slices the string or calls `new Date(wire)`.
 *
 * The hub sends three shapes:
 *  - an ISO string with a zone (`...Z`, `...+00:00`): exact;
 *  - a bare SQLite stamp `YYYY-MM-DD HH:MM:SS`: SQLite writes UTC, so
 *    it reads as UTC (not as local time);
 *  - a bare ISO string `YYYY-MM-DDTHH:MM:SS`: the hub wrote its local
 *    wall time, so it reads as local time;
 *  - a bare date `YYYY-MM-DD`: a local day (not UTC midnight, which is
 *    the day before in a zone west of UTC);
 *  - a number: epoch seconds (below 1e12) or epoch milliseconds.
 * Junk reads as null. */
export function wireDate(value: unknown): Date | null {
  if (value === null || value === undefined || value === "") return null;
  let date: Date;
  if (value instanceof Date) {
    date = value;
  } else if (typeof value === "number") {
    if (!Number.isFinite(value)) return null;
    date = new Date(value < 1e12 ? value * 1000 : value);
  } else {
    const text = String(value).trim();
    const day = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
    if (day) return new Date(Number(day[1]), Number(day[2]) - 1, Number(day[3]));
    date = new Date(
      /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(text)
        ? `${text.replace(" ", "T")}Z`
        : text,
    );
  }
  return Number.isNaN(date.getTime()) ? null : date;
}

/** A wire time as the local 24-hour clock `HH:MM` (`HH:MM:SS` with
 * `seconds`); empty string when the value is not a time. */
export function wireClock(value: unknown, seconds = false): string {
  const date = wireDate(value);
  if (!date) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  const clock = `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  return seconds ? `${clock}:${pad(date.getSeconds())}` : clock;
}

/** A wire timestamp (ISO string or epoch seconds/ms) as a short human
 * phrase; empty string when the value is not a time. */
export function humanTime(value: unknown): string {
  const date = wireDate(value);
  if (!date) return "";
  const diff = Date.now() - date.getTime();
  if (Math.abs(diff) < 45_000) return "just now";
  if (diff > 0) {
    const mins = Math.round(diff / 60_000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.round(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.round(hours / 24);
    if (days < 7) return `${days}d ago`;
  }
  const sameYear = date.getFullYear() === new Date().getFullYear();
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}

/** A wire identifier ("source_type", "agent-question") as words. */
export function deSnake(value: unknown): string {
  return String(value ?? "")
    .replace(/[_-]+/g, " ")
    .trim();
}

/** A wire value fit to render — or "" when it carries no meaning
 * (null, empty, "unknown", "none", "n/a"). Callers OMIT empties. */
export function presentValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  const text = String(value).trim();
  if (!text) return "";
  const lowered = text.toLowerCase();
  if (["unknown", "none", "null", "undefined", "n/a"].includes(lowered))
    return "";
  return text;
}

/** HS-101 B3 — the dated stream's time grammar. The wire sends epoch
 * seconds, epoch millis, or ISO strings; junk reads as null and the
 * stream files it under "Undated" rather than inventing a date. */
export function streamDate(value: unknown): Date | null {
  return wireDate(value);
}

function sameDay(a: Date, b: Date): boolean {
  return a.toDateString() === b.toDateString();
}

export function streamDayLabel(date: Date | null, now?: Date): string {
  if (!date) return "Undated";
  const today = now ?? new Date();
  const dated = date.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  if (sameDay(date, today)) return `Today: ${dated}`;
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (sameDay(date, yesterday)) return `Yesterday: ${dated}`;
  return dated;
}

export function streamTime(date: Date | null): string {
  if (!date) return "";
  return date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function isSameStreamDay(a: Date, b: Date): boolean {
  return sameDay(a, b);
}
