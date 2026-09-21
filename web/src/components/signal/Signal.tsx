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
  type ComponentPropsWithRef,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
  useId,
} from "react";

/** HS-202-03 — the CHROME variant.
 *
 * Some verbs are not plated buttons: a menu row, a wing tab, a dock chip, a
 * formatting-rail key, the mic, the record orb.  Their material is drawn by
 * the strip they ride (`chrome-menus.css` keys off `.desk-menu-list button`,
 * `pullout.css` off `.desk-wing`, `window-chrome.css` off `.desk-dock-*`,
 * and so on), so for `variant="chrome"` the plate classes (`btn`,
 * `btn--secondary`, `btn--sm`) are WITHHELD and only the marker
 * `btn--chrome` is stamped: the strip keeps its own ink to the pixel.
 *
 * What the variant DOES carry is the species (UX-CANON A.1 — every verb is
 * the library Button): one element, one `type="button"` default, one
 * `loading` / `disabled` / `aria-busy` grammar.  Before HS-202-03 the
 * surface inventory of 2026-09-20 (§3.3) found these shared controls were
 * the WORST raw-HTML sites in the product — every menu item, every wing
 * tab, the dock itself — so a stranger's first five minutes met raw HTML at
 * every turn.
 *
 * It is not a licence to draw a new look: a `chrome` verb always carries the
 * className of a strip that already owns its material, and `Signal.test.tsx`
 * plus `desk/__tests__/hs202ChromeSpecies.test.tsx` fence the no-plate rule.
 */
export function Button({
  variant = "secondary",
  dense = false,
  loading = false,
  children,
  className = "",
  disabled,
  type = "button",
  ...props
}: ComponentPropsWithRef<"button"> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "chrome";
  dense?: boolean;
  loading?: boolean;
}) {
  // A raw <button> in a form submits; the species never does unless asked.
  return (
    <button
      type={type}
      className={
        variant === "chrome"
          ? `btn--chrome ${className}`.trim()
          : `btn btn--${variant}${dense ? " btn--sm" : ""} ${className}`
      }
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
