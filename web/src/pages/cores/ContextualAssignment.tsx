import { useCallback, useEffect, useMemo, useState } from "react";
import { readableError } from "../../lib/api";
import { openSurfaceOr } from "../../desk/shell";
import { onReturnToTask } from "../../desk/returnToTask";
import { AssignmentSummary } from "./AssignmentSummary";
import {
  getAssignmentEditor,
  type AssignmentEditorProjection,
  type AssignmentScope,
} from "./assignmentExperience";

function namedChain(editor: AssignmentEditorProjection): string {
  const entries = editor.effective?.assignment?.entries ?? [];
  const chain = entries.length ? entries.map((entry) => entry.label).join(" → ") : "No default model";
  const source = editor.effective?.inherited_from;
  return source ? `Uses ${source} · ${chain}` : chain;
}

function isProjection(editor: AssignmentEditorProjection | null): editor is AssignmentEditorProjection {
  return Boolean(editor?.effective && editor?.selected_capability && editor?.scope);
}

/**
 * The contextual assignment atom for an open owner object: a READ of what
 * this object runs on, from the canonical assignment service.
 *
 * PHILO-16 (C), ruling 2026-10-09: its Change opens Runs on with this
 * object's job selected (hot wires). The AssignmentEditor sheet it used to
 * open is parked; a per-object wire on the board is backlog.
 */
export function ContextualAssignment({
  label,
  capabilityId,
  scope,
}: {
  label: string;
  capabilityId: string;
  scope: AssignmentScope;
  /** Kept for callers; Runs on announces its own changes. */
  onChanged?: () => void;
}) {
  const scopeKey = JSON.stringify(scope);
  const stableScope = useMemo(() => scope, [scopeKey]);
  const [editor, setEditor] = useState<AssignmentEditorProjection | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const next = await getAssignmentEditor(stableScope, capabilityId);
      setEditor(next);
      setError("");
    } catch (reason) {
      setError(readableError(reason));
    }
  }, [capabilityId, stableScope]);

  useEffect(() => { void refresh(); }, [refresh]);
  // Runs on announces a patch with the readiness signal; read again on it.
  useEffect(() => onReturnToTask(() => void refresh()), [refresh]);

  const change = () => {
    // The job is the capability's group; Runs on resolves it from the id.
    openSurfaceOr("open-concierge", "/models", capabilityId);
  };

  const projection = isProjection(editor) ? editor : null;

  return <div className="contextual-assignment" data-capability={capabilityId}>
    {projection ? <AssignmentSummary
      label={label}
      effective={namedChain(projection)}
      repair={projection.effective.repair}
      onChange={change}
    /> : error ? <p className="contextual-assignment-error" role="status">{error}</p> : editor ? <p className="contextual-assignment-error" role="status">Assignment unavailable</p> : <p className="contextual-assignment-loading">Loading assignment</p>}
  </div>;
}
