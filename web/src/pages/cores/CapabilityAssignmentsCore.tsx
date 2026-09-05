import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { SurfaceState, SurfaceVerbs } from "../../desk/surface/Surface";
import { countLabel } from "../../desk/surface";
import { readableError } from "../../lib/api";
import { AssignmentEditor } from "./AssignmentEditor";
import { AssignmentSummary } from "./AssignmentSummary";
import {
  getAssignmentEditor,
  getAssignmentSummary,
  type AssignmentProjection,
  type AssignmentScope,
  type AssignmentSummary as AssignmentSummaryProjection,
  type AssignmentSummaryRow,
} from "./assignmentExperience";

type AssignmentTaskOverride = AssignmentSummaryProjection["task_overrides"][number];

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

/** Bounded owner Settings glass; server owns assignment, compatibility, and inheritance truth. */
export function CapabilityAssignmentsCore() {
  const [summary, setSummary] = useState<AssignmentSummaryProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [selected, setSelected] = useState<AssignmentSummaryRow | null>(null);
  const [editor, setEditor] = useState<Awaited<ReturnType<typeof getAssignmentEditor>> | null>(null);
  const [editorError, setEditorError] = useState("");
  const [showOverrides, setShowOverrides] = useState(false);
  const [allTasks, setAllTasks] = useState(false);
  const [receipt, setReceipt] = useState("");
  const openingFocus = useRef<HTMLElement | null>(null);

  const reload = useCallback(async () => {
    setLoading(true); setLoadError("");
    try { setSummary(await getAssignmentSummary()); } catch (reason) { setLoadError(readableError(reason)); } finally { setLoading(false); }
  }, []);
  useEffect(() => { void reload(); }, [reload]);

  const rows = useMemo(
    () => [...(summary?.rows ?? [])].sort((left, right) => Number(Boolean(right.repair)) - Number(Boolean(left.repair))),
    [summary],
  );
  const open = async (row: AssignmentSummaryRow, opener?: HTMLElement) => {
    if (!row.editor_capability_id) return;
    if (opener) openingFocus.current = opener;
    setReceipt(""); setSelected(row); setEditor(null); setEditorError("");
    try { setEditor(await getAssignmentEditor(scopeFor(row), row.editor_capability_id)); } catch (reason) { setEditorError(readableError(reason)); }
  };
  const close = () => { setSelected(null); setEditor(null); setEditorError(""); };
  const saved = async (nextReceipt: string) => {
    close(); setReceipt(nextReceipt); await reload();
  };
  const taskRows: AssignmentTaskOverride[] = (summary?.task_overrides ?? []).filter(
    (row: AssignmentTaskOverride) => allTasks || row.has_override || row.issues.length > 0,
  );

  if (loading) return <SurfaceState loading />;
  if (loadError) return <SurfaceState error={loadError} onRetry={() => void reload()} />;
  // This is a server-summary readiness fact, not a browser-derived route state.
  // Real-hub consumers may wait for it before measuring the bounded row roster.
  return <section className="capability-assignments" aria-labelledby="assignments-title" data-assignment-summary-state="loaded" data-editor-open={selected && editor ? "true" : undefined}>
    <SurfaceVerbs status={summary?.issue_count ? <span role="status">{countLabel("ISSUES", summary.issue_count)}</span> : null} />
    <header className="capability-assignments-head"><h2 id="assignments-title">Assignments</h2><span>Next run</span></header>
    {receipt ? <div className="assignment-receipt" role="status">{receipt}</div> : null}
    <div className="assignment-editor-layout">
      <div className="assignment-overview">
        <div className="capability-assignment-rows">
          {rows.map((row: AssignmentSummaryRow) => <AssignmentSummary
            key={row.id}
            label={row.label}
            effective={effectiveCopy(row)}
            repair={row.repair}
            onChange={(opener) => void open(row, opener)}
          />)}
        </div>
        <details className="assignment-overrides" open={showOverrides} onToggle={(event) => setShowOverrides((event.currentTarget as HTMLDetailsElement).open)}>
          <summary>Show task overrides</summary>
          <div className="assignment-override-filter"><Button dense variant={!allTasks ? "primary" : "ghost"} aria-pressed={!allTasks} onClick={() => setAllTasks(false)}>Overrides & issues</Button><Button dense variant={allTasks ? "primary" : "ghost"} aria-pressed={allTasks} onClick={() => setAllTasks(true)}>All tasks</Button></div>
          {taskRows.length ? <div className="assignment-task-rows">{taskRows.map((task: AssignmentTaskOverride) => <article key={task.id}><span>{task.group.label}</span><strong>{task.label}</strong><span className="surface-token">{task.effective.assignment ? chain(task.effective.assignment.entries) : "No default model"}</span></article>)}</div> : <SurfaceState empty emptyContent={<span>No task overrides</span>} />}
        </details>
      </div>
      {selected && editor ? <AssignmentEditor
        title={selected.label}
        editor={editor}
        returnFocus={openingFocus.current}
        onClose={close}
        onRefresh={() => open(selected)}
        onSaved={saved}
      /> : null}
      {selected && editorError ? <SurfaceState error={editorError} onRetry={() => void open(selected)} /> : null}
    </div>
  </section>;
}
