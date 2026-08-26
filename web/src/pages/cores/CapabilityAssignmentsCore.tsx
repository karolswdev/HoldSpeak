import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { readableError } from "../../lib/api";
import { EgressChip, FoldGadget } from "../../desk/surface/gadgets";
import { SurfaceState, SurfaceVerbs } from "../../desk/surface/Surface";
import {
  clearAssignmentDefault,
  getAssignmentEditor,
  getAssignmentSummary,
  previewAssignmentDefault,
  saveAssignment,
  type AssignmentCandidate,
  type AssignmentEditorProjection,
  type AssignmentProjection,
  type AssignmentScope,
  type AssignmentSummary,
  type AssignmentSummaryRow,
} from "./assignmentExperience";

function chain(entries: AssignmentProjection["entries"] | undefined): string {
  if (!entries?.length) return "No default model";
  const names = entries.slice(0, 2).map((entry) => entry.label);
  return `${names.join(" → ")}${entries.length > 2 ? ` +${entries.length - 2}` : ""}`;
}

function effectiveCopy(row: AssignmentSummaryRow): string {
  if (!row.assignment) return "No default model";
  const prefix = row.inherited_from === "global" ? "Uses default · " : "";
  return `${prefix}${chain(row.assignment.entries)}`;
}

function scopeFor(row: AssignmentSummaryRow): AssignmentScope {
  return row.id === "global" ? { kind: "global" } : { kind: "group", group_id: row.id };
}

function isCloud(candidate: Pick<AssignmentCandidate, "boundary">): boolean {
  return candidate.boundary === "cloud";
}

function AssignmentShell({
  row,
  editor,
  onClose,
  onSaved,
}: {
  row: AssignmentSummaryRow;
  editor: AssignmentEditorProjection;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [draft, setDraft] = useState<AssignmentCandidate[]>(() => {
    const saved = editor.configured_assignment?.entries ?? [];
    return saved.map((entry) => ({
      profile_id: entry.profile_id, profile_revision: entry.profile_revision,
      label: entry.label, boundary: entry.boundary, readiness: entry.readiness,
      status: "compatible", issues: [],
    }));
  });
  const [preview, setPreview] = useState<AssignmentProjection | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const scope = editor.scope;

  const choose = (candidate: AssignmentCandidate) => {
    setDraft((current) => current.some((entry) => entry.profile_id === candidate.profile_id)
      ? current.filter((entry) => entry.profile_id !== candidate.profile_id)
      : [...current, candidate].slice(0, 4));
  };
  const save = async () => {
    if (!draft.length) { setError("Choose a model chain."); return; }
    setBusy(true); setError("");
    try {
      await saveAssignment(scope, editor.draft_base_revision, draft, editor.configured_assignment?.retry_policy_id ?? null);
      await onSaved();
    } catch (reason) { setError(readableError(reason)); } finally { setBusy(false); }
  };
  const showDefault = async () => {
    setBusy(true); setError("");
    try {
      const value = await previewAssignmentDefault(scope, editor.selected_capability.id);
      setPreview(value.effective.assignment);
    } catch (reason) { setError(readableError(reason)); } finally { setBusy(false); }
  };
  const clear = async () => {
    setBusy(true); setError("");
    try {
      await clearAssignmentDefault(scope, editor.selected_capability.id, editor.draft_base_revision);
      await onSaved();
    } catch (reason) { setPreview(null); setError(readableError(reason)); } finally { setBusy(false); }
  };

  return <section className="assignment-sheet" aria-label={`${row.label} assignment`}>
    <header className="assignment-sheet-head"><div><span>Assignments</span><h2>{row.label}</h2></div><button type="button" onClick={onClose}>Close</button></header>
    {error ? <SurfaceState error={error} /> : null}
    <div className="assignment-default">
      <strong>Use default</strong><span>{preview ? chain(preview.entries) : chain(editor.effective.assignment?.entries)}</span>
      {preview ? <button type="button" disabled={busy} onClick={() => void clear()}>Use default</button> : <button type="button" disabled={busy || !editor.configured_assignment} onClick={() => void showDefault()}>Preview</button>}
    </div>
    <section className="assignment-draft" aria-label="Custom assignment">
      <h3>Custom</h3>
      {draft.length ? <ol>{draft.map((entry) => <li key={entry.profile_id}>{entry.label}<small>{entry.readiness}</small>{isCloud(entry) ? <EgressChip label="Egress" scope="cloud" title="This fallback can leave this device." /> : null}</li>)}</ol> : <p>No custom chain</p>}
      <div className="assignment-candidates" role="radiogroup" aria-label="Compatible models">
        {editor.candidates.map((candidate) => {
          const picked = draft.some((entry) => entry.profile_id === candidate.profile_id);
          return <button type="button" role="radio" aria-checked={picked} data-selected={picked || undefined} key={candidate.profile_id} onClick={() => choose(candidate)}>
            <span><strong>{candidate.label}</strong><small>{candidate.readiness}</small></span>
            {isCloud(candidate) ? <EgressChip label="Egress" scope="cloud" title="This model can leave this device." /> : null}
          </button>;
        })}
      </div>
    </section>
    <FoldGadget title="RAW" token="Details"><span>Policy {editor.retry_policy.default_id}</span></FoldGadget>
    <footer className="assignment-sheet-footer"><button type="button" onClick={onClose}>Cancel</button><Button variant="primary" loading={busy} disabled={busy || !draft.length} onClick={() => void save()}>Save assignment</Button></footer>
  </section>;
}

/** Bounded owner settings glass; all assignment and candidate truth is server-projected. */
export function CapabilityAssignmentsCore() {
  const [summary, setSummary] = useState<AssignmentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [selected, setSelected] = useState<AssignmentSummaryRow | null>(null);
  const [editor, setEditor] = useState<AssignmentEditorProjection | null>(null);
  const [editorError, setEditorError] = useState("");
  const [showOverrides, setShowOverrides] = useState(false);
  const [allTasks, setAllTasks] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true); setLoadError("");
    try { setSummary(await getAssignmentSummary()); } catch (reason) { setLoadError(readableError(reason)); } finally { setLoading(false); }
  }, []);
  useEffect(() => { void reload(); }, [reload]);

  const rows = useMemo(() => [...(summary?.rows ?? [])].sort((left, right) => Number(Boolean(right.repair)) - Number(Boolean(left.repair))), [summary]);
  const open = async (row: AssignmentSummaryRow) => {
    if (!row.editor_capability_id) return;
    setSelected(row); setEditor(null); setEditorError("");
    try { setEditor(await getAssignmentEditor(scopeFor(row), row.editor_capability_id)); } catch (reason) { setEditorError(readableError(reason)); }
  };
  const saved = async () => { setEditor(null); setSelected(null); await reload(); };
  const taskRows = (summary?.task_overrides ?? []).filter((row) => allTasks || row.has_override || row.issues.length > 0);

  if (loading) return <SurfaceState loading />;
  if (loadError) return <SurfaceState error={loadError} onRetry={() => void reload()} />;
  if (selected && editor) return <AssignmentShell row={selected} editor={editor} onClose={() => { setSelected(null); setEditor(null); }} onSaved={saved} />;
  if (selected && editorError) return <SurfaceState error={editorError} onRetry={() => void open(selected)} />;

  return <section className="capability-assignments" aria-labelledby="assignments-title">
    <SurfaceVerbs status={summary?.issue_count ? <span role="status">{summary.issue_count} issue{summary.issue_count === 1 ? "" : "s"}</span> : null} />
    <header className="capability-assignments-head"><h2 id="assignments-title">Assignments</h2><span>Next run</span></header>
    <div className="capability-assignment-rows">
      {rows.map((row) => <article className="capability-assignment-row" key={row.id} data-issue={row.repair ? "true" : undefined}>
        <div><strong>{row.label}</strong><span>{effectiveCopy(row)}</span></div>
        <div>{row.repair ? <span className="assignment-repair">{row.repair}</span> : null}<button type="button" onClick={() => void open(row)}>{row.repair === "Fix" ? "Fix" : "Change"}</button></div>
      </article>)}
    </div>
    <details className="assignment-overrides" open={showOverrides} onToggle={(event) => setShowOverrides((event.currentTarget as HTMLDetailsElement).open)}>
      <summary>Show task overrides</summary>
      <div className="assignment-override-filter"><button type="button" aria-pressed={!allTasks} onClick={() => setAllTasks(false)}>Overrides & issues</button><button type="button" aria-pressed={allTasks} onClick={() => setAllTasks(true)}>All tasks</button></div>
      {taskRows.length ? <div className="assignment-task-rows">{taskRows.map((task) => <article key={task.id}><span>{task.group.label}</span><strong>{task.label}</strong><small>{task.effective.assignment ? chain(task.effective.assignment.entries) : "No default model"}</small></article>)}</div> : <SurfaceState empty emptyContent={<span>No task overrides</span>} />}
    </details>
  </section>;
}
