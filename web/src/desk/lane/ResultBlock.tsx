/** Betterment AG10: the Result of a turn (agents/DESIGN.md §4, "The agent's
 *  window"). When the turn is done it leads the Story: the agent's last
 *  words, what changed (files, branch, the PR), and what it did on the desk
 *  with its launch credential: Looked at, Wrote, Prepared (the hub's own
 *  log of its MCP calls). */
import { FoldGadget } from "../surface/gadgets";
import { AgentWords } from "../components/AgentWords";
import { branchFace, isNotRead, type LaneWire } from "./laneWire";

export interface LaneUseRow {
  ref: string;
  title?: string;
  label?: string;
}

export interface LaneUsed {
  looked_at?: LaneUseRow[];
  wrote?: LaneUseRow[];
  prepared?: LaneUseRow[];
}

/** `1 file changed`, `3 files changed`; "" with none. */
export function filesWords(n: number): string {
  return n ? `${n} ${n === 1 ? "file" : "files"} changed` : "";
}

function names(rows: readonly LaneUseRow[] | undefined): string[] {
  return (rows ?? []).map((row) => row.label || row.title || row.ref).filter(Boolean);
}

export function ResultBlock({ lane }: { lane: LaneWire }) {
  const worktree = lane.worktree;
  const files = isNotRead(worktree) ? null : worktree.files.length;
  const branch = branchFace(lane.launch.branch ?? (isNotRead(worktree) ? null : worktree.branch)) || "";
  const session = (lane.session && typeof lane.session === "object" ? lane.session : {}) as { last_assistant_text?: string | null };
  const said = String(session.last_assistant_text ?? "").trim();
  const used = (lane as LaneWire & { used?: LaneUsed | { not_read: string } }).used;
  const use = used && !("not_read" in used) ? used : null;
  const pr = lane.follow_through?.pr;
  const folds: Array<[string, string[], string]> = [
    ["Looked at", names(use?.looked_at), "lane-result-looked"],
    ["Wrote", names(use?.wrote), "lane-result-wrote"],
    ["Prepared", names(use?.prepared), "lane-result-prepared"],
  ];
  const facts = [filesWords(files ?? 0), branch, pr?.number != null ? `PR #${pr.number}` : ""].filter(Boolean);
  return (
    <section className="lw-result" data-testid="lane-result" aria-label="Result">
      <h3 className="lw-result-cap">Result</h3>
      {said ? <AgentWords className="lw-result-said" text={said} data-testid="lane-result-said" /> : null}
      {facts.length ? <span className="lw-result-facts" data-testid="lane-result-facts">{facts.join(" · ")}</span> : null}
      {folds.filter(([, rows]) => rows.length).map(([word, rows, testId]) => (
        <FoldGadget key={word} title={`${word}: ${rows.slice(0, 2).join(", ")}${rows.length > 2 ? ` and ${rows.length - 2} more` : ""}`} className="lw-result-fold">
          <ul className="lw-result-list" data-testid={testId}>
            {rows.map((name, i) => <li key={`${name}:${i}`}>{name}</li>)}
          </ul>
        </FoldGadget>
      ))}
    </section>
  );
}
