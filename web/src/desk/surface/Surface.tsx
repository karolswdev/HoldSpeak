// HS-98-01 — the surface kit: the ONE way to build window content
// (DESIGN_SYSTEM.md, "The surface idiom"). Content sits directly on the
// window material — no nested cards, no page grids. Layout answers to
// the WINDOW via @container queries on .desk-surface-body; Signal
// controls (Button, inputs, Switch…) stay — this kit owns surfaces,
// not controls.
import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Button } from "../../components/signal/Signal";
import { humanTime, presentValue } from "./format";
import "./surface.css";

/** The one verb bar, sticky at the surface top. Primary verbs live
 * here; everything else is a row verb. */
export function SurfaceVerbs({
  children,
  status,
}: {
  children?: ReactNode;
  /** A quiet leading slot (state chip, scope chip). */
  status?: ReactNode;
}) {
  return (
    <div className="surface-verbs">
      {status ? <span className="surface-verbs-status">{status}</span> : null}
      <span className="surface-verbs-actions">{children}</span>
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
}: {
  glyph?: ReactNode;
  title: ReactNode;
  detail?: ReactNode;
  meta?: ReactNode;
  verbs?: ReactNode;
  selected?: boolean;
  onOpen?: () => void;
  children?: ReactNode;
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
    <li className="surface-row" data-selected={selected || undefined}>
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
  onRetry,
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
  onRetry?: () => void;
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
          ⚠
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
 * are omitted (rule 4), never rendered as zeros-theater. */
export function MetricStrip({
  items,
}: {
  items: Array<{ label: string; value: unknown }>;
}) {
  const kept = items.filter((item) => presentValue(item.value) !== "");
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

/** A bare switch for row-right placement (the row carries the label). */
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
    <label className="signal-switch surface-toggle">
      <input
        type="checkbox"
        role="switch"
        aria-label={label}
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="signal-switch-track" aria-hidden="true">
        <span />
      </span>
    </label>
  );
}

/** The inline two-step for destructive verbs (rule 5): first press
 * arms, second fires; arming self-disarms. Never a modal. */
export function ConfirmVerb({
  label,
  confirmLabel = "Sure?",
  busy,
  disabled,
  onConfirm,
}: {
  label: ReactNode;
  confirmLabel?: ReactNode;
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
