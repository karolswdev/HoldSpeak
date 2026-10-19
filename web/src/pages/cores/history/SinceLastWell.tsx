// betterment/capture C6 — Since last time.
// One folded line under the summary: "Since <title>, <date>: …", the last
// meeting of the same kind (the hub's aftercare: the same calendar series,
// else the same project, else the same people). Unfolded, what closed, what
// is still open and what is new, each a link. No previous meeting: no line.
import { Button } from "../../../components/signal/Signal";
import { Disclosure } from "../../../desk/surface/patterns";
import { SurfaceWell } from "../../../desk/surface/Surface";
import { openRef } from "../../../desk/openObject";
import { lookedAtDay } from "./LookedAtWell";

type SinceItem = {
  id?: string;
  task?: string;
  decision?: string;
  owner?: string | null;
  meeting_id?: string;
  provenance?: { segment_index?: number } | null;
};

export type SinceLastMeeting = {
  previous_meeting?: { id?: string; title?: string | null; date?: string } | null;
  closed_actions?: SinceItem[];
  still_open_actions?: SinceItem[];
  new_actions?: SinceItem[];
  new_decisions?: SinceItem[];
};

/** The aftercare body's `since_last_meeting`, or null. */
export function readSinceLast(aftercare: Record<string, unknown> | null | undefined): SinceLastMeeting | null {
  const since = aftercare?.since_last_meeting;
  if (!since || typeof since !== "object") return null;
  const previous = (since as SinceLastMeeting).previous_meeting;
  return previous?.id ? (since as SinceLastMeeting) : null;
}

/** The parts of the line, never a zero ("1 closed · 2 still open · 2 new"). */
export function sinceFacts(since: SinceLastMeeting): string {
  const closed = since.closed_actions?.length ?? 0;
  const open = since.still_open_actions?.length ?? 0;
  const fresh = (since.new_actions?.length ?? 0) + (since.new_decisions?.length ?? 0);
  const parts = [
    closed ? `${closed} closed` : "",
    open ? `${open} still open` : "",
    fresh ? `${fresh} new` : "",
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : "nothing changed";
}

export function SinceLastWell({
  since,
  meetingId,
  onOpen = openRef,
}: {
  since: SinceLastMeeting | null;
  meetingId: string;
  onOpen?: (ref: string) => void;
}) {
  const previous = since?.previous_meeting;
  if (!since || !previous?.id) return null;
  const title = (previous.title ?? "").trim() || "the last meeting";
  const day = previous.date ? lookedAtDay(previous.date) : "";
  const head = `Since ${title}${day ? `, ${day}` : ""}`;
  const lastRef = `meeting:${previous.id}`;
  // A new item is in THIS meeting: its link is its moment in the transcript.
  const hereRef = (item: SinceItem) => {
    const segment = item.provenance?.segment_index;
    return typeof segment === "number" ? `meeting:${meetingId}?segment=${segment}` : null;
  };
  const groups: Array<{ key: string; label: string; items: SinceItem[]; ref: (item: SinceItem) => string | null }> = [
    { key: "closed", label: "Closed", items: since.closed_actions ?? [], ref: () => lastRef },
    { key: "open", label: "Still open", items: since.still_open_actions ?? [], ref: () => lastRef },
    { key: "new", label: "New", items: [...(since.new_decisions ?? []), ...(since.new_actions ?? [])], ref: hereRef },
  ].filter((group) => group.items.length > 0);
  return (
    <div className="meetings-since-fold">
    <Disclosure label={`${head}: ${sinceFacts(since)}`}>
      <SurfaceWell>
        <div className="meetings-since" data-testid="meeting-since">
          <Button variant="ghost" dense onClick={() => onOpen(lastRef)}>{`Open ${title}`}</Button>
          {groups.map((group) => (
            <div key={group.key} className="meetings-since-group" data-testid={`meeting-since-${group.key}`}>
              <span className="surface-caption">{group.label}</span>
              <ul className="meetings-looked-at">
                {group.items.map((item, index) => {
                  const words = String(item.task ?? item.decision ?? "").trim();
                  const ref = group.ref(item);
                  return (
                    <li key={item.id ?? `${group.key}-${index}`}>
                      {ref ? (
                        <Button variant="ghost" dense onClick={() => onOpen(ref)}>{words}</Button>
                      ) : <span>{words}</span>}
                      {item.owner ? <span className="meetings-since-owner">{item.owner}</span> : null}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      </SurfaceWell>
    </Disclosure>
    </div>
  );
}
