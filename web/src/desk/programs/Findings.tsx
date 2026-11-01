/* PG-LANG JRN8 to JRN10 (journey J7, a reviewer-only program): the audit's
 * faces in the Program window, never a second window.
 *
 * - AuditLine: under the track, the one fact of an audit ("Reviewer only:
 *   nothing is written").
 * - FindingsBoard: every finding once, as rows ("Must fix: …", "Should
 *   fix: …", "Noted: …"), its evidence as plain words, the steps that found
 *   it, and the Door task a filed finding became (Open task). The hub's
 *   head says the count; a board with no rows says only the head. After
 *   his Make the fix program is a link (Open the fix program). */
import { Button } from "../../components/signal/Signal";
import { openRef } from "../openObject";
import { openProgram } from "./open";
import type { FindingRow, Program } from "./types";

export function isAudit(program: Pick<Program, "template">): boolean {
  return program.template === "audit";
}

export function AuditLine({ program }: { program: Program }) {
  if (!isAudit(program)) return null;
  return <p className="pg-audit-line" data-testid="programs-audit-line">Reviewer only: nothing is written</p>;
}

/** `Step 2`, `Steps 1 and 2`, `Steps 1, 2 and 4`. */
function stepsWords(steps: readonly number[]): string {
  if (!steps.length) return "";
  if (steps.length === 1) return `Step ${steps[0]}`;
  return `Steps ${steps.slice(0, -1).join(", ")} and ${steps[steps.length - 1]}`;
}

function FindingLine({ row }: { row: FindingRow }) {
  const evidence = row.evidence.join(", ");
  return (
    <li className="kit-listrow pg-finding" data-level={row.level} data-testid="programs-finding" data-key={row.key}>
      <span className="pg-finding-text"><b>{`${row.words}:`}</b> {row.text}</span>
      <span className="pg-finding-meta">
        {[stepsWords(row.steps), evidence ? `Evidence: ${evidence}` : ""].filter(Boolean).join(" · ")}
      </span>
      {row.filed && row.task_id ? (
        <span className="pg-finding-verbs">
          <Button dense variant="ghost" onClick={() => openRef(`action:${row.task_id}`)} data-testid="programs-finding-task">
            Open Door task
          </Button>
        </span>
      ) : null}
    </li>
  );
}

export function FindingsBoard({ program }: { program: Program }) {
  const board = program.findings_board;
  if (!board) return null;
  return (
    <section className="pg-findings" aria-label="Findings" data-testid="programs-findings">
      <h3 className="pg-board-caption">Findings<span className="pg-fold-sub">{` · ${board.head}`}</span></h3>
      {program.fix_program_id ? (
        <p className="pg-findings-fix">
          <Button dense variant="secondary" onClick={() => openProgram(program.fix_program_id!)} data-testid="programs-findings-fix">
            Open the fix program
          </Button>
        </p>
      ) : null}
      {board.rows.length ? (
        <ul className="kit-listrows">
          {board.rows.map((row) => <FindingLine key={row.key} row={row} />)}
        </ul>
      ) : null}
    </section>
  );
}
