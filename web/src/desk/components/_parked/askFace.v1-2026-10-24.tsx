// The Ask face (window grammar, 2026-10-24): the parts of the Ask window
// that draw, with no hub, thread or engine authority. AskPanel composes them
// over the live Ask; Components ▸ Conversation composes the same parts over a
// local fixture. Title bar → Toolbar (New ask, Recent, the About line) → the
// thread (question with the asker's disc, the answer as a reading document
// with its 20 px glyph and its verbs in one row) → the composer → StatusBar.
// The composer itself stays in its host (AskPanel composes ComposerWell,
// PadGadget and its MicButton in one component: the voice law's host
// authority, scripts/ux_canon_scan.py MIC_HOST_AUTHORITIES).
import type { ReactNode, Ref, RefObject } from "react";
import { Button } from "../../components/signal/Signal";
import { Avatar, ToolGlyph, Toolbar } from "../surface/kit";
import { ScrollHint } from "../surface";
import { glyphSprite, spriteUrl } from "../sprites";

/** The Ask object's own drawing (a conversation), at 64 and at 20 px. */
export const ASK_SPRITE = spriteUrl("thread", "ask");
export const ASK_GLYPH = glyphSprite(ASK_SPRITE);

/** The toolbar under the title bar: New ask (the one primary), Recent ▾
 *  (the saved threads), Forget when a thread is open; the About line at the
 *  trailing end. */
export function AskToolbar({ onNew, recentOpen, onRecent, onForget, about }: {
  onNew: () => void;
  recentOpen: boolean;
  onRecent: () => void;
  onForget?: () => void;
  about: ReactNode;
}) {
  return (
    <Toolbar label="Ask" className="desk-ask-toolbar" data-testid="ask-toolbar" trailing={about}>
      <Button dense variant="primary" className="desk-ask-new" onClick={onNew}>
        <ToolGlyph kind="ask" />
        New ask
      </Button>
      <Button dense variant="secondary" aria-expanded={recentOpen} onClick={onRecent}>
        <ToolGlyph kind="open" />
        Recent<span className="desk-ask-caret" aria-hidden="true">▾</span>
      </Button>
      {onForget ? <Button dense variant="secondary" onClick={onForget}>Forget</Button> : null}
    </Toolbar>
  );
}

export interface AskAboutRow {
  ref: string;
  title: string;
}

/** The About line: what the question is about, `My whole desk` when
 *  nothing is chosen. Each chosen object opens and has its ✕; + opens the
 *  picker. It is the toolbar's trailing control. */
export function AskAbout({ rows, picking, onTogglePick, onOpen, onRemove }: {
  rows: readonly AskAboutRow[];
  picking: boolean;
  onTogglePick: () => void;
  /** Absent for a row that only names a set (`This week's meetings`). */
  onOpen?: (row: AskAboutRow) => (() => void) | undefined;
  onRemove: (row: AskAboutRow) => void;
}) {
  return (
    <div className="desk-ask-about" data-testid="ask-context">
      <span className="desk-ask-about-label">About</span>
      {rows.length ? rows.map((row) => {
        const open = onOpen?.(row);
        return (
          <span className="desk-ask-about-chip" key={row.ref} data-testid="ask-about-chip">
            {open
              ? <Button dense variant="ghost" onClick={open}>{row.title}</Button>
              : <span className="desk-ask-about-set">{row.title}</span>}
            <Button dense variant="ghost" className="desk-ask-about-remove" aria-label={`Remove ${row.title}`} onClick={() => onRemove(row)}>✕</Button>
          </span>
        );
      }) : <span className="desk-ask-about-desk">My whole desk</span>}
      <Button dense variant="ghost" className="desk-ask-about-add" aria-label="Add to About" aria-expanded={picking} onClick={onTogglePick}>
        <ToolGlyph kind="new" />
      </Button>
    </div>
  );
}

/** The reading viewport of the thread: it scrolls inside the window; the
 *  newest turn is at the bottom. */
export function AskThread({ readingRef, empty, children, testId }: {
  readingRef: RefObject<HTMLDivElement | null>;
  empty?: boolean;
  children: ReactNode;
  testId?: string;
}) {
  return (
    <ScrollHint axis="y" scrollRef={readingRef} className="desk-ask-reading-wrap">
      <div
        ref={readingRef as Ref<HTMLDivElement>}
        className={`conversation-reading desk-ask-reading${empty ? " desk-ask-empty" : ""}`}
        role="region"
        aria-label="Ask conversation"
        tabIndex={0}
        data-testid={testId}
      >
        {empty ? children : <ol className="desk-ask-thread">{children}</ol>}
      </div>
    </ScrollHint>
  );
}

/** One turn: the question, then its answer (or its run line). */
export function AskTurnRow({ children, testId = "ask-turn" }: { children: ReactNode; testId?: string | null }) {
  return <li className="desk-ask-turn" data-testid={testId ?? undefined}>{children}</li>;
}

/** The question: the asker's disc and his words, sans 15/500 ink. */
export function AskQuestion({ asker, children }: { asker: string; children: ReactNode }) {
  return (
    <div className="desk-ask-question">
      <Avatar name={asker} />
      <div className="desk-ask-question-text">{children}</div>
    </div>
  );
}

/** The answer: led by Ask's 20 px glyph; the body is the reading document
 *  (its own headings allowed), then its facts and its verbs. */
export function AskAnswer({ children, failed }: { children: ReactNode; failed?: boolean }) {
  return (
    <div className="desk-ask-reply" data-failed={failed || undefined}>
      <img className="desk-ask-reply-glyph" src={ASK_GLYPH} alt="" width={20} height={20} draggable={false} />
      <div className="desk-ask-reply-body">{children}</div>
    </div>
  );
}

/** The answer's verbs, in one row under it: quiet Buttons, icon + label. */
export function AskVerbs({ children }: { children: ReactNode }) {
  return <div className="surface-row-verbs desk-ask-verbs">{children}</div>;
}

/** A fresh Ask: Ask's big drawing and the starter questions. */
export function AskFresh({ onPrompt }: { onPrompt: (text: string) => void }) {
  return (
    <>
      <img className="desk-ask-empty-sprite" src={ASK_SPRITE} alt="" width={64} height={64} draggable={false} />
      <div className="desk-ask-prompts">
        <Button dense variant="ghost" className="desk-ask-starter" onClick={() => onPrompt("What needs my attention?")}>
          <img src={glyphSprite(spriteUrl("action", "ask-attention"))} alt="" width={20} height={20} draggable={false} />
          <span className="desk-ask-starter-label">What needs my attention?</span>
        </Button>
        <Button dense variant="ghost" className="desk-ask-starter" onClick={() => onPrompt("Summarize this week's meetings")}>
          <img src={glyphSprite(spriteUrl("meeting", "ask-meetings"))} alt="" width={20} height={20} draggable={false} />
          <span className="desk-ask-starter-label">Summarize this week's meetings</span>
        </Button>
      </div>
    </>
  );
}
