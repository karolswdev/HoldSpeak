import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { readableError } from "../../lib/api";
import { AssignmentEditor } from "./AssignmentEditor";
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
 * The contextual assignment atom for an open owner object. It reads and writes
 * only the canonical assignment service through the shared editor; a feature
 * never receives a raw inference-target selector or a parallel writer.
 */
export function ContextualAssignment({
  label,
  capabilityId,
  scope,
}: {
  label: string;
  capabilityId: string;
  scope: AssignmentScope;
}) {
  const scopeKey = JSON.stringify(scope);
  const stableScope = useMemo(() => scope, [scopeKey]);
  const [editor, setEditor] = useState<AssignmentEditorProjection | null>(null);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState("");
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLButtonElement | null>(null);

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

  const change = (button: HTMLButtonElement) => {
    opener.current = button;
    setReceipt("");
    setOpen(true);
    void refresh();
  };
  const close = () => {
    // Restore synchronously before unmounting the sheet; some browser focus
    // managers otherwise fall through to body during Escape's key event.
    opener.current?.focus();
    setOpen(false);
  };
  const saved = async (nextReceipt: string) => {
    setReceipt(nextReceipt);
    close();
    await refresh();
  };

  const projection = isProjection(editor) ? editor : null;

  return <div className="contextual-assignment" data-capability={capabilityId}>
    {projection ? <AssignmentSummary
      label={label}
      effective={namedChain(projection)}
      repair={projection.effective.repair}
      onChange={change}
    /> : error ? <p className="contextual-assignment-error" role="status">{error}</p> : editor ? <p className="contextual-assignment-error" role="status">Assignment unavailable</p> : <p className="contextual-assignment-loading">Loading assignment</p>}
    {receipt ? <p className="contextual-assignment-receipt" role="status">{receipt}</p> : null}
    {open && projection ? createPortal(
      <div className="contextual-assignment-layer">
        <AssignmentEditor
          title={label}
          editor={projection}
          returnFocus={opener.current}
          onClose={close}
          onRefresh={refresh}
          onSaved={saved}
        />
      </div>,
      document.getElementById("desk-next") ?? document.body,
    ) : null}
  </div>;
}
