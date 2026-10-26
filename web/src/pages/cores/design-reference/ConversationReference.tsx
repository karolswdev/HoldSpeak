import { useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { AskSourceFrame } from "../../../desk/components/AskSourceFrame";
import { DeskComposer } from "../../../desk/components/DeskComposer";
import {
  AskAbout,
  AskAnswer,
  AskFresh,
  AskQuestion,
  AskThread,
  AskToolbar,
  AskTurnRow,
  AskVerbs,
  type AskAboutRow,
} from "../../../desk/components/askFace";
import { FootSlotContext, Material, RunLine, StatusBar, ToolGlyph, type StatusBarItem } from "../../../desk/surface";
import "../../../desk/components/ask-panel.css";
import "../../../desk/surface/patterns/conversation.css";

/** Components ▸ Conversation: the Ask window's own parts (askFace) over a
 *  local fixture adapter. The same toolbar, thread, answer verbs, source
 *  frame, composer and status bar the live Ask composes; no hub read, no
 *  engine, no thread write, no egress. */
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
const ABOUT: AskAboutRow[] = [{ ref: "note:specimen", title: "Ledger rollback" }];

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
  const [about, setAbout] = useState<AskAboutRow[]>(preset === "empty" ? [] : ABOUT);
  const [picking, setPicking] = useState(false);
  const [recentOpen, setRecentOpen] = useState(false);
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
    pending ? { key: "asking", lamp: "info", text: "Asking…" } : null,
    !pending && !failed ? { key: "engine", lamp: "ok", text: "qwen3.8-27b · Private network" } : null,
    savedCount && !pending ? { key: "saved", lamp: "ok", text: "Saved as note" } : null,
    receipt ? { key: "receipt", text: <span role="status">{receipt}</span> } : null,
  ].filter(Boolean) as StatusBarItem[];
  const hasThread = turns.length > 0 || Boolean(pending) || Boolean(failed);

  return (
    <section className="reference-example reference-conversation" data-testid="reference-conversation" aria-label="Conversation pattern">
      <div className="reference-window-frame reference-conversation-frame desk-ask">
        <div className="desk-ask-body">
          <AskToolbar
            onNew={() => { setTurns([]); setFailed(null); setPending(null); setSaved({}); setAbout([]); }}
            recentOpen={recentOpen}
            onRecent={() => setRecentOpen((open) => !open)}
            onForget={turns.length ? () => setTurns([]) : undefined}
            about={<AskAbout rows={about} picking={picking} onTogglePick={() => setPicking((open) => !open)}
              onOpen={() => () => setReceipt("Opened locally")} onRemove={(row) => setAbout((rows) => rows.filter((r) => r.ref !== row.ref))} />}
          />
          {/* The source frame as it is (AskSourceFrame). In the live Ask it
              rides in the composer's details; the specimen shows it under
              the toolbar so its Back stays in reach in a short gallery
              window. */}
          <div className="reference-conversation-source" data-testid="reference-conversation-source">
            <AskSourceFrame quote={sourceQuote} open={sourceOpen} onToggle={setSourceOpen}
              onClear={() => setSourceQuote("")} onBack={() => setReceipt("Back to the Note, locally")} />
          </div>
          {recentOpen ? (
            <div className="desk-ask-recent" role="region" aria-label="Recent">
              <span className="desk-ask-recent-note">Nothing asked yet</span>
            </div>
          ) : null}
          {hasThread ? (
            <AskThread readingRef={readingRef}>
              {turns.map((turn) => (
                <AskTurnRow key={turn.key}>
                  <AskQuestion asker="Karol A">{turn.question}</AskQuestion>
                  <AskAnswer>
                    <div className="desk-ask-answer"><Material>{turn.answer}</Material></div>
                    {turn.sources.length ? (
                      <span className="desk-ask-saved">Looked at · {turn.sources.join(", ")}</span>
                    ) : null}
                    <AskVerbs>
                      {saved[turn.key]
                        ? <Button dense variant="ghost" onClick={() => setReceipt("Opened locally")}><ToolGlyph kind="open" />Open note</Button>
                        : <Button dense variant="ghost" onClick={() => setSaved((current) => ({ ...current, [turn.key]: true }))}><ToolGlyph kind="note" />Save as note</Button>}
                      <Button dense variant="ghost" onClick={() => setReceipt("Copied locally")}>Copy</Button>
                      <Button dense variant="ghost" onClick={() => setReceipt("Send prepared locally")}><ToolGlyph kind="send" />Send…</Button>
                    </AskVerbs>
                  </AskAnswer>
                </AskTurnRow>
              ))}
              {pending || failed ? (
                <AskTurnRow testId={null}>
                  <AskQuestion asker="Karol A">{pending ?? failed}</AskQuestion>
                  <AskAnswer failed={Boolean(failed)}>
                    {pending
                      ? <RunLine phase="running" verb="Working" model="qwen3.8-27b" />
                      : <RunLine phase="failure" reason="did_not_answer" onRetry={retry} />}
                  </AskAnswer>
                </AskTurnRow>
              ) : null}
            </AskThread>
          ) : (
            <AskThread readingRef={readingRef} empty>
              <AskFresh onPrompt={setDraft} />
            </AskThread>
          )}
          <div className="reference-conversation-composer">
            {/* The shared ComposerWell and PadGadget (DeskComposer, no mic:
                a specimen records nothing); Ask's own host composes the same
                species with its MicButton. */}
            <DeskComposer className="desk-ask-input" value={draft} onChange={setDraft} placeholder="Ask about your work"
              multiline rows={3} mic={false} micDraftScope="design-reference-conversation" actionLabel="Ask"
              actionDisabled={Boolean(pending) || !draft.trim()} onAction={ask} />
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
