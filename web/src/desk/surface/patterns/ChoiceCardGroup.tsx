/** ChoiceCardGroup — real radio semantics with roving focus.
 *  Uses visually hidden radio inputs and useRovingRows for keyboard nav.
 *  Selection requires a separate confirmation action.
 *
 *  HS-156-08 — a card is an OBJECT, not a list. New slots:
 *  `summary` (the one-line anchor), `emblem` (tier mark), `tier`
 *  (accent temperature via data-tier), and `fold`/`foldLabel` (per-item
 *  detail behind a Disclosure instead of splattered rows). The group
 *  gains `layout="row"` so tiers stand side by side where width allows.
 */
import { Children, useRef, type CSSProperties, type ReactNode } from "react";
import { useRovingRows } from "../roving";
import { Disclosure } from "./Disclosure";
import "./choice-card.css";

export function ChoiceCardGroup({
  name,
  value,
  onChange,
  children,
  confirmLabel,
  onConfirm,
  disabled,
  ariaLabel,
  layout = "column",
}: {
  name: string;
  value: string | null;
  onChange: (value: string) => void;
  children: ReactNode;
  confirmLabel?: string;
  onConfirm?: () => void;
  disabled?: boolean;
  ariaLabel?: string;
  /** "row" lays cards out as equal siblings where width allows (stacks narrow). */
  layout?: "column" | "row";
}) {
  const groupRef = useRef<HTMLDivElement>(null);

  useRovingRows(groupRef, {
    selector: 'input[type="radio"]',
  });

  return (
    <div
      ref={groupRef}
      className="surface-choice-group"
      role="radiogroup"
      aria-label={ariaLabel ?? name}
      data-layout={layout !== "column" ? layout : undefined}
      style={
        layout === "row"
          ? ({ "--choice-cards": Children.count(children) } as CSSProperties)
          : undefined
      }
    >
      {children}
      {confirmLabel && onConfirm ? (
        <button
          type="button"
          className="surface-choice-confirm-btn"
          disabled={disabled || value == null}
          onClick={onConfirm}
        >
          {confirmLabel}
        </button>
      ) : null}
    </div>
  );
}

export function ChoiceCard({
  value,
  label,
  description,
  recommended,
  disabled,
  facts,
  cost,
  children,
  name,
  selectedValue,
  onChange,
  summary,
  emblem,
  tier,
  fold,
  foldLabel,
}: {
  value: string;
  label: string;
  description?: string;
  recommended?: boolean;
  disabled?: boolean;
  facts?: { label: string; value: string }[];
  cost?: ReactNode;
  children?: ReactNode;
  /** Injected by group or passed directly */
  name?: string;
  selectedValue?: string | null;
  onChange?: (value: string) => void;
  /** The one-line anchor: what this choice actually does, in one breath. */
  summary?: ReactNode;
  /** Tier mark rendered beside the label; colored by `tier`. */
  emblem?: ReactNode;
  /** Accent temperature key (e.g. "light" | "balanced" | "full") → data-tier. */
  tier?: string;
  /** Per-item detail folded behind a Disclosure — never splattered rows. */
  fold?: ReactNode;
  foldLabel?: string;
}) {
  const isSelected = selectedValue === value;

  return (
    <label
      className="surface-choice-card"
      data-selected={isSelected || undefined}
      data-recommended={recommended || undefined}
      data-disabled={disabled || undefined}
      data-tier={tier}
    >
      <input
        type="radio"
        className="surface-choice-card-radio"
        name={name}
        value={value}
        checked={isSelected}
        disabled={disabled}
        onChange={() => onChange?.(value)}
      />
      <div className="surface-choice-card-head">
        {emblem != null ? (
          <span className="surface-choice-card-emblem" aria-hidden="true">
            {emblem}
          </span>
        ) : null}
        <span className="surface-choice-card-label">{label}</span>
      </div>
      {description ? (
        <div className="surface-choice-card-desc">{description}</div>
      ) : null}
      {summary != null ? (
        <div className="surface-choice-card-summary">{summary}</div>
      ) : null}
      {facts?.length ? (
        <div className="surface-choice-card-facts">
          {facts.map((fact) => (
            <div
              key={`${fact.label}:${fact.value}`}
              className="surface-choice-card-fact"
            >
              <span className="surface-choice-card-fact-key">{fact.label}</span>
              <span className="surface-choice-card-fact-val">{fact.value}</span>
            </div>
          ))}
        </div>
      ) : null}
      {cost != null ? (
        <div className="surface-choice-card-cost">{cost}</div>
      ) : null}
      {children}
      {fold != null ? (
        <div
          className="surface-choice-card-fold"
          // A click inside the fold inspects; it must never flip the radio.
          onClick={(event) => event.preventDefault()}
        >
          <Disclosure label={foldLabel ?? "Details"} defaultOpen={false}>
            {fold}
          </Disclosure>
        </div>
      ) : null}
    </label>
  );
}
