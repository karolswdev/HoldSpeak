/** The first plate (the bold language, 2026-11-08; canvas NB): the one
 *  thing that waits on him most, raised over the ledger. The small brass
 *  label, the item's glyph and name in the display face, its facts in mono,
 *  its brief (three lines; More reads the whole item), and its verbs: the
 *  lead as the brass Button (Merge, Decide, Done), Open when it has a home,
 *  Later. Nothing waits: no plate.
 *
 *  The pick: a must-fix row first, then a Program that waits on him, then
 *  the oldest; in the hub's rank when those are equal. A source, a setup
 *  blocker, a recording that arms and an agent's ask stay in the ledger. */
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu } from "../components/DeskMenu";
import { clearWriteFailure, reportWriteFailure } from "../hooks/useWriteReceipt";
import { refreshNeedsYou } from "../needsYou";
import { briefable, deferItem, LATER_TIMES } from "../reach";
import { listSprite } from "../sprites";
import { objectSprite } from "../surface/objects/kinds";
import { wireDate } from "../surface/format";
import { followThrough, tomorrowDay } from "./needsApi";
import { glyphWord, ledgerFact, quietState, RowVerbs, RowWells, useRowMenu } from "./NeedRow";
import { faceOpener, needsRowSprite } from "./NeedVerbs";
import { readsInPlace, useReadInPlace } from "./ItemReader";
import { tierWord, type NeedFace } from "./needsFace";
import { DotWord } from "../surface/kit";
import { ProjectButton } from "../surface/patterns/ProjectButton";
import { openProjectRoom } from "../shell";
import { stateWords } from "../surface/words";

const NOT_FIRST = new Set(["setup", "none", "arming", "calendar", "repair"]);

/** The face the plate shows, or null when nothing waits. */
export function pickFirst(faces: readonly NeedFace[]): NeedFace | null {
  const candidates = faces
    .map((face, rank) => ({ face, rank }))
    .filter(({ face }) => !face.source && !face.uncounted && !face.askOf && face.group !== "agents"
      && !NOT_FIRST.has(face.verbs.kind));
  const since = (face: NeedFace) => {
    const at = face.since ? wireDate(face.since) : null;
    return at ? at.getTime() : Number.POSITIVE_INFINITY;
  };
  candidates.sort((a, b) =>
    Number(b.face.tier === "must") - Number(a.face.tier === "must")
    || Number(b.face.kind === "program") - Number(a.face.kind === "program")
    || since(a.face) - since(b.face)
    || a.rank - b.rank);
  return candidates[0]?.face ?? null;
}

/** The lead verb already opens the item: the plate draws no second Open. */
function leadOpens(face: NeedFace): boolean {
  const v = face.verbs;
  if (v.kind === "program") return !(v.ask === "merge" && v.choices.includes("merge")) && !(v.ask === "decide" && v.choices.length > 0);
  return ["open", "session", "link", "pr", "review", "summarize"].includes(v.kind);
}

/** The plate's brief: the step's own words when the name is the Program's
 *  title; else nothing (the name is the text). */
function plateText(face: NeedFace): string {
  const text = String(face.factTitle ?? "").trim();
  return text && text !== face.name ? text : "";
}

const LONG_TEXT = 160;

/** The plate says at most about three lines; the reader has the rest. A
 *  cut ends at a whole word and says so with an ellipsis. */
export function cutWords(text: string, max: number = LONG_TEXT): string {
  if (text.length <= max) return text;
  const head = text.slice(0, max);
  const space = head.lastIndexOf(" ");
  return `${(space > max * 0.6 ? head.slice(0, space) : head).trimEnd()}…`;
}

export function FirstPlate({ face, projects }: { face: NeedFace; projects: boolean }) {
  const ctl = useRowMenu(face, projects);
  const read = useReadInPlace(face);
  const [busy, setBusy] = useState(false);
  const [times, setTimes] = useState<{ x: number; y: number } | null>(null);
  const opener = readsInPlace(face) ? null : faceOpener(face);
  const v = face.verbs;
  const text = plateText(face);
  // The whole text is in the reader (an item with no other home) or at
  // its home: only then is a long text cut here.
  const long = Boolean(read) && (text || face.name).length > LONG_TEXT;
  const state = quietState(face);
  const fact = ledgerFact(face);
  const glyph = listSprite(needsRowSprite(face) ?? objectSprite(face.kind, face.id));

  const later = async (write: () => Promise<unknown>) => {
    if (busy) return;
    setBusy(true);
    try {
      await write();
      clearWriteFailure(face.id);
      void refreshNeedsYou(false);
    } catch (error) {
      reportWriteFailure("Later", error, () => void later(write), face.id);
    } finally {
      setBusy(false);
    }
  };
  const laterTimes = v.kind === "program" && v.ref && briefable(v.itemKind) && !v.later ? String(v.ref) : "";
  const laterTomorrow = v.kind === "work" && v.direction !== "theirs" ? v.cardId : "";

  return (
    <section className="needs-first" aria-label="Waits on you first" data-testid="needs-first">
      <h3 className="needs-first-label">Waits on you first</h3>
      <ul className="needs-list needs-first-list" aria-label="Waits on you first">
        <li {...ctl.rowProps} className="needs-row needs-first-row" data-object-id={face.id} data-kind={face.kind}>
          <img className="needs-first-glyph" src={glyph} alt={face.tier ? tierWord(face.tier) : glyphWord(face) ?? ""} draggable={false} />
          <span className="needs-row-what">
            <span className="needs-row-name" title={long && !text ? face.name : undefined}>{long && !text ? cutWords(face.name) : face.name}</span>
            {state || fact || ctl.project ? (
              <span className="needs-first-facts">
                {state ? <DotWord tone={state.tone} data-testid="needs-row-state">{stateWords(state.label)}</DotWord> : null}
                {fact ? <span className="needs-row-fact" title={face.factTitle || undefined}>{fact}</span> : null}
                {ctl.project ? (
                  <ProjectButton name={ctl.project.name} onOpen={() => openProjectRoom(ctl.project!.id)} plain
                    className="needs-row-project" data-testid="needs-row-project" />
                ) : null}
              </span>
            ) : null}
            {text ? <span className="needs-first-text">{long ? cutWords(text) : text}</span> : null}
          </span>
          <span className="needs-first-verbs">
            <span className="needs-row-verbs"><RowVerbs face={face} primary brass ctl={ctl} /></span>
            {long && read ? (
              <Button dense variant="ghost" aria-label={`More: ${face.name}`} data-testid="needs-first-more" onClick={read}>More</Button>
            ) : null}
            {opener && !leadOpens(face) ? (
              <Button dense variant="secondary" aria-label={`Open: ${face.name}`} data-testid="needs-first-open" onClick={() => opener()}>
                {face.kind === "program" ? "Open the Program" : "Open"}
              </Button>
            ) : null}
            {laterTimes ? (
              <Button dense variant="ghost" aria-haspopup="menu" disabled={busy} data-testid="needs-first-later"
                onClick={(event) => {
                  const box = event.currentTarget.getBoundingClientRect();
                  setTimes({ x: box.left, y: box.bottom });
                }}>Later</Button>
            ) : laterTomorrow ? (
              <Button dense variant="ghost" disabled={busy} title="Comes back tomorrow" data-testid="needs-first-later"
                onClick={() => void later(() => followThrough(laterTomorrow, "snooze", { until: tomorrowDay() }))}>Later</Button>
            ) : null}
            {times ? (
              <WorkMenu label="Later" x={times.x} y={times.y} autoFocus onClose={() => setTimes(null)}
                entries={LATER_TIMES.map((time) => ({ type: "item" as const, id: `later-${time.id}`, label: time.label,
                  onSelect: () => void later(() => deferItem(laterTimes, time.id)) }))} />
            ) : null}
          </span>
        </li>
        <RowWells face={face} well={ctl.well} setWell={ctl.setWell} />
      </ul>
    </section>
  );
}
