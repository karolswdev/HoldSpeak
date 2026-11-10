// Parked: app-owned rail replaced by surface Rail.
/* The rail of decisions (the native Decisions app, 2026-11-08; the language
 * of Programs, the Room and People): the left edge of the Decisions window.
 * New decision, the search and Current only at the head; then one row per
 * decision: its words, the day in mono and where it was decided, and a
 * spine in its state's colour (proposed brass, decided steel, committed
 * moss, disputed coral, superseded graphite). A press picks the row; the
 * right pane is that decision. ↑ and ↓ walk the rows. At 393 the rail is
 * the whole window until a pick (decisions.css). */
import { useRef, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { CheckGadget, Spine, StringGadget, useRovingRows, type SpineTone } from "../surface";
import { ToolGlyph } from "../surface/kit";

export type RailDecision = { key: string; title: string; day: string; where: string; tone: SpineTone; word: string };

export function DecisionsRail({ rows, picked, query, onQuery, current, onCurrent, onPick, onNew, composing, head, more }: {
  rows: RailDecision[]; picked: string | null;
  query: string; onQuery(next: string): void;
  current: boolean; onCurrent(next: boolean): void;
  onPick(key: string): void; onNew(): void;
  /** The composer is the plate: New decision shows it is pressed. */
  composing: boolean;
  /** Under the head: All decisions, when the window shows only some. */
  head?: ReactNode;
  /** Show more, when the ledger holds more than one page. */
  more?: ReactNode;
}) {
  const ref = useRef<HTMLElement | null>(null);
  useRovingRows(ref, { selector: ".decisions-rail-row" });
  return (
    <nav ref={ref} className="decisions-rail" aria-label="Decisions" data-testid="decisions-rail">
      <div className="decisions-rail-head">
        <Button dense variant="primary" aria-expanded={composing} onClick={onNew} data-testid="decisions-new">
          <ToolGlyph kind="new" />New decision
        </Button>
        <StringGadget label="Search decisions" type="search" value={query} onChange={onQuery} placeholder="Search decisions" />
        <CheckGadget label="Current only" variant="token" checked={current} onChange={onCurrent} />
        {head}
      </div>
      <ul className="decisions-rail-list">
        {rows.map((row) => (
          <li key={row.key} data-testid="decisions-row" data-kind="decision" data-state={row.tone}>
            <Button variant="chrome" className="decisions-rail-row" aria-current={row.key === picked ? "true" : undefined}
              aria-label={`${row.title}, ${row.word}`} onClick={() => onPick(row.key)}>
              <span className="decisions-rail-title">{row.title}</span>
              <span className="decisions-rail-facts">
                {row.day ? <span className="decisions-rail-day">{row.day}</span> : null}
                {row.where ? <span>{row.where}</span> : null}
                <span className="decisions-rail-word" data-tone={row.tone} data-testid="decisions-state">{row.word}</span>
              </span>
              <Spine className="decisions-rail-spine" tone={row.tone} />
            </Button>
          </li>
        ))}
      </ul>
      {more}
    </nav>
  );
}
