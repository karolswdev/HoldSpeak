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
import type { CSSProperties, ReactNode } from "react";
import type { ObjectTone } from "./objects/kinds";
import { FilterTokens, type FilterTokenOption } from "./FilterTokens";
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
