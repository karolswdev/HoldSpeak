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
