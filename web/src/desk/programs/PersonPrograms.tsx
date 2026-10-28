/* Programs (design §9b, "Who it is for: the person"): the person room's
 * Programs line under Commitments ("The hub stops stalling · 4 of 6 · PR
 * #1591 waits on you"), and the 1:1 prep's "To show them" (a step merged
 * since the last 1:1) and "To ask" (a finding or a review waits on them).
 * Nothing when no Program is for this person. */
import { Button } from "../../components/signal/Signal";
import { DotWord, StateChip } from "../surface";
import { spriteUrl } from "../sprites";
import { programChip } from "./model";
import { openProgram } from "./open";
import type { PersonProgramRow } from "./types";
import "./programs.css";

export function personProgramsOf(...sources: unknown[]): PersonProgramRow[] {
  for (const source of sources) {
    const rows = (source as { programs?: unknown } | null | undefined)?.programs;
    if (Array.isArray(rows)) return rows.filter((row): row is PersonProgramRow => Boolean(row && typeof row === "object" && (row as PersonProgramRow).id));
  }
  return [];
}

export function PersonPrograms({ programs, name }: { programs: readonly PersonProgramRow[]; name: string }) {
  if (!programs.length) return null;
  const show = programs.flatMap((row) => (row.to_show ?? []).map((step) => ({ program: row, step })));
  const ask = programs.flatMap((row) => (row.to_ask ?? []).map((step) => ({ program: row, step })));
  return (
    <section className="people-section pg-person" aria-label="Programs" data-testid="person-programs">
      <header className="people-section-head"><h3 className="people-section-cap">Programs</h3></header>
      <ul className="kit-listrows">
        {programs.map((row) => (
          <li key={row.id} className="kit-listrow pg-person-row" data-testid="person-program-row">
            <span className="kit-listrow-main">
              <img className="kit-listrow-glyph" src={spriteUrl("program", row.id, "rest", null, 20)} alt="" width={20} height={20} />
              <span className="kit-listrow-name">{row.line || `${row.title} · ${row.done} of ${row.total}`}</span>
            </span>
            <StateChip state={programChip(row.state)} label={row.state_word} />
            <span className="kit-listrow-verbs">
              <Button dense variant="ghost" onClick={() => openProgram(row.id)} aria-label={`Open ${row.title}`} data-testid="person-program-open">Open program</Button>
            </span>
          </li>
        ))}
      </ul>
      {show.length ? (
        <div className="pg-person-lines" data-testid="person-programs-show">
          <h4 className="people-owe-cap">To show them</h4>
          <ul className="kit-listrows">
            {show.map(({ program, step }) => (
              <li key={`${program.id}:${step.step_id}`} className="kit-listrow">
                <DotWord tone="ok">{`${step.title}${step.pr_number ? ` · Merged #${step.pr_number}` : ""}`}</DotWord>
                <span className="kit-listrow-age">{program.title}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {ask.length ? (
        <div className="pg-person-lines" data-testid="person-programs-ask">
          <h4 className="people-owe-cap">To ask</h4>
          <ul className="kit-listrows">
            {ask.map(({ program, step }) => (
              <li key={`${program.id}:${step.step_id}:${step.kind}`} className="kit-listrow">
                <DotWord tone="ask">{step.kind === "ask_review" ? `Ask ${name} to review ${step.title}` : step.title}</DotWord>
                <span className="kit-listrow-age">{program.title}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
