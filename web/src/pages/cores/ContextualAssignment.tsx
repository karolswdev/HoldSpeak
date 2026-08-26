import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { readableError } from "../../lib/api";
import { AssignmentEditor } from "./AssignmentEditor";
import { AssignmentSummary } from "./AssignmentSummary";
import {
  getAssignmentEditor,
  type AssignmentEditorProjection,
  type AssignmentScope,
} from "./assignmentExperience";

function namedChain(editor: AssignmentEditorProjection): string {
  const entries = editor.effective.assignment?.entries ?? [];
  const chain = entries.length ? entries.map((entry) => entry.label).join(" → ") : "No default model";
  const source = editor.effective.inherited_from;
  return source ? `Uses ${source} · ${chain}` : chain;
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
  const saved = async (nextReceipt: string) => {
    setReceipt(nextReceipt);
    setOpen(false);
    await refresh();
  };

  return <div className="contextual-assignment" data-capability={capabilityId}>
    {editor ? <AssignmentSummary
      label={label}
      effective={namedChain(editor)}
      repair={editor.effective.repair}
      onChange={change}
    /> : error ? <p className="contextual-assignment-error" role="status">{error}</p> : <p className="contextual-assignment-loading">Loading assignment</p>}
    {receipt ? <p className="contextual-assignment-receipt" role="status">{receipt}</p> : null}
    {open && editor ? <AssignmentEditor
      title={label}
      editor={editor}
      returnFocus={opener.current}
      onClose={() => setOpen(false)}
      onRefresh={refresh}
      onSaved={saved}
    /> : null}
  </div>;
}
