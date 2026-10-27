// The Ask face, direction D1 "The question at the top" (canvas
// docs/internal/betterment/canvases/ask-direction-2026-10-27.html, ratified
// 2026-10-27: "go with suggestions going forward, they are good").
//
// Title bar → the composer IS the toolbar row ([Recent] [scope ▾] [field]
// [mic] [engine] [Ask ⏎]) → the Recent rail at the left and the answer as a
// document at the right → the 24 px status bar. These parts draw and hold
// no hub, thread or engine authority: AskPanel composes them over the live
// Ask; Components ▸ Conversation composes the same parts over a fixture.
// The composer row takes its field and its mic from its host (the voice
// law's host authority, scripts/ux_canon_scan.py MIC_HOST_AUTHORITIES), so
// Memory's and the Room's Ask boxes can adopt AskComposer later.
//
// The parts of the 2026-10-24 grammar (New ask in the toolbar, the About
// chips, the You / answer pair, the big drawing) are parked in
// `_parked/askFace.v1-2026-10-24.tsx`.
import { useEffect, useMemo, useRef, useState, type ReactNode, type Ref, type RefObject } from "react";
import { Button } from "../../components/signal/Signal";
import { DotWord, ToolGlyph, Toolbar } from "../surface/kit";
import { ScrollHint } from "../surface";
import { StringGadget } from "../surface/gadgets";
import { glyphSprite, spriteUrl } from "../sprites";
import { humanTime } from "../surface/format";
import { aboutMatches, type AboutCandidate } from "./about/AboutPicker";
import type { AskPrompt } from "../askPrompts";
// The parts carry their own style: Memory and the Room compose them too.
import "./ask-panel.css";

/** The Ask object's own drawing (a conversation), at 64 and at 20 px. */
export const ASK_SPRITE = spriteUrl("thread", "ask");
export const ASK_GLYPH = glyphSprite(ASK_SPRITE);

/** The 20 px drawing of a desk object kind (a reference row, a menu row). */
export function kindGlyph(kind: string, id = "ask"): string {
  const k = kind === "action_item" ? "action" : kind === "people" ? "person" : kind;
  return spriteUrl(k, id, "rest", null, 20);
}

function RailGlyph() {
  return (
    <svg className="kit-toolglyph" width={16} height={16} viewBox="0 0 16 16" fill="none" stroke="currentColor"
      strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M2.5 3h11v10h-11Z M6.5 3v10" />
    </svg>
  );
}

function MoreGlyph() {
  return (
    <svg className="kit-toolglyph" width={16} height={16} viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" focusable="false">
      <circle cx="3.5" cy="8" r="1.1" /><circle cx="8" cy="8" r="1.1" /><circle cx="12.5" cy="8" r="1.1" />
    </svg>
  );
}

/** Close a popover on Escape and on a press outside it. */
function useDismiss(open: boolean, ref: RefObject<HTMLElement | null>, onClose: () => void) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      onClose();
    };
    const onDown = (event: PointerEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) onClose();
    };
    document.addEventListener("keydown", onKey, true);
    document.addEventListener("pointerdown", onDown, true);
    return () => {
      document.removeEventListener("keydown", onKey, true);
      document.removeEventListener("pointerdown", onDown, true);
    };
  }, [open, ref, onClose]);
}

/* ── The composer row (kit Toolbar species) ─────────────────────────── */

/** The composer is the toolbar row: [Recent] [scope ▾] [field] [mic]
 *  [engine] [Ask ⏎]. The field grows to three lines, then scrolls. On a
 *  phone the row takes two lines: the scope and the engine, then the field,
 *  the mic and Ask. The host passes the field and its mic. */
export function AskComposer({ className, railOpen, onRail, scope, field, capture, engine, action, details, "data-testid": testId }: {
  className?: string;
  /** Absent: no rail in this host (the button is not drawn). */
  railOpen?: boolean;
  onRail?: () => void;
  scope: ReactNode;
  field: ReactNode;
  capture?: ReactNode;
  engine?: ReactNode;
  /** Ask ⏎ (absent when the field carries its own verb). */
  action?: ReactNode;
  /** A band under the row for a handed-over source (the Note's quote). */
  details?: ReactNode;
  "data-testid"?: string;
}) {
  return (
    <>
      <Toolbar label="Ask" className={`desk-ask-composer-row${className ? ` ${className}` : ""}`} data-testid={testId}>
        {onRail ? (
          <Button dense variant="ghost" className="desk-ask-railtoggle" aria-label="Recent" aria-pressed={Boolean(railOpen)}
            title="Recent asks" onClick={onRail}>
            <RailGlyph />
          </Button>
        ) : null}
        <span className="desk-ask-composer-scope">{scope}</span>
        <span className="desk-ask-composer-field">{field}</span>
        <span className="desk-ask-composer-end">
          {capture}
          {engine}
          {action}
        </span>
      </Toolbar>
      {details ? <div className="desk-ask-composer-details">{details}</div> : null}
    </>
  );
}

/** Ask ⏎: the one primary verb, with its key. A host whose window has its
 *  own primary (the Room's Write update) passes `secondary`: one filled
 *  primary per face. */
export function AskSendButton({ disabled, onClick, variant = "primary" }: {
  disabled: boolean;
  onClick: () => void;
  variant?: "primary" | "secondary";
}) {
  return (
    <Button dense variant={variant} className="desk-ask-send" disabled={disabled} onClick={onClick} aria-label="Ask">
      Ask<span className="desk-ask-key" aria-hidden="true">⏎</span>
    </Button>
  );
}

/** The engine: a dot and its name (`● Codex`); grey and `No engine` when
 *  none answers Ask. A press opens the engine choice. No host, no mono. */
export function AskEngineWord({ state, name, title, onPress }: {
  state: "set" | "none" | "unread" | "failed";
  name: string;
  title?: string;
  onPress?: () => void;
}) {
  const words = state === "set" ? name : state === "failed" ? "Engine not read" : state === "unread" ? "Engine" : "No engine";
  const tone = state === "set" ? "ok" : state === "failed" ? "warn" : "idle";
  return (
    <Button dense variant="ghost" className="desk-ask-engine" data-testid="engine-line" data-state={state} title={title}
      aria-label={state === "set" ? `Engine: ${name}` : words} onClick={onPress}>
      <DotWord tone={tone}>{words}</DotWord>
    </Button>
  );
}

/* ── The scope word and its menu ─────────────────────────────────────── */

export interface AskScopeRow {
  ref: string;
  title: string;
}

/** The scope word: what the question is about, with ▾. `My whole desk`
 *  when nothing is chosen; one object's name; or `<name> and N more`. */
export function scopeWord(rows: readonly AskScopeRow[]): string {
  if (!rows.length) return "My whole desk";
  if (rows.length === 1) return rows[0].title;
  return `${rows[0].title} and ${rows.length - 1} more`;
}

/** The scope word ▾ and the menu it opens under it (no band, no modal):
 *  My whole desk, This week's meetings, Projects, People, with a filter
 *  field. One pick changes the word. What is chosen now is listed first,
 *  each with its ✕. */
export function AskScope({ rows, candidates, weekCount, onPick, onRemove, onOpenRow, compact }: {
  rows: readonly AskScopeRow[];
  candidates: readonly AboutCandidate[];
  /** This week's meetings, said at the set's row (no zero). */
  weekCount?: number;
  onPick: (pick: AboutCandidate) => void;
  onRemove: (row: AskScopeRow) => void;
  /** Open a chosen object's window (absent for a set). */
  onOpenRow?: (row: AskScopeRow) => (() => void) | undefined;
  compact?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapRef = useRef<HTMLSpanElement | null>(null);
  const close = () => { setOpen(false); setQuery(""); };
  useDismiss(open, wrapRef, close);
  const word = scopeWord(rows);
  const single = rows.length === 1 ? rows[0] : null;
  const glyphKind = single ? single.ref.split(":")[0] : "";
  const groups = useMemo(() => {
    const chosen = new Set(rows.map((row) => row.ref));
    const asked = query.trim();
    const list = asked
      ? aboutMatches([...candidates], asked, 10)
      : candidates.filter((c) => c.kind === "project" || c.kind === "person" || c.ref === "meetings:this_week");
    const out: Array<{ key: string; caption: string; rows: AboutCandidate[] }> = [];
    const caption: Record<string, string> = {
      project: "Projects", person: "People", meeting: "Meetings", note: "Notes", decision: "Decisions", zone: "Drawers", set: "",
    };
    for (const c of list) {
      if (c.ref === "desk:whole" || chosen.has(c.ref)) continue;
      const key = c.kind;
      const group = out.find((g) => g.key === key);
      if (group) { if (group.rows.length < 6) group.rows.push(c); }
      else out.push({ key, caption: caption[key] ?? "Other", rows: [c] });
    }
    return out;
  }, [candidates, query, rows]);

  const pick = (candidate: AboutCandidate) => {
    onPick(candidate);
    close();
  };

  return (
    <span className="desk-ask-scope" ref={wrapRef}>
      <Button dense variant="ghost" className="desk-ask-scope-word" data-testid="ask-context" aria-expanded={open}
        aria-haspopup="true" aria-label={`About: ${word}`} onClick={() => (open ? close() : setOpen(true))}>
        {single && glyphKind && glyphKind !== "meetings" ? <img src={kindGlyph(glyphKind, single.ref)} alt="" width={16} height={16} draggable={false} /> : null}
        <span className="desk-ask-scope-text">{word}</span>
        <span className="desk-ask-caret" aria-hidden="true">▾</span>
      </Button>
      {open ? (
        <div className="desk-menu-list desk-ask-scope-menu" role="group" aria-label="About" data-compact={compact || undefined} data-testid="ask-scope-menu">
          <div className="desk-ask-scope-find">
            <StringGadget label="Find a meeting, note, person" value={query} onChange={setQuery} placeholder="Find a meeting, note, person…" autoFocus
              onKeyDown={(event) => {
                if (event.key !== "Enter") return;
                const top = groups[0]?.rows[0];
                if (!top) return;
                event.preventDefault();
                pick(top);
              }} />
          </div>
          {!query.trim() ? (
            <Button variant="chrome" className="desk-ask-scope-row" aria-checked={!rows.length} role="menuitemradio"
              onClick={() => pick({ ref: "desk:whole", kind: "set", label: "My whole desk" })}>
              <span className="desk-menu-glyph desk-ask-check" aria-hidden="true">{rows.length ? "" : "✓"}</span>
              <span className="desk-menu-label">My whole desk</span>
            </Button>
          ) : null}
          {rows.map((row) => {
            const openRow = onOpenRow?.(row);
            const kind = row.ref.split(":")[0];
            return (
              <span className="desk-ask-scope-chosen" key={row.ref} data-testid="ask-about-chip">
                <Button variant="chrome" className="desk-ask-scope-row" aria-checked="true" role="menuitemcheckbox"
                  onClick={() => { if (openRow) { openRow(); close(); } }}>
                  <span className="desk-menu-glyph desk-ask-check" aria-hidden="true">✓</span>
                  {kind !== "meetings" && kind !== "desk" ? <img src={kindGlyph(kind, row.ref)} alt="" width={16} height={16} draggable={false} /> : null}
                  <span className="desk-menu-label">{row.title}</span>
                </Button>
                <Button variant="chrome" className="desk-ask-scope-remove" aria-label={`Remove ${row.title}`} onClick={() => onRemove(row)}>✕</Button>
              </span>
            );
          })}
          {groups.map((group) => (
            <div key={group.key} className="desk-ask-scope-group">
              {group.caption ? <span className="desk-ask-scope-caption">{group.caption}</span> : null}
              {group.rows.map((c) => (
                <Button key={c.ref} variant="chrome" className="desk-ask-scope-row" role="menuitemradio" aria-checked="false"
                  data-testid="about-match" data-kind={c.kind} onClick={() => pick(c)}>
                  <span className="desk-menu-glyph desk-ask-check" aria-hidden="true" />
                  {c.kind !== "set" ? <img src={kindGlyph(c.kind === "zone" ? "directory" : c.kind, c.ref)} alt="" width={16} height={16} draggable={false} />
                    : <img src={kindGlyph("meeting", c.ref)} alt="" width={16} height={16} draggable={false} />}
                  <span className="desk-menu-label">{c.label}</span>
                  {c.ref === "meetings:this_week" && weekCount ? <span className="desk-ask-scope-meta">{weekCount}</span> : null}
                </Button>
              ))}
            </div>
          ))}
          {query.trim() && !groups.length ? <span className="desk-ask-scope-none">Nothing on this desk has that name</span> : null}
        </div>
      ) : null}
    </span>
  );
}

/* ── The Recent rail ─────────────────────────────────────────────────── */

export interface AskRailRow {
  id: string;
  title: string;
  /** The last turn's time (ISO, epoch ms or epoch seconds). */
  at?: unknown;
  /** Ask hub gap 5: an ask that has no answer yet says so (a dot + word). */
  state?: "writing" | "not_answered";
}

function toMs(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) return value < 1e12 ? value * 1000 : value;
  const parsed = Date.parse(String(value ?? ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

/** Today / Yesterday / This week / Earlier, by local day. */
export function railGroups(rows: readonly AskRailRow[], now = new Date()): Array<{ caption: string; rows: AskRailRow[] }> {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const day = 86_400_000;
  const order = ["Today", "Yesterday", "This week", "Earlier"];
  const groups = new Map<string, AskRailRow[]>();
  for (const row of [...rows].sort((a, b) => toMs(b.at) - toMs(a.at))) {
    const at = toMs(row.at);
    const caption = at >= today ? "Today" : at >= today - day ? "Yesterday" : at >= today - 6 * day ? "This week" : "Earlier";
    groups.set(caption, [...(groups.get(caption) ?? []), row]);
  }
  return order.filter((c) => groups.has(c)).map((caption) => ({ caption, rows: groups.get(caption)! }));
}

/** The Recent rail: + New ask ⌘N, then the kept asks grouped by day, the
 *  current one selected. It folds with the composer row's first button. */
export function AskRail({ rows, selectedId, onPick, onNew, loading, failed, onRetry, sheet }: {
  rows: readonly AskRailRow[];
  selectedId?: string | null;
  onPick: (id: string) => void;
  onNew: () => void;
  loading?: boolean;
  failed?: boolean;
  onRetry?: () => void;
  /** On a phone the rail opens as a sheet over the page. */
  sheet?: boolean;
}) {
  const groups = railGroups(rows);
  return (
    <nav className="desk-ask-rail" aria-label="Recent" data-testid="ask-recent" data-sheet={sheet || undefined}>
      <Button dense variant="ghost" className="desk-ask-rail-row desk-ask-rail-new" onClick={onNew}>
        <ToolGlyph kind="new" />
        <span className="desk-ask-rail-title">New ask</span>
        <span className="desk-ask-rail-key" aria-hidden="true">⌘N</span>
      </Button>
      {loading && !rows.length ? <span className="desk-ask-rail-note">Reading</span> : null}
      {failed ? (
        <span className="desk-ask-rail-note">
          <DotWord tone="warn">Recent not read</DotWord>
          {onRetry ? <Button dense variant="ghost" onClick={onRetry}>Try again</Button> : null}
        </span>
      ) : null}
      {groups.map((group) => (
        <div key={group.caption} className="desk-ask-rail-group" role="group" aria-label={group.caption}>
          <span className="desk-ask-rail-caption">{group.caption}</span>
          {group.rows.map((row) => (
            <Button key={row.id} dense variant="ghost" className="desk-ask-rail-row" aria-current={row.id === selectedId ? "true" : undefined}
              title={row.title} onClick={() => onPick(row.id)} data-state={row.state}>
              <span className="desk-ask-rail-title">{row.title}</span>
              {row.state ? (
                <DotWord tone={row.state === "writing" ? "info" : "warn"} className="desk-ask-rail-state">
                  {row.state === "writing" ? "Writing…" : "Not answered"}
                </DotWord>
              ) : null}
            </Button>
          ))}
        </div>
      ))}
    </nav>
  );
}

/* ── The answer as a document ────────────────────────────────────────── */

/** The page: it scrolls inside the window; the newest turn is at the foot. */
export function AskPage({ readingRef, children, testId, empty }: {
  readingRef: RefObject<HTMLDivElement | null>;
  children: ReactNode;
  testId?: string;
  empty?: boolean;
}) {
  return (
    <ScrollHint axis="y" scrollRef={readingRef} className="desk-ask-reading-wrap">
      <div
        ref={readingRef as Ref<HTMLDivElement>}
        className={`desk-ask-reading${empty ? " desk-ask-empty" : ""}`}
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

/** One turn: the question as the heading line with its age at the right,
 *  then the answer, its references and its verbs. A rule sits between
 *  turns. */
export function AskTurnDoc({ question, at, children, testId = "ask-turn" }: {
  question: string;
  at?: unknown;
  children?: ReactNode;
  testId?: string | null;
}) {
  const when = at == null ? "" : humanTime(typeof at === "number" && at < 1e12 ? at * 1000 : at);
  return (
    <li className="desk-ask-turn" data-testid={testId ?? undefined}>
      <h3 className="desk-ask-q">
        <span className="desk-ask-q-text">{question}</span>
        {when ? <span className="desk-ask-q-when">{when === "just now" ? "now" : when}</span> : null}
      </h3>
      {children}
    </li>
  );
}

export interface AskReferenceRowData {
  ref: string;
  title: string;
  /** The object kind (from the ref's prefix). */
  kind: string;
  /** Quiet words at the right: `Meeting · 2h ago`, `Direct report`. */
  meta?: string;
  /** A state lamp before the meta (`● Accepted`). */
  lamp?: "ok" | "warn" | "info" | "idle";
  /** Absent: the row only names what was read (a PR or a Jira item). */
  onOpen?: () => void;
}

/** References: what the answer read, as dense object rows that open their
 *  windows. A ref with no local record shows its title only. */
export function AskReferences({ rows }: { rows: readonly AskReferenceRowData[] }) {
  if (!rows.length) return null;
  return (
    <div className="desk-ask-refs" data-testid="ask-looked-at">
      <span className="desk-ask-refs-caption">References</span>
      {rows.map((row) => {
        const body = (
          <>
            <img src={kindGlyph(row.kind, row.ref)} alt="" width={16} height={16} draggable={false} />
            <span className="desk-ask-ref-title">{row.title}</span>
            {row.meta ? (
              <span className="desk-ask-ref-meta">
                {row.lamp ? <span className="kit-dot" data-tone={row.lamp} aria-hidden="true" /> : null}
                {row.meta}
              </span>
            ) : null}
          </>
        );
        return row.onOpen ? (
          <Button key={row.ref} dense variant="ghost" className="desk-ask-ref" data-ref={row.ref} onClick={row.onOpen}>{body}</Button>
        ) : (
          <span key={row.ref} className="desk-ask-ref" data-ref={row.ref} data-static="true">{body}</span>
        );
      })}
    </div>
  );
}

/** Ask hub gap 3: the quiet word in the answer's verbs row. It opens the
 *  list of the answer's claims and the records that support them (no inline
 *  marks: the hub sends no text offsets). */
export function AskGroundedWord({ records, open, onToggle }: { records: number; open: boolean; onToggle: () => void }) {
  if (!records) return null;
  return (
    <Button dense variant="ghost" className="desk-ask-basis" aria-expanded={open} onClick={onToggle} data-testid="ask-grounded">
      {records === 1 ? "Grounded in 1 record" : `Grounded in ${records} records`}
    </Button>
  );
}

/** The claims under an answer, each with the record that supports it. */
export function AskClaims({ claims, onOpen }: {
  claims: ReadonlyArray<{ text: string; ref?: string; title?: string; label: string }>;
  onOpen: (ref: string) => (() => void) | undefined;
}) {
  return (
    <ul className="desk-ask-basis-list" data-testid="ask-claims" aria-label="Claims and their records">
      {claims.map((claim, index) => {
        const open = claim.ref ? onOpen(claim.ref) : undefined;
        return (
          <li key={`${index}:${claim.text}`} className="desk-ask-basis-row" data-label={claim.label}>
            <span className="desk-ask-basis-text">{claim.text}</span>
            {claim.ref ? (
              open ? (
                <Button dense variant="ghost" className="desk-ask-basis-record" data-ref={claim.ref} onClick={open}>
                  <img src={kindGlyph(claim.ref.split(":", 1)[0], claim.ref)} alt="" width={16} height={16} draggable={false} />
                  {claim.title || "A source"}
                </Button>
              ) : <span className="desk-ask-basis-record" data-ref={claim.ref}>{claim.title || "A source"}</span>
            ) : null}
            {claim.label === "partial" ? <span className="desk-ask-basis-partial">In part</span> : null}
          </li>
        );
      })}
    </ul>
  );
}

/** The answer's verbs, in one row under it. */
export function AskVerbs({ children }: { children: ReactNode }) {
  return <div className="desk-ask-verbs" role="group" aria-label="Answer">{children}</div>;
}

/** ⋯ on an answer: the rarer verbs in a small menu under it. */
export function AskMore({ children, label = "More" }: { children: (close: () => void) => ReactNode; label?: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement | null>(null);
  const close = () => setOpen(false);
  useDismiss(open, ref, close);
  return (
    <span className="desk-ask-more" ref={ref}>
      <Button dense variant="ghost" className="desk-ask-more-press" aria-label={label} aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <MoreGlyph />
      </Button>
      {open ? <div className="desk-menu-list desk-ask-more-menu" role="group" aria-label={label}>{children(close)}</div> : null}
    </span>
  );
}

/** Ask D1's words for an Ask that did not answer: one line, why. */
export function askReasonLine(reason: string, fallbackWords: string): string {
  if (reason === "no_engine") return "No engine answers Ask yet.";
  if (reason === "timed_out") return "The engine did not answer in time.";
  if (reason === "did_not_answer") return "The engine did not answer.";
  if (reason === "not_reachable") return "The engine could not be reached.";
  return fallbackWords;
}

/** Not answered: ONE line under the question that says why, and the one
 *  verb that fixes it. The question is kept. Never red, never mono. */
export function AskNotAnswered({ reason, words, verb }: { reason: string; words: string; verb?: ReactNode }) {
  return (
    <div className="desk-ask-fail" data-testid="ask-not-answered" data-reason={reason} role="status">
      <DotWord tone={reason === "stopped" ? "idle" : "warn"}>{words}</DotWord>
      {verb}
    </div>
  );
}

/** A fresh Ask: no picture, no cards. "From your desk now" and the
 *  questions built from this desk, as plain links with their source at the
 *  right. A press fills the composer; it does not send. */
export function AskPrompts({ prompts, onPrompt }: { prompts: readonly AskPrompt[]; onPrompt: (text: string) => void }) {
  return (
    <div className="desk-ask-prompts">
      <span className="desk-ask-prompts-caption">From your desk now</span>
      {prompts.map((p) => (
        <Button key={p.key} dense variant="ghost" className="desk-ask-prompt" onClick={() => onPrompt(p.text)} aria-label={p.text}>
          <img src={kindGlyph(p.kind)} alt="" width={16} height={16} draggable={false} />
          <span className="desk-ask-prompt-text">{p.text}</span>
          {p.source ? <span className="desk-ask-prompt-source">{p.source}</span> : null}
        </Button>
      ))}
    </div>
  );
}
