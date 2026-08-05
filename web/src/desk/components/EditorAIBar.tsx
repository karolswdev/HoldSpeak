import "./inline-editor.css";
import { useEffect, useMemo, useRef, useState } from "react";
import type { EditorView } from "@codemirror/view";
import { runAsk } from "../ask";
import { AI_VERBS, type EditorAIVerb } from "../editorAI";
import { useDesk } from "../store";
import { RunsOnPicker } from "./RunsOnPicker";
import { LampGadget } from "../surface/gadgets";
import { inferenceEgressLamp } from "../inferenceEgress";

export interface EditorAIProposal {
  original: string;
  proposed: string;
  lens: string;
  receipt: {
    target: string;
    model: string;
    latency: number;
  };
  range: { from: number; to: number };
}

interface EditorAIBarProps {
  editorView: EditorView | null;
  /** A transform is proposed to the editor; it is never applied here. */
  onProposal?: (proposal: EditorAIProposal) => void;
  /** DeskEditor's Cmd+J gives the user an explicit way to open this bar. */
  forceVisible?: boolean;
  onDismiss?: () => void;
  /** An outstanding proposal must be decided before another transform runs. */
  disabled?: boolean;
}

type Receipt = { tone: "error"; text: string };

const CONTINUE_CONTEXT_LENGTH = 500;

/** A compact, selection-scoped Ask control. It never persists a result itself. */
export function EditorAIBar({
  editorView,
  onProposal,
  forceVisible = false,
  onDismiss,
  disabled = false,
}: EditorAIBarProps) {
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
  const [inferenceTargetId, setInferenceTargetId] = useState("this_machine");
  const [selectionKey, setSelectionKey] = useState("");
  const [shownSelection, setShownSelection] = useState("");
  const [pending, setPending] = useState(false);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const target = useMemo(
    () =>
      inferenceTargets.find((item) => item.id === inferenceTargetId) ||
      inferenceTargets[0],
    [inferenceTargetId, inferenceTargets],
  );
  const targetLamp = inferenceEgressLamp(target);

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

  useEffect(() => () => abortRef.current?.abort(), []);

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
    const startedAt = performance.now();
    const template = AI_VERBS[verb].prompt.replace("{text}", context);
    const result = await runAsk({
      prompt: template,
      lens: AI_VERBS[verb].label,
      context: [],
      inferenceTargetId: target?.id,
      signal: controller.signal,
    });
    const latency = Math.round(performance.now() - startedAt);
    if (controller.signal.aborted) return;

    editorView.dom.classList.remove("is-ai-pending");
    setPending(false);
    abortRef.current = null;
    if (!result.ok) {
      setReceipt({ tone: "error", text: result.output || "AI request failed." });
      return;
    }
    onProposal?.({
      original: context,
      proposed: result.output,
      lens: AI_VERBS[verb].label,
      receipt: {
        target: result.egress?.host || result.egress?.scope || "local",
        model: result.model,
        latency,
      },
      range: { from, to },
    });
    dismiss();
  };

  return (
    <div className="desk-editor-ai-bar" style={positionStyle} role="toolbar" aria-label="Selection AI">
      <div className="desk-editor-ai-bar-verbs">
        {(Object.keys(AI_VERBS) as EditorAIVerb[]).map((verb) => (
          <button
            key={verb}
            type="button"
            className="desk-chip quiet"
            disabled={pending || disabled || !target}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => void run(verb)}
          >
            {pending ? "Working…" : AI_VERBS[verb].label}
          </button>
        ))}
        <RunsOnPicker
          targets={inferenceTargets}
          selectedId={inferenceTargetId}
          onChange={setInferenceTargetId}
          disabled={pending}
        />
        <LampGadget on {...targetLamp} />
        <button type="button" className="desk-chip quiet" onClick={dismiss} aria-label="Dismiss AI controls">×</button>
      </div>
      {receipt ? (
        <span role="status" className="desk-editor-ai-bar-error">{receipt.text}</span>
      ) : null}
    </div>
  );
}
