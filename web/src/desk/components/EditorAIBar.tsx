import { useEffect, useMemo, useRef, useState } from "react";
import type { EditorView } from "@codemirror/view";
import { runAsk } from "../ask";
import { AI_VERBS, type EditorAIVerb } from "../editorAI";
import { EgressChip } from "../surface/gadgets";

interface EditorAIBarProps {
  editorView: EditorView | null;
  onResult?: (text: string) => void;
  /** DeskEditor's Cmd+J gives the user an explicit way to open this bar. */
  forceVisible?: boolean;
  onDismiss?: () => void;
}

type Receipt =
  | { tone: "error"; text: string }
  | { tone: "egress"; text: string; scope: "local" | "mixed" | "cloud" };

const CONTINUE_CONTEXT_LENGTH = 500;

function egressReceipt(result: Awaited<ReturnType<typeof runAsk>>): Receipt {
  if (!result.egress) return { tone: "egress", text: result.model || "Run complete", scope: "local" };
  const scope = result.egress.scope === "mesh" ? "mixed" : result.egress.scope;
  const marker = result.egress.scope === "local" ? "⌂" : result.egress.scope === "mesh" ? "⇄" : "→";
  return {
    tone: "egress",
    scope,
    text: [marker, result.egress.host, result.model].filter(Boolean).join(" "),
  };
}

/** A compact, selection-scoped Ask control. It never persists a result itself. */
export function EditorAIBar({
  editorView,
  onResult,
  forceVisible = false,
  onDismiss,
}: EditorAIBarProps) {
  const [selectionKey, setSelectionKey] = useState("");
  const [shownSelection, setShownSelection] = useState("");
  const [pending, setPending] = useState(false);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const receiptTimer = useRef<number | null>(null);

  const selection = useMemo(() => {
    if (!editorView) return null;
    const { from, to } = editorView.state.selection.main;
    return { from, to, empty: from === to };
  }, [editorView, selectionKey]);

  // CodeMirror owns the selection state. A small polling bridge keeps this
  // component outside the editor's extension set and follows keyboard and mouse
  // selections alike.
  useEffect(() => {
    if (!editorView) return;
    const sync = () => {
      const { from, to } = editorView.state.selection.main;
      const next = `${from}:${to}:${editorView.state.doc.length}`;
      setSelectionKey((current) => (current === next ? current : next));
    };
    sync();
    const id = window.setInterval(sync, 80);
    return () => window.clearInterval(id);
  }, [editorView]);

  useEffect(() => {
    if (!selection || selection.empty || pending) return;
    const key = `${selection.from}:${selection.to}`;
    const delay = window.setTimeout(() => setShownSelection(key), 300);
    return () => window.clearTimeout(delay);
  }, [selection?.from, selection?.to, pending]);

  useEffect(() => {
    if (!editorView) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || !pending) return;
      event.preventDefault();
      event.stopPropagation();
      abortRef.current?.abort();
      editorView.dom.classList.remove("is-ai-pending");
      setPending(false);
      setReceipt(null);
      onDismiss?.();
    };
    document.addEventListener("keydown", onKeyDown, true);
    return () => document.removeEventListener("keydown", onKeyDown, true);
  }, [editorView, pending, onDismiss]);

  useEffect(
    () => () => {
      abortRef.current?.abort();
      if (receiptTimer.current) window.clearTimeout(receiptTimer.current);
    },
    [],
  );

  if (!editorView || !selection) return null;
  const key = `${selection.from}:${selection.to}`;
  const visible =
    forceVisible ||
    pending ||
    receipt !== null ||
    (!selection.empty && shownSelection === key);
  if (!visible) return null;

  const coords = editorView.coordsAtPos(selection.from);
  if (!coords) return null;
  const positionStyle: React.CSSProperties = {
    position: "fixed",
    left: `${Math.max(8, coords.left)}px`,
    top: `${Math.max(8, coords.top - 42)}px`,
    zIndex: 90,
    transform: "translateX(-8px)",
  };

  const dismiss = () => {
    setShownSelection("");
    setReceipt(null);
    onDismiss?.();
  };

  const run = async (verb: EditorAIVerb) => {
    const { from, to } = editorView.state.selection.main;
    const context =
      verb === "continue" && from === to
        ? editorView.state.doc.sliceString(Math.max(0, from - CONTINUE_CONTEXT_LENGTH), from)
        : editorView.state.doc.sliceString(from, to);
    if (!context.trim()) {
      setReceipt({ tone: "error", text: "Select text or place the cursor after text." });
      return;
    }

    const controller = new AbortController();
    // No editor change is made until a successful response arrives, so Escape
    // can abort the transmission without having to reconstruct the source text.
    abortRef.current = controller;
    setPending(true);
    setReceipt(null);
    editorView.dom.classList.add("is-ai-pending");
    const template = AI_VERBS[verb].prompt.replace("{text}", context);
    const result = await runAsk({
      prompt: template,
      lens: AI_VERBS[verb].label,
      context: [],
      signal: controller.signal,
    });
    if (controller.signal.aborted) return;

    editorView.dom.classList.remove("is-ai-pending");
    setPending(false);
    abortRef.current = null;
    if (!result.ok) {
      setReceipt({ tone: "error", text: result.output || "AI request failed." });
      return;
    }
    editorView.dispatch({ changes: { from, to, insert: result.output } });
    editorView.focus();
    onResult?.(result.output);
    setReceipt(egressReceipt(result));
    if (receiptTimer.current) window.clearTimeout(receiptTimer.current);
    receiptTimer.current = window.setTimeout(() => {
      setReceipt(null);
      dismiss();
    }, 3000);
  };

  return (
    <div className="desk-editor-ai-bar" style={positionStyle} role="toolbar" aria-label="Selection AI">
      <div className="desk-editor-ai-bar-verbs">
        {(Object.keys(AI_VERBS) as EditorAIVerb[]).map((verb) => (
          <button
            key={verb}
            type="button"
            className="desk-chip quiet"
            disabled={pending}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => void run(verb)}
          >
            {pending ? "Working…" : AI_VERBS[verb].label}
          </button>
        ))}
        <button type="button" className="desk-chip quiet" onClick={dismiss} aria-label="Dismiss AI controls">×</button>
      </div>
      {receipt ? (
        receipt.tone === "egress" ? (
          <EgressChip label={receipt.text} scope={receipt.scope} title="This AI result's actual egress." />
        ) : (
          <span role="status" className="desk-editor-ai-bar-error">{receipt.text}</span>
        )
      ) : null}
    </div>
  );
}
