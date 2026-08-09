/** Knowledge inline editor content (HS-117-15). */
import { useMemo, useState } from "react";
import type { EditorView } from "@codemirror/view";
import { useDesk } from "../../store";
import { DeskEditor } from "../../components/DeskEditor";
import { EditorAIBar, type EditorAIProposal } from "../../components/EditorAIBar";
import { MicButton } from "../../components/MicButton";
import { StringGadget } from "../../surface/gadgets";
import { runAsk } from "../../ask";
import { AI_VERBS } from "../../editorAI";
import { editorVoiceGrammar } from "../../voice/grammars/editor";
import type { VoiceProposal } from "../../voice/grammar";
import type { KB } from "../../../lib/primitives";
import { useDebouncedSave } from "./useDebouncedSave";
import type { InlineEditorContentProps } from "./types";

export function KbEditor({ object: o, onClose }: InlineEditorContentProps) {
  const items = useDesk((s) => s.items);
  const save = useDebouncedSave("kb", o.id);
  const [editorView, setEditorView] = useState<EditorView | null>(null);
  const [aiBarForced, setAIBarForced] = useState(false);
  const [proposal, setProposal] = useState<EditorAIProposal | null>(null);
  const [appliedReceipt, setAppliedReceipt] = useState<string | null>(null);

  const live = useMemo(
    () => (items.kb || []).find((x) => x.id === o.id) || o.ref as KB,
    [items, o.id],
  );
  const [f, setF] = useState<Record<string, string>>(() => ({
    name: String(live.name || ""),
    body: String("bodyMarkdown" in live && live.bodyMarkdown ? live.bodyMarkdown : ""),
  }));

  const set = (key: string, wire: string, value: string) => {
    setF((prev) => ({ ...prev, [key]: value }));
    save({ [wire]: value });
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
      if (!result.ok) throw new Error(result.output || "AI request failed. Your draft is unchanged. Retry.");
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

  const proposalInset = proposal ? (
    <div className="surface-aerogel editor-proposal-inset" role="status" aria-live="polite">
      <span className="editor-proposal-heading">
        PROPOSED {proposal.lens.toUpperCase()}
      </span>
      <div className="editor-proposal-copy">{proposal.proposed}</div>
      <div className="editor-proposal-actions">
        <button
          type="button"
          className="desk-chip editor-proposal-action is-accept"
          onClick={acceptProposal}
        >
          ACCEPT
        </button>
        <button
          type="button"
          className="desk-chip editor-proposal-action is-reject"
          onClick={() => setProposal(null)}
        >
          REJECT
        </button>
        <span className="editor-proposal-receipt">
          {proposal.receipt.target} · {proposal.receipt.model || "model"} · {proposal.receipt.latency}ms
        </span>
      </div>
    </div>
  ) : null;

  return (
    <>
      <StringGadget
        label="Knowledge base name"
        value={f.name}
        placeholder="Name"
        onChange={(value) => set("name", "name", value)}
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
          // HS-129-07 — the editor mic fills the document, not its name.
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
      </div>
    </>
  );
}
