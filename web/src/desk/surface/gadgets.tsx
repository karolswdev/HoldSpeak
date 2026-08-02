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
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { ConfirmVerb } from "./Surface";
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
}) {
  return (
    <span className="gadget-string">
      <input
        aria-label={label}
        type={type}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
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
  onAdd,
  addLabel = "+ ADD",
  verbs,
}: {
  head: string[];
  rows: ReactNode[][];
  onDelete?(index: number): void;
  onAdd?(): void;
  addLabel?: string;
  /** HS-111-02 — the row-verbs slot: renders in the trailing cell in
   * place of the bare × (an arming FORGET?, a Replace…). */
  verbs?(index: number): ReactNode;
}) {
  const cols = { "--gadget-cols": head.length } as CSSProperties;
  return (
    <div className="gadget-table" style={cols} data-verbs={verbs ? "" : undefined}>
      <div className="gadget-table-head">
        {head.map((column) => (
          <span key={column}>{column}</span>
        ))}
        <span aria-hidden="true" />
      </div>
      {rows.map((cells, index) => (
        <div className="gadget-table-row" key={index}>
          {cells.map((cell, cellIndex) => (
            <span key={cellIndex} className="gadget-table-cell">
              {cell}
            </span>
          ))}
          {verbs ? (
            <span className="gadget-table-verbs">{verbs(index)}</span>
          ) : onDelete ? (
            <button
              type="button"
              className="gadget-x"
              aria-label={`Delete row ${index + 1}`}
              onClick={() => onDelete(index)}
            >
              ×
            </button>
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
}: {
  label: string;
  on: boolean;
  tone?: "ok" | "warn";
}) {
  return (
    <span className="gadget-lamp" data-on={on} data-tone={tone}>
      <span className="gadget-lamp-dot" aria-hidden="true" />
      {label}
    </span>
  );
}

/* ── TransportKey: the square momentary gadget (glyph over mono word;
   held/active = inverted video, bevel flips to sunken) ── */

export function TransportKey({
  label,
  glyph,
  active,
  disabled,
  onClick,
  tone,
  compact,
  title,
}: {
  label: string;
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
      <span className="gadget-transport-word">{label}</span>
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
}: {
  label?: string;
  /** HS-111-04 — an off-device reply names its honest boundary; the
   * default stays the on-device promise. */
  title?: string;
}) {
  return (
    <span className="gadget-chip gadget-chip-egress" title={title}>
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
