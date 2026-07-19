// HS-98-01 — honest-row formatters (DESIGN_SYSTEM.md, "The surface
// idiom" rule 4): times humanized, labels de-snaked, unknowns OMITTED —
// a surface never prints "unknown"/"none" theater.

/** A wire timestamp (ISO string or epoch seconds/ms) as a short human
 * phrase; empty string when the value is not a time. */
export function humanTime(value: unknown): string {
  if (value === null || value === undefined || value === "") return "";
  let date: Date;
  if (typeof value === "number") {
    date = new Date(value < 1e12 ? value * 1000 : value);
  } else {
    const text = String(value);
    // Bare "YYYY-MM-DD HH:MM:SS" (SQLite) parses as local time once the
    // space becomes a T; a full ISO string passes through unchanged.
    date = new Date(/^\d{4}-\d{2}-\d{2} /.test(text) ? text.replace(" ", "T") : text);
  }
  if (Number.isNaN(date.getTime())) return "";
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
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Date(value > 1e12 ? value : value * 1000);
  }
  if (typeof value === "string" && value) {
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) return parsed;
  }
  return null;
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
  if (sameDay(date, today)) return `Today — ${dated}`;
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (sameDay(date, yesterday)) return `Yesterday — ${dated}`;
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
