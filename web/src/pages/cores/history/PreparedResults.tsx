// betterment/capture C5 — the Results the meeting prepared.
// Under Outcomes: "Prepared · N", one row per Result (the follow-up, then
// each draft the meeting asked for: an ADR, an update for stakeholders, a
// diagram). A ready row unfolds to the rendered draft and carries Open as
// note, Copy and Send (the shared Send well; nothing leaves without his
// press). A draft still being written says "Writing… N s" in place; a failed
// one says why. The hub's read: GET /api/meetings/<id>/prepared.
import { useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection } from "../../../desk/surface";
import { RunLine } from "../../../desk/surface/RunLine";
import { SendWellsFold } from "../../../desk/surface/send";
import { artifactDoc } from "../../../desk/documentSends";
import { AgentWords } from "../../../desk/components/AgentWords";
import { useCopyReceipt } from "../../../desk/hooks/useCopyReceipt";
import { openRef } from "../../../desk/openObject";
import { apiFetch } from "../../../lib/api";

export type PreparedResult = {
  kind: string;
  label: string;
  state: "ready" | "writing" | "failed";
  title?: string;
  body_markdown?: string;
  artifact_id?: string;
  document_ref?: string;
  seconds?: number | null;
  since?: string;
  reason?: string;
  serves?: string[];
};

/** The press on an action's "Draft ready": open that Result's row. */
export const PREPARED_OPEN = "holdspeak:meeting-prepared-open";
export type PreparedOpen = { meetingId: string; kind: string };

export function readPrepared(body: unknown): PreparedResult[] {
  const results = (body as { results?: unknown } | null)?.results;
  return Array.isArray(results) ? (results as PreparedResult[]).filter((r) => r && typeof r.kind === "string") : [];
}

/** The ready Result that serves this action item, if any. */
export function resultServing(results: PreparedResult[], actionItemId: string | undefined): PreparedResult | null {
  if (!actionItemId) return null;
  return results.find((r) => r.state === "ready" && (r.serves ?? []).includes(actionItemId)) ?? null;
}

export function openPrepared(meetingId: string, kind: string) {
  window.dispatchEvent(new CustomEvent<PreparedOpen>(PREPARED_OPEN, { detail: { meetingId, kind } }));
}

/** A draft's words without a leading heading that repeats its title. */
function draftText(result: PreparedResult): string {
  const body = String(result.body_markdown ?? "").trim();
  const title = String(result.title ?? "").trim();
  if (!title) return body;
  const echo = new RegExp(`^#{1,3}\\s+${title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*\\n+`, "i");
  return body.replace(echo, "");
}

function ResultVerbs({ meetingId, result, reading, onRead }: {
  meetingId: string; result: PreparedResult; reading: boolean; onRead(): void;
}) {
  const { copy, state: copyState } = useCopyReceipt();
  const [noting, setNoting] = useState(false);
  const [noteFailed, setNoteFailed] = useState(false);
  const noteId = useRef<string | null>(null);
  const text = draftText(result);
  const title = String(result.title || result.label);
  const doc = result.artifact_id
    ? artifactDoc(result.artifact_id, title, result.kind)
    : result.document_ref
      ? { ref: result.document_ref, title, label: result.label.toUpperCase() }
      : null;
  const openAsNote = async () => {
    // One note per Result: a second press opens the same note.
    if (noteId.current) { openRef(`note:${noteId.current}`); return; }
    setNoting(true);
    setNoteFailed(false);
    try {
      const made = await apiFetch<{ note?: { id?: string } }>("/api/notes", {
        method: "POST", json: { title, body_markdown: text, tags: ["meeting", `meeting:${meetingId}`] },
      });
      const id = String(made.note?.id ?? "");
      if (!id) { setNoteFailed(true); return; }
      noteId.current = id;
      openRef(`note:${id}`);
    } catch {
      setNoteFailed(true);
    } finally {
      setNoting(false);
    }
  };
  return (
    <div className="meeting-prepared-verbs">
      <Button dense variant="ghost" aria-expanded={reading} onClick={onRead} data-testid="prepared-read">
        {reading ? "Fold" : "Read"}
      </Button>
      <Button dense variant="secondary" loading={noting} onClick={() => void openAsNote()}
        data-testid="prepared-open-note">
        {noteFailed ? "Note not made · Try again" : "Open as note"}
      </Button>
      <Button dense variant="ghost" onClick={() => void copy(text)} data-testid="prepared-copy">
        {copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy"}
      </Button>
      {doc ? <SendWellsFold doc={doc} /> : null}
    </div>
  );
}

export function PreparedResults({ meetingId, results }: { meetingId: string; results: PreparedResult[] }) {
  const [open, setOpen] = useState<string | null>(null);
  const section = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const onOpen = (event: Event) => {
      const detail = (event as CustomEvent<PreparedOpen>).detail;
      if (!detail || detail.meetingId !== meetingId) return;
      setOpen(detail.kind);
      window.requestAnimationFrame(() => {
        section.current?.querySelector(`[data-testid="meeting-prepared-${detail.kind}"]`)
          ?.scrollIntoView?.({ block: "nearest", behavior: "smooth" });
      });
    };
    window.addEventListener(PREPARED_OPEN, onOpen);
    return () => window.removeEventListener(PREPARED_OPEN, onOpen);
  }, [meetingId]);
  if (!results.length) return null;
  return (
    <div ref={section}>
      <SurfaceSection label="Prepared" count={results.length || null} data-testid="meeting-prepared"
        className="meeting-outcome-section">
        <SurfaceLedger label="Prepared" cols="meeting-outcomes">
          <ul className="surface-ledger-rows">
            {results.map((result) => {
              const ready = result.state === "ready";
              const isOpen = ready && open === result.kind;
              const name = result.title || result.label;
              const failed = result.state === "failed";
              return (
                <SurfaceLedgerRow
                  key={result.kind}
                  data-testid={`meeting-prepared-${result.kind}`}
                  primary={name}
                  meta={result.title && result.title !== result.label ? result.label : undefined}
                  metaTone={failed ? "fail" : undefined}
                  wrap
                  open={ready || failed}
                  onToggle={ready ? () => setOpen(isOpen ? null : result.kind) : undefined}
                  expands={false}
                  lineLabel={ready ? `${isOpen ? "Fold" : "Read"} ${name}` : undefined}
                  trailing={result.state === "writing" ? (
                    <span data-testid="meeting-prepared-writing">
                      <RunLine phase="running" verb="Writing…"
                        startedAt={result.since ? Date.parse(result.since) : undefined} />
                    </span>
                  ) : undefined}
                >
                  {ready ? (
                    <>
                      {isOpen ? (
                        <div className="meeting-prepared-draft" data-testid="meeting-prepared-draft">
                          <AgentWords text={draftText(result)} />
                        </div>
                      ) : null}
                      {/* The verbs sit under the row, full width: the Send
                          well opens here, never in the narrow trailing slot. */}
                      <ResultVerbs meetingId={meetingId} result={result} reading={isOpen}
                        onRead={() => setOpen(isOpen ? null : result.kind)} />
                    </>
                  ) : failed ? (
                    <p className="meeting-prepared-failed" data-testid="meeting-prepared-failed">
                      {result.reason || "This draft did not run."}
                    </p>
                  ) : null}
                </SurfaceLedgerRow>
              );
            })}
          </ul>
        </SurfaceLedger>
      </SurfaceSection>
    </div>
  );
}

/** The action row's verb: "Draft ready ›" opens the Result that serves it. */
export function DraftReady({ meetingId, result }: { meetingId: string; result: PreparedResult }) {
  return (
    <Button dense variant="ghost" data-testid="draft-ready"
      aria-label={`Draft ready: ${result.title || result.label}`}
      onClick={() => openPrepared(meetingId, result.kind)}>
      Draft ready ›
    </Button>
  );
}
