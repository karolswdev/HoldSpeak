/** Phase 16 — THE INTERIOR KIT (COMPOSITOR.md §11, canvas
 *  `docs/internal/philo/phase-16/01-canvas/compositor.html`, the CSS block
 *  "THE INTERIOR KIT").
 *
 *  An internal app (Needs you, a Room, the Conductor, a meeting) is composed
 *  from the kit and nothing else, in this order: AppHead (with its
 *  StatusStrip) → FilterBar → Section → Ledger / IconGrid → AskWell → Foot.
 *
 *  This module holds the two species the library lacked: `AppHead` with its
 *  `StatusStrip`, and the `FilterBar` rail. The rest of the kit is the
 *  library's existing species in the new material: Section is
 *  `SurfaceSection` (`count`), Ledger is `SurfaceLedger` / `SurfaceLedgerRow`
 *  (`kind`, `meta`), IconGrid is `IconGrid` (`well`), AskWell is the
 *  `StringGadget` well (and the `AskWell` question that holds one), Foot is
 *  `SurfaceFooter`, Verb is the library `Button` (contract.md, "The interior
 *  kit").
 */
import { useContext, useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { createPortal } from "react-dom";
import type { ObjectTone } from "./objects/kinds";
import { FilterTokens, type FilterTokenOption } from "./FilterTokens";
import { FootSlotContext } from "./foot";
import { Button } from "../../components/signal/Signal";
// kit.css is imported by surface.css (the kit restyles live beside it).

/** One token of a StatusStrip: a lamp square and a word, a word alone, a
 *  word with a bold value, or a verb (the library Button). Never prose. */
export type StatusStripItem = {
  /** A stable key (default: the item's index). */
  key?: string;
  /** The lamp square before the word (8 px, 1 px ink border). */
  lamp?: ObjectTone;
  /** The word (`7 of 7 available`, `Checked just now`). */
  text?: ReactNode;
  /** A value drawn bold in ink after the word (`Status` **On track**). */
  value?: ReactNode;
  /** A verb in the strip (`Connect calendar`): the library Button. */
  verb?: ReactNode;
  /** Pass-through data-testid for the token. */
  testId?: string;
};

/** The status strip: tokens on one baseline (mono 12 upper), wrapping at a
 *  narrow width. An empty strip draws nothing. */
export function StatusStrip({
  items,
  className,
  "data-testid": testId,
}: {
  items: ReadonlyArray<StatusStripItem | null | false | undefined>;
  /** An extra class on the strip (a face's hook). */
  className?: string;
  "data-testid"?: string;
}) {
  const shown = items.filter((item): item is StatusStripItem => Boolean(item));
  if (!shown.length) return null;
  return (
    <div className={className ? `kit-strip ${className}` : "kit-strip"} data-testid={testId}>
      {shown.map((item, index) =>
        item.verb ? (
          <span key={item.key ?? index} className="kit-strip-verb" data-testid={item.testId}>
            {item.verb}
          </span>
        ) : (
          <span key={item.key ?? index} className="kit-strip-token" data-testid={item.testId}>
            {item.lamp ? <span className="kit-sq" data-tone={item.lamp} aria-hidden="true" /> : null}
            {item.text}
            {item.value != null ? (
              <>
                {item.text != null ? " " : null}
                <b>{item.value}</b>
              </>
            ) : null}
          </span>
        ),
      )}
    </div>
  );
}

/** The app head: the ONE big fact of the window (display 26/650, once per
 *  window) with the StatusStrip on the same baseline. */
export function AppHead({
  fact,
  children,
  as: Tag = "h2",
  className,
  "data-testid": testId,
  factTestId,
}: {
  /** The one big fact (`7 need you`, the Room's name, the meeting title). */
  fact: ReactNode;
  /** The StatusStrip (or nothing). */
  children?: ReactNode;
  /** The fact's element (default `h2`). */
  as?: "h1" | "h2" | "div";
  /** An extra class on the head (a face's hook). */
  className?: string;
  "data-testid"?: string;
  /** Pass-through data-testid for the fact element. */
  factTestId?: string;
}) {
  return (
    <div className={className ? `kit-apphead ${className}` : "kit-apphead"} data-testid={testId}>
      <Tag className="surface-display kit-disp" data-testid={factTestId}>
        {fact}
      </Tag>
      {children}
    </div>
  );
}

/** The filter rail: the FilterTokens strip (CycleGadgets on one rail; the
 *  active token is the selection blue, sunken) and a trailing verb group at
 *  the rail's right. One per window at most. Without `options` the rail
 *  holds only the trailing verbs. */
export function FilterBar({
  options,
  value,
  onChange,
  label,
  trailing,
  disabled,
  "data-testid": testId,
}: {
  options?: FilterTokenOption[];
  value?: string;
  onChange?(next: string): void;
  /** The strip's accessible name (e.g. "Drawer view"). */
  label: string;
  /** Verbs at the rail's right (library Buttons). */
  trailing?: ReactNode;
  disabled?: boolean;
  "data-testid"?: string;
}) {
  return (
    <div className="kit-filterbar" data-testid={testId}>
      {options && options.length && onChange ? (
        <FilterTokens
          options={options}
          value={value ?? ""}
          onChange={onChange}
          label={label}
          disabled={disabled}
        />
      ) : null}
      <span className="kit-filterbar-sp" aria-hidden="true" />
      {trailing ? <span className="kit-filterbar-trailing">{trailing}</span> : null}
    </div>
  );
}

/** Window grammar (2026-10-24) — the toolbar: a 36 px band directly under
 *  the title bar, a 1 px soft rule under it. Verbs (library Buttons; the
 *  quiet secondary form, ONE primary at most) sit at the left; the
 *  `trailing` slot (a search StringGadget, a filter) sits at the right. No
 *  headline, no count, no stat tiles. At a narrow width the band wraps and
 *  every Button keeps its 44 px target.
 *
 *  THE PRIMARY VERB (W1-KIT, 2026-10-27): a collection window's one blue
 *  verb is the verb that MAKES its object (Record meeting, New Project,
 *  New decision, Add person, Start an agent, Add an engine) — always, on an
 *  empty desk and a full one. A fix verb for a warning (Choose engine) and
 *  a selection's verbs are never the primary, and the primary never lives
 *  in the status bar.
 *
 *  The band carries an empty sort slot (`.kit-toolbar-sort`): on a narrow
 *  surface a dense ObjectList puts its "Sort" verb there in place of its
 *  column header. */
export function Toolbar({
  label,
  children,
  trailing,
  trailingStays = false,
  className,
  "data-testid": testId,
}: {
  /** The toolbar's accessible name (`Meetings`). */
  label: string;
  /** The verbs: library Buttons. */
  children?: ReactNode;
  /** The right slot: a search well or a filter. */
  trailing?: ReactNode;
  /** The trailing control is the band's own (the Note's mic), not a search
   *  well: it stays at the band's right end at every width instead of
   *  taking its own line at a narrow width. */
  trailingStays?: boolean;
  className?: string;
  "data-testid"?: string;
}) {
  return (
    <div
      role="toolbar"
      aria-label={label}
      className={className ? `kit-toolbar ${className}` : "kit-toolbar"}
      data-trailing={trailingStays ? "stays" : undefined}
      data-testid={testId}
    >
      <span className="kit-toolbar-verbs">{children}</span>
      <span className="kit-toolbar-sort" />
      {trailing ? <span className="kit-toolbar-trailing">{trailing}</span> : null}
    </div>
  );
}

/** The toolbar verb glyphs (window grammar: a verb is icon + label, the
 *  Workbench/Finder way). 16 px, a 1.5 px pen in the Workbench blue (paper
 *  on the primary); Record keeps its red dot. Decorative: the label names
 *  the verb. */
export type ToolGlyphKind =
  | "record" | "import" | "engine" | "new" | "summary" | "retry" | "open"
  | "note" | "ask" | "tasks" | "project" | "send" | "done" | "run" | "edit"
  | "copy";

const TOOL_PATHS: Record<Exclude<ToolGlyphKind, "record">, string> = {
  import: "M8 2.5v7M5 6.5l3 3 3-3M2.75 10.5v2.25h10.5V10.5",
  engine: "M5 4.5h6v7H5Z M6.5 2.5v2M9.5 2.5v2M6.5 11.5v2M9.5 11.5v2M3 6.5h2M3 9.5h2M11 6.5h2M11 9.5h2",
  new: "M8 3.5v9M3.5 8h9",
  summary: "M3 4h10M3 7h10M3 10h6M11.5 9.5l.9 1.8 1.8.9-1.8.9-.9 1.8-.9-1.8-1.8-.9 1.8-.9Z",
  retry: "M12.5 8a4.5 4.5 0 1 1-1.4-3.25M11.5 2.5v2.5H9",
  open: "M6.5 3H3v10h10V9.5M9 3h4v4M13 3L7.5 8.5",
  note: "M4 2.5h5.5L12 5v8.5H4Z M9.5 2.5V5H12 M6 8h4M6 10.5h4",
  ask: "M2.75 3.25h10.5v7H7.5l-3 2.5v-2.5H2.75Z M5.75 6.25h4.5M5.75 8.25h2.5",
  tasks: "M2.5 4.25l1.25 1.25L6 3.25 M2.5 10l1.25 1.25L6 9 M8.25 4.5h5.25M8.25 10.25h5.25",
  project: "M2.5 3.5h3.75l1.5 1.5h5.75v7.5h-11Z M2.5 7h11",
  send: "M13.5 2.5L2.5 7l4.5 2 2 4.5Z M7 9l6.5-6.5",
  done: "M3 8.5l3.25 3.25L13 4.75",
  run: "M5 3.25v9.5l7.75-4.75Z",
  edit: "M10.5 2.75l2.75 2.75L6 12.75H3.25V10Z M9 4.25l2.75 2.75",
  copy: "M5.5 5.5h7.25v7.75H5.5Z M3.25 10.5V2.75h7.25",
};

export function ToolGlyph({ kind }: { kind: ToolGlyphKind }) {
  return (
    <svg
      className="kit-toolglyph"
      data-kind={kind}
      width={16}
      height={16}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {kind === "record" ? (
        <>
          <circle cx="8" cy="8" r="5.75" />
          <circle cx="8" cy="8" r="3" className="kit-toolglyph-dot" stroke="none" />
        </>
      ) : (
        <path d={TOOL_PATHS[kind]} />
      )}
    </svg>
  );
}

/** A status-bar count in warm words: `5 meetings`, `1 meeting`; null at
 *  zero (UX-CANON A.8), so the StatusBar drops the item. `plural` defaults
 *  to the noun with an `s`. */
export function countWords(count: number, noun: string, plural = `${noun}s`): string | null {
  if (!Number.isFinite(count) || count <= 0) return null;
  return `${count} ${count === 1 ? noun : plural}`;
}

/** One item of a StatusBar: a word, a word with a bold value, a lamp dot
 *  before the word. Never prose; a count of zero is not an item (the caller
 *  drops it, UX-CANON A.8). */
export type StatusBarItem = {
  key?: string;
  /** The word (`5 meetings`, `No engine for summaries`), or a receipt node. */
  text?: ReactNode;
  /** A value drawn in ink after the word. */
  value?: ReactNode;
  /** A round lamp dot before the word, in its tone. */
  lamp?: ObjectTone;
  /** DELIGHT (2026-10-27): a value that changes when the moment happens
   *  (the Note passes its kept time). Each change AFTER the first paint
   *  pulses the lamp once: its ring opens and fades (600 ms, a lamp is not
   *  a control, so the still fence holds); instant under reduced motion. */
  pulse?: string | number | null;
  testId?: string;
};

/** The status bar's lamp: lit dots (ok, info, ask) glow (kit.css); a change
 *  of `pulse` after the first paint replays the pulse (a new key). */
function StatusLamp({ tone, pulse }: { tone: ObjectTone; pulse?: string | number | null }) {
  const seen = useRef(pulse);
  const [beat, setBeat] = useState(0);
  useEffect(() => {
    if (pulse == null || pulse === seen.current) return;
    seen.current = pulse;
    setBeat((count) => count + 1);
  }, [pulse]);
  return <span key={beat} className="kit-dot" data-tone={tone} data-pulse={beat ? "" : undefined} aria-hidden="true" />;
}

/** Window grammar (2026-10-24) — the status bar: a 24 px band at the
 *  window's foot, sans 12 muted: items separated by a middle dot at the
 *  left, the egress chip at the right (egress where egress happens). Inside
 *  a hosted window it is portaled into the frame's foot slot (as
 *  SurfaceFooter is); elsewhere it renders in place. With no item and no
 *  egress it draws nothing, and the empty foot folds away. */
export function StatusBar({
  items,
  egress,
  verbs,
  trailing,
  className,
  "data-testid": testId,
}: {
  items: ReadonlyArray<StatusBarItem | null | false | undefined>;
  egress?: ReactNode;
  /** A quiet fact at the bar's right end (`2 people · 1 decision`). */
  trailing?: ReactNode;
  /** The selection's verbs (library Buttons) at the right, before the
   *  egress chip: the bar grows from the foot, so nothing above moves. */
  verbs?: ReactNode;
  className?: string;
  "data-testid"?: string;
}) {
  const target = useContext(FootSlotContext);
  const shown = items.filter((item): item is StatusBarItem => Boolean(item) && (item as StatusBarItem).text != null);
  if (!shown.length && !egress && !verbs && !trailing) return null;
  const bar = (
    <div
      className={className ? `kit-statusbar ${className}` : "kit-statusbar"}
      data-testid={testId}
    >
      <span className="kit-statusbar-items" role="status">
        {shown.map((item, index) => (
          <span key={item.key ?? index} className="kit-statusbar-item" data-testid={item.testId}>
            {item.lamp ? <StatusLamp tone={item.lamp} pulse={item.pulse} /> : null}
            {item.text}
            {item.value != null ? (
              <>
                {item.text != null ? " " : null}
                <b>{item.value}</b>
              </>
            ) : null}
          </span>
        ))}
      </span>
      {verbs ? <span className="kit-statusbar-verbs">{verbs}</span> : null}
      {trailing ? <span className="kit-statusbar-trailing">{trailing}</span> : null}
      {egress ? <span className="kit-statusbar-egress">{egress}</span> : null}
    </div>
  );
  return target ? createPortal(bar, target) : <footer className="kit-statusbar-foot">{bar}</footer>;
}

/** Window grammar: a state fact as a dot and a sentence-case word
 *  (`● No engine for answers`), sans 12, no plate. `idle` (default) is the
 *  plain grey dot. The word names the state; the dot is never colour alone. */
export function DotWord({
  tone,
  children,
  className,
  "data-testid": testId,
}: {
  tone?: ObjectTone | "idle";
  children: ReactNode;
  className?: string;
  "data-testid"?: string;
}) {
  return (
    <span className={className ? `kit-dotword ${className}` : "kit-dotword"} data-tone={tone ?? "idle"} data-testid={testId}>
      <span className="kit-dot" data-tone={tone ?? "idle"} aria-hidden="true" />
      {children}
    </span>
  );
}

const KIND_WORDS: Record<string, string> = {
  meeting: "Meeting",
  mtg: "Meeting",
  decision: "Decision",
  dec: "Decision",
  action: "Action",
  act: "Action",
  commitment: "Action",
  cmt: "Action",
};

/** The kind plate of a LedgerRow: a raised Steel plate with a plain word on
 * mixed lists. Unknown kinds keep their existing short token because they
 * are not part of this shared words table. */
export function KindPlate({ kind, title }: { kind: string; title?: string }) {
  const word = KIND_WORDS[kind.trim().toLowerCase()] ?? kind;
  return (
    <span className="kit-kind" title={title} data-testid="kit-kind">
      {word}
    </span>
  );
}

/** PHILO-17 ALIVE: the initials of a person's name or address (`Avery
 *  Lin` → `AL`, `Avery` → `A`, `sam.ortiz@x.io` → `SO`). Two letters at most. */
export function initialsOf(name: string): string {
  const base = name.includes("@") ? name.split("@")[0] : name;
  const parts = base.split(/[\s._-]+/).filter(Boolean);
  if (!parts.length) return "?";
  const letters = parts.length === 1 ? parts[0][0] : parts[0][0] + parts[parts.length - 1][0];
  return letters.toUpperCase();
}

/** PHILO-17 ALIVE: one of eight soft hues, the same for the same name. */
export function hueOf(name: string): number {
  let hash = 0;
  for (let index = 0; index < name.length; index += 1) hash = (hash * 31 + name.charCodeAt(index)) | 0;
  return Math.abs(hash) % 8;
}

/** PHILO-17 ALIVE: a person's initials on a round tile in their own hue. */
export function Avatar({ name, size = "sm" }: { name: string; size?: "sm" | "md" }) {
  return (
    <span className="kit-avatar" data-hue={hueOf(name)} data-size={size} title={name} aria-hidden="true">
      {initialsOf(name)}
    </span>
  );
}

/** PHILO-17 ALIVE: the people of a row, as overlapped avatars (`max`
 *  tiles, then `+N`). The group's accessible name lists every person. */
export function AvatarStack({
  names,
  max = 4,
  "data-testid": testId,
}: {
  names: ReadonlyArray<string>;
  max?: number;
  "data-testid"?: string;
}) {
  const shown = names.filter(Boolean);
  if (!shown.length) return null;
  const extra = shown.length - max;
  return (
    <span className="kit-avatars" role="img" aria-label={`With ${shown.join(", ")}`} data-testid={testId}>
      {shown.slice(0, max).map((name) => (
        <Avatar key={name} name={name} />
      ))}
      {extra > 0 ? <span className="kit-avatar" data-more="" aria-hidden="true">+{extra}</span> : null}
    </span>
  );
}

/** PHILO-17 ALIVE: the app's accent tile: its pixel sprite on a rounded
 *  tile in the app's own hue (`--app-hue` on the window). Decorative. */
export function AppTile({ sprite, hue }: { sprite: string; hue: number }) {
  return (
    <span className="kit-apptile" aria-hidden="true" style={{ "--app-hue": hue } as CSSProperties}>
      <img src={`${import.meta.env.BASE_URL || "/_built/"}desk/sprites/32/${sprite}.png`} alt="" draggable={false} />
    </span>
  );
}

/** One figure of a FigureStrip: a number and its words, in a tone. */
export type Figure = { key: string; value: number; label: string; tone?: "ok" | "warn" | "danger" | "info" | "accent" };

/** PHILO-17 ALIVE: a strip of tinted figures (`5 meetings · 4 summaries ·
 *  1 failed`) under a caption. A figure of zero is not drawn (no counters
 *  of zero, UX-CANON A.8); a strip with no figure draws nothing. */
export function FigureStrip({
  caption,
  figures,
  "data-testid": testId,
}: {
  caption: string;
  figures: ReadonlyArray<Figure>;
  "data-testid"?: string;
}) {
  const shown = figures.filter((figure) => figure.value > 0);
  if (!shown.length) return null;
  return (
    <div className="kit-figures" data-testid={testId}>
      <span className="kit-figures-caption">{caption}</span>
      {shown.map((figure) => (
        <span key={figure.key} className="kit-figure" data-tone={figure.tone}>
          <b>{figure.value}</b> {figure.label}
        </span>
      ))}
    </div>
  );
}

/** One step of a Steps rail. */
export type Step = { key: string; label: string; state: "done" | "now" | "later" | "failed" };

/** PHILO-17 (the Today language): a sequence as raised square plates on a
 *  dotted pixel wire (Prep · Record · Summary · Send follow-up). The step
 *  that is now is lit (the selection blue, sunken); a done step is green
 *  with a check; a failed one is red. Words under each plate. */
export function Steps({ steps, label, "data-testid": testId }: { steps: ReadonlyArray<Step>; label: string; "data-testid"?: string }) {
  return (
    <ol className="kit-steps" aria-label={label} data-testid={testId}>
      {steps.map((step, index) => (
        <li key={step.key} className="kit-step" data-state={step.state} aria-current={step.state === "now" ? "step" : undefined}>
          <span className="kit-step-n" aria-hidden="true">{step.state === "done" ? "✓" : step.state === "failed" ? "!" : index + 1}</span>
          <span className="kit-step-word">{step.label}</span>
        </li>
      ))}
    </ol>
  );
}

const LOADING_WIDTHS = ["62%", "48%", "56%"];

/** Lane HUB TIMEOUTS (2026-10-27): a first read that has not answered in
 *  this long is said, never drawn as Loading for good. The owner's desk, away
 *  from his LAN, showed two windows Loading forever while the hub was held. */
export const NOT_ANSWERED_MS = 8000;

/** True when `active` (still reading) has lasted `ms`; false again when the
 *  read lands or restarts. `ms` 0 never times out. */
export function useNotAnswered(active: boolean, ms: number = NOT_ANSWERED_MS): boolean {
  const [late, setLate] = useState(false);
  useEffect(() => {
    setLate(false);
    if (!active || !(ms > 0)) return undefined;
    const timer = window.setTimeout(() => setLate(true), ms);
    return () => window.clearTimeout(timer);
  }, [active, ms]);
  return active && late;
}

/** The window's not-answered line: `● Not answering` and one verb, Try
 *  again (the caller's read again; without one, the desk reads again). The
 *  read that is still on its way still lands and replaces this line. */
export function NotAnswering({
  onRetry,
  "data-testid": testId,
}: {
  onRetry?: () => void;
  "data-testid"?: string;
}) {
  return (
    <div className="kit-not-answering" role="status" data-kind="not-answering" data-testid={testId ?? "not-answering"}>
      <DotWord tone="fail">Not answering</DotWord>
      <Button dense variant="secondary" onClick={onRetry ?? (() => window.location.reload())}>Try again</Button>
    </div>
  );
}

/** W1-KIT (2026-10-27) — THE LOADING FACE: a window's first read. The
 *  toolbar stays (the caller draws it first); the body shows ghost rows of
 *  the list grammar: 32 px rows, a glyph square and two pale steel bars. No
 *  spinner, no "Loading…" word on the glass, nothing moves (the sweep
 *  settles on `aria-busy`). Meetings, People, Projects, Decisions and the
 *  Room wear it. */
export function Loading({
  rows = 3,
  label = "Loading",
  timeout = NOT_ANSWERED_MS,
  onRetry,
  "data-testid": testId,
}: {
  rows?: number;
  /** The words a screen reader hears. */
  label?: string;
  /** After this many ms the face is the not-answered line (0: never). */
  timeout?: number;
  /** Try again on the not-answered line: the caller's read again. */
  onRetry?: () => void;
  "data-testid"?: string;
}) {
  const late = useNotAnswered(true, timeout);
  if (late) return <NotAnswering onRetry={onRetry} />;
  return (
    <div className="kit-loading" role="status" aria-busy="true" data-kind="loading" data-testid={testId}>
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }, (_, index) => (
        <span key={index} className="kit-loading-row" aria-hidden="true">
          <span className="kit-loading-glyph" />
          <span className="kit-loading-bar" style={{ width: LOADING_WIDTHS[index % LOADING_WIDTHS.length] }} />
          <span className="kit-loading-bar kit-loading-meta" />
        </span>
      ))}
    </div>
  );
}

/** W1-TRUTH (atlas 2026-10-27): a meeting's four steps, one list for
 *  Today and Live (Prep · Record · Summary · Send follow-up); `step` is the
 *  index of the step that is now. */
export const MEETING_STEPS = ["Prep", "Record", "Summary", "Send follow-up"] as const;

export function meetingSteps(step: number): Step[] {
  return MEETING_STEPS.map((label, index) => ({
    key: label, label, state: index < step ? "done" : index === step ? "now" : "later",
  }));
}
