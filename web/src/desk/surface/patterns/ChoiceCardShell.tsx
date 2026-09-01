/** ChoiceCardShell — the material of a choice card without an interaction model.
 *
 *  HS-159 — the ChoiceCard (HS-156-08) ships a radio-based single-select
 *  card inside ChoiceCardGroup. The suggestion-cards interview step needs
 *  the same visual language for a multi-select listbox. This shell owns
 *  the surface-choice-card-* CSS classes and renders all presentational
 *  slots (head, label, emblem, summary, facts, cost, fold, children) on
 *  the element the caller supplies (via `as`), but imposes NO interaction
 *  model — no radio, no label element, no onChange.
 *
 *  ChoiceCard composes this shell internally so there is ONE source of
 *  material. Feature code that needs the card visual language in a
 *  different interaction context consumes the shell via the barrel.
 */
import { type ReactNode, type ElementType, type ComponentPropsWithoutRef } from "react";
import { Disclosure } from "./Disclosure";
import "./choice-card.css";

type OwnProps = {
  /** The wrapper element tag. Defaults to "div". */
  as?: ElementType;
  /** Card label (the primary name). */
  label: ReactNode;
  /** Optional description (the one-sentence character). */
  description?: ReactNode;
  /** Optional one-line summary anchor. */
  summary?: ReactNode;
  /** Tier mark beside the label, aria-hidden. */
  emblem?: ReactNode;
  /** Accent-temperature key stamped as data-tier. */
  tier?: string;
  /** Fact chips. */
  facts?: { label: string; value: string }[];
  /** Cost slot. */
  cost?: ReactNode;
  /** Per-item detail behind a Disclosure. */
  fold?: ReactNode;
  /** Disclosure trigger label for the fold. */
  foldLabel?: string;
  /** Whether the card is visually selected (accent wash). */
  selected?: boolean;
  /** Whether the card is recommended (accent presence). */
  recommended?: boolean;
  /** Whether the card is disabled. */
  disabled?: boolean;
  /** Content rendered before the head (e.g. a visually-hidden radio input
   *  whose :focus-visible + .head selector needs DOM adjacency). */
  beforeHead?: ReactNode;
  /** Content rendered after the built-in slots (before the fold). */
  children?: ReactNode;
  /** Click handler on the fold (e.g. stopPropagation). */
  onFoldClick?: (e: React.MouseEvent) => void;
};

export type ChoiceCardShellProps = OwnProps & Omit<ComponentPropsWithoutRef<"div">, keyof OwnProps>;

export function ChoiceCardShell({
  as: Tag = "div",
  label,
  description,
  summary,
  emblem,
  tier,
  facts,
  cost,
  fold,
  foldLabel,
  selected,
  recommended,
  disabled,
  beforeHead,
  children,
  className,
  onFoldClick,
  ...rest
}: ChoiceCardShellProps) {
  return (
    <Tag
      className={
        className
          ? `surface-choice-card ${className}`
          : "surface-choice-card"
      }
      data-selected={selected || undefined}
      data-recommended={recommended || undefined}
      data-disabled={disabled || undefined}
      data-tier={tier}
      {...rest}
    >
      {/* Before-head slot (e.g. visually-hidden radio for :focus-visible + .head) */}
      {beforeHead}

      {/* Head: emblem + label */}
      <div className="surface-choice-card-head">
        {emblem != null ? (
          <span className="surface-choice-card-emblem" aria-hidden="true">
            {emblem}
          </span>
        ) : null}
        <span className="surface-choice-card-label">{label}</span>
      </div>

      {/* Description */}
      {description ? (
        <div className="surface-choice-card-desc">{description}</div>
      ) : null}

      {/* Summary: the one-line anchor */}
      {summary != null ? (
        <div className="surface-choice-card-summary">{summary}</div>
      ) : null}

      {/* Facts: chips */}
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

      {/* Cost */}
      {cost != null ? (
        <div className="surface-choice-card-cost">{cost}</div>
      ) : null}

      {/* Caller-provided content between standard slots and fold */}
      {children}

      {/* Fold: per-item detail behind a Disclosure */}
      {fold != null ? (
        <div
          className="surface-choice-card-fold"
          onClick={onFoldClick ?? ((e) => e.preventDefault())}
        >
          <Disclosure label={foldLabel ?? "Details"} defaultOpen={false}>
            {fold}
          </Disclosure>
        </div>
      ) : null}
    </Tag>
  );
}
