/* Direction A, step 2 (owner pick 2026-10-27, "The page and its margin";
 * docs/internal/betterment/canvases/note-workspace-2026-10-27.html).
 *
 * The text never moves. Answers and found tasks land in a margin at the
 * window's right edge (248 px), each card beside the line it came from.
 * Under 900 px of window the margin is a drawer at the foot of the page.
 *
 * - Cards: an Ask answer (Add to note, Dismiss) and an older thought's open
 *   question or draft. A card with a line sits beside it, with a thin lead to
 *   the line; a card without one sits at the top.
 * - Found in this note: the rows of Find the tasks, one verb each (Confirm;
 *   a confirmed row says Done). Rows arrive one by one. A row finds its line
 *   by its words (the hub sends no positions): the pointer on a row lights
 *   the line, and a press puts the caret there.
 * - The note's decision lines ("Decision: …"), under the tasks; a press
 *   opens the Decisions window. */
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import { Button } from "../../components/signal/Signal";
import { DotWord, RunLine, ToolGlyph } from "../surface";
import { StringGadget } from "../surface/gadgets";
import { hueOf } from "../surface/kit";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import type { DeskEditorHandle } from "../components/DeskEditor";
import { spriteUrl } from "../sprites";
import type { NoteOutcome } from "../noteOutcomes";
import type { NoteOutcomesState } from "./NoteOutcomesWell";
import { decisionLines, findLine, ownerInitials, type LineRange } from "./marginText";

export interface MarginCard {
  key: string;
  /** The note position the card is about; null puts it at the top. */
  anchor: number | null;
  node: ReactNode;
}

const GAP = 8;
/** The card's question row, where the lead meets the card. */
const LEAD_AT = 14;

function useCardPlaces(
  cards: MarginCard[],
  editorRef: RefObject<DeskEditorHandle | null>,
  bodyRef: RefObject<HTMLDivElement | null>,
  body: string,
) {
  const cardEls = useRef<Record<string, HTMLElement | null>>({});
  const [places, setPlaces] = useState<{ tops: Record<string, number>; leads: Record<string, number | null>; height: number }>(
    { tops: {}, leads: {}, height: 0 },
  );
  const [tick, setTick] = useState(0);
  const signature = cards.map((card) => `${card.key}@${card.anchor ?? "-"}`).join("|");
  useLayoutEffect(() => {
    const scroller = bodyRef.current;
    if (!scroller) return;
    const rect = scroller.getBoundingClientRect();
    const contentTop = rect.top - scroller.scrollTop;
    const editor = editorRef.current;
    const wanted = cards.map((card) => {
      const lineTop = card.anchor == null ? null : editor?.lineTop?.(card.anchor) ?? null;
      return { key: card.key, line: lineTop == null ? null : lineTop - contentTop };
    });
    // Cards with no line first, then by their line, top to bottom.
    wanted.sort((a, b) => (a.line ?? -Infinity) - (b.line ?? -Infinity));
    const tops: Record<string, number> = {};
    const leads: Record<string, number | null> = {};
    let cursor = GAP;
    for (const card of wanted) {
      const height = cardEls.current[card.key]?.offsetHeight ?? 0;
      const top = Math.max(card.line == null ? GAP : card.line - 4, cursor);
      tops[card.key] = top;
      // The lead meets the middle of the line's first row (about 11 px down).
      leads[card.key] = card.line == null || card.line < 0 ? null : Math.round(card.line + 11 - top);
      cursor = top + height + GAP;
    }
    const height = wanted.length ? cursor : 0;
    setPlaces((current) => {
      const same = current.height === height &&
        Object.keys(tops).length === Object.keys(current.tops).length &&
        Object.entries(tops).every(([key, value]) => current.tops[key] === value && current.leads[key] === leads[key]);
      return same ? current : { tops, leads, height };
    });
  }, [signature, body, tick]); // eslint-disable-line react-hooks/exhaustive-deps
  // The cards follow their lines as the note scrolls or the window resizes.
  useEffect(() => {
    const scroller = bodyRef.current;
    const page = scroller?.closest(".thought-note-document");
    if (!scroller || !page) return;
    let frame = 0;
    const again = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => setTick((value) => value + 1));
    };
    page.addEventListener("scroll", again, true);
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(again);
    observer?.observe(page);
    for (const element of Object.values(cardEls.current)) if (element) observer?.observe(element);
    return () => {
      cancelAnimationFrame(frame);
      page.removeEventListener("scroll", again, true);
      observer?.disconnect();
    };
  }, [signature]); // eslint-disable-line react-hooks/exhaustive-deps
  return { cardEls, places };
}

function RowGlyph({ kind }: { kind: "task" | "decision" }) {
  return <img className="note-margin-glyph" src={spriteUrl(kind === "task" ? "action" : "decision", kind, "rest", null, 20)} alt="" width={16} height={16} />;
}

function OutcomeMarginRow({
  row,
  index,
  line,
  outcomes,
  onLight,
  onGo,
  testId,
}: {
  row: NoteOutcome;
  index: number;
  line: LineRange | null;
  outcomes: NoteOutcomesState;
  onLight: (line: LineRange | null) => void;
  onGo: (line: LineRange) => void;
  testId: string;
}) {
  const { confirming, confirm, dismiss, edit } = outcomes;
  const [more, setMore] = useState<{ x: number; y: number; autoFocus: boolean } | null>(null);
  const [editing, setEditing] = useState<{ text: string; owner: string; due: string } | null>(null);
  const moreRef = useRef<HTMLButtonElement | null>(null);
  const made = row.state === "confirmed";
  const task = row.kind === "task";
  const owner = row.owner.trim() || "Me";
  const meta = task ? `${owner} · ${made ? "Confirmed" : row.due.trim() ? `by ${row.due.trim()}` : "no date"}` : made ? "Proposed on your desk" : "Proposed";
  const entries: WorkMenuEntry[] = [
    { type: "item", id: `edit-${row.id}`, label: editing ? "Close edit" : "Edit",
      onSelect: () => setEditing(editing ? null : { text: row.text, owner: row.owner, due: row.due }) },
    { type: "item", id: `dismiss-${row.id}`, label: "Dismiss", onSelect: () => void dismiss(row) },
  ];
  const save = async () => {
    if (!editing) return;
    const fields = task ? { text: editing.text, owner_name: editing.owner, due: editing.due } : { text: editing.text };
    if (await edit(row, fields)) setEditing(null);
  };
  return <li className="note-margin-row" data-testid={testId} data-state={made ? "done" : "proposed"}
    data-tied={line ? "" : undefined} style={{ ["--arrive" as string]: `${index * 120}ms` }}
    onMouseEnter={() => onLight(line)} onMouseLeave={() => onLight(null)}>
    <div className="note-margin-row-line">
      <Button variant="chrome" className="note-margin-row-go" title={meta} disabled={!line}
        aria-label={line ? `Go to: ${row.text}` : row.text}
        onFocus={() => onLight(line)} onBlur={() => onLight(null)} onClick={() => { if (line) onGo(line); }}>
        <RowGlyph kind={row.kind} />
        <span className="note-margin-row-text">{row.text}</span>
      </Button>
      {task ? <span className="kit-avatar note-margin-who" data-hue={hueOf(owner)} data-size="sm" title={meta}>{ownerInitials(owner)}</span> : null}
      {made ? <DotWord tone="ok" className="note-margin-done">Done</DotWord> : editing ? (
        <Button dense variant="secondary" loading={confirming === row.id} disabled={Boolean(confirming) || !editing.text.trim()} onClick={() => void save()}>Save</Button>
      ) : (
        <Button dense variant="secondary" loading={confirming === row.id} disabled={Boolean(confirming)}
          aria-label={`Confirm: ${row.text}`} onClick={() => void confirm(row)}>Confirm</Button>
      )}
      {made ? null : <Button ref={moreRef} dense variant="ghost" className="note-margin-more" aria-label={`More for ${row.text}`}
        aria-haspopup="menu" aria-expanded={Boolean(more)} disabled={Boolean(confirming)}
        onClick={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          setMore(more ? null : { x: rect.left, y: rect.bottom, autoFocus: event.detail === 0 });
        }}>⋯</Button>}
      {more ? <WorkMenu label={`More actions for ${row.text}`} x={more.x} y={more.y} entries={entries}
        autoFocus={more.autoFocus} returnFocus={() => moreRef.current?.focus()} onClose={() => setMore(null)} /> : null}
    </div>
    {editing ? <div className="note-outcome-edit" data-testid="note-outcome-edit">
      <StringGadget label={task ? "Task" : "Decision"} value={editing.text}
        onChange={(value) => setEditing({ ...editing, text: value })} disabled={Boolean(confirming)} />
      {task ? <>
        <StringGadget label="Who?" value={editing.owner} onChange={(value) => setEditing({ ...editing, owner: value })} disabled={Boolean(confirming)} />
        <StringGadget label="When?" value={editing.due} onChange={(value) => setEditing({ ...editing, due: value })} disabled={Boolean(confirming)} />
      </> : null}
    </div> : null}
  </li>;
}

export function NoteMargin({
  body,
  editorRef,
  cards,
  outcomes,
  showFound,
  onClose,
  onOpenDecision,
}: {
  body: string;
  editorRef: RefObject<DeskEditorHandle | null>;
  cards: MarginCard[];
  outcomes: NoteOutcomesState;
  /** Found in this note shows once Find the tasks has run (or its rows are kept). */
  showFound: boolean;
  onClose: () => void;
  onOpenDecision: (recordId: string | null) => void;
}) {
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const { cardEls, places } = useCardPlaces(cards, editorRef, bodyRef, body);
  const light = (line: LineRange | null) => editorRef.current?.lightRange?.(line);
  useEffect(() => () => { editorRef.current?.lightRange?.(null); }, [editorRef]);
  const go = (line: LineRange) => {
    light(null);
    editorRef.current?.restoreSelection(line.from, line.from, { focus: true });
  };
  const tasks = outcomes.rows.filter((row) => row.kind === "task");
  const hubDecisions = outcomes.rows.filter((row) => row.kind === "decision");
  const lines = decisionLines(body);
  // A decision line the hub also found shows once: the hub's row keeps its Confirm.
  const extraLines = lines.filter((line) => !hubDecisions.some((row) => findLine(line.text, row.text)));
  return <aside className="note-margin" aria-label="In the margin" data-testid="note-margin">
    <div className="note-margin-head">
      <span className="note-margin-title">In the margin</span>
      <Button dense variant="ghost" className="note-margin-close" aria-label="Close the margin" onClick={onClose}>✕</Button>
    </div>
    <div ref={bodyRef} className="note-margin-body">
      {cards.length ? <div className="note-margin-cards" style={{ ["--cards-h" as string]: `${places.height}px` }}>
        {cards.map((card) => {
          const lead = places.leads[card.key];
          return <div key={card.key} ref={(element) => { cardEls.current[card.key] = element; }}
            className="note-margin-card-place"
            data-lead={lead == null ? undefined : lead < LEAD_AT ? "up" : lead > LEAD_AT ? "down" : "level"}
            style={{ ["--top" as string]: `${places.tops[card.key] ?? GAP}px`, ...(lead == null ? {} : { ["--lead" as string]: `${lead}px` }) }}>
            {card.node}
          </div>;
        })}
      </div> : null}
      {showFound ? <section className="note-margin-found note-outcomes" aria-label="Found in this note" data-testid="note-outcomes">
        <div className="note-margin-cap">Found in this note</div>
        {outcomes.finding ? <div className="note-margin-run"><RunLine phase="running" verb="Finding the tasks" startedAt={outcomes.startedAt} /></div> : null}
        {tasks.length ? <ul className="note-margin-list" data-testid="note-commitments">
          {tasks.map((row, index) => <OutcomeMarginRow key={row.id} row={row} index={index} line={findLine(body, row.text)}
            outcomes={outcomes} onLight={light} onGo={go} testId="note-commitments-row" />)}
        </ul> : null}
        {hubDecisions.length || extraLines.length ? <ul className="note-margin-list note-margin-decisions" data-testid="note-decisions">
          {hubDecisions.map((row, index) => <OutcomeMarginRow key={row.id} row={row} index={tasks.length + index}
            line={findLine(body, row.text)} outcomes={outcomes} onLight={light} onGo={go} testId="note-decisions-row" />)}
          {extraLines.map((line, index) => <li key={`line-${line.from}`} className="note-margin-row" data-testid="note-decision-line"
            style={{ ["--arrive" as string]: `${(tasks.length + hubDecisions.length + index) * 120}ms` }}
            onMouseEnter={() => light(line)} onMouseLeave={() => light(null)}>
            <div className="note-margin-row-line">
              <Button variant="chrome" className="note-margin-row-go" aria-label={`Open the decision: ${line.text}`}
                title="Open in Decisions" onFocus={() => light(line)} onBlur={() => light(null)}
                onClick={() => onOpenDecision(line.recordId)}>
                <RowGlyph kind="decision" />
                <span className="note-margin-row-text">{line.text}</span>
              </Button>
            </div>
          </li>)}
        </ul> : null}
      </section> : null}
    </div>
  </aside>;
}

/** The card frame of the margin: the question line, then what came back,
 *  then its verbs. */
export function MarginNote({ question, children, verbs, testId, label, className }: {
  question: ReactNode;
  children?: ReactNode;
  verbs?: ReactNode;
  testId?: string;
  label?: string;
  className?: string;
}) {
  return <section className={className ? `note-margin-card ${className}` : "note-margin-card"} aria-label={label} data-testid={testId}>
    <div className="note-margin-q"><ToolGlyph kind="ask" /><span>{question}</span></div>
    {children}
    {verbs ? <div className="note-margin-verbs">{verbs}</div> : null}
  </section>;
}
