import { useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { AskSourceFrame } from "../../../desk/components/AskSourceFrame";
import { DeskComposer } from "../../../desk/components/DeskComposer";
import {
  AskComposer,
  AskEngineWord,
  AskNotAnswered,
  AskPage,
  AskPrompts,
  AskRail,
  AskReferences,
  AskScope,
  AskTurnDoc,
  AskVerbs,
  type AskScopeRow,
} from "../../../desk/components/askFace";
import type { AskPrompt } from "../../../desk/askPrompts";
import { FootSlotContext, Material, RunLine, StatusBar, ToolGlyph, type StatusBarItem } from "../../../desk/surface";
import "../../../desk/components/ask-panel.css";
import "../../../desk/surface/patterns/conversation.css";

/** Components ▸ Conversation: the Ask window's own parts (askFace, Ask D1
 *  "The question at the top") over a local fixture adapter. The same
 *  composer row, Recent rail, answer document, references, source frame
 *  and status bar the live Ask composes; no hub read, no engine, no thread
 *  write, no egress. */
export type ConversationPreset = "empty" | "ordinary" | "busy" | "failed" | "saved";

export const CONVERSATION_STATES: Array<{ id: ConversationPreset; label: string }> = [
  { id: "empty", label: "Fresh" },
  { id: "ordinary", label: "Answered with source" },
  { id: "busy", label: "Asking" },
  { id: "failed", label: "Failed" },
  { id: "saved", label: "Saved" },
];

type Turn = { key: string; question: string; answer: string; sources: string[] };

export const FAILED_REQUEST = "Can we keep the release note local while we review it?";
export const FAILED_REPLY = "The reply is available locally for the captured request.";
const QUESTION = "What did we decide about the ledger?";
const ANSWER = "## Ledger freeze\n\nThe team agreed to **freeze the ledger on Nov 12**. Mira owns the rollback runbook.\n\n- Review the cutover plan by Thursday.\n- Book the second hiring loop.";
const LOCAL_REPLY = "Yes. The source stays beside the result.";
const ABOUT: AskScopeRow[] = [{ ref: "note:specimen", title: "Ledger rollback" }];
const PROMPTS: AskPrompt[] = [
  { key: "needs", text: "What needs my attention today?", source: "14 in Needs you", kind: "action" },
  { key: "decision", text: "What did we decide about “Freeze the old ledger on Nov 5”?", source: "Accepted, 2h ago", kind: "decision" },
  { key: "waiting", text: "Who is waiting on me?", source: "Avery, Jordan and Sam", kind: "person" },
];
const RAIL = [
  { id: "r1", title: "What did we decide about the ledger?", at: Date.now() },
  { id: "r2", title: "Summarize the tracing review", at: Date.now() - 86_400_000 },
];

function presetTurns(preset: ConversationPreset): Turn[] {
  if (preset === "empty" || preset === "failed") return [];
  return [{ key: "t1", question: QUESTION, answer: ANSWER, sources: ["Ledger cutover sync", "Vendor sync"] }];
}

export function ConversationReference({ preset }: { preset: ConversationPreset }) {
  const [turns, setTurns] = useState<Turn[]>(() => presetTurns(preset));
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState<string | null>(preset === "busy" ? "Who owns the rollback runbook?" : null);
  const [failed, setFailed] = useState<string | null>(preset === "failed" ? FAILED_REQUEST : null);
  const [saved, setSaved] = useState<Record<string, boolean>>(preset === "saved" ? { t1: true } : {});
  const [about, setAbout] = useState<AskScopeRow[]>(preset === "empty" ? [] : ABOUT);
  const [railOpen, setRailOpen] = useState(false);
  const [sourceQuote, setSourceQuote] = useState("The source stays beside the decision.");
  const [sourceOpen, setSourceOpen] = useState(true);
  const [receipt, setReceipt] = useState("");
  const retryTimer = useRef<number | null>(null);
  const readingRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => () => {
    if (retryTimer.current !== null) window.clearTimeout(retryTimer.current);
  }, []);

  const ask = () => {
    const question = draft.trim();
    if (!question || pending) return;
    setTurns((items) => [...items, { key: `t${items.length + 1}`, question, answer: LOCAL_REPLY, sources: [] }]);
    setDraft("");
  };
  // Retry runs the captured request again; a newer draft stays as it is.
  const retry = () => {
    const request = failed;
    if (!request || pending || retryTimer.current !== null) return;
    setFailed(null);
    setPending(request);
    retryTimer.current = window.setTimeout(() => {
      setTurns((items) => [...items, { key: `t${items.length + 1}`, question: request, answer: FAILED_REPLY, sources: [] }]);
      setPending(null);
      retryTimer.current = null;
    }, 120);
  };
  const stop = () => {
    if (retryTimer.current !== null) window.clearTimeout(retryTimer.current);
    retryTimer.current = null;
    setFailed(pending);
    setPending(null);
  };

  const savedCount = Object.values(saved).filter(Boolean).length;
  const items: StatusBarItem[] = [
    pending ? { key: "asking", lamp: "info", text: "Writing the answer · 3 s" } : null,
    !pending && failed ? { key: "failed", text: "Not answered · your question is kept" } : null,
    !pending && !failed && !turns.length ? { key: "scope", text: "My whole desk: 3 projects · 3 meetings this week · 4 people" } : null,
    savedCount && !pending ? { key: "saved", lamp: "ok", text: "Saved as note" } : null,
    receipt ? { key: "receipt", text: <span role="status">{receipt}</span> } : null,
  ].filter(Boolean) as StatusBarItem[];
  const hasThread = turns.length > 0 || Boolean(pending) || Boolean(failed);

  return (
    <section className="reference-example reference-conversation" data-testid="reference-conversation" aria-label="Conversation pattern">
      <div className="reference-window-frame reference-conversation-frame desk-ask">
        <div className="desk-ask-body" data-rail={railOpen ? "open" : "folded"}>
          <AskComposer
            railOpen={railOpen}
            onRail={() => setRailOpen((open) => !open)}
            scope={<AskScope rows={about} candidates={[]} onPick={(pick) => setAbout(pick.ref === "desk:whole" ? [] : [{ ref: pick.ref, title: pick.label }])}
              onRemove={(row) => setAbout((rows) => rows.filter((r) => r.ref !== row.ref))} onOpenRow={() => () => setReceipt("Opened locally")} />}
            field={
              // The shared ComposerWell and PadGadget (DeskComposer, no mic:
              // a specimen records nothing); Ask's own host composes the same
              // row with its MicButton.
              <DeskComposer className="desk-ask-input" value={draft} onChange={setDraft} placeholder="Ask about your work"
                multiline rows={1} mic={false} micDraftScope="design-reference-conversation" actionLabel="Ask"
                actionDisabled={Boolean(pending) || !draft.trim()} onAction={ask} />
            }
            engine={<AskEngineWord state="set" name="Codex" onPress={() => setReceipt("Engines open in Settings")} />}
            details={
              /* The source frame as it is (AskSourceFrame), under the row. */
              <div className="reference-conversation-source" data-testid="reference-conversation-source">
                <AskSourceFrame quote={sourceQuote} open={sourceOpen} onToggle={setSourceOpen}
                  onClear={() => setSourceQuote("")} onBack={() => setReceipt("Back to the Note, locally")} />
              </div>
            }
          />
          <div className="desk-ask-main">
            {railOpen ? (
              <AskRail rows={RAIL} selectedId="r1" onPick={() => setReceipt("Opened locally")}
                onNew={() => { setTurns([]); setFailed(null); setPending(null); setSaved({}); setAbout([]); }} />
            ) : null}
            {hasThread ? (
              <AskPage readingRef={readingRef}>
                {turns.map((turn) => (
                  <AskTurnDoc key={turn.key} question={turn.question}>
                    <div className="desk-ask-answer"><Material>{turn.answer}</Material></div>
                    <AskReferences rows={turn.sources.map((title, index) => ({
                      ref: `meeting:specimen-${index}`, title, kind: "meeting", meta: "Meeting · 2h ago", onOpen: () => setReceipt("Opened locally"),
                    }))} />
                    <AskVerbs>
                      {saved[turn.key]
                        ? <Button dense variant="secondary" onClick={() => setReceipt("Opened locally")}><ToolGlyph kind="open" />Open note</Button>
                        : <Button dense variant="secondary" onClick={() => setSaved((current) => ({ ...current, [turn.key]: true }))}><ToolGlyph kind="note" />Save as note</Button>}
                      <Button dense variant="ghost" onClick={() => setReceipt("Copied locally")}><ToolGlyph kind="copy" />Copy</Button>
                      <Button dense variant="ghost" onClick={() => setReceipt("Send prepared locally")}><ToolGlyph kind="send" />Send…</Button>
                    </AskVerbs>
                  </AskTurnDoc>
                ))}
                {pending || failed ? (
                  <AskTurnDoc testId={null} question={(pending ?? failed)!}>
                    {pending
                      ? <RunLine phase="running" verb="Working" />
                      : <AskNotAnswered reason="did_not_answer" words="The engine did not answer."
                          verb={<Button dense variant="secondary" onClick={retry}>Try again</Button>} />}
                  </AskTurnDoc>
                ) : null}
              </AskPage>
            ) : (
              <AskPage readingRef={readingRef} empty>
                <AskPrompts prompts={PROMPTS} onPrompt={setDraft} />
              </AskPage>
            )}
          </div>
        </div>
        <FootSlotContext.Provider value={null}>
          <StatusBar
            data-testid="reference-conversation-status"
            items={items}
            verbs={pending ? <Button dense variant="secondary" onClick={stop}>Stop</Button> : undefined}
          />
        </FootSlotContext.Provider>
      </div>
    </section>
  );
}
