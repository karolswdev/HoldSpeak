/** Prepared-result parsing, words and the existing agenda write for Today rows. */
import { apiFetch } from "../../../../lib/api";

export type PreparedRead = {
  prepared: null | {
    workbench_id: string;
    name: string;
    engine: string;
    result: {
      artifact_id?: string | null;
      text?: string | null;
      completed_at?: string | null;
      new?: boolean;
      used?: { looked_at?: Array<{ ref: string; label?: string }> } | null;
    };
  };
  automation: null | { id: string; name: string };
};

export type PreparedCard = {
  time: string;
  title: string;
  lines: string[];
  raise: string[];
};
export type PreparedDay = {
  cards: PreparedCard[];
  mine: string[];
  nudges: string[];
  other: string[];
};

const MEETING = /^(\d{1,2}:\d{2})\s+(.+)$/;
const bullet = (line: string) => line.replace(/^\s*[-*]\s+/, "").trim();
const nothing = (text: string) => /^nothing\.?$/i.test(text);

/** The form the Morning prep Do asks for, as cards and lists. */
export function readPrepared(text: string): PreparedDay {
  const day: PreparedDay = { cards: [], mine: [], nudges: [], other: [] };
  let section: "card" | "mine" | "nudges" | "other" = "other";
  for (const raw of String(text ?? "").split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const heading = line.match(/^#{1,3}\s+(.+)$/);
    if (heading) {
      const words = heading[1].trim();
      const meeting = words.match(MEETING);
      if (meeting) {
        day.cards.push({
          time: meeting[1],
          title: meeting[2].trim(),
          lines: [],
          raise: [],
        });
        section = "card";
      } else if (/^mine/i.test(words)) section = "mine";
      else if (/^nudge/i.test(words)) section = "nudges";
      else {
        section = "other";
        day.other.push(words);
      }
      continue;
    }
    const item = bullet(line);
    if (!item || nothing(item)) continue;
    if (section === "card") {
      const card = day.cards[day.cards.length - 1];
      const raise = item.match(/^raise:\s*(.+)$/i);
      if (raise) card.raise.push(raise[1].trim());
      else if (!/:\s*nothing\.?$/i.test(item)) card.lines.push(item);
    } else if (section === "mine") day.mine.push(item);
    else if (section === "nudges") day.nudges.push(item);
    else day.other.push(item);
  }
  return day;
}

/** An address is egress, never a label (owner rule: no host:port chips). */
const ADDRESS =
  /^(?:\d{1,3}(?:\.\d{1,3}){3}|[\w-]+(?:\.[\w-]+)*):\d+$|^https?:\/\//i;
/** A raw id (8+ hex) is never his words. */
const RAW_ID = /\b[0-9a-f]{8,}\b/i;
/** The engine's word for a meeting record it could not read. */
const NO_RECORD =
  /\b(?:time|title)\s+unavailable\b|\bmeeting\s+[0-9a-f]{6,}\b/i;

/** "Prepared 18:27 · Claude Code": the time, and the engine's name when it
 *  is a name (an address is left out). */
export function preparedBy(
  time: string,
  engine: string | null | undefined,
): string {
  const name = String(engine ?? "").trim();
  return [time, name && !ADDRESS.test(name) ? name : ""]
    .filter(Boolean)
    .join(" · ");
}

/** Keep generated record ids out of the list's names. */
export function preparedOther(day: PreparedDay): string[] {
  return day.other.filter((line) => !RAW_ID.test(line));
}

/** The chief-of-staff line when the result holds nothing for him: what the
 *  automation prepared and why, in his words. ``null`` when there is work. */
export function nothingLine(text: string, day: PreparedDay): string | null {
  if (
    day.cards.length ||
    day.mine.length ||
    day.nudges.length ||
    preparedOther(day).length
  ) {
    return null;
  }
  return NO_RECORD.test(String(text ?? ""))
    ? "The automation prepared nothing: the meeting record has no time or title"
    : "The automation prepared nothing for today";
}

/** Add a suggested point to this person's next 1:1 (the prep's own path:
 *  the open 1:1, else a new one, then its agenda item). */
export async function addToAgenda(
  relationshipId: string,
  body: string,
): Promise<void> {
  const base = `/api/people/relationships/${encodeURIComponent(relationshipId)}`;
  const read = await apiFetch<{
    relationship?: { sessions?: Array<{ id: string }> };
  }>(base);
  const session =
    read.relationship?.sessions?.[0] ??
    (
      await apiFetch<{ one_on_one: { id: string } }>(`${base}/one-on-ones`, {
        method: "POST",
        json: { visibility: "shared_intent" },
      })
    ).one_on_one;
  await apiFetch(
    `/api/people/one-on-ones/${encodeURIComponent(session.id)}/agenda`,
    {
      method: "POST",
      json: {
        body,
        visibility: "shared_intent",
        state: "open",
        source: { kind: "manual" },
      },
    },
  );
}
