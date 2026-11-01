/* PG-IMPORT IMP7 (BROCREW-IMPORT-2026-11-01, "the forest"): the Program's
 * family in the Program window, in direction A's plain rows. BroCrew: "Work
 * is a tree, not a thread … trace any result back to what asked for it."
 *
 * "Came from": the Program this one came from (an audit for its fix program,
 * the Program whose step's agent made it). "It made": the Programs it made.
 * Each row is the name, one state word, the ending word when it ended, and the
 * hub's one line; a press opens that Program. No family: nothing is drawn. */
import { Button } from "../../components/signal/Signal";
import { DotWord } from "../surface";
import { programTone } from "./model";
import { openProgram } from "./open";
import type { FamilyRow, ProgramFamily } from "./types";

function Row({ row }: { row: FamilyRow }) {
  const ended = row.ending && row.ending !== "none" ? row.ending : "";
  return (
    <li className="kit-listrow pg-family-row" data-state={row.state} data-testid="programs-family-row" data-program={row.id}>
      <Button variant="chrome" className="pg-family-open" onClick={() => openProgram(row.id)} aria-label={`Open ${row.name}`}
        data-testid="programs-family-open">
        <span className="pg-family-name">{row.name}</span>
        <DotWord tone={programTone(row.state)} className="pg-family-state">{ended ? `${row.state_word} · ${ended}` : row.state_word}</DotWord>
        {row.line ? <span className="pg-family-line" title={row.line}>{row.line}</span> : null}
      </Button>
    </li>
  );
}

export function ProgramFamilyRows({ family }: { family?: ProgramFamily | null }) {
  if (!family || (!family.parent && !family.children.length)) return null;
  return (
    <section className="pg-family" aria-label="Family" data-testid="programs-family">
      {family.parent ? (
        <>
          <h3 className="pg-board-caption">Came from</h3>
          <ul className="kit-listrows" data-testid="programs-family-parent"><Row row={family.parent} /></ul>
        </>
      ) : null}
      {family.children.length ? (
        <>
          <h3 className="pg-board-caption">It made</h3>
          <ul className="kit-listrows" data-testid="programs-family-children">
            {family.children.map((row) => <Row key={row.id} row={row} />)}
          </ul>
        </>
      ) : null}
    </section>
  );
}
