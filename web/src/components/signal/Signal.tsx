import {
  type ButtonHTMLAttributes,
  type DialogHTMLAttributes,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
  useEffect,
  useId,
  useRef,
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

export function Checkbox({
  label,
  description,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  description?: string;
}) {
  return (
    <label className="hs-check">
      <input type="checkbox" {...props} />
      <span>
        <strong>{label}</strong>
        {description ? <small>{description}</small> : null}
      </span>
    </label>
  );
}

export function Switch(
  props: InputHTMLAttributes<HTMLInputElement> & {
    label: string;
    description?: string;
  },
) {
  const { label, description, ...input } = props;
  return (
    <label className="signal-switch">
      <input type="checkbox" role="switch" {...input} />
      <span className="signal-switch-track" aria-hidden="true">
        <span />
      </span>
      <span>
        <strong>{label}</strong>
        {description ? <small>{description}</small> : null}
      </span>
    </label>
  );
}

export function ChoiceCard({
  label,
  description,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  description?: string;
}) {
  return (
    <label className="signal-choice">
      <input type="radio" {...props} />
      <span>
        <strong>{label}</strong>
        {description ? <small>{description}</small> : null}
      </span>
    </label>
  );
}

export function Tabs({
  tabs,
  active,
  onChange,
  label,
}: {
  tabs: Array<{ id: string; label: string; disabled?: boolean }>;
  active: string;
  onChange(id: string): void;
  label: string;
}) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const moveFocus = (from: number, direction: 1 | -1) => {
    for (let offset = 1; offset <= tabs.length; offset += 1) {
      const index = (from + direction * offset + tabs.length) % tabs.length;
      if (!tabs[index].disabled) {
        onChange(tabs[index].id);
        refs.current[index]?.focus();
        return;
      }
    }
  };
  return (
    <div className="signal-tabs" role="tablist" aria-label={label}>
      {tabs.map((tab, index) => (
        <button
          key={tab.id}
          ref={(element) => {
            refs.current[index] = element;
          }}
          type="button"
          role="tab"
          aria-selected={active === tab.id}
          disabled={tab.disabled}
          tabIndex={active === tab.id ? 0 : -1}
          onClick={() => onChange(tab.id)}
          onKeyDown={(event) => {
            if (event.key === "ArrowRight") {
              event.preventDefault();
              moveFocus(index, 1);
            } else if (event.key === "ArrowLeft") {
              event.preventDefault();
              moveFocus(index, -1);
            } else if (event.key === "Home") {
              event.preventDefault();
              const first = tabs.findIndex((item) => !item.disabled);
              if (first >= 0) {
                onChange(tabs[first].id);
                refs.current[first]?.focus();
              }
            } else if (event.key === "End") {
              event.preventDefault();
              let last = tabs.length - 1;
              while (last >= 0 && tabs[last].disabled) last -= 1;
              if (last >= 0) {
                onChange(tabs[last].id);
                refs.current[last]?.focus();
              }
            }
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export function Disclosure({
  title,
  children,
  open,
}: {
  title: string;
  children: ReactNode;
  open?: boolean;
}) {
  return (
    <details className="signal-disclosure" open={open}>
      <summary>{title}</summary>
      <div>{children}</div>
    </details>
  );
}

export function Dialog({
  open,
  title,
  children,
  onClose,
  ...props
}: DialogHTMLAttributes<HTMLDialogElement> & {
  open: boolean;
  title: string;
  onClose(): void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      returnFocus.current = document.activeElement as HTMLElement | null;
      dialog.showModal();
    } else if (!open && dialog.open) dialog.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      className="signal-dialog"
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClose={() => {
        onClose();
        returnFocus.current?.focus();
      }}
      {...props}
    >
      <header>
        <h2 id={titleId}>{title}</h2>
        <Button variant="ghost" aria-label="Close dialog" onClick={onClose}>
          ×
        </Button>
      </header>
      {children}
    </dialog>
  );
}

export function InlineMessage({
  tone = "info",
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & {
  tone?: "info" | "success" | "warning" | "error";
}) {
  return (
    <div
      className={`signal-message is-${tone}`}
      role={tone === "error" ? "alert" : "status"}
      {...props}
    >
      {children}
    </div>
  );
}

export function EmptyState({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="signal-empty">
      <span aria-hidden="true">◇</span>
      <h2>{title}</h2>
      <p>{children}</p>
      {action}
    </div>
  );
}

export function StatusPill({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "success" | "warning" | "error" | "live";
  children: ReactNode;
}) {
  return (
    <span className={`signal-status is-${tone}`}>
      <span aria-hidden="true" />
      {children}
    </span>
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

export function Toolbar({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="signal-toolbar" role="toolbar" aria-label={label}>
      {children}
    </div>
  );
}

export function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="signal-skeleton" aria-label="Loading" aria-busy="true">
      {Array.from({ length: rows }, (_, index) => (
        <span key={index} />
      ))}
    </div>
  );
}
