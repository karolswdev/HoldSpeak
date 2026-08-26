import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, readableError } from "../../lib/api";
import { EgressChip, FoldGadget } from "../../desk/surface/gadgets";
import { SurfaceState } from "../../desk/surface/Surface";
import {
  clearAssignmentDefault,
  previewAssignmentDefault,
  saveAssignment,
  type AssignmentCandidate,
  type AssignmentEditorProjection,
  type AssignmentEntry,
  type AssignmentProjection,
  type AssignmentUseDefaultPreview,
} from "./assignmentExperience";
import { AssignmentModelChooser } from "./AssignmentModelChooser";

type DraftEntry = AssignmentEntry & { status?: AssignmentCandidate["status"] };

function chain(entries: AssignmentEntry[] | undefined): string {
  if (!entries?.length) return "No default model";
  return entries.map((entry) => entry.label).join(" → ");
}

function isCloud(entry: Pick<AssignmentEntry, "boundary">): boolean {
  return entry.boundary === "cloud";
}

function draftFrom(editor: AssignmentEditorProjection): DraftEntry[] {
  const byProfile = new Map(editor.candidates.map((candidate) => [candidate.profile_id, candidate]));
  return (editor.configured_assignment?.entries ?? []).map((entry) => ({
    ...entry,
    status: byProfile.get(entry.profile_id)?.status,
  }));
}

function previewChain(preview: AssignmentUseDefaultPreview): AssignmentProjection | null {
  return preview.effective.assignment;
}

/** One in-world, atomic assignment editor shared by Settings and future subject surfaces. */
export function AssignmentEditor({
  title,
  editor,
  returnFocus,
  onClose,
  onRefresh,
  onSaved,
}: {
  title: string;
  editor: AssignmentEditorProjection;
  returnFocus: HTMLElement | null;
  onClose: () => void;
  onRefresh: () => Promise<void>;
  onSaved: (receipt: string) => Promise<void>;
}) {
  const sheet = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const [draft, setDraft] = useState<DraftEntry[]>(() => draftFrom(editor));
  const [preview, setPreview] = useState<AssignmentUseDefaultPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const scope = editor.scope;
  const draftIds = useMemo(() => new Set(draft.map((entry) => entry.profile_id)), [draft]);

  useEffect(() => {
    closeButton.current?.focus();
    return () => { returnFocus?.focus(); };
  }, [returnFocus]);

  const resetProblem = () => { setError(""); setConflict(false); };
  const choose = (candidate: AssignmentCandidate) => {
    resetProblem();
    setDraft((current) => {
      const existing = current.findIndex((entry) => entry.profile_id === candidate.profile_id);
      if (existing >= 0) {
        setAnnouncement(`${candidate.label} removed from the draft.`);
        return current.filter((entry) => entry.profile_id !== candidate.profile_id);
      }
      if (current.length === 4) {
        setAnnouncement("A chain can contain up to four models.");
        return current;
      }
      setAnnouncement(`${candidate.label} added at position ${current.length + 1}.`);
      return [...current, { ...candidate, ordinal: current.length + 1 }];
    });
  };
  const remove = (index: number) => {
    const removed = draft[index];
    resetProblem();
    setDraft((current) => current.filter((_, entryIndex) => entryIndex !== index));
    setAnnouncement(`${removed.label} removed from the draft.`);
  };
  const move = (from: number, to: number) => {
    if (to < 0 || to >= draft.length || from === to) return;
    resetProblem();
    setDraft((current) => {
      const next = [...current];
      const [entry] = next.splice(from, 1);
      next.splice(to, 0, entry);
      return next.map((value, ordinal) => ({ ...value, ordinal: ordinal + 1 }));
    });
    setAnnouncement(`${draft[from].label} is now position ${to + 1}.`);
  };
  const save = async () => {
    if (!draft.length) { setError("Choose a model chain."); return; }
    setBusy(true); resetProblem();
    try {
      await saveAssignment(
        scope,
        editor.draft_base_revision,
        draft.map(({ profile_id, profile_revision }) => ({ profile_id, profile_revision })),
        editor.configured_assignment?.retry_policy_id ?? null,
      );
      await onSaved(`Assignment changed to ${chain(draft)}. Next run.`);
    } catch (reason) {
      setConflict(reason instanceof ApiError && reason.status === 409);
      setError(readableError(reason));
    } finally { setBusy(false); }
  };
  const showDefault = async () => {
    setBusy(true); resetProblem();
    try {
      setPreview(await previewAssignmentDefault(scope, editor.selected_capability.id));
    } catch (reason) {
      setConflict(reason instanceof ApiError && reason.status === 409);
      setError(readableError(reason));
    } finally { setBusy(false); }
  };
  const clear = async () => {
    if (!preview) return;
    setBusy(true); resetProblem();
    try {
      await clearAssignmentDefault(scope, editor.selected_capability.id, preview.expected_revision);
      await onSaved(`Using ${chain(previewChain(preview)?.entries)}. Next run.`);
    } catch (reason) {
      // A clear conflict means the preview no longer names the head being
      // cleared. Discard it rather than comparing browser-owned snapshots.
      setPreview(null);
      setConflict(reason instanceof ApiError && reason.status === 409);
      setError(readableError(reason));
    } finally { setBusy(false); }
  };
  const refresh = async () => {
    setBusy(true); setPreview(null); resetProblem();
    try { await onRefresh(); } catch (reason) { setError(readableError(reason)); } finally { setBusy(false); }
  };
  const onSheetKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Escape") { event.preventDefault(); onClose(); return; }
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      if (!busy) void save();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = Array.from(sheet.current?.querySelectorAll<HTMLElement>(
      "button:not([disabled]), [href], [tabindex]:not([tabindex='-1'])",
    ) ?? []).filter((element) => !element.hasAttribute("disabled"));
    if (!focusable.length) return;
    const current = document.activeElement as HTMLElement;
    const index = focusable.indexOf(current);
    if ((!event.shiftKey && index === focusable.length - 1) || (event.shiftKey && index <= 0)) {
      event.preventDefault();
      (event.shiftKey ? focusable.at(-1) : focusable[0])?.focus();
    }
  };

  const projectedDefault = preview ? previewChain(preview) : editor.effective.assignment;
  return <section
    ref={sheet}
    className="assignment-sheet"
    aria-label={`${title} assignment`}
    onKeyDown={onSheetKeyDown}
  >
    <header className="assignment-sheet-head"><div><span>Assignments</span><h2>{title}</h2></div><button ref={closeButton} type="button" onClick={onClose}>Close</button></header>
    <div className="assignment-sheet-body">
      {error ? <div className="assignment-sheet-error"><SurfaceState error={error} />{conflict ? <button type="button" onClick={() => void refresh()} disabled={busy}>Refresh</button> : null}</div> : null}
      <section className="assignment-default" aria-label="Use default">
        <div><strong>Use default</strong><span>{chain(projectedDefault?.entries)}</span></div>
        {preview ? <button type="button" disabled={busy} onClick={() => void clear()}>Use default</button> : <button type="button" disabled={busy || !editor.configured_assignment} onClick={() => void showDefault()}>Preview</button>}
        {preview ? <div className="assignment-default-preview" role="status">
          <strong>Will use {chain(projectedDefault?.entries)}</strong>
          <span>Retry follows the server policy for {editor.selected_capability.label}.</span>
          {projectedDefault?.entries.map((entry, index) => isCloud(entry) ? <span className="assignment-boundary" key={entry.profile_id}><EgressChip label="Egress" scope="cloud" title="This fallback can leave this device." /> Fallback {index + 1} can leave this device.</span> : null)}
        </div> : null}
      </section>
      <section className="assignment-draft" aria-label="Custom assignment">
        <header><h3>Custom</h3><span>{draft.length}/4</span></header>
        {draft.length ? <ol className="assignment-draft-list">{draft.map((entry, index) => <li
          key={`${entry.profile_id}:${entry.profile_revision}`}
          draggable
          onDragStart={(event) => event.dataTransfer.setData("text/plain", String(index))}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => { event.preventDefault(); move(Number(event.dataTransfer.getData("text/plain")), index); }}
        >
          <span className="assignment-ordinal" aria-hidden="true">{index + 1}</span>
          <span className="assignment-leg-name"><strong>{entry.label}</strong><small>{entry.readiness}</small></span>
          {isCloud(entry) ? <EgressChip label="Egress" scope="cloud" title="This fallback can leave this device." /> : null}
          {entry.readiness !== "ready" ? <button type="button" className="assignment-leg-repair" onClick={() => sheet.current?.querySelector<HTMLElement>(".assignment-candidates button")?.focus()}>Replace unavailable model</button> : null}
          <div className="assignment-leg-actions">
            <button type="button" aria-label={`Move ${entry.label} up`} disabled={index === 0} onClick={() => move(index, index - 1)}>Move up</button>
            <button type="button" aria-label={`Move ${entry.label} down`} disabled={index === draft.length - 1} onClick={() => move(index, index + 1)}>Move down</button>
            <button type="button" aria-label={`Remove ${entry.label}`} onClick={() => remove(index)}>Remove</button>
          </div>
        </li>)}</ol> : <p>No custom chain</p>}
        <span className="assignment-section-label">Add fallback</span>
        <AssignmentModelChooser candidates={editor.candidates} draftProfileIds={draftIds} onChoose={choose} />
      </section>
      <div className="assignment-live" aria-live="polite">{announcement}</div>
      <FoldGadget title="RAW" token="Details"><span>Policy {editor.retry_policy.default_id}</span></FoldGadget>
    </div>
    <footer className="assignment-sheet-footer"><button type="button" onClick={onClose}>Cancel</button><Button variant="primary" loading={busy} disabled={busy || !draft.length} onClick={() => void save()}>Save assignment</Button></footer>
  </section>;
}
