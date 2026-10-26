// betterment/capture C5, C5b — the Results the meeting prepared.
// Under Outcomes: "Prepared · N", one line per Result (the follow-up, then
// each draft the meeting asked for or he asked for: an ADR, an update for
// stakeholders, a diagram …). A line is its title and its kind, its verbs on
// the right: Send (the lead verb; the shared Send well opens under the line,
// nothing leaves without his press), Open as note, Copy. A press on the title
// reads the draft. A draft being written says "Writing… N s" in place; a
// failed one says why, with Write again. Prepare… writes one more kind.
// The hub's read: GET /api/meetings/<id>/prepared; the press:
// POST /api/meetings/<id>/prepare (a drafts-only job; never the summary).
import { useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection } from "../../../desk/surface";
import { RunLine } from "../../../desk/surface/RunLine";
import { SendWells } from "../../../desk/surface/send";
import { artifactDoc } from "../../../desk/documentSends";
import { AgentWords } from "../../../desk/components/AgentWords";
import { WorkMenu } from "../../../desk/components/DeskMenu";
import { useCopyReceipt } from "../../../desk/hooks/useCopyReceipt";
import { openRef } from "../../../desk/openObject";
import { apiFetch, readableError } from "../../../lib/api";

export type PreparedResult = {
  kind: string;
  label: string;
  plugin_id?: string;
  state: "ready" | "writing" | "failed";
  title?: string;
  body_markdown?: string;
  artifact_id?: string;
  document_ref?: string;
  seconds?: number | null;
  since?: string;
  reason?: string;
  retry?: boolean;
  serves?: string[];
};
export type PreparableKind = { plugin_id: string; kind: string; label: string };

/** The press on an action's "Draft ready": open that Result's row. */
export const PREPARED_OPEN = "holdspeak:meeting-prepared-open";
export type PreparedOpen = { meetingId: string; kind: string };

export function readPrepared(body: unknown): PreparedResult[] {
  const results = (body as { results?: unknown } | null)?.results;
  return Array.isArray(results) ? (results as PreparedResult[]).filter((r) => r && typeof r.kind === "string") : [];
}

export function readCanPrepare(body: unknown): PreparableKind[] {
  const kinds = (body as { can_prepare?: unknown } | null)?.can_prepare;
  return Array.isArray(kinds) ? (kinds as PreparableKind[]).filter((k) => k && typeof k.plugin_id === "string") : [];
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

function docOf(result: PreparedResult) {
  const title = String(result.title || result.label);
  if (result.artifact_id) return artifactDoc(result.artifact_id, title, result.kind);
  if (result.document_ref) return { ref: result.document_ref, title, label: result.label.toUpperCase() };
  return null;
}

function ResultVerbs({ meetingId, result, sending, onSend }: {
  meetingId: string; result: PreparedResult; sending: boolean; onSend(): void;
}) {
  const { copy, state: copyState } = useCopyReceipt();
  const sendRef = useRef<HTMLButtonElement>(null);
  const wasSending = useRef(sending);
  const [noting, setNoting] = useState(false);
  const [noteFailed, setNoteFailed] = useState(false);
  const noteId = useRef<string | null>(null);
  const text = draftText(result);
  const title = String(result.title || result.label);
  useEffect(() => {
    const returning = wasSending.current && !sending;
    wasSending.current = sending;
    if (!returning) return;
    const frame = window.requestAnimationFrame(() => sendRef.current?.focus());
    return () => window.cancelAnimationFrame(frame);
  }, [sending]);
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
    <span className="meeting-prepared-verbs">
      {docOf(result) ? (
        <Button ref={sendRef} dense variant="secondary" aria-expanded={sending} onClick={onSend} data-testid="prepared-send">
          {sending ? "Hide" : "Send…"}
        </Button>
      ) : null}
      <Button dense variant="ghost" loading={noting} onClick={() => void openAsNote()}
        data-testid="prepared-open-note">
        {noteFailed ? "Note not made · Try again" : "Open as note"}
      </Button>
      <Button dense variant="ghost" onClick={() => void copy(text)} data-testid="prepared-copy">
        {copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy"}
      </Button>
    </span>
  );
}

export function PreparedResults({ meetingId, results, canPrepare = [], selectionHash, onChanged }: {
  meetingId: string;
  results: PreparedResult[];
  /** The kinds Prepare… offers (the hub's `can_prepare`). */
  canPrepare?: PreparableKind[];
  /** The Meeting summaries route he was shown (planned_route.selection_hash). */
  selectionHash?: string | null;
  /** Read the Prepared rows again (after a press, and while one is written). */
  onChanged?: () => void;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const [sending, setSending] = useState<string | null>(null);
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);
  const [asking, setAsking] = useState<string | null>(null);
  const [refusal, setRefusal] = useState("");
  const section = useRef<HTMLDivElement>(null);
  const prepareRef = useRef<HTMLButtonElement>(null);
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
  // While a draft is written, read again every few seconds.
  const writing = results.some((r) => r.state === "writing");
  useEffect(() => {
    if (!writing || !onChanged) return;
    const timer = window.setInterval(onChanged, 4000);
    return () => window.clearInterval(timer);
  }, [writing, onChanged]);
  const prepare = async (pluginId: string) => {
    setAsking(pluginId);
    setRefusal("");
    try {
      await apiFetch(`/api/meetings/${encodeURIComponent(meetingId)}/prepare`, {
        method: "POST", json: { plugin_id: pluginId, expected_selection_hash: selectionHash ?? null },
      });
      onChanged?.();
    } catch (cause) {
      setRefusal(readableError(cause) || "The draft did not start. Nothing was written.");
    } finally {
      setAsking(null);
    }
  };
  if (!results.length && !canPrepare.length) return null;
  const controls = canPrepare.length ? (
    <>
      <Button ref={prepareRef} dense variant="ghost" aria-haspopup="menu" aria-expanded={Boolean(menu)}
        loading={Boolean(asking)} disabled={writing} data-testid="prepared-prepare"
        onClick={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          setMenu(menu ? null : { x: rect.left, y: rect.bottom });
        }}>
        Prepare…
      </Button>
      {menu ? (
        <WorkMenu label="Prepare one more" x={menu.x} y={menu.y} autoFocus
          entries={canPrepare.map((kind) => ({
            type: "item" as const, id: `prepare-${kind.plugin_id}`, label: kind.label,
            onSelect: () => void prepare(kind.plugin_id),
          }))}
          returnFocus={() => prepareRef.current?.focus()}
          onClose={() => setMenu(null)} />
      ) : null}
    </>
  ) : null;
  return (
    <div ref={section}>
      {/* 2026-10-25 audit: Prepare… sits at the right of the caption (its
          actions slot), not alone in a blank band above the rows. */}
      <SurfaceSection label="Prepared" count={results.length || null} data-testid="meeting-prepared"
        className="meeting-outcome-section meeting-prepared-section" actions={controls}>
        <SurfaceLedger label="Prepared" cols="meeting-outcomes">
          {refusal ? <p className="meeting-prepared-failed" role="alert">{refusal}</p> : null}
          <ul className="surface-ledger-rows">
            {results.map((result) => {
              const ready = result.state === "ready";
              const failed = result.state === "failed";
              const reading = ready && open === result.kind;
              const isSending = ready && sending === result.kind;
              const name = result.title || result.label;
              const doc = docOf(result);
              const trailing = ready ? (
                <ResultVerbs meetingId={meetingId} result={result} sending={isSending}
                  onSend={() => setSending(isSending ? null : result.kind)} />
              ) : result.state === "writing" ? (
                <span data-testid="meeting-prepared-writing">
                  <RunLine phase="running" verb="Writing…"
                    startedAt={result.since ? Date.parse(result.since) : undefined} />
                </span>
              ) : failed && result.retry && result.plugin_id ? (
                <Button dense variant="secondary" loading={asking === result.plugin_id}
                  data-testid="prepared-write-again" onClick={() => void prepare(result.plugin_id!)}>
                  Write again
                </Button>
              ) : undefined;
              return (
                <SurfaceLedgerRow
                  key={result.kind}
                  data-testid={`meeting-prepared-${result.kind}`}
                  primary={name}
                  meta={result.title && result.title !== result.label ? result.label : undefined}
                  metaTone={failed ? "fail" : undefined}
                  wrap
                  open={reading || isSending || failed}
                  onToggle={ready ? () => setOpen(reading ? null : result.kind) : undefined}
                  expands={ready}
                  lineLabel={ready ? `${reading ? "Fold" : "Read"} ${name}` : undefined}
                  trailing={trailing}
                >
                  {reading ? (
                    <div className="meeting-prepared-draft" data-testid="meeting-prepared-draft">
                      <AgentWords text={draftText(result)} />
                    </div>
                  ) : null}
                  {isSending && doc ? (
                    <div className="meeting-prepared-send" data-testid="meeting-prepared-send">
                      <SendWells doc={doc} onBack={() => setSending(null)} />
                    </div>
                  ) : null}
                  {failed ? (
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
