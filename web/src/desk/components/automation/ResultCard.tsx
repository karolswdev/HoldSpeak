/** Betterment A3 — one result of an automation (DESIGN §4, "Results").
 *
 * The rendered answer (AgentWords: no `##`, no `**`) on paper, its head line
 * (when, how long, which model, where the prompt went, NEW), its verbs (Open
 * as note, Copy, Send), and a failure in words with Run again. While a run is
 * working, the head says so in place and nothing under it moves.
 *
 * The slot for what the agent used (Looked at / Wrote / Prepared; MCP M2)
 * draws nothing until the hub sends that record. */
import { Button } from "../../../components/signal/Signal";
import { AgentWords } from "../AgentWords";
import { EgressChip, FoldGadget, RunLine, StateChip } from "../../surface";
import { SendWellsFold } from "../../surface/send";
import { artifactDoc } from "../../documentSends";
import { boundaryEgressLamp } from "../../inferenceEgress";
import { openRef } from "../../openObject";
import { useCopyReceipt } from "../../hooks/useCopyReceipt";
import {
  costWords,
  failureWords,
  resultWhen,
  secondsWords,
  withoutIds,
  type AutomationResult,
  type AutomationUse,
} from "./model";

function egressScope(boundary: string): "local" | "remote" | "cloud" | undefined {
  if (!boundary) return undefined;
  if (boundary === "same_device" || boundary === "local") return "local";
  if (boundary === "cloud" || boundary === "external_service") return "cloud";
  return "remote";
}

function Egress({ boundary }: { boundary: string }) {
  if (!boundary) return null;
  const lamp = boundaryEgressLamp(boundary);
  return <EgressChip label={lamp.label} scope={egressScope(boundary)} title={`The prompt went: ${lamp.label}`} />;
}

/** Looked at / Wrote / Prepared (MCP M2). Nothing when absent or empty:
 *  never a counter of zero. */
function UsedSlot({ used }: { used?: AutomationUse | null }) {
  if (!used) return null;
  const groups: Array<[string, Array<{ ref: string; label: string }> | undefined]> = [
    ["Looked at", used.looked_at],
    ["Wrote", used.wrote],
    ["Prepared", used.prepared],
  ];
  const shown = groups.filter(([, rows]) => rows && rows.length);
  if (!shown.length) return null;
  return (
    <div className="automation-used" data-testid="automation-used">
      {shown.map(([label, rows]) => (
        <FoldGadget key={label} title={label} token={rows!.length > 0 ? rows!.length : undefined}>
          <ul className="automation-used-list">
            {rows!.map((row) => (
              <li key={row.ref}>
                <Button dense variant="ghost" onClick={() => openRef(row.ref)}>{row.label}</Button>
              </li>
            ))}
          </ul>
        </FoldGadget>
      ))}
    </div>
  );
}

export function ResultHead({ result, isNew }: { result: AutomationResult; isNew: boolean }) {
  const facts = [
    resultWhen(result.completed_at),
    secondsWords(result.seconds),
    result.model || null,
    costWords(result.cost_usd),
  ].filter(Boolean);
  return (
    <span className="automation-card-facts">
      <span className="automation-card-when">{facts.join(" · ")}</span>
      {result.status === "failed" ? <StateChip state="failure" label="FAILED" /> : null}
      <Egress boundary={result.boundary} />
      {isNew ? <StateChip state="active" label="NEW" data-testid="automation-new" /> : null}
    </span>
  );
}

export function ResultBody({
  result,
  onRunAgain,
  runAgainDisabled,
}: {
  result: AutomationResult;
  onRunAgain: () => void;
  runAgainDisabled?: boolean;
}) {
  const { copy, state: copyState } = useCopyReceipt();
  if (result.status === "failed") {
    return (
      <div className="automation-failure" data-testid="automation-failure">
        <p className="automation-failure-words">{failureWords(result.error)}</p>
        <Button dense variant="secondary" onClick={onRunAgain} disabled={runAgainDisabled}
          data-testid="automation-run-again">
          Run again
        </Button>
      </div>
    );
  }
  const text = withoutIds(result.text ?? "");
  return (
    <>
      <div className="automation-reading" data-testid="automation-reading">
        {text.trim() ? <AgentWords text={text} /> : <p className="automation-quiet">The engine gave no words.</p>}
      </div>
      <UsedSlot used={result.used} />
      <div className="automation-card-verbs">
        {result.note_id ? (
          <Button dense variant="secondary" onClick={() => openRef(`note:${result.note_id}`)}
            data-testid="automation-open-note">
            Open as note
          </Button>
        ) : null}
        {text.trim() ? (
          <Button dense variant="ghost" onClick={() => void copy(text)} data-testid="automation-copy">
            {copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy"}
          </Button>
        ) : null}
        {result.artifact_id ? (
          <SendWellsFold doc={artifactDoc(result.artifact_id, result.title, "automation result")} />
        ) : null}
      </div>
    </>
  );
}

/** The newest result, open: its head, or the working line in its place. */
export function ResultCard({
  result,
  isNew,
  working,
  onRunAgain,
}: {
  result: AutomationResult | null;
  isNew: boolean;
  /** A run in progress: when it began and on which engine. */
  working: { startedAt: number; engine: string } | null;
  onRunAgain: () => void;
}) {
  const head = working ? (
    <RunLine phase="running" verb="Working…" model={working.engine} startedAt={working.startedAt} />
  ) : result ? (
    <ResultHead result={result} isNew={isNew} />
  ) : (
    <span className="automation-card-empty">No results yet. Run now makes the first one.</span>
  );
  return (
    <article
      className="automation-card"
      data-testid="automation-newest"
      data-working={working ? "" : undefined}
      data-status={result?.status}
      aria-busy={working ? true : undefined}
    >
      <header className="automation-card-head">{head}</header>
      {result ? (
        <div className="automation-card-body">
          <ResultBody result={result} onRunAgain={onRunAgain} runAgainDisabled={Boolean(working)} />
        </div>
      ) : null}
    </article>
  );
}
