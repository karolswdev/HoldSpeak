/** Betterment A3 — one result of an automation (DESIGN §4, "Results").
 *
 * The rendered answer (AgentWords: no `##`, no `**`) on paper, its head line
 * (when, how long, which model, where the prompt went, NEW), its verbs (Open
 * as note, Copy, Send), and a failure in words with Run again. While a run is
 * working, the head says so in place and nothing under it moves.
 *
 * Under the answer, what the run's agent used and did (MCP M2): Looked at
 * (each read object, a link), Wrote (each desk write, with Undo for what the
 * run made) and Prepared (each prepared send, with Send). Nothing when the
 * agent touched nothing. */
import { Button } from "../../../components/signal/Signal";
import { AgentWords } from "../AgentWords";
import { RunLine, StateChip } from "../../surface";
import { SendWellsFold } from "../../surface/send";
import { artifactDoc } from "../../documentSends";
import { UsedLines } from "../UsedLines";
import { openRef } from "../../openObject";
import { useCopyReceipt } from "../../hooks/useCopyReceipt";
import {
  costWords,
  failureWords,
  resultWhen,
  secondsWords,
  withoutIds,
  type AutomationResult,
} from "./model";

export function ResultHead({ result, isNew }: { result: AutomationResult; isNew: boolean }) {
  const facts = [
    resultWhen(result.completed_at),
    secondsWords(result.seconds),
    result.model || null,
    costWords(result.cost_usd),
  ].filter(Boolean);
  return (
    <span className="automation-card-facts">
      {/* A4: NEW leads the line, so a narrow card never pushes it off. */}
      {isNew ? <StateChip state="active" label="NEW" data-testid="automation-new" /> : null}
      <span className="automation-card-when">{facts.join(" · ")}</span>
      {result.status === "failed" ? <StateChip state="failure" label="FAILED" /> : null}
    </span>
  );
}

export function ResultBody({
  result,
  onRunAgain,
  runAgainDisabled,
  send = true,
}: {
  result: AutomationResult;
  onRunAgain: () => void;
  runAgainDisabled?: boolean;
  /** Window grammar: false when the window's toolbar carries Send…. */
  send?: boolean;
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
      <UsedLines used={result.used} testPrefix="automation" />
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
        {send && result.artifact_id ? (
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
  send = true,
}: {
  result: AutomationResult | null;
  isNew: boolean;
  /** A run in progress: when it began and on which engine. */
  working: { startedAt: number; engine: string } | null;
  onRunAgain: () => void;
  /** Window grammar: false when the window's toolbar carries Send…. */
  send?: boolean;
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
      className="automation-card surface-group-well"
      data-testid="automation-newest"
      data-working={working ? "" : undefined}
      data-status={result?.status}
      aria-busy={working ? true : undefined}
    >
      <header className="automation-card-head">{head}</header>
      {result ? (
        <div className="automation-card-body">
          <ResultBody result={result} onRunAgain={onRunAgain} runAgainDisabled={Boolean(working)} send={send} />
        </div>
      ) : null}
    </article>
  );
}
