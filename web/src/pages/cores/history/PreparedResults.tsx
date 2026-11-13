import { useEffect, useRef, useState } from "react";
import { InspectorFacts, PaneNotice, ListPane, ListView, PreferencePane, PreferenceWell, ReadingDocument, LiveWell, Elapsed, SurfaceState, type ListVerb } from "../../../desk/surface";
import { SendWells } from "../../../desk/surface/send";
import { artifactDoc } from "../../../desk/documentSends";
import { useWindowBack } from "../../../desk/surface/back";
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
  if (result.document_ref) return { ref: result.document_ref, title, label: result.label };
  return null;
}


export function PreparedResults({ meetingId, results, canPrepare = [], selectionHash, onChanged, initialPicked = null, onPick, noteIds, onSendState }: {
  onSendState?(open: boolean): void;
  initialPicked?: string | null; onPick?(id: string): void; noteIds?: Map<string, string>;
  meetingId: string; results: PreparedResult[]; canPrepare?: PreparableKind[]; selectionHash?: string | null; onChanged?(): void;
}) {
  const [picked, setPicked] = useState<string | null>(initialPicked), [sending, setSending] = useState(false), [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const retry = useRef<(() => Promise<unknown>) | null>(null);
  const pending = useRef(false), localNotes = useRef(new Map<string, string>());
  const notes = noteIds ?? localNotes.current;
  const { copy, state: copyState } = useCopyReceipt();
  const selected = results.find(row => row.kind === picked);
  const doc = selected ? docOf(selected) : null;
  const sendOpen = sending && Boolean(doc);
  const write = async (action: () => Promise<unknown>) => {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError("");
    try { await action(); } catch (cause) { retry.current = action; setError(readableError(cause)); }
    finally { pending.current = false; setBusy(false); }
  };
  const prepare = (pluginId: string) => write(async () => {
    await apiFetch(`/api/meetings/${encodeURIComponent(meetingId)}/prepare`, { method: "POST", json: { plugin_id: pluginId, expected_selection_hash: selectionHash ?? null } });
    onChanged?.();
  });
  const writing = results.some(row => row.state === "writing");
  useEffect(() => { if (!writing || !onChanged) return; const timer = setInterval(onChanged, 4000); return () => clearInterval(timer); }, [writing, onChanged]);
  useEffect(() => {
    const open = (event: Event) => { const target = (event as CustomEvent<PreparedOpen>).detail; if (target?.meetingId === meetingId) setPicked(target.kind); };
    window.addEventListener(PREPARED_OPEN, open); return () => window.removeEventListener(PREPARED_OPEN, open);
  }, [meetingId]);
  useWindowBack(sendOpen ? { onBack: () => setSending(false) } : null, [sendOpen]);
  useEffect(() => { onSendState?.(sendOpen); return () => onSendState?.(false); }, [sendOpen, onSendState]);
  const ready = Boolean(selected?.state === "ready");
  const verbs: ListVerb[] = [
    { id: "open", label: "Read", key: "Enter", enabled: () => ready, run: () => setSending(false) },
    { id: "send", label: "Send…", enabled: () => ready && Boolean(doc), run: () => setSending(true) },
    { id: "note", label: "Open as note", enabled: () => ready && !busy, run: () => { if (!selected) return; void write(async () => {
      const saved = notes.get(selected.kind);
      if (saved) { openRef(`note:${saved}`); return; }
      const made = await apiFetch<{ note?: { id?: string } }>("/api/notes", { method: "POST", json: { title: selected.title || selected.label, body_markdown: draftText(selected), tags: ["meeting", `meeting:${meetingId}`] } });
      if (!made.note?.id) throw new Error("Note not made");
      notes.set(selected.kind, made.note.id); openRef(`note:${made.note.id}`);
    }); } },
    { id: "copy", label: copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy", enabled: () => ready, run: () => { if (selected) void copy(draftText(selected)); } },
    { id: "retry", label: "Write again", enabled: () => Boolean(selected?.state === "failed" && selected.retry && selected.plugin_id) && !busy, run: () => { if (selected?.plugin_id) void prepare(selected.plugin_id); } },
    ...(canPrepare.length ? [{ id: "prepare", label: "Prepare", enabled: () => !busy && !writing, run: () => undefined,
      items: canPrepare.map(kind => ({ id: `prepare-${kind.plugin_id}`, label: `Prepare ${kind.label}`, enabled: () => !busy && !writing, run: () => void prepare(kind.plugin_id) })),
    }] : []),
  ];
  return <PreferencePane label="Prepared results" testId="meeting-prepared" data-feedback-redact="true">
    <ListPane label="Prepared result" notice={error ? <SurfaceState error={error} onRetry={() => { if (retry.current) void write(retry.current); }} />
      : selected?.state === "failed" ? <SurfaceState error={selected.reason || "This draft did not run."} onRetry={selected.retry && selected.plugin_id ? () => void prepare(selected.plugin_id!) : undefined} /> : undefined}
      list={<ListView label="Prepared results" ordered rows={results.map(result => ({ id: result.kind, name: result.title || result.label, kind: "artifact", state: result.state === "failed" ? { label: "Failed", tone: "fail" as const } : result.state === "writing" ? { label: "Writing", tone: "info" as const } : undefined }))}
      columns={[{ key: "name", word: "Result", track: "minmax(0,1fr)", priority: 100 }, { key: "state", word: "State", track: "120px", priority: 20 }]} selectedId={picked} onSelect={id => { setPicked(id); onPick?.(id); setSending(false); }} defaultVerb="open" verbs={verbs.filter(verb => verb.id === "open" || verb.enabled?.(null))} rowProps={row => ({ "data-testid": `meeting-prepared-${row.id}` })} />}>
      {sending && doc ? <SendWells doc={doc} onBack={() => setSending(false)} />
        : selected && (selected.state !== "failed" || selected.title && selected.title !== selected.label) ? <PreferenceWell>
        {selected.title && selected.title !== selected.label ? <InspectorFacts header={false} name={selected.title} rows={[{ label: "Kind", value: selected.label }]} /> : null}
        {selected.state !== "failed" ? <PaneNotice>{selected.state === "writing" ? <><Elapsed start={selected.since || ""} /><LiveWell label="Prepared draft" working lines={[{ id: selected.kind, text: "Writing draft" }]} /></>
          : <ReadingDocument data-testid="meeting-prepared-draft">{draftText(selected)}</ReadingDocument>}</PaneNotice> : null}
      </PreferenceWell> : !results.length ? <PaneNotice>No prepared results</PaneNotice> : null}
    </ListPane>
  </PreferencePane>;
}
