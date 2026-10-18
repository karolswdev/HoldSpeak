/** Looked at / Wrote / Prepared: what an agent used and did, in words.
 *
 * MCP M2 drew it under an automation's result; Betterment Q7 draws it under
 * an Ask answer too. Three folded lines, each says what in words (`3
 * meetings`): Looked at (each read object, a link), Wrote (each desk write, a
 * link, with Undo for what the agent made) and Prepared (each prepared send,
 * with Send). Nothing when absent or empty: never a counter of zero. */
import "./used-lines.css";
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { FoldGadget } from "../surface";
import { SendWellsFold } from "../surface/send";
import type { DocRef } from "../surface/send";
import { artifactDoc, deskDecisionDoc, noteDoc } from "../documentSends";
import { deleteSeatShown } from "../deleteSeat";
import { OBJECT_DELETE_REQUEST } from "../verbRegistry";
import { openRef } from "../openObject";
import { apiFetch } from "../../lib/api";
import { reportWriteFailure } from "../hooks/useWriteReceipt";
import { sendWords, usedWords, type AgentUse, type UsedRow } from "../used";

/** The document a prepared send carries, for its send fold. */
function preparedDoc(row: UsedRow): DocRef {
  const [kind, ...rest] = row.ref.split(":");
  const id = rest.join(":");
  if (kind === "note") return noteDoc(id, row.label);
  if (kind === "artifact") return artifactDoc(id, row.label, "automation result");
  if (kind === "decision") return deskDecisionDoc(id, row.label);
  return { ref: row.ref, title: row.label, label: kind.toUpperCase() };
}

/** A task the agent added is set aside (dismissed): Undo of a task. */
async function dismissTask(ref: string): Promise<void> {
  const id = ref.slice("action_item:".length);
  await apiFetch(`/api/all-action-items/${encodeURIComponent(id)}`, { method: "PATCH", json: { status: "dismissed" } });
}

/** A thing the agent made: open it; Undo takes it back. A task is
 *  dismissed; a desk object goes to the desk's one delete (its receipt keeps
 *  the Undo of that), withheld where no receipt seat is shown (UX-CANON
 *  A.11: a verb that does nothing is a lie). */
function WroteRow({ row, testPrefix }: { row: UsedRow & { undo?: boolean }; testPrefix: string }) {
  const [undone, setUndone] = useState(false);
  const isTask = row.ref.startsWith("action_item:");
  const canUndo = Boolean(row.undo) && !undone && (isTask || deleteSeatShown());
  return (
    <li className="used-lines-row" data-testid={`${testPrefix}-wrote-row`}>
      <Button dense variant="ghost" onClick={() => openRef(row.ref)}>{row.label}</Button>
      {undone && isTask ? <span className="used-lines-undone" role="status">Undone</span> : null}
      {canUndo ? (
        <Button dense variant="secondary" data-testid={`${testPrefix}-wrote-undo`}
          onClick={() => {
            if (isTask) {
              setUndone(true);
              void dismissTask(row.ref).catch((cause) => {
                setUndone(false);
                reportWriteFailure("Undo", cause);
              });
              return;
            }
            window.dispatchEvent(new CustomEvent(OBJECT_DELETE_REQUEST, { detail: { ref: row.ref } }));
            setUndone(true);
          }}>
          Undo
        </Button>
      ) : null}
    </li>
  );
}

export function UsedLines({
  used,
  testPrefix,
  lookedAt = true,
}: {
  used?: AgentUse | null;
  /** The test ids' prefix (`automation-used`, `ask-used`). */
  testPrefix: string;
  /** False where the face draws Looked at itself (the Ask answer). */
  lookedAt?: boolean;
}) {
  if (!used) return null;
  const looked = lookedAt ? used.looked_at ?? [] : [];
  const wrote = used.wrote ?? [];
  const prepared = used.prepared ?? [];
  if (!looked.length && !wrote.length && !prepared.length) return null;
  return (
    <div className="used-lines" data-testid={`${testPrefix}-used`}>
      {looked.length ? (
        <FoldGadget title="Looked at" token={usedWords(looked)} className="used-lines-fold">
          <ul className="used-lines-list" data-testid={`${testPrefix}-looked-at`}>
            {looked.map((row) => (
              <li key={row.ref}>
                <Button dense variant="ghost" onClick={() => openRef(row.ref)}>{row.label}</Button>
              </li>
            ))}
          </ul>
        </FoldGadget>
      ) : null}
      {wrote.length ? (
        <FoldGadget title="Wrote" token={usedWords(wrote)} className="used-lines-fold">
          <ul className="used-lines-list" data-testid={`${testPrefix}-wrote`}>
            {wrote.map((row) => <WroteRow key={row.ref} row={row} testPrefix={testPrefix} />)}
          </ul>
        </FoldGadget>
      ) : null}
      {prepared.length ? (
        <FoldGadget title="Prepared" token={sendWords(prepared.length)} className="used-lines-fold">
          <ul className="used-lines-sends" data-testid={`${testPrefix}-prepared`}>
            {prepared.map((row) => (
              <li key={row.send_id || row.ref} className="used-lines-send">
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
