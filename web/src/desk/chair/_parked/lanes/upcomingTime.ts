// HS-144-04 — the one Chair grammar for an upcoming server time fact.

const MONTHS = [
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
];

/**
 * Preserve Phase 136's scanned-on-Chair time idiom. Invalid or absent server
 * timestamps are not a time fact, so callers render no substitute fiction.
 */
export function upcomingTimeLabel(iso: string | null | undefined, now = new Date()): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const diffMs = date.getTime() - now.getTime();
  if (diffMs > 0 && diffMs < 86_400_000) {
    const hours = Math.floor(diffMs / 3_600_000);
    const minutes = Math.floor((diffMs % 3_600_000) / 60_000);
    if (hours > 0) return `in ${hours}h ${minutes}m`;
    return `in ${minutes}m`;
  }
  return `${MONTHS[date.getMonth()]} ${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}
