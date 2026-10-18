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
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { AgentWords } from "../AgentWords";
import { EgressChip, FoldGadget, RunLine, StateChip } from "../../surface";
import { SendWellsFold } from "../../surface/send";
import type { DocRef } from "../../surface/send";
import { artifactDoc, deskDecisionDoc, noteDoc } from "../../documentSends";
import { deleteSeatShown } from "../../deleteSeat";
import { OBJECT_DELETE_REQUEST } from "../../verbRegistry";
import { boundaryEgressLamp } from "../../inferenceEgress";
import { openRef } from "../../openObject";
import { useCopyReceipt } from "../../hooks/useCopyReceipt";
import {
  costWords,
  failureWords,
  resultWhen,
  secondsWords,
  sendWords,
  usedWords,
  withoutIds,
  type AutomationResult,
  type AutomationUse,
  type UsedRow,
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

/** The document a prepared send carries, for its send fold. */
function preparedDoc(row: UsedRow): DocRef {
  const [kind, ...rest] = row.ref.split(":");
  const id = rest.join(":");
  if (kind === "note") return noteDoc(id, row.label);
  if (kind === "artifact") return artifactDoc(id, row.label, "automation result");
  if (kind === "decision") return deskDecisionDoc(id, row.label);
  return { ref: row.ref, title: row.label, label: kind.toUpperCase() };
}

/** A thing the agent made: open it; Undo hands it to the desk's one delete
 *  (its receipt keeps the Undo of that). Withheld where no receipt seat is
 *  shown (UX-CANON A.11: a verb that does nothing is a lie). */
function WroteRow({ row }: { row: UsedRow & { undo?: boolean } }) {
  const [undone, setUndone] = useState(false);
  const canUndo = Boolean(row.undo) && !undone && deleteSeatShown();
  return (
    <li className="automation-used-row" data-testid="automation-wrote-row">
      <Button dense variant="ghost" onClick={() => openRef(row.ref)}>{row.label}</Button>
      {canUndo ? (
        <Button dense variant="secondary" data-testid="automation-wrote-undo"
          onClick={() => {
            window.dispatchEvent(new CustomEvent(OBJECT_DELETE_REQUEST, { detail: { ref: row.ref } }));
            setUndone(true);
          }}>
          Undo
        </Button>
      ) : null}
    </li>
  );
}

/** Looked at / Wrote / Prepared (MCP M2): three folded lines, each says what
 *  in words (`3 meetings`). Nothing when absent or empty: never a counter of
 *  zero. */
function UsedSlot({ used }: { used?: AutomationUse | null }) {
  if (!used) return null;
  const looked = used.looked_at ?? [];
  const wrote = used.wrote ?? [];
  const prepared = used.prepared ?? [];
  if (!looked.length && !wrote.length && !prepared.length) return null;
  return (
    <div className="automation-used" data-testid="automation-used">
      {looked.length ? (
        <FoldGadget title="Looked at" token={usedWords(looked)} className="automation-used-fold">
          <ul className="automation-used-list" data-testid="automation-looked-at">
            {looked.map((row) => (
              <li key={row.ref}>
                <Button dense variant="ghost" onClick={() => openRef(row.ref)}>{row.label}</Button>
              </li>
            ))}
          </ul>
        </FoldGadget>
      ) : null}
      {wrote.length ? (
        <FoldGadget title="Wrote" token={usedWords(wrote)} className="automation-used-fold">
          <ul className="automation-used-list" data-testid="automation-wrote">
            {wrote.map((row) => <WroteRow key={row.ref} row={row} />)}
          </ul>
        </FoldGadget>
      ) : null}
      {prepared.length ? (
        <FoldGadget title="Prepared" token={sendWords(prepared.length)} className="automation-used-fold">
          <ul className="automation-used-sends" data-testid="automation-prepared">
            {prepared.map((row) => (
              <li key={row.send_id || row.ref} className="automation-used-send">
                <Button dense variant="ghost" onClick={() => openRef(row.ref)}>
                  {row.destination ? `${row.label} to ${row.destination}` : row.label}
                </Button>
                <SendWellsFold doc={preparedDoc(row)} />
              </li>
            ))}
          </ul>
        </FoldGadget>
      ) : null}
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
      {/* A4: NEW leads the line, so a narrow card never pushes it off. */}
      {isNew ? <StateChip state="active" label="NEW" data-testid="automation-new" /> : null}
      <span className="automation-card-when">{facts.join(" · ")}</span>
      {result.status === "failed" ? <StateChip state="failure" label="FAILED" /> : null}
      <Egress boundary={result.boundary} />
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
