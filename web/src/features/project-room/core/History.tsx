import { wireDate } from "../../../desk/surface/format";
import { localDateStr } from "./format";
import type { RoomChangeRow } from "../model";

export function historyEventsWords(changes: RoomChangeRow[]): string {
  const count = changes.length;
  if (!count) return "No history yet";
  const times = changes
    .map((c) => (c.occurredAt ? wireDate(c.occurredAt) : null))
    .filter((d): d is Date => Boolean(d))
    .map((d) => d.getTime());
  const words = `${count} ${count === 1 ? "event" : "events"}`;
  if (!times.length) return words;
  const first = new Date(Math.min(...times));
  const since = localDateStr(first) === localDateStr(new Date())
    ? "today"
    : first.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return `${words} · since ${since}`;
}
