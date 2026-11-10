// Parked: Run now moved to the mast; the result plate only owns its result and retries.
/** The plate of an automation (the language, 2026-11-08): the one raised
 * thing, the one thing that matters now, with its one lead verb.
 *
 * - a run in progress: "Running now", the engine and the clock;
 * - a refused run or a failed result: "Failed", why in words, Run again;
 * - a result: "Last result", when, how long, which model, the cost, NEW;
 *   the rendered answer (AgentWords: no `##`, no `**`), what the run's
 *   agent used (Looked at, Wrote, Prepared), Open as note, Copy, Send;
 * - a run that started a Program: the Program in its state, Open;
 * - no run yet: the next run (or "First run") and Run now.
 *
 * The plate is one element in every state, so nothing under it moves when
 * a run starts or ends. Run now rides the plate except where Run again
 * says the same thing. */
import type { ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { AgentWords } from "../AgentWords";
import { RunLine, StateChip } from "../../surface";
import { SendWellsFold } from "../../surface/send";
import { artifactDoc, noteDoc } from "../../documentSends";
import { UsedLines } from "../UsedLines";
import { openRef } from "../../openObject";
import { openProgram } from "../../programs/open";
import { useCopyReceipt } from "../../hooks/useCopyReceipt";
import {
  costWords,
  failureWords,
  resultWhen,
  runTone,
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
      {/* NEW leads the line, so a narrow plate never pushes it off. */}
      {isNew ? <StateChip state="active" label="NEW" data-testid="automation-new" /> : null}
      <span className="automation-card-when">{facts.join(" · ")}</span>
    </span>
  );
}

/** A result's reading (or its failure with Run again) and what its agent used. */
export function ResultBody({
  result,
  onRunAgain,
  runAgainDisabled,
}: {
  result: AutomationResult;
  onRunAgain: () => void;
  runAgainDisabled?: boolean;
}) {
  if (result.status === "failed") {
    return (
      <div className="automation-failure" data-testid="automation-failure">
        <p className="automation-failure-words">{failureWords(result.error)}</p>
        <Button dense variant="primary" onClick={onRunAgain} disabled={runAgainDisabled}
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
    </>
  );
}

function PlateHead({ title, facts }: { title: ReactNode; facts?: ReactNode }) {
  return (
    <header className="automation-plate-head automation-card-head">
      <h3 className="automation-plate-title">{title}</h3>
      {facts ? <span className="automation-plate-facts">{facts}</span> : null}
    </header>
  );
}

export function RunPlate({
  result,
  isNew,
  working,
  refusal,
  next,
  canRun,
  onRunNow,
}: {
  result: AutomationResult | null;
  isNew: boolean;
  /** A run in progress: when it began and on which engine. */
  working: { startedAt: number; engine: string } | null;
  /** A Run now the hub refused, in its words. */
  refusal: string | null;
  /** `Next: Fri 15:00` when it is on a schedule. */
  next: string | null;
  canRun: boolean;
  onRunNow: () => void;
}) {
  const { copy, state: copyState } = useCopyReceipt();
  const runNow = (lead: boolean) => (
    <Button dense variant={lead ? "primary" : "secondary"} onClick={onRunNow}
      disabled={!canRun || Boolean(working)} data-testid="automation-run-now">
      Run now
    </Button>
  );
  const program = result && !result.program_run && result.status !== "failed" ? result.program : undefined;
  const tone = working ? "steel" : refusal ? "coral" : result ? runTone(result) : "idle";

  let head: ReactNode;
  let body: ReactNode = null;
  let verbs: ReactNode;
  if (working) {
    head = <PlateHead title="Running now" facts={<RunLine phase="running" verb="Working…" model={working.engine} startedAt={working.startedAt} />} />;
    verbs = runNow(true);
  } else if (refusal) {
    head = <PlateHead title="Not run" />;
    body = (
      <div className="automation-failure" data-testid="automation-refusal">
        <p className="automation-failure-words">{failureWords(refusal)}</p>
        <Button dense variant="primary" onClick={onRunNow} disabled={!canRun}>Run again</Button>
      </div>
    );
  } else if (result?.status === "failed") {
    head = <PlateHead title="Failed" facts={<ResultHead result={result} isNew={false} />} />;
    body = <ResultBody result={result} onRunAgain={onRunNow} runAgainDisabled={!canRun} />;
  } else if (program) {
    head = <PlateHead title={program.title}
      facts={[program.state_word, program.total ? `${program.done} of ${program.total} steps` : ""].filter(Boolean).join(" · ")} />;
    verbs = (
      <>
        <Button dense variant="primary" onClick={() => openProgram(program.id)} data-testid="automation-open-program">Open program</Button>
        {runNow(false)}
      </>
    );
  } else if (result) {
    const text = withoutIds(result.text ?? "").trim();
    head = <PlateHead title="Last result" facts={<ResultHead result={result} isNew={isNew} />} />;
    body = <ResultBody result={result} onRunAgain={onRunNow} runAgainDisabled={!canRun} />;
    const doc = result.program_run
      ? (result.note_id ? noteDoc(result.note_id, result.title) : null)
      : (result.artifact_id ? artifactDoc(result.artifact_id, result.title, "automation result") : null);
    verbs = (
      <>
        {result.note_id ? (
          <Button dense variant="primary" onClick={() => openRef(`note:${result.note_id}`)} data-testid="automation-open-note">
            Open as note
          </Button>
        ) : null}
        {text ? (
          <Button dense variant="secondary" onClick={() => void copy(text)} data-testid="automation-copy">
            {copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy"}
          </Button>
        ) : null}
        {runNow(!result.note_id)}
        {doc ? <SendWellsFold doc={doc} /> : null}
      </>
    );
  } else {
    head = <PlateHead title={next ? next.replace(/^Next: /, "Next run · ") : "First run"} />;
    verbs = runNow(true);
  }
  return (
    <article
      className="automation-plate"
      data-testid="automation-newest"
      data-tone={tone}
      data-working={working ? "" : undefined}
      data-status={result?.status}
      aria-busy={working ? true : undefined}
    >
      {head}
      {body ? <div className="automation-card-body">{body}</div> : null}
      {verbs ? <div className="automation-plate-verbs">{verbs}</div> : null}
    </article>
  );
}
