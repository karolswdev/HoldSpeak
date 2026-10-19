/* Betterment P3, the Now wing: the pure words of the project window's head,
 * Waiting on and This week (docs/internal/betterment/projects/DESIGN.md,
 * "The project window: Now"). No reads here; ProjectRoomCore and the
 * sections draw what these return. */
import type { RoomHealthData, RoomNeedsYouItem, RoomNowData, RoomNudgeDestination, RoomSnapshot } from "../model";
import { roomIsEmpty } from "../model";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** A day (`2026-10-23` or a full stamp) as a local calendar day. */
function localDay(value: string): Date | null {
  const text = (value || "").trim();
  if (!text) return null;
  const bare = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  const d = bare ? new Date(Number(bare[1]), Number(bare[2]) - 1, Number(bare[3])) : new Date(text);
  if (Number.isNaN(d.getTime())) return null;
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function dayDiff(day: Date, now: Date): number {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((day.getTime() - today.getTime()) / 86_400_000);
}

/** `Thu 23 Oct`. */
export function dayWords(value: string): string {
  const d = localDay(value);
  if (!d) return "";
  return `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
}

/** An owed item's due date as he says it: `today`, `tomorrow`, `Tue`,
 *  `2 days late`, `23 Oct`. Empty when there is no date. */
export function dueWords(value: string | undefined, now: Date = new Date()): string {
  const d = value ? localDay(value) : null;
  if (!d) return "";
  const diff = dayDiff(d, now);
  if (diff === 0) return "today";
  if (diff === 1) return "tomorrow";
  if (diff < 0) return `${-diff} ${diff === -1 ? "day" : "days"} late`;
  if (diff < 7) return DAYS[d.getDay()];
  return `${d.getDate()} ${MONTHS[d.getMonth()]}`;
}

export type StateLine = {
  /** The display line: `At risk: <reason>`, `On track`, `New`. */
  text: string;
  tone: "danger" | "warn" | "ok" | "info" | "muted";
  /** The ref the reason rests on (its source opens it). */
  ref: string | null;
};

const STATE_WORD = { on_track: "On track", at_risk: "At risk", blocked: "Blocked" } as const;

/** The head's one big fact: the state and its reason, in his words.
 *  ``sourceStale``: a source was not read on time (PHILO-15 B69). */
export function stateLine(room: RoomSnapshot, sourceStale = false): StateLine {
  if (room.health.state !== "ok") return { text: "Not all read", tone: "muted", ref: null };
  const health = room.health as RoomHealthData & { state: "ok" };
  const state = health.projectState ?? (health.assessment === "at_risk" ? "at_risk" : "on_track");
  // PHILO-15 B69: with a source not read, "On track" is not known.
  if (state === "on_track" && sourceStale) return { text: "Not all read", tone: "muted", ref: null };
  if (state === "on_track" && roomIsEmpty(room)) return { text: "New", tone: "info", ref: null };
  const word = STATE_WORD[state];
  const reason = (health.stateReason ?? "").trim();
  return {
    text: state !== "on_track" && reason ? `${word}: ${reason}` : word,
    tone: state === "blocked" ? "danger" : state === "at_risk" ? "warn" : "ok",
    ref: state !== "on_track" ? health.stateRef ?? null : null,
  };
}

/** The line under the head: the next date, the last update, this week's
 *  meetings. A part with nothing to say is left out (no counters of zero). */
export function headFacts(now: RoomNowData | null): string[] {
  if (!now) return [];
  const parts: string[] = [];
  if (now.nextDate) {
    const when = dayWords(now.nextDate.at);
    if (when) parts.push(`${now.nextDate.label || "Next"} ${when}`);
  }
  if (now.lastUpdateAt) {
    const when = dayWords(now.lastUpdateAt);
    if (when) parts.push(`last update ${when}`);
  }
  if (now.meetingsThisWeek > 0) {
    parts.push(`${now.meetingsThisWeek} ${now.meetingsThisWeek === 1 ? "meeting" : "meetings"} this week`);
  }
  return parts;
}

/** A Needs you row is his unless it names another person who owes it. */
export function isMine(item: RoomNeedsYouItem): boolean {
  return item.direction !== "theirs";
}

export type WaitingItem = {
  title: string;
  due: string;
  late: boolean;
  actionItemId?: string;
  /** A destination is required before Now may offer an outbound Nudge. */
  url?: string | null;
  nudge?: RoomNudgeDestination;
};
export type WaitingPerson = { person: string; items: WaitingItem[] };

/** Other people's owed items, one group per person: the person with the
 *  most late work first, then the most items, then by name. */
export function waitingOn(items: RoomNeedsYouItem[], now: Date = new Date()): WaitingPerson[] {
  const groups = new Map<string, WaitingPerson>();
  for (const item of items) {
    if (item.direction !== "theirs") continue;
    const person = (item.owner ?? "").trim();
    if (!person) continue;
    const key = person.toLowerCase();
    const group = groups.get(key) ?? { person, items: [] };
    const due = dueWords(item.dueAt, now);
    const waitingItem: WaitingItem = {
      title: item.title,
      due,
      late: due.endsWith("late"),
      actionItemId: item.actionItemId,
    };
    if (item.url) waitingItem.url = item.url;
    if (item.nudge) waitingItem.nudge = item.nudge;
    group.items.push(waitingItem);
    groups.set(key, group);
  }
  const late = (g: WaitingPerson) => g.items.filter((i) => i.late).length;
  return [...groups.values()].sort((a, b) =>
    late(b) - late(a) || b.items.length - a.items.length || a.person.localeCompare(b.person));
}
