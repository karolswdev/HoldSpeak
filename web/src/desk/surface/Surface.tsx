// HS-98-01 — the surface kit: the ONE way to build window content
// (DESIGN_SYSTEM.md, "The surface idiom"). Content sits directly on the
// window material — no nested cards, no page grids. Layout answers to
// the WINDOW via @container queries on .desk-surface-body; Signal
// controls (Button, inputs, Switch…) stay — this kit owns surfaces,
// not controls.
import {
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { CheckGadget, StringGadget } from "./gadgets";
import type { PaneGeometry } from "./XtermPane";
import { humanTime, presentValue } from "./format";
import { Disclosure } from "./patterns";
import { useRovingRows } from "./roving";
import { SPARSE_THRESHOLD } from "./sparse";
import "./surface.css";

/** The one verb bar, sticky at the surface top. Primary verbs live
 * here; everything else is a row verb. */
export function SurfaceVerbs({
  children,
  status,
  active,
}: {
  children?: ReactNode;
  /** A quiet leading slot (state chip, scope chip). */
  status?: ReactNode;
  /** HS-167-03 — the verb key rendered lit (aria-current="true"); the
   *  posture strip stamps the active posture. */
  active?: string;
}) {
  return (
    <div className="surface-verbs" data-active-verb={active || undefined}>
      {status ? <span className="surface-verbs-status">{status}</span> : null}
      <span className="surface-verbs-actions">{children}</span>
    </div>
  );
}

/** HS-167-03 — the project orientation band: name (the Primary type step),
 *  chip row, optional purpose (folds past 2 lines), outcome as a target
 *  token row, optional fold body, trailing token (e.g. read time). */
export function SurfaceIdentity({
  name,
  chips,
  purpose,
  outcome,
  fold,
  trailing,
  "data-testid": rootTestId,
  nameTestId,
}: {
  /** The project name, rendered at the Primary type step (15px/600). */
  name: string;
  /** Chip row: StateChips + tokens. Wraps at the narrow container. */
  chips: ReactNode;
  /** One line of the owner's purpose text. Folds past two lines via Disclosure. */
  purpose?: string;
  /** Rendered as a target token row (prepended with a target mark). */
  outcome?: string;
  /** Additional content inside a fold (Disclosure body). */
  fold?: ReactNode;
  /** A trailing token (e.g. the read-time label), right-aligned on the chip row. */
  trailing?: ReactNode;
  /** Pass-through data-testid for the root element. */
  "data-testid"?: string;
  /** Pass-through data-testid for the name element (glass readiness signal). */
  nameTestId?: string;
}) {
  return (
    <div className="surface-identity" data-testid={rootTestId ?? "surface-identity"}>
      <div className="surface-identity-name" data-testid={nameTestId}>{name}</div>
      <div className="surface-identity-chips">
        {chips}
        {trailing != null ? (
          <span className="surface-identity-trailing">{trailing}</span>
        ) : null}
      </div>
      {purpose ? (
        <Disclosure label="more" defaultOpen={true} variant="raw">
          <div className="surface-identity-purpose">{purpose}</div>
        </Disclosure>
      ) : null}
      {outcome ? (
        <div className="surface-identity-outcome">
          <span className="surface-identity-outcome-mark" aria-hidden="true">{"◎"}</span>
          <span>{outcome}</span>
        </div>
      ) : null}
      {fold ?? null}
    </div>
  );
}

/** A group on the window material: hairline + quiet label, never a
 * nested card. */
export function SurfaceSection({
  label,
  actions,
  children,
  className,
}: {
  label?: string;
  /** Quiet section-scoped verbs, right-aligned on the label line. */
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={className ? `surface-section ${className}` : "surface-section"}>
      {label || actions ? (
        <header className="surface-section-head">
          {label ? <h3>{label}</h3> : <span />}
          {actions}
        </header>
      ) : null}
      {children}
    </section>
  );
}

export function SurfaceRows({ children }: { children: ReactNode }) {
  return <ul className="surface-rows">{children}</ul>;
}

/** A dense honest row: title + detail, quiet meta, verbs revealed on
 * hover/focus (always present under coarse pointers). Pass `onOpen` to
 * make the row's body one press target. */
export function SurfaceRow({
  glyph,
  title,
  detail,
  meta,
  verbs,
  selected,
  onOpen,
  children,
  quiet,
  id,
  role,
  ariaSelected,
}: {
  glyph?: ReactNode;
  title: ReactNode;
  detail?: ReactNode;
  meta?: ReactNode;
  verbs?: ReactNode;
  selected?: boolean;
  onOpen?: () => void;
  children?: ReactNode;
  /** HS-102-04 — a row with nothing pending reads quieter than one
   * waiting on a verdict (composition rule 2's reviewing posture);
   * never the only signal (pair with `meta`, never color/weight alone). */
  quiet?: boolean;
  id?: string;
  role?: "option";
  ariaSelected?: boolean;
}) {
  const body = (
    <>
      {glyph ? <span className="surface-row-glyph">{glyph}</span> : null}
      <span className="surface-row-text">
        <strong>{title}</strong>
        {detail ? <small>{detail}</small> : null}
      </span>
      {meta ? <span className="surface-row-meta">{meta}</span> : null}
    </>
  );
  return (
    <li
      id={id}
      role={role}
      aria-selected={ariaSelected}
      className="surface-row"
      data-selected={selected || undefined}
      data-quiet={quiet || undefined}
    >
      <div className="surface-row-line">
        {onOpen ? (
          <button type="button" className="surface-row-open" onClick={onOpen}>
            {body}
          </button>
        ) : (
          <span className="surface-row-main">{body}</span>
        )}
        {verbs ? <span className="surface-row-verbs">{verbs}</span> : null}
      </div>
      {children}
    </li>
  );
}

/** Loading, empty, and error as ONE quiet treatment (rule 6). */
export function SurfaceState({
  loading,
  error,
  empty,
  emptyLabel = "Nothing yet",
  emptyGlyph = "○",
  emptyImage,
  emptyContent,
  onRetry,
  onAction,
  actionLabel,
  children,
}: {
  loading?: boolean;
  error?: string;
  empty?: boolean;
  emptyLabel?: string;
  emptyGlyph?: string;
  /** A pixel-sprite URL — the world's own objects carry the empty
   * state (wins over the glyph). */
  emptyImage?: string;
  /** Compact custom content inside the shared in-flow empty-state material. */
  emptyContent?: ReactNode;
  onRetry?: () => void;
  /** An optional in-flow action for the empty state. */
  onAction?: () => void;
  /** The visible label for the empty-state action. */
  actionLabel?: string;
  children?: ReactNode;
}) {
  if (loading)
    return (
      <div className="surface-state" data-kind="loading" role="status">
        <span className="surface-state-glyph" aria-hidden>
          ◌
        </span>
        <span className="sr-only">Loading</span>
      </div>
    );
  if (error)
    return (
      <div className="surface-state" data-kind="error" role="alert">
        <span className="surface-state-glyph" aria-hidden>
          ⚠︎
        </span>
        <span>{error}</span>
        {onRetry ? (
          <Button dense variant="ghost" onClick={onRetry}>
            Try again
          </Button>
        ) : null}
      </div>
    );
  if (empty)
    return (
      <div className="surface-state" data-kind="empty">
        {emptyContent ?? <>
          {emptyImage ? (
            <img
              className="surface-state-sprite"
              src={emptyImage}
              alt=""
              aria-hidden
            />
          ) : (
            <span className="surface-state-glyph" aria-hidden>
              {emptyGlyph}
            </span>
          )}
          <span>{emptyLabel}</span>
          {onAction && actionLabel ? (
            <button
              type="button"
              className="desk-chip surface-state-action"
              onClick={onAction}
            >
              {actionLabel}
            </button>
          ) : null}
        </>}
      </div>
    );
  return children;
}

/** Two groups sharing the width when the WINDOW is wide, stacked when
 * narrow — the direct replacement for the page grid's span-8/span-4. */
export function SurfaceColumns({
  main,
  side,
}: {
  main: ReactNode;
  side: ReactNode;
}) {
  return (
    <div className="surface-columns">
      <div className="surface-columns-main">{main}</div>
      <div className="surface-columns-side">{side}</div>
    </div>
  );
}

/** Master–detail that answers to the WINDOW: two panes when the
 * surface container is wide and the detail is open; the detail
 * replaces the master when narrow. The detail slot owns its own back/
 * close verb. */
export function SurfaceSplit({
  main,
  detail,
  detailOpen,
}: {
  main: ReactNode;
  detail?: ReactNode;
  detailOpen?: boolean;
}) {
  return (
    <div
      className={
        detailOpen && detail ? "surface-split surface-split-open" : "surface-split"
      }
    >
      <div className="surface-split-main">{main}</div>
      {detailOpen && detail ? (
        <div className="surface-split-detail">{detail}</div>
      ) : null}
    </div>
  );
}

/** A quiet strip of labeled figures. Items whose value presents empty
 * are omitted (rule 4), never rendered as zeros-theater.
 * HS-135-04 L10 — below SPARSE_THRESHOLD zero-value tiles also
 * collapse (a strip of zeros over 3 items is noise). */
export function MetricStrip({
  items,
  itemCount,
}: {
  items: Array<{ label: string; value: unknown }>;
  /** HS-135-04 L10 — the total item count the surface holds.  Below
   *  SPARSE_THRESHOLD zero-valued metric tiles are hidden. */
  itemCount?: number;
}) {
  const sparse = itemCount !== undefined && itemCount < SPARSE_THRESHOLD;
  const kept = items.filter((item) => {
    const text = presentValue(item.value);
    if (text === "") return false;
    // L10: below threshold, collapse zero-value tiles.
    if (sparse && (text === "0" || Number(text) === 0)) return false;
    return true;
  });
  if (!kept.length) return null;
  return (
    <div className="surface-metrics">
      {kept.map((item) => (
        <div key={item.label}>
          <strong>{presentValue(item.value)}</strong>
          <small>{item.label}</small>
        </div>
      ))}
    </div>
  );
}

/** A wire object as honest fact rows (rule 4): keys de-snaked, values
 * through presentValue — meaningless entries OMITTED, never "—". */
export function SurfaceFacts({
  value,
  limit = 18,
}: {
  value: unknown;
  limit?: number;
}) {
  if (!value || typeof value !== "object") {
    const text = presentValue(value);
    return text ? <p className="surface-fact-line">{text}</p> : null;
  }
  const entries = Object.entries(value as Record<string, unknown>)
    .filter(([, item]) =>
      ["string", "number", "boolean"].includes(typeof item),
    )
    .map(([key, item]) => {
      // Rule 4 — a time-shaped value renders as a human phrase.
      const timeish =
        typeof item === "string" && /^\d{4}-\d{2}-\d{2}[T ]/.test(item)
          ? humanTime(item)
          : "";
      return [key, timeish || presentValue(item)] as const;
    })
    .filter(([, text]) => text !== "")
    .slice(0, limit);
  if (!entries.length) return null;
  return (
    <dl className="surface-facts">
      {entries.map(([key, text]) => (
        <div key={key}>
          <dt>{deSnakeLabel(key)}</dt>
          <dd>{text}</dd>
        </div>
      ))}
    </dl>
  );
}

function deSnakeLabel(key: string): string {
  return key.replace(/[_-]+/g, " ");
}

/** A raw trace (JSON, hook output) on the surface material. */
export function SurfaceCode({ children }: { children: ReactNode }) {
  return <pre className="surface-code">{children}</pre>;
}

/** HS-111-03 — the sunken well (audit §3.2): a scrolling inset on the
 * window-well tone with an inset etch (never a border rail). The
 * record's body reads INSIDE the machine: transcripts, routing
 * receipts, run logs, kernel ledgers. The head slot is a mono token
 * line ("TRANSCRIPT · 4 SEG"), never a sentence. */
export function SurfaceWell({
  head,
  children,
}: {
  /** Mono token line etched on the well's lip. */
  head?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="surface-well">
      {head ? <div className="surface-well-head">{head}</div> : null}
      <div className="surface-well-body">{children}</div>
    </div>
  );
}

/** HS-111-06/11 — the shared pane mount (audit §3.4): ONE seam over
 * the sunken pane well, consumed by BOTH the session pullout and the
 * delivery terminal, so both inherit every interior by construction.
 * HS-111-11 made the interior a real terminal: raw ANSI renders
 * through xterm.js (lazy chunk — the desk's first paint never pays
 * for an emulator) with scrollback search and copy-on-select; when
 * the wire cannot give raw (older hub, stripped-only consumer) the
 * mono pre face stays, named honestly in the head. The terminal is a
 * VIEWER — no keystroke here ever reaches a pane; typing goes through
 * the armed steer composer only (Article XI / Phase 87 law). */

const XtermPane = lazy(() => import("./XtermPane"));

/** The last-change age as a mono token — the operator's staleness
 * glance. Ticks locally; the poll only moves the anchor. */
function AgeToken({ changedAt }: { changedAt: number }) {
  const [, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 1_000);
    return () => clearInterval(t);
  }, []);
  const seconds = Math.max(0, Math.floor((Date.now() - changedAt) / 1000));
  const face =
    seconds < 60
      ? `${seconds}S`
      : `${Math.floor(seconds / 60)}M ${String(seconds % 60).padStart(2, "0")}S`;
  return <span className="surface-token">Δ {face}</span>;
}

export function PaneWell({
  live,
  lines,
  absence,
  raw,
  pane,
  changedAt,
}: {
  /** The pane renders while the peek is live/resyncing. */
  live: boolean;
  lines: string[];
  /** The absence face content (✕ token + typed detail). */
  absence?: ReactNode;
  /** The raw ANSI snapshot (HS-111-11). null/undefined = the wire is
   * stripped-only; the pre face renders with the honest head token. */
  raw?: string | null;
  /** tmux pane geometry + cursor when the raw wire names it. */
  pane?: PaneGeometry | null;
  /** Epoch ms of the last content change — the Δ fact in the head. */
  changedAt?: number | null;
}) {
  const preRef = useRef<HTMLPreElement | null>(null);
  const [query, setQuery] = useState("");
  const [seq, setSeq] = useState(0);
  // The newest output is the point of a peek: follow the tail.
  useEffect(() => {
    const pre = preRef.current;
    if (pre) pre.scrollTop = pre.scrollHeight;
  }, [lines]);
  if (!live) return <p className="desk-session-state">{absence}</p>;
  const hasRaw = raw !== null && raw !== undefined;
  const lineCount = hasRaw ? raw.split("\n").length : lines.length;
  return (
    <div className="terminal-well">
      <div className="terminal-well-head">
        <span className="surface-token">
          {hasRaw ? "RAW" : "STRIPPED · RAW UNAVAILABLE"}
        </span>
        <span className="surface-token">LINES {lineCount}</span>
        {changedAt ? <AgeToken changedAt={changedAt} /> : null}
        {hasRaw ? (
          <span className="terminal-well-find">
            <StringGadget
              label="Find in scrollback"
              value={query}
              placeholder="FIND"
              onChange={setQuery}
              onKeyDown={(e) => {
                if (e.key === "Enter" && query) setSeq((n) => n + 1);
              }}
            />
          </span>
        ) : null}
      </div>
      {hasRaw ? (
        // The screen tone is set on the frame BEFORE xterm opens — the
        // suspense gap and the mount both paint the same opaque well.
        <Suspense fallback={<div className="terminal-well-screen" />}>
          <XtermPane raw={raw} pane={pane} search={{ query, seq }} />
        </Suspense>
      ) : (
        <pre ref={preRef} className="desk-session-pane">
          {lines.join("\n")}
        </pre>
      )}
    </div>
  );
}

/** HS-111-04 — the transmission log (audit §3, optional species): a
 * SurfaceWell whose body is prefixed mono turn blocks (`YOU>` /
 * `<NAME>>`), a verbs slot per turn, no bubbles, no animation.
 * Reusable by Ask answers and the delivery terminal later. */
export function SurfaceTraffic({
  head,
  empty = "NO TRAFFIC",
  showEmpty,
  children,
}: {
  /** Mono token line etched on the well's lip. */
  head?: ReactNode;
  empty?: string;
  /** The caller knows whether traffic exists (children may include a
   * busy meter while a reply is inbound). */
  showEmpty?: boolean;
  children?: ReactNode;
}) {
  return (
    <div className="surface-traffic">
      <SurfaceWell head={head}>
        {showEmpty ? (
          <div className="surface-traffic-empty">{empty}</div>
        ) : (
          children
        )}
      </SurfaceWell>
    </div>
  );
}

export function SurfaceTrafficTurn({
  prefix,
  error,
  meta,
  verbs,
  children,
}: {
  /** The mono handle prefix (`YOU>`, `SCOUT>`). */
  prefix: ReactNode;
  /** An error turn keeps the ✕ token beside its prefix. */
  error?: boolean;
  /** Fact tokens riding the turn (egress chip, model). */
  meta?: ReactNode;
  /** Verbs riding the line (KEEP). */
  verbs?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="surface-traffic-turn" data-error={error || undefined}>
      <span className="surface-traffic-prefix">
        {error ? <span className="surface-traffic-x">✕ </span> : null}
        {prefix}
      </span>
      <div className="surface-traffic-text">{children}</div>
      {meta || verbs ? (
        <div className="surface-traffic-meta">
          {meta}
          {verbs ? <span className="surface-row-verbs">{verbs}</span> : null}
        </div>
      ) : null}
    </div>
  );
}

/** A grouped inset list on the rail tone — the OS settings idiom:
 * rows divided by hairlines inside one rounded container, never a
 * form stack. */
export function SurfaceGroup({
  label,
  children,
}: {
  label?: string;
  children: ReactNode;
}) {
  return (
    <section className="surface-group-wrap">
      {label ? <h3 className="surface-group-label">{label}</h3> : null}
      <div className="surface-group">{children}</div>
    </section>
  );
}

/** One setting: icon + label + quiet description on the LEFT, a
 * compact control on the RIGHT (`wide` stacks the control under the
 * text for editors). */
export function SurfaceSettingRow({
  icon,
  label,
  description,
  control,
  wide,
}: {
  icon?: ReactNode;
  label: ReactNode;
  description?: ReactNode;
  control: ReactNode;
  wide?: boolean;
}) {
  return (
    <div className={wide ? "surface-setting-row is-wide" : "surface-setting-row"}>
      {icon ? <span className="surface-setting-icon">{icon}</span> : null}
      <span className="surface-setting-text">
        <strong>{label}</strong>
        {description ? <small>{description}</small> : null}
      </span>
      <span className="surface-setting-control">{control}</span>
    </div>
  );
}

/** A bare boolean for row-right placement (the row carries the label).
 * HS-111-01: the sliding toggle species is dead — this IS the checkbox
 * gadget, everywhere (audit §3.3/§4 blast radius). */
export function SurfaceToggle({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  checked: boolean;
  onChange(next: boolean): void;
  disabled?: boolean;
}) {
  return (
    <CheckGadget
      label={label}
      checked={checked}
      onChange={onChange}
      disabled={disabled}
    />
  );
}

/** HS-101 rule 2 — the dated stream: the composition for material
 * that happens over time (the Journal). A head that leads with the
 * one big fact, day bands, entries whose TEXT is the material at the
 * primary step, verbs revealed on the entry. */
export function SurfaceStream({
  count,
  countLabel,
  controls,
  children,
}: {
  count: ReactNode;
  countLabel?: ReactNode;
  controls?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="surface-stream">
      <div className="surface-stream-head">
        <span className="surface-display">{count}</span>
        {countLabel ? (
          <small className="surface-stream-count-label">{countLabel}</small>
        ) : null}
        {controls ? (
          <span className="surface-stream-controls">{controls}</span>
        ) : null}
      </div>
      {children}
    </div>
  );
}

export function SurfaceStreamDay({
  label,
  children,
}: {
  label: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="surface-stream-day">
      <h4 className="surface-stream-day-label">{label}</h4>
      <ul className="surface-stream-entries">{children}</ul>
    </section>
  );
}

export function SurfaceStreamEntry({
  when,
  meta,
  verbs,
  aside,
  children,
}: {
  when?: ReactNode;
  meta?: ReactNode;
  verbs?: ReactNode;
  /** Below-the-entry material (a receipt, a preview) — sits beside
   * the said-text in the grid, not inside it. */
  aside?: ReactNode;
  children: ReactNode;
}) {
  return (
    <li className="surface-stream-entry">
      {when != null ? (
        <span className="surface-stream-when">{when}</span>
      ) : null}
      <div className="surface-stream-said">{children}</div>
      {meta || verbs ? (
        <div className="surface-stream-meta">
          {meta}
          {verbs ? (
            <span className="surface-stream-verbs surface-row-verbs">
              {verbs}
            </span>
          ) : null}
        </div>
      ) : null}
      {aside}
    </li>
  );
}

/** HS-111-02 — the machine ledger (audit §3.2): columnar mono rows for
 * events over time. One line per event, full-width hover band, click
 * opens the row IN PLACE (the tracker's cursor line — sunken fill);
 * exactly one row open is the CALLER's contract. SurfaceStream stays
 * the said-text composition (LiveCore); this is the machine-rows one.
 * Reused by: dictation Journal, History, Activity, run histories. */
export function SurfaceLedger({
  count,
  controls,
  cols,
  children,
}: {
  /** The head's mono token line (e.g. "TODAY 2 · TAUGHT 1"). */
  count: ReactNode;
  controls?: ReactNode;
  /** HS-111-03 — a named column template (CSS `data-cols` hook), never
   * a second ledger component. */
  cols?: string;
  children: ReactNode;
}) {
  // HS-111-08 — roving focus is kit law: ONE Tab stop for the whole
  // ledger, arrows walk rows; every consumer inherits (audit §3.1).
  const rootRef = useRef<HTMLDivElement>(null);
  useRovingRows(rootRef, { selector: ".surface-ledger-line" });
  return (
    <div ref={rootRef} className="surface-ledger" data-cols={cols}>
      <div className="surface-ledger-head">
        <span className="surface-ledger-count">{count}</span>
        {controls ? (
          <span className="surface-ledger-controls">{controls}</span>
        ) : null}
      </div>
      {children}
    </div>
  );
}

export function SurfaceLedgerRow({
  time,
  lead,
  primary,
  cells,
  trailing,
  wrap,
  open,
  onToggle,
  onLineKeyDown,
  onLineContextMenu,
  lineLabel,
  expands = true,
  children,
  "data-testid": dataTestId,
}: {
  /** The fixed leading time token (HH:MM). */
  time?: ReactNode;
  /** HS-111-07 — an alternate leading token (the desk face's [x]
   * selection mark); rides the time slot's geometry. */
  lead?: ReactNode;
  /** The one-line mono material (ellipsized, never wrapped). */
  primary: ReactNode;
  /** Trailing fact cells (destination, ms, taught chip). */
  cells?: ReactNode;
  /** HS-167-03 — a quiet verb or chevron, right-aligned after cells
   *  (its own grid slot, never overlapping the 52px time column). */
  trailing?: ReactNode;
  /** HS-167-03 — when true the primary wraps instead of ellipsizing;
   *  at the narrow container cells fall under. */
  wrap?: boolean;
  open?: boolean;
  onToggle?: () => void;
  /** HS-111-07 — row keyboard verbs (Space = Ask-context on the desk
   * face); the caller owns the grammar. */
  onLineKeyDown?: (e: React.KeyboardEvent<HTMLButtonElement>) => void;
  onLineContextMenu?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  lineLabel?: string;
  /** false = the row is a plain verb line (no aria-expanded claim). */
  expands?: boolean;
  /** The in-place expansion rendered while open. */
  children?: ReactNode;
  "data-testid"?: string;
}) {
  return (
    <li className="surface-ledger-row" data-open={open || undefined} data-wrap={wrap || undefined}>
      <button
        type="button"
        className="surface-ledger-line"
        data-testid={dataTestId}
        data-has-trailing={trailing != null || undefined}
        aria-expanded={expands ? open || false : undefined}
        aria-label={lineLabel}
        onClick={onToggle}
        onKeyDown={onLineKeyDown}
        onContextMenu={onLineContextMenu}
      >
        {time != null ? (
          <span className="surface-ledger-time">{time}</span>
        ) : null}
        {lead != null ? (
          <span className="surface-ledger-lead">{lead}</span>
        ) : null}
        <span className="surface-ledger-primary">{primary}</span>
        {cells}
        {trailing != null ? (
          <span className="surface-ledger-trailing">{trailing}</span>
        ) : null}
      </button>
      {open && children ? (
        <div className="surface-ledger-open">{children}</div>
      ) : null}
    </li>
  );
}

/** HS-101 rule 2 — the library: the composition for a shelf of kept
 * material (Blocks). Tiles wear their PAYLOAD as the face; the name
 * and provenance ride the spine; create is a ghost tile in the
 * shelf, never a side form. */
export function SurfaceLibrary({
  count,
  countLabel,
  token,
  controls,
  children,
}: {
  count: ReactNode;
  countLabel?: ReactNode;
  /** HS-111-03 — a mono count token head ("15 ARTIFACTS") in place of
   * the display numeral (the receipt shelf's grammar). */
  token?: ReactNode;
  controls?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="surface-library-wrap">
      <div className={token ? "surface-ledger-head" : "surface-stream-head"}>
        {token ? (
          <span className="surface-ledger-count">{token}</span>
        ) : (
          <>
            <span className="surface-display">{count}</span>
            {countLabel ? (
              <small className="surface-stream-count-label">{countLabel}</small>
            ) : null}
          </>
        )}
        {controls ? (
          <span className="surface-stream-controls">{controls}</span>
        ) : null}
      </div>
      <ul className="surface-library">{children}</ul>
    </div>
  );
}

export function SurfaceLibraryTile({
  face,
  name,
  lamp,
  says,
  stamp,
  variant,
  verbs,
}: {
  /** The payload rendered AS the tile's face (rule 2). */
  face: ReactNode;
  name: ReactNode;
  /** Never color-only — pair with the name it describes. */
  lamp?: ReactNode;
  says?: ReactNode;
  /** HS-111-03 — the receipt's mono index line ("ART 03 · DECISION ·
   * 21:31") stamped on the spine. */
  stamp?: ReactNode;
  /** "receipt" scopes the receipt dress so Blocks is unaffected. */
  variant?: "receipt";
  verbs?: ReactNode;
}) {
  return (
    <li className="surface-tile" data-variant={variant}>
      <div className="surface-tile-face">{face}</div>
      <div className="surface-tile-spine">
        {stamp ? <div className="surface-tile-stamp">{stamp}</div> : null}
        <div className="surface-tile-name surface-primary">
          {name}
          {lamp}
        </div>
        {says ? <div className="surface-tile-says">{says}</div> : null}
      </div>
      {verbs ? <div className="surface-row-verbs">{verbs}</div> : null}
    </li>
  );
}

export function SurfaceLibraryGhost({
  label,
  hint,
  onCreate,
}: {
  label: ReactNode;
  hint?: ReactNode;
  onCreate: () => void;
}) {
  return (
    <li className="surface-tile surface-tile-ghost">
      <button type="button" className="surface-tile-ghost-btn" onClick={onCreate}>
        <span className="surface-tile-ghost-plus" aria-hidden="true">
          ＋
        </span>
        <span>{label}</span>
        {hint ? <small>{hint}</small> : null}
      </button>
    </li>
  );
}

/** HS-101 rule 2 — the switchboard: the composition for routing
 * material (Runs on). One bay per destination; the route bay leads
 * with its model at display step; lamps are never color-only; the
 * boundary badge sits ON the bay, at the point of decision. */
export function SurfaceSwitchboard({ children }: { children: ReactNode }) {
  return <ul className="surface-switchboard">{children}</ul>;
}

export function SurfaceBay({
  route,
  lamp,
  name,
  state,
  model,
  where,
  badge,
  tag,
  verbs,
  expanded,
  editor,
  ghost,
  onClick,
}: {
  /** True on THE current route — the bay that leads. */
  route?: boolean;
  lamp?: ReactNode;
  name?: ReactNode;
  /** Short liveness text beside the name (never color alone). */
  state?: ReactNode;
  model?: ReactNode;
  where?: ReactNode;
  badge?: ReactNode;
  tag?: ReactNode;
  verbs?: ReactNode;
  /** HS-102-01 — the bay IS the editor while true: the summary row
   * (name/model/where/badge) yields to `editor` in place, spanning
   * the switchboard's full width. No separate form section. */
  expanded?: boolean;
  editor?: ReactNode;
  /** A dashed, low-emphasis bay for the switchboard's "add" affordance
   * (never a floating header button for the same act). */
  ghost?: boolean;
  onClick?: () => void;
}) {
  if (expanded) {
    return (
      <li className="surface-bay surface-bay-expanded">
        <div className="surface-bay-editor">{editor}</div>
      </li>
    );
  }
  return (
    <li
      className={
        (route ? "surface-bay surface-bay-route" : "surface-bay") +
        (ghost ? " surface-bay-ghost" : "")
      }
      {...(ghost && onClick
        ? {
            role: "button",
            tabIndex: 0,
            onClick,
            onKeyDown: (event: KeyboardEvent<HTMLLIElement>) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onClick();
              }
            },
          }
        : {})}
    >
      <div className="surface-bay-main">
        <div className="surface-bay-who surface-primary">
          {lamp}
          {name}
          {state ? <span className="surface-bay-state">{state}</span> : null}
        </div>
        {model ? <div className="surface-bay-model">{model}</div> : null}
        {where ? <div className="surface-bay-where">{where}</div> : null}
      </div>
      <div className="surface-bay-side">
        {badge}
        {tag ? <span className="surface-bay-tag">{tag}</span> : null}
        {verbs ? <span className="surface-row-verbs">{verbs}</span> : null}
      </div>
    </li>
  );
}

/** HS-101 rule 1 — data is the material: the presented text IS the
 * editor. Click or Enter swaps it for a same-geometry editor;
 * Enter/blur commits, Escape reverts. A value that cannot be edited
 * stays presented and names why (never a bare disabled input). */
export function EditInPlace({
  value,
  onCommit,
  label,
  disabledReason,
  multiline,
  className,
  mic = true,
}: {
  value: string;
  onCommit: (next: string) => void | Promise<void>;
  label: string;
  disabledReason?: string;
  multiline?: boolean;
  className?: string;
  /** HS-111-08 — every text editor carries the speak-to-fill mic
   * (mic law); false only where a host renders its own. */
  mic?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const editorRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(
    null,
  );
  const commit = () => {
    setEditing(false);
    const next = draft.trim();
    if (next && next !== value) void onCommit(next);
    else setDraft(value);
  };
  const revert = () => {
    setDraft(value);
    setEditing(false);
  };
  const cx = ["surface-edit-in-place", className].filter(Boolean).join(" ");
  if (disabledReason) {
    return (
      <span
        className={`${cx} is-locked`}
        title={disabledReason}
        aria-label={`${label}: ${disabledReason}`}
      >
        {value}
      </span>
    );
  }
  if (!editing) {
    return (
      <button
        type="button"
        className={cx}
        aria-label={`Edit ${label}`}
        onClick={() => {
          setDraft(value);
          setEditing(true);
        }}
      >
        {value}
      </button>
    );
  }
  const shared = {
    className: `${cx} is-editing`,
    "aria-label": label,
    value: draft,
    autoFocus: true,
    // Placeholder-shaped values ("No knowledge yet. Click to add.")
    // ride the same `value` prop as real content; select it on focus
    // so typing REPLACES the placeholder instead of appending after it.
    onFocus: (event: { target: HTMLInputElement | HTMLTextAreaElement }) =>
      event.target.select(),
    // Pressing the in-place mic must not commit-and-close under the
    // speaker's finger — the mic is part of the editor.
    onBlur: (event: { relatedTarget: EventTarget | null }) => {
      const next = event.relatedTarget as HTMLElement | null;
      if (next?.closest?.(".surface-edit-mic")) return;
      commit();
    },
    onKeyDown: (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        revert();
      } else if (event.key === "Enter" && !(multiline && event.shiftKey)) {
        event.preventDefault();
        commit();
      }
    },
  };
  const editor = multiline ? (
    <textarea
      {...shared}
      ref={(node) => {
        editorRef.current = node;
      }}
      rows={Math.max(2, draft.split("\n").length)}
      onChange={(event) => setDraft(event.target.value)}
    />
  ) : (
    <input
      {...shared}
      ref={(node) => {
        editorRef.current = node;
      }}
      onChange={(event) => setDraft(event.target.value)}
    />
  );
  if (!mic) return editor;
  return (
    <span className="surface-edit-wrap">
      {editor}
      <span className="surface-edit-mic">
        <MicButton
          label={`Speak ${label}`}
          onText={(text) => {
            setDraft(text);
            editorRef.current?.focus();
          }}
        />
      </span>
    </span>
  );
}

/** The inline two-step for destructive verbs (rule 5): first press
 * arms, second fires; arming self-disarms. Never a modal. */
export function ConfirmVerb({
  label,
  confirmLabel = "Sure?",
  ariaLabel,
  busy,
  disabled,
  onConfirm,
}: {
  label: ReactNode;
  confirmLabel?: ReactNode;
  /** A stable accessible name when the visible label is a glyph (×). */
  ariaLabel?: string;
  busy?: boolean;
  disabled?: boolean;
  onConfirm: () => void;
}) {
  const [armed, setArmed] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);
  return (
    <Button
      dense
      variant={armed ? "danger" : "ghost"}
      aria-label={ariaLabel}
      loading={busy}
      disabled={disabled}
      onClick={() => {
        if (armed) {
          clearTimeout(timer.current);
          setArmed(false);
          onConfirm();
          return;
        }
        setArmed(true);
        timer.current = setTimeout(() => setArmed(false), 3000);
      }}
    >
      {armed ? confirmLabel : label}
    </Button>
  );
}

/* ══════════════════════════════════════════════════════════════════════
   HS-167-03 — ScrollHint: gradient edge fades for scrolling wells.
   ONE species, axis prop. Promoted from DoorBoardLane (horizontal) and
   steward/model.ts (vertical) — both copies deleted, this is canonical.
   ══════════════════════════════════════════════════════════════════════ */

/** The four overflow states for a scroll-hint edge fade. */
export type ScrollHintState = "none" | "start" | "end" | "both";

/** Pure function: derive a scroll-hint from viewport geometry.
 *  Works for both axes — the caller passes the scroll offset, total
 *  scrollable extent, and visible extent. The 20px tolerance absorbs
 *  scrollbar-gutter: stable both-edges. */
export function computeScrollHint(
  scrollOffset: number,
  scrollExtent: number,
  clientExtent: number,
): ScrollHintState {
  if (scrollExtent <= clientExtent) return "none";
  const atStart = scrollOffset <= 0;
  const atEnd = scrollOffset + clientExtent >= scrollExtent - 20;
  if (atStart && atEnd) return "none";
  if (atStart) return "end";
  if (atEnd) return "start";
  return "both";
}

/** Map the axis-neutral ScrollHintState to the data attribute values
 *  the CSS expects (left/right for x, top/bottom for y). */
function hintToAttr(hint: ScrollHintState, axis: "x" | "y"): string {
  if (hint === "none" || hint === "both") return hint;
  if (axis === "x") return hint === "start" ? "left" : "right";
  return hint === "start" ? "top" : "bottom";
}

/** HS-167-03 — the scroll-hint hook: attaches scroll and resize
 *  listeners and sets `data-scroll-hint` on the wrapper element. */
export function useScrollHint(
  wrapRef: React.RefObject<HTMLElement | null>,
  scrollRef: React.RefObject<HTMLElement | null> | null,
  axis: "x" | "y",
) {
  useEffect(() => {
    const wrap = wrapRef.current;
    const el = scrollRef?.current ?? wrap?.parentElement ?? null;
    if (!wrap || !el) return;
    let raf = 0;
    const update = () => {
      raf = 0;
      const offset = axis === "x" ? el.scrollLeft : el.scrollTop;
      const extent = axis === "x" ? el.scrollWidth : el.scrollHeight;
      const client = axis === "x" ? el.clientWidth : el.clientHeight;
      const hint = computeScrollHint(offset, extent, client);
      const attr = hintToAttr(hint, axis);
      if (wrap.dataset.scrollHint !== attr) wrap.dataset.scrollHint = attr;
    };
    const schedule = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    update();
    el.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      if (raf) cancelAnimationFrame(raf);
      el.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  });
}

/** HS-167-03 — ScrollHint wrapper component. Renders a positioned
 *  wrapper with gradient fades on the scrolled axis. */
export function ScrollHint({
  axis,
  scrollRef,
  className,
  children,
}: {
  axis: "x" | "y";
  scrollRef: React.RefObject<HTMLElement | null>;
  className?: string;
  children: ReactNode;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  useScrollHint(wrapRef, scrollRef, axis);
  return (
    <div
      ref={wrapRef}
      className={className ? `surface-scroll-hint ${className}` : "surface-scroll-hint"}
      data-axis={axis}
    >
      {children}
    </div>
  );
}
