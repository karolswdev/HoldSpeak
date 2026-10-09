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
import type { ReactNode } from "react";
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

/** The kind plate of a LedgerRow: a raised Steel plate (44 px) with the
 *  kind's short word (`CC`, `DEC`, `MTG`, `GH`). Its accessible word is the
 *  caller's (`title`); the plate itself is aria-hidden when `label` is set
 *  elsewhere. */
export function KindPlate({ kind, title }: { kind: string; title?: string }) {
  return (
    <span className="kit-kind" title={title} data-testid="kit-kind">
      {kind}
    </span>
  );
}
