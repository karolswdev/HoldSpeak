// HS-111-08 — the legacy Signal dialect retired (audit §1/§4): Switch,
// Tabs, StatusPill, InlineMessage, Disclosure, Dialog, ChoiceCard,
// Checkbox, Toolbar, EmptyState, and Skeleton died with the gadget-kit
// conformance sweep. What remains is the surviving roster:
// - Button — the VERB species (TransportKey is the instrument key; the
//   split of duties is deliberate: Button = verb, TransportKey =
//   momentary instrument control).
// - Field/TextInput/TextArea/Select — legacy input faces kept ONLY for
//   the InlineEditor native cluster (rides to HS-111-10); new code
//   composes StringGadget/PadGadget/CycleGadget.
// - Panel — the document-shell card (non-desk routes).
import {
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
  useId,
} from "react";

export function Button({
  variant = "secondary",
  dense = false,
  loading = false,
  children,
  className = "",
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  dense?: boolean;
  loading?: boolean;
}) {
  return (
    <button
      className={`btn btn--${variant}${dense ? " btn--sm" : ""} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <span className="signal-spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}

export function Field({
  label,
  description,
  error,
  children,
}: {
  label: string;
  description?: string;
  error?: string;
  children: (ids: { id: string; describedBy?: string }) => ReactNode;
}) {
  const id = useId();
  const descriptionId = description ? `${id}-description` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  return (
    <div className="hs-field">
      <label className="hs-field-label" htmlFor={id}>
        {label}
      </label>
      {children({
        id,
        describedBy:
          [descriptionId, errorId].filter(Boolean).join(" ") || undefined,
      })}
      {description ? (
        <span className="hs-field-hint" id={descriptionId}>
          {description}
        </span>
      ) : null}
      {error ? (
        <span className="hs-field-error" id={errorId}>
          {error}
        </span>
      ) : null}
    </div>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`hs-control ${props.className ?? ""}`} {...props} />;
}

export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`hs-control signal-textarea ${props.className ?? ""}`}
      {...props}
    />
  );
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`hs-control hs-select ${props.className ?? ""}`}
      {...props}
    />
  );
}

export function Panel({
  title,
  eyebrow,
  actions,
  children,
  className = "",
}: {
  title?: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`signal-panel ${className}`}>
      {title ? (
        <header>
          {eyebrow ? <span className="signal-eyebrow">{eyebrow}</span> : null}
          <h2>{title}</h2>
          {actions ? <div>{actions}</div> : null}
        </header>
      ) : null}
      <div className="signal-panel-body">{children}</div>
    </section>
  );
}
