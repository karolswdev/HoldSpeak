/** Note inline editor content (HS-117-15). */
import { useMemo, useState } from "react";
import type { EditorView } from "@codemirror/view";
import { useDesk } from "../../store";
import { DeskEditor } from "../../components/DeskEditor";
import { EditorAIBar, type EditorAIProposal } from "../../components/EditorAIBar";
import { MicButton } from "../../components/MicButton";
import { runAsk } from "../../ask";
import { AI_VERBS } from "../../editorAI";
import { editorVoiceGrammar } from "../../voice/grammars/editor";
import type { VoiceProposal } from "../../voice/grammar";
import type { Note } from "../../../lib/primitives";
import { useDebouncedSave } from "./useDebouncedSave";
import type { InlineEditorContentProps } from "./types";

export function NoteEditor({ object: o, onClose }: InlineEditorContentProps) {
  const items = useDesk((s) => s.items);
  const save = useDebouncedSave("note", o.id);
  const [editorView, setEditorView] = useState<EditorView | null>(null);
  const [aiBarForced, setAIBarForced] = useState(false);
  const [proposal, setProposal] = useState<EditorAIProposal | null>(null);
  const [appliedReceipt, setAppliedReceipt] = useState<string | null>(null);

  const live = useMemo(
    () => (items.note || []).find((x) => x.id === o.id) || o.ref as Note,
    [items, o.id],
  );
  const [f, setF] = useState<Record<string, string>>(() => ({
    title: String(live.title || ""),
    body: String(live.bodyMarkdown || ""),
    tags: (live.tags || []).join(", "),
  }));

  const set = (key: string, wire: string, value: string, split = false) => {
    setF((prev) => ({ ...prev, [key]: value }));
    save({
      [wire]: split
        ? value.split(",").map((t) => t.trim()).filter(Boolean)
        : value,
    });
  };

  const confirmEditorVoice = async (p: VoiceProposal) => {
    const view = editorView;
    if (!view) return;
    const { from, to } = view.state.selection.main;
    const selectedText = view.state.doc.sliceString(from, to);
    const replace = (text: string) => {
      view.dispatch({ changes: { from, to, insert: text } });
      view.focus();
    };
    if (p.intentId === "bold") return replace(`**${selectedText}**`);
    if (p.intentId === "italic") return replace(`*${selectedText}*`);
    if (p.intentId === "heading") return replace(`# ${selectedText}`);
    if (p.intentId === "list") {
      return replace(selectedText.split("\n").map((line) => `- ${line}`).join("\n"));
    }
    if (p.intentId === "readback") {
      window.speechSynthesis?.speak(new SpeechSynthesisUtterance(selectedText));
      return;
    }
    if (
      p.intentId === "rewrite" ||
      p.intentId === "expand" ||
      p.intentId === "continue"
    ) {
      const context =
        p.intentId === "continue" && from === to
          ? view.state.doc.sliceString(Math.max(0, from - 500), from)
          : selectedText;
      const startedAt = performance.now();
      const result = await runAsk({
        lens: AI_VERBS[p.intentId].label,
        prompt: AI_VERBS[p.intentId].prompt.replace("{text}", context),
        context: [],
      });
      if (!result.ok) throw new Error(result.output || "AI request failed.");
      setProposal({
        original: context,
        proposed: result.output,
        lens: AI_VERBS[p.intentId].label,
        receipt: {
          target: result.egress?.host || result.egress?.scope || "local",
          model: result.model,
          latency: Math.round(performance.now() - startedAt),
        },
        range: { from, to },
      });
    }
  };

  const acceptProposal = () => {
    if (!proposal || !editorView) return;
    const { from, to } = proposal.range;
    editorView.dispatch({
      changes: { from, to, insert: proposal.proposed },
      selection: { anchor: from, head: from + proposal.proposed.length },
    });
    editorView.focus();
    setAppliedReceipt(`${proposal.lens.toUpperCase()} APPLIED · ⌘Z TO UNDO`);
    setProposal(null);
  };

  const proposalButtonStyle: React.CSSProperties = {
    border: "1px solid var(--border)",
    borderRadius: 0,
    font: "600 10px/1 var(--font-mono)",
    letterSpacing: ".06em",
    padding: "4px 12px",
  };
  const proposalInset = proposal ? (
    <div className="surface-aerogel" role="status" aria-live="polite">
      <span style={{ fontSize: "var(--desk-surface-detail-size)", fontFamily: "var(--font-mono)", letterSpacing: ".06em" }}>
        PROPOSED {proposal.lens.toUpperCase()}
      </span>
      <div style={{ fontSize: "13px", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
        {proposal.proposed}
      </div>
      <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 6 }}>
        <button
          type="button"
          className="desk-chip"
          style={{ ...proposalButtonStyle, background: "var(--ok-soft)", color: "var(--ok)" }}
          onClick={acceptProposal}
        >
          ACCEPT
        </button>
        <button
          type="button"
          className="desk-chip"
          style={{
            ...proposalButtonStyle,
            background: "var(--danger-signal-soft, color-mix(in srgb, var(--danger-signal) 12%, var(--surface-2)))",
            color: "var(--danger-signal)",
          }}
          onClick={() => setProposal(null)}
        >
          REJECT
        </button>
        <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", opacity: 0.72 }}>
          {proposal.receipt.target} · {proposal.receipt.model || "model"} · {proposal.receipt.latency}ms
        </span>
      </div>
    </div>
  ) : null;

  return (
    <>
      <input
        value={f.title}
        placeholder="Title"
        onChange={(e) => set("title", "title", e.target.value)}
      />
      <DeskEditor
        value={f.body}
        placeholder="Write"
        autoFocus
        onEscape={onClose}
        onChange={(value) => set("body", "body_markdown", value)}
        onViewChange={setEditorView}
        onAIBarToggle={() => setAIBarForced((shown) => !shown)}
      />
      <EditorAIBar
        editorView={editorView}
        forceVisible={aiBarForced}
        onDismiss={() => setAIBarForced(false)}
        onProposal={setProposal}
        disabled={Boolean(proposal)}
      />
      {proposalInset}
      <input
        value={f.tags}
        placeholder="Tags"
        onChange={(e) => set("tags", "tags", e.target.value, true)}
      />
      <div className="desk-inline-editor-foot">
        <MicButton
          draftScope={`inline:${o.kind}:${o.id}`}
          grammar={editorView ? editorVoiceGrammar : undefined}
          surfaceKind="editor"
          hasSelection={Boolean(
            editorView &&
              editorView.state.selection.main.from !== editorView.state.selection.main.to,
          )}
          onProposalConfirm={confirmEditorVoice}
          onText={(t) => {
            set("body", "body_markdown", (f.body ? f.body + " " : "") + t);
          }}
        />
        {appliedReceipt ? (
          <span role="status" style={{ fontFamily: "var(--font-mono)", fontSize: "var(--desk-surface-detail-size)" }}>
            {appliedReceipt}
          </span>
        ) : null}
        <span className="desk-inline-editor-spacer" />
        <button
          type="button"
          className="desk-chip quiet"
          onClick={onClose}
        >
          Done
        </button>
      </div>
    </>
  );
}
