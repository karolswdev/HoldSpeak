// HS-111-01 — the gadget kit (audit §3.3): the Workbench-wide control
// primitives the Prefs rethink is built from. Every gadget wraps a REAL
// input (checkbox, select, range, text) so the accessibility tree stays
// honest; the face is the square, beveled Signal Workbench grammar.
// Stories 02-08 consume these — they live in the surface kit, not in
// Settings.
import {
  useEffect,
  useId,
  useRef,
  useState,
  type ComponentPropsWithoutRef,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
  type Ref,
} from "react";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { ConfirmVerb } from "./Surface";
import { useRovingRows } from "./roving";
import "./gadgets.css";

/* ── the sheet: two aligned columns, 26px rows, engraved groups ── */

export function GadgetGroup({
  label,
  children,
}: {
  label?: string;
  children: ReactNode;
}) {
  return (
    <section className="gadget-group">
      {label ? <h4 className="gadget-group-label">{label}</h4> : null}
      <div className="gadget-sheet">{children}</div>
    </section>
  );
}

/** One row of the gadget sheet: label column, gadget column. A `fact`
 * is a token (unit, range), never a sentence. `wide` spans the row
 * (tables, mx radios). `highlight` marks the filter's landing row. */
export function GadgetRow({
  label,
  fact,
  wide,
  highlight,
  children,
}: {
  label: ReactNode;
  fact?: ReactNode;
  wide?: boolean;
  highlight?: boolean;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (highlight) ref.current?.scrollIntoView({ block: "center" });
  }, [highlight]);
  return (
    <div
      ref={ref}
      className="gadget-row"
      data-wide={wide || undefined}
      data-highlight={highlight || undefined}
    >
      <span className="gadget-row-label">
        {label}
        {fact ? <span className="gadget-fact">{fact}</span> : null}
      </span>
      <span className="gadget-row-gadget">{children}</span>
    </div>
  );
}

/* ── CheckGadget: the boolean species (kills the sliding toggle) ── */

export function CheckGadget({
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
    <label className="gadget-check">
      <input
        type="checkbox"
        aria-label={label}
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="gadget-check-well" aria-hidden="true">
        <svg viewBox="0 0 16 16">
          <path d="M3.5 8.5 6.5 11.5 12.5 4.5" />
        </svg>
      </span>
    </label>
  );
}

/* ── CycleGadget: a real <select> wearing the ↻ VALUE face ── */

export type CycleOption = {
  value: string;
  label?: string;
  /** An unavailable destination stays listed and named, never picked. */
  disabled?: boolean;
};

export function CycleGadget({
  label,
  value,
  options,
  onChange,
  disabled,
}: {
  label: string;
  value: string;
  options: CycleOption[];
  onChange(next: string): void;
  disabled?: boolean;
}) {
  // An off-roster value stays visible and selectable (never silently
  // rewritten): it rides as an extra option until the next change.
  const known = options.some((option) => option.value === value);
  return (
    <span className="gadget-cycle">
      <span className="gadget-cycle-glyph" aria-hidden="true">
        ↻
      </span>
      <select
        aria-label={label}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      >
        {known ? null : <option value={value}>{value || "—"}</option>}
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label ?? option.value}
          </option>
        ))}
      </select>
    </span>
  );
}

/* ── MxRadio: every option visible; the pick reveals its own gadgets ── */

export type MxOption = {
  value: string;
  label: ReactNode;
  caption?: ReactNode;
  children?: ReactNode;
};

export function MxRadio({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: MxOption[];
  onChange(next: string): void;
}) {
  const name = useId();
  return (
    <div className="gadget-mx" role="radiogroup" aria-label={label}>
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <div
            key={option.value}
            className="gadget-mx-option"
            data-selected={selected || undefined}
          >
            <label className="gadget-mx-row">
              <input
                type="radio"
                name={name}
                checked={selected}
                onChange={() => onChange(option.value)}
              />
              <span className="gadget-mx-box" aria-hidden="true" />
              <span className="gadget-mx-label">{option.label}</span>
              {option.caption ? (
                <span className="gadget-mx-caption">{option.caption}</span>
              ) : null}
            </label>
            {selected && option.children ? (
              <div className="gadget-mx-deps gadget-indent">
                {option.children}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

/* ── StringGadget: left-aligned, fills the column, mic in the well ── */

export function StringGadget({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  mic = true,
  disabled,
  autoFocus,
  onKeyDown,
  inputRef,
  inputProps,
}: {
  label: string;
  value: string;
  onChange(next: string): void;
  placeholder?: string;
  type?: string;
  /** Every text well carries the speak-to-fill mic unless secret. */
  mic?: boolean;
  disabled?: boolean;
  autoFocus?: boolean;
  onKeyDown?: (event: KeyboardEvent<HTMLInputElement>) => void;
  /** Chrome consumers (the palette) focus the well imperatively. */
  inputRef?: Ref<HTMLInputElement>;
  /** Extra native input attributes for specialized patterns such as a combobox. */
  inputProps?: Omit<
    ComponentPropsWithoutRef<"input">,
    "aria-label" | "autoFocus" | "disabled" | "onChange" | "onKeyDown" | "placeholder" | "ref" | "type" | "value"
  >;
}) {
  const autoFocusRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    if (!autoFocus) return;
    // Two-frame delay: the DeskWindowFrame's own useEffect focuses the
    // shell synchronously; a single rAF can race with React 18's
    // concurrent paint.  A short timeout ensures we fire after all
    // parent effects AND the browser's layout pass.
    const t = window.setTimeout(() => autoFocusRef.current?.focus(), 50);
    return () => window.clearTimeout(t);
  }, [autoFocus]);

  return (
    <span className="gadget-string">
      <input
        {...inputProps}
        ref={(el) => {
          autoFocusRef.current = el;
          if (typeof inputRef === "function") inputRef(el);
          else if (inputRef && typeof inputRef === "object")
            (inputRef as React.MutableRefObject<HTMLInputElement | null>).current = el;
        }}
        aria-label={label}
        type={type}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete={type === "password" ? "new-password" : undefined}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={onKeyDown}
      />
      {mic && type !== "password" ? (
        <MicButton label={`Speak ${label}`} onText={(text) => onChange(text)} />
      ) : null}
    </span>
  );
}

/* ── PadGadget: the multiline species (HS-111-08, audit §3.5) —
   StringGadget's grammar at N rows: sunken well, mono, the speak-to-
   fill mic in the corner. The kit's ONLY textarea face. ── */

export function PadGadget({
  label,
  value,
  onChange,
  placeholder,
  rows = 3,
  mic = true,
  autoGrow,
  disabled,
  autoFocus,
  onKeyDown,
}: {
  label: string;
  value: string;
  onChange(next: string): void;
  placeholder?: string;
  rows?: number;
  /** Every text well carries the speak-to-fill mic unless the host
   * renders its own capture path. */
  mic?: boolean;
  /** Grow with the content instead of scrolling. */
  autoGrow?: boolean;
  disabled?: boolean;
  autoFocus?: boolean;
  onKeyDown?: (event: KeyboardEvent<HTMLTextAreaElement>) => void;
}) {
  const padRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (!autoGrow) return;
    const pad = padRef.current;
    if (!pad) return;
    pad.style.height = "auto";
    pad.style.height = `${pad.scrollHeight + 2}px`;
  }, [value, autoGrow]);
  return (
    <span className="gadget-pad" data-grow={autoGrow || undefined}>
      <textarea
        ref={padRef}
        aria-label={label}
        value={value}
        placeholder={placeholder}
        rows={rows}
        disabled={disabled}
        autoFocus={autoFocus}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={onKeyDown}
      />
      {mic ? (
        <MicButton
          label={`Speak ${label}`}
          onText={(text) =>
            onChange(
              value && !/\s$/.test(value) ? `${value} ${text}` : value + text,
            )
          }
        />
      ) : null}
    </span>
  );
}

/* ── FoldGadget: the ONE disclosure species (HS-111-08, audit §3.3) —
   <details> semantics (free keyboard + a11y), the house quiet-row
   face, a trailing token slot (the 05 budget gap). ── */

export function FoldGadget({
  title,
  token,
  glyph,
  open,
  onToggle,
  className,
  children,
}: {
  /** The summary line — reads as a token, never a sentence. */
  title: ReactNode;
  /** Trailing budget/count token, right-aligned (mono, dim). */
  token?: ReactNode;
  /** Optional leading glyph beside the caret. */
  glyph?: ReactNode;
  open?: boolean;
  /** Optional controlled hook — fires with the <details> open state. */
  onToggle?: (open: boolean) => void;
  className?: string;
  children: ReactNode;
}) {
  return (
    <details
      className={className ? `gadget-fold ${className}` : "gadget-fold"}
      data-token={token != null ? "" : undefined}
      open={open}
      onToggle={
        onToggle
          ? (event) => onToggle((event.target as HTMLDetailsElement).open)
          : undefined
      }
    >
      <summary>
        {glyph ? (
          <span className="gadget-fold-glyph" aria-hidden="true">
            {glyph}
          </span>
        ) : null}
        <span className="gadget-fold-title">{title}</span>
        {token != null ? (
          <span className="gadget-fold-token">{token}</span>
        ) : null}
      </summary>
      <div className="gadget-fold-body">{children}</div>
    </details>
  );
}

/* ── StepperGadget: string gadget + ▲▼ arrows + a unit fact ── */

export function StepperGadget({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  unit,
}: {
  label: string;
  value: number;
  onChange(next: number): void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
}) {
  const clamp = (next: number) => {
    let out = next;
    if (typeof min === "number") out = Math.max(min, out);
    if (typeof max === "number") out = Math.min(max, out);
    // Kill float drift from repeated ± steps.
    return Number(out.toFixed(6));
  };
  return (
    <span className="gadget-string gadget-stepper">
      <input
        aria-label={label}
        type="number"
        value={Number.isFinite(value) ? value : 0}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(clamp(Number(event.target.value)))}
      />
      {unit ? <span className="gadget-unit">{unit}</span> : null}
      <span className="gadget-arrows">
        <button
          type="button"
          aria-label={`Increase ${label}`}
          onClick={() => onChange(clamp((value || 0) + step))}
        >
          ▲
        </button>
        <button
          type="button"
          aria-label={`Decrease ${label}`}
          onClick={() => onChange(clamp((value || 0) - step))}
        >
          ▼
        </button>
      </span>
    </span>
  );
}

/* ── PropGadget: bounded scalar on a sunken track ── */

export function PropGadget({
  label,
  value,
  onChange,
  min = 0,
  max = 1,
  step = 0.01,
}: {
  label: string;
  value: number;
  onChange(next: number): void;
  min?: number;
  max?: number;
  step?: number;
}) {
  const decimals = step < 1 ? 2 : 0;
  return (
    <span className="gadget-prop">
      <input
        type="range"
        aria-label={label}
        min={min}
        max={max}
        step={step}
        value={Number.isFinite(value) ? value : min}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <output className="gadget-prop-read" aria-hidden="true">
        {(Number.isFinite(value) ? value : min).toFixed(decimals)}
      </output>
    </span>
  );
}

/* ── GadgetTable: dense list editor (24px rows, ghost ADD row) ── */

export function GadgetTable({
  head,
  rows,
  onDelete,
  deleteLabel = "DELETE?",
  rowKey,
  onAdd,
  addLabel = "+ ADD",
  verbs,
}: {
  head: string[];
  rows: ReactNode[][];
  onDelete?(index: number): void;
  /** HS-111-08 — the armed face of the kit-default delete (doctrine
   * P0 F4): callers name the loss ("FORGET?"), never opt out. */
  deleteLabel?: string;
  /** Stable row identity so arming never migrates rows when the list
   * reorders or a neighbor is deleted; defaults to the index. */
  rowKey?(index: number): string;
  onAdd?(): void;
  addLabel?: string;
  /** HS-111-02 — the row-verbs slot: renders in the trailing cell in
   * place of the default armed × (an arming FORGET?, a Replace…). */
  verbs?(index: number): ReactNode;
}) {
  const cols = { "--gadget-cols": head.length } as CSSProperties;
  // HS-111-08 — roving focus is kit law (audit §3.1): the table is ONE
  // Tab stop; Up/Down walk rows, Left/Right walk a row's controls.
  const rootRef = useRef<HTMLDivElement>(null);
  useRovingRows(rootRef, {
    selector:
      ".gadget-table-row button, .gadget-table-row input, .gadget-table-row select",
    rowSelector: ".gadget-table-row",
  });
  return (
    <div
      ref={rootRef}
      className="gadget-table"
      style={cols}
      data-verbs={verbs || onDelete ? "" : undefined}
    >
      <div className="gadget-table-head">
        {head.map((column) => (
          <span key={column}>{column}</span>
        ))}
        <span aria-hidden="true" />
      </div>
      {rows.map((cells, index) => (
        <div className="gadget-table-row" key={rowKey ? rowKey(index) : index}>
          {cells.map((cell, cellIndex) => (
            <span key={cellIndex} className="gadget-table-cell">
              {cell}
            </span>
          ))}
          {verbs ? (
            <span className="gadget-table-verbs">{verbs(index)}</span>
          ) : onDelete ? (
            // The kit default is ARMED (× → DELETE? → gone); a bare
            // immediate delete is not a thing the kit renders.
            <span className="gadget-table-verbs">
              <ConfirmVerb
                key={rowKey ? rowKey(index) : index}
                label="×"
                confirmLabel={deleteLabel}
                ariaLabel={`Delete row ${index + 1}`}
                onConfirm={() => onDelete(index)}
              />
            </span>
          ) : (
            <span aria-hidden="true" />
          )}
        </div>
      ))}
      {onAdd ? (
        <button type="button" className="gadget-table-add" onClick={onAdd}>
          {addLabel}
        </button>
      ) : null}
    </div>
  );
}

/* ── LedMeter: the sampler's segmented level meter (audit §3.5) ──
   Flat segment fills in a sunken track, dark at rest; `scanning`
   plays one walking segment (the tape is winding). Never color-only:
   the mono axis label sits with it. No gradients, no glow. */

export function LedMeter({
  label,
  value,
  segments = 12,
  scanning,
}: {
  label: string;
  /** 0..1 — how many segments light. */
  value: number;
  segments?: number;
  /** Busy posture: one walking segment instead of a level. */
  scanning?: boolean;
}) {
  const clamped = Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
  const lit = scanning ? 0 : Math.round(clamped * segments);
  return (
    <span
      className="gadget-ledmeter"
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={1}
      aria-valuenow={scanning ? undefined : clamped}
      aria-valuetext={scanning ? "scanning" : undefined}
      data-scanning={scanning || undefined}
    >
      <span className="gadget-ledmeter-label">{label}</span>
      <span className="gadget-ledmeter-track" aria-hidden="true">
        {Array.from({ length: segments }, (_, index) => (
          <span
            key={index}
            className="gadget-ledmeter-seg"
            data-lit={index < lit || undefined}
            data-hot={index < lit && (index + 1) / segments > 0.8 ? "" : undefined}
            style={{ "--seg-i": index } as CSSProperties}
          />
        ))}
      </span>
    </span>
  );
}

/* ── LampGadget: the square lamp + its mono axis label as ONE species
   (never color-only by construction) ── */

export function LampGadget({
  label,
  on,
  tone = "ok",
  block = false,
}: {
  label: string;
  on: boolean;
  /** HS-111-08 — `fail` joined the roster (the readiness column's
   * honest red); the lamp is never color-only by construction. */
  tone?: "ok" | "warn" | "fail";
  /** HS-135-02 L6 — block system messages wrap instead of truncating. */
  block?: boolean;
}) {
  return (
    <span
      className={`gadget-lamp${block ? " is-block" : ""}`}
      data-on={on}
      data-tone={tone}
      title={label}
    >
      <span className="gadget-lamp-dot" aria-hidden="true" />
      {label}
    </span>
  );
}

/* ── TransportKey: the square momentary gadget (glyph over mono word;
   held/active = inverted video, bevel flips to sunken) ── */

export function TransportKey({
  label,
  word,
  glyph,
  active,
  disabled,
  onClick,
  tone,
  compact,
  title,
}: {
  label: string;
  /** HS-112-06 — the engraved word when the label is longer than the
   * key is wide (48px of 9px mono ≈ 7 characters). The label stays the
   * accessible name; only the engraving shortens. */
  word?: string;
  glyph: ReactNode;
  /** Held/armed — inverted video. */
  active?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  /** HS-111-04 — the loud key (^C, KILL): danger tone; active =
   * inverted danger video. */
  tone?: "danger";
  /** HS-111-04 — the in-row key (a composer's SEND/ENTER): same
   * species at input height, glyph beside the word. */
  compact?: boolean;
  title?: string;
}) {
  return (
    <button
      type="button"
      className="gadget-transport-key"
      aria-label={label}
      aria-pressed={active || undefined}
      data-active={active || undefined}
      data-tone={tone}
      data-compact={compact || undefined}
      disabled={disabled}
      title={title}
      onClick={onClick}
    >
      <span className="gadget-transport-glyph" aria-hidden="true">
        {glyph}
      </span>
      <span className="gadget-transport-word">{word ?? label}</span>
    </button>
  );
}

export function TransportRow({ children }: { children: ReactNode }) {
  return <span className="gadget-transport-row">{children}</span>;
}

/* ── the ONE egress badge chip: a token, never prose ── */

export function EgressChip({
  label = "⌂ This device",
  title = "Transcript processing stays on this device.",
  scope,
  className,
  ariaLabel,
  onClick,
}: {
  label?: string;
  /** HS-111-04 — an off-device reply names its honest boundary; the
   * default stays the on-device promise. */
  title?: string;
  /** HS-111-07 — scope color variant (local = ok, mixed/cloud = accent);
   * unset keeps the on-device tone. */
  scope?: "local" | "mixed" | "cloud";
  className?: string;
  ariaLabel?: string;
  /** HS-111-07 — the chrome badge is this SAME species with a click
   * (the one tap into Privacy and Trust); a plain fact chip stays a span. */
  onClick?: () => void;
}) {
  const cls =
    "gadget-chip gadget-chip-egress" + (className ? ` ${className}` : "");
  if (onClick) {
    return (
      <button
        type="button"
        className={cls}
        data-scope={scope}
        title={title}
        aria-label={ariaLabel}
        onClick={onClick}
      >
        {label}
      </button>
    );
  }
  return (
    <span className={cls} data-scope={scope} title={title}>
      {label}
    </span>
  );
}

/* ── SecretRow: SET/— chip, hover verbs, in-row armed replace ── */

export function SecretRow({
  label,
  configured,
  destination,
  busy,
  rotatable,
  onReplace,
  onRotate,
  onDelete,
}: {
  label: string;
  configured: boolean;
  destination?: string;
  busy?: boolean;
  rotatable?: boolean;
  onReplace(value: string): void;
  onRotate?(): void;
  onDelete?(): void;
}) {
  const [arming, setArming] = useState(false);
  const [draft, setDraft] = useState("");
  const disarm = () => {
    setArming(false);
    setDraft("");
  };
  return (
    <div className="gadget-secret">
      <span className="gadget-secret-label">
        {label}
        {destination ? <small>{destination}</small> : null}
      </span>
      {arming ? (
        <StringGadget
          label={`Replacement ${label}`}
          type="password"
          value={draft}
          onChange={setDraft}
          autoFocus
          placeholder="new value"
          onKeyDown={(event) => {
            if (event.key === "Enter" && draft.trim()) {
              onReplace(draft.trim());
              disarm();
            } else if (event.key === "Escape") {
              disarm();
            }
          }}
        />
      ) : (
        <span>
          <span className="gadget-chip" data-set={configured || undefined}>
            {configured ? "SET" : "—"}
          </span>
        </span>
      )}
      <span className="gadget-secret-verbs surface-row-verbs">
        <Button
          dense
          variant="ghost"
          disabled={busy}
          onClick={() => (arming ? disarm() : setArming(true))}
        >
          {arming ? "Cancel" : "Replace"}
        </Button>
        {rotatable && onRotate ? (
          <ConfirmVerb
            label="Rotate"
            confirmLabel="Rotate?"
            busy={busy}
            onConfirm={onRotate}
          />
        ) : null}
        {configured && onDelete ? (
          <ConfirmVerb
            label="Delete"
            confirmLabel="Delete?"
            busy={busy}
            onConfirm={onDelete}
          />
        ) : null}
      </span>
    </div>
  );
}
