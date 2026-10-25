/** Betterment daily D9 — Today's Prepared block (owner decision 3).
 *
 * The newest result of the automation whose Put it in is Today (Morning
 * prep, weekdays 07:30), read from `GET /api/automations/prepared`. The
 * starter's Do asks the engine for one form, and this block reads it:
 *
 *   ## HH:MM <meeting title>      one card per meeting today
 *   - <name> owes: …  - I owe: …  each side's open items
 *   - Raise: …                    a *suggested* point; Add puts it on the
 *                                 1:1 agenda (only his press adds it)
 *   ## Mine today                 what is his and due
 *   ## Nudges                     drafted nudges; he sends them himself
 *
 * An answer in another form is shown as its lines. Looked at names what the
 * agent read (MCP M2). No result: no block (never an empty frame). */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { calendarOpener } from "../../openObject";
import { useDesk } from "../../store";

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

export type PreparedCard = { time: string; title: string; lines: string[]; raise: string[] };
export type PreparedDay = { cards: PreparedCard[]; mine: string[]; nudges: string[]; other: string[] };

type Event = { id: string; title?: string; event_title?: string; starts_at: string; person_relationship_id?: string; project_id?: string };

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
        day.cards.push({ time: meeting[1], title: meeting[2].trim(), lines: [], raise: [] });
        section = "card";
      } else if (/^mine/i.test(words)) section = "mine";
      else if (/^nudge/i.test(words)) section = "nudges";
      else { section = "other"; day.other.push(words); }
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

const pad = (n: number) => String(n).padStart(2, "0");

/** Add a suggested point to this person's next 1:1 (the prep's own path:
 *  the open 1:1, else a new one, then its agenda item). */
async function addToAgenda(relationshipId: string, body: string): Promise<void> {
  const base = `/api/people/relationships/${encodeURIComponent(relationshipId)}`;
  const read = await apiFetch<{ relationship?: { sessions?: Array<{ id: string }> } }>(base);
  const session = read.relationship?.sessions?.[0]
    ?? (await apiFetch<{ one_on_one: { id: string } }>(`${base}/one-on-ones`, { method: "POST", json: { visibility: "shared_intent" } })).one_on_one;
  await apiFetch(`/api/people/one-on-ones/${encodeURIComponent(session.id)}/agenda`, {
    method: "POST", json: { body, visibility: "shared_intent", state: "open", source: { kind: "manual" } },
  });
}

function PreparedCardView({ card, event }: { card: PreparedCard; event: Event | null }) {
  const [added, setAdded] = useState<Record<string, "busy" | "added" | "failed">>({});
  const person = event?.person_relationship_id ?? "";
  const open = event ? calendarOpener(event) : null;
  const add = (point: string) => {
    setAdded((state) => ({ ...state, [point]: "busy" }));
    addToAgenda(person, point).then(
      () => setAdded((state) => ({ ...state, [point]: "added" })),
      () => setAdded((state) => ({ ...state, [point]: "failed" })),
    );
  };
  return (
    <article className="today-prepared-card" data-testid="today-prepared-card" aria-label={`${card.time} ${card.title}`}>
      <header className="today-prepared-card-head">
        <span className="today-prepared-time">{card.time}</span>
        <span className="today-prepared-title">{card.title}</span>
        {open ? <Button dense variant="ghost" onClick={open} data-testid="today-prepared-prep">Prep</Button> : null}
      </header>
      {card.lines.length ? (
        <ul className="today-prepared-lines">{card.lines.map((line, i) => <li key={i}>{line}</li>)}</ul>
      ) : null}
      {card.raise.map((point) => (
        <div key={point} className="today-prepared-raise" data-testid="today-prepared-raise">
          <span className="today-prepared-raise-text">To raise: {point}</span>
          <span className="kit-pill" data-tone="info">Suggested</span>
          {person ? (
            added[point] === "added" ? (
              <span className="kit-pill" data-tone="ok" role="status">On the agenda</span>
            ) : (
              <Button dense variant="secondary" loading={added[point] === "busy"}
                aria-label={`Add to the agenda: ${point}`} onClick={() => add(point)}>
                Add
              </Button>
            )
          ) : null}
          {added[point] === "failed" ? <span className="kit-pill" data-tone="danger" role="status">Not added. Try again</span> : null}
        </div>
      ))}
    </article>
  );
}

export function PreparedBlock({ read, events }: { read: PreparedRead | null; events: Event[] }) {
  const prepared = read?.prepared;
  if (!prepared?.result?.text) return null;
  const day = readPrepared(prepared.result.text);
  const at = prepared.result.completed_at ? new Date(prepared.result.completed_at) : null;
  const time = at && !Number.isNaN(at.getTime()) ? `${pad(at.getHours())}:${pad(at.getMinutes())}` : "";
  const looked = (prepared.result.used?.looked_at ?? []).map((row) => row.label || row.ref).filter(Boolean);
  const match = (title: string) => events.find((e) =>
    String(e.title || e.event_title || "").trim().toLowerCase() === title.trim().toLowerCase()) ?? null;
  const openAutomation = () => useDesk.getState().openWorkbenchWindow(prepared.workbench_id);
  return (
    <section className="today-prepared" data-testid="today-prepared" aria-label="Prepared">
      <header className="today-prepared-bar">
        <span className="today-prepared-label">Prepared</span>
        <span className="today-prepared-by" data-testid="today-prepared-by">
          {[time, prepared.engine].filter(Boolean).join(" · ")}
        </span>
        {prepared.result.new ? <span className="kit-pill" data-tone="info" data-testid="today-prepared-new">NEW</span> : null}
        <span className="today-head-sp" />
        <Button dense variant="ghost" aria-label={`Open ${prepared.name}`} onClick={openAutomation}>Open the automation</Button>
      </header>
      {day.cards.length ? (
        <div className="today-prepared-cards">
          {day.cards.map((card) => <PreparedCardView key={`${card.time} ${card.title}`} card={card} event={match(card.title)} />)}
        </div>
      ) : null}
      {day.mine.length ? (
        <div className="today-prepared-list" data-testid="today-prepared-mine">
          <span className="today-prepared-cap">Mine today</span>
          <ul>{day.mine.map((line, i) => <li key={i}>{line}</li>)}</ul>
        </div>
      ) : null}
      {day.nudges.length ? (
        <div className="today-prepared-list" data-testid="today-prepared-nudges">
          <span className="today-prepared-cap">Nudges to send</span>
          <ul>{day.nudges.map((line, i) => <li key={i}>{line}</li>)}</ul>
        </div>
      ) : null}
      {day.other.length ? (
        <div className="today-prepared-list"><ul>{day.other.map((line, i) => <li key={i}>{line}</li>)}</ul></div>
      ) : null}
      {looked.length ? (
        <p className="today-prepared-looked" data-testid="today-prepared-looked">Looked at: {looked.join(", ")}</p>
      ) : null}
    </section>
  );
}
