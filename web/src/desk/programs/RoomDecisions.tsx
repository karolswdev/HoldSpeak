/* PG16 (design §9b, "What drives it"): the Room's proposed decisions, in
 * the Project drawer. A Skip of a finding or a merge the engine made by rule
 * becomes a proposed decision record; each row shows its words, the
 * "Proposed" dot, its Program and its PR, and Open (the record in the
 * Decisions window, where he accepts it). Nothing when there is none. */
import { Button } from "../../components/signal/Signal";
import { DotWord, FoldGadget, ListView } from "../surface";
import { spriteUrl } from "../sprites";
import { openDecisionRecord } from "../openObject";
import type { RoomProposedDecision } from "../../features/project-room/model";
import "./programs.css";

/** `The words wave · PR #101` (the PR only once it is open). */
export function proposedFrom(row: RoomProposedDecision): string {
  const prs = row.prs.map((pr) => (pr.number != null ? `PR #${pr.number}` : "PR")).join(", ");
  return [row.program.title, prs].filter(Boolean).join(" · ");
}

export function RoomDecisions({ proposed }: { proposed: readonly RoomProposedDecision[] }) {
  if (!proposed.length) return null;
  return (
    <FoldGadget className="pg-room" title="Proposed decisions" token={String(proposed.length)} open>
      <ListView label="Proposed decisions" data-testid="room-proposed-decisions">
        <ul className="kit-listrows">
          {proposed.map((row) => (
            <li key={row.id} className="kit-listrow pg-room-row" data-testid="room-proposed-decision">
              <span className="kit-listrow-main">
                <img className="kit-listrow-glyph" src={spriteUrl("decision", row.id, "rest", null, 20)} alt="" width={20} height={20} />
                <span className="kit-listrow-text">
                  <span className="kit-listrow-name">{row.text}</span>
                  <span className="kit-listrow-meta" data-testid="room-proposed-from">{proposedFrom(row)}</span>
                </span>
              </span>
              <DotWord tone="ask" className="kit-listrow-state">Proposed</DotWord>
              <span className="kit-listrow-verbs">
                <Button dense variant="secondary" onClick={() => openDecisionRecord(row.id)} aria-label={`Open ${row.text}`}
                  data-testid="room-proposed-open">Open decision</Button>
              </span>
            </li>
          ))}
        </ul>
      </ListView>
    </FoldGadget>
  );
}
