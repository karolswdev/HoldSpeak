// The Room's words for times, source tokens, severities and change kinds.
import { clockOf, wireDate } from "../../../desk/surface/format";
import { humanTime } from "../../../desk/surface";
import type { RoomSourceItem } from "../model";

/* ── time formatting ── */

export function formatTimeShort(iso: string | null): string {
  if (!iso) return "";
  const d = wireDate(iso);
  if (!d) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return clockOf(d);
}


/** Format a due date as a short day name (FRI) when within ~7 days, else MMM DD. */
export function formatDueShort(iso: string): string {
  const d = wireDate(iso);
  if (!d) return iso;
  const days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const diffDays = Math.abs(diffMs) / 86_400_000;
  if (diffDays <= 7) return days[d.getDay()];
  const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}

/** Local-time YYYY-MM-DD (same derivation as streamDayLabel's sameDay). */
export function localDateStr(d: Date): string {
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** PHILO-15 B69: the Room head's one source word, from the hub's freshness
 *  states (the rule Needs you reads), in sentence case (2026-10-25 audit):
 *  `Stale · checked 10h ago`, `Quiet until 08:00`, else `Checked <age>`.
 *  Null with no checked source. */
export function sourcesWord(items: RoomSourceItem[], quietUntil?: string | null): { word: string; stale: boolean } | null {
  const checked = maxCheckedAt(items);
  if (items.some((i) => i.freshness === "stale")) {
    return { word: checked ? `Stale · checked ${humanTime(checked)}` : "Stale", stale: true };
  }
  if (quietUntil && items.some((i) => i.freshness === "quiet")) {
    return { word: `Quiet until ${formatTimeShort(quietUntil)}`, stale: false };
  }
  return checked ? { word: `Checked ${humanTime(checked)}`, stale: false } : null;
}

/** A hub source token in sentence case (2026-10-25 audit): `13 OVERDUE` →
 *  `13 overdue`, `3 OPEN PRS` → `3 open PRs`, `CI RED` → `CI red`,
 *  `NEXT MON 10:00` → `Next Mon 10:00`. The hub keeps its caps over MCP. */
const TOKEN_WORDS: Record<string, string> = {
  pr: "PR", prs: "PRs", ci: "CI",
  mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun",
};
export function sentenceToken(token: string): string {
  if (!/[A-Z]/.test(token) || /\p{Ll}/u.test(token)) return token; // mixed case: written as meant
  const words = token.toLowerCase().replace(/\p{L}+/gu, (word) => TOKEN_WORDS[word] ?? word);
  return words.replace(/^\p{Ll}/u, (c) => c.toUpperCase());
}

function maxCheckedAt(items: RoomSourceItem[]): string | null {
  let best: string | null = null;
  for (const item of items) {
    if (item.checkedAt && (!best || item.checkedAt > best)) {
      best = item.checkedAt;
    }
  }
  return best;
}

/* ── proposal date formatting ── */

export function formatMMDD(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = wireDate(iso);
  if (!d) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/* ── severity ── */

export function severityTone(severity: string): string | undefined {
  if (severity === "danger") return "danger";
  if (severity === "warning") return "warn";
  return undefined;
}

export function severityColor(severity: string): string {
  if (severity === "danger") return "#f87171";
  if (severity === "warning") return "#fbbf24";
  return "var(--text-muted)";
}

/* ── HISTORY: kind->phrase map ── */

const KIND_PHRASE_MAP: Record<string, string> = {
  "project.created": "Created",
  "project.updated": "Updated",
  "project.archived": "Archived",
  "project.restored": "Restored",
  "project.resource.linked": "Resource linked",
  "project.resource.unlinked": "Resource unlinked",
  "item.created": "Item created",
  "item.updated": "Item updated",
  "item.deleted": "Item deleted",
  "watch.activated": "Watch activated",
  "watch.paused": "Watch paused",
  "watch.retired": "Watch retired",
  "watch.evaluated": "Check completed",
  "update.drafted": "Update drafted",
  "update.published": "Update published",
  "steward.run": "Sources watched",
  "review.opened": "Review opened",
  "review.accepted": "Review accepted",
  "decision.recorded": "Decided",
  "decision.accepted": "Decision accepted",
};

export function kindToPhrase(kind: string): string {
  if (KIND_PHRASE_MAP[kind]) return KIND_PHRASE_MAP[kind];
  const last = kind.split(".").pop() || kind;
  return last.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}
