/** ChoiceCardGroup — real radio semantics with roving focus.
 *  Uses visually hidden radio inputs and useRovingRows for keyboard nav.
 *  Selection requires a separate confirmation action. */
import { useRef, type ReactNode } from "react";
import { useRovingRows } from "../roving";
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
}: {
  name: string;
  value: string | null;
  onChange: (value: string) => void;
  children: ReactNode;
  confirmLabel?: string;
  onConfirm?: () => void;
  disabled?: boolean;
  ariaLabel?: string;
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
}) {
  const isSelected = selectedValue === value;

  return (
    <label
      className="surface-choice-card"
      data-selected={isSelected || undefined}
      data-recommended={recommended || undefined}
      data-disabled={disabled || undefined}
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
        <span className="surface-choice-card-label">{label}</span>
      </div>
      {description ? (
        <div className="surface-choice-card-desc">{description}</div>
      ) : null}
      {facts?.length ? (
        <div className="surface-choice-card-facts">
          {facts.map((fact) => (
            <div key={fact.label} className="surface-choice-card-fact">
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
    </label>
  );
}
