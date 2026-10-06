/* The first-run card: ChoiceCardShell with a title and one state slot. */
import type { ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { ChoiceCardShell, StateChip } from "../surface";

export function Card({
  title,
  state,
  lit,
  selected,
  disabled,
  className,
  testId,
  children,
}: {
  title: string;
  state?: ReactNode;
  lit?: boolean;
  selected?: boolean;
  disabled?: boolean;
  className?: string;
  testId: string;
  children: ReactNode;
}) {
  return (
    <ChoiceCardShell
      as="section"
      aria-label={title}
      className={`firstrun-card${className ? ` ${className}` : ""}`}
      data-testid={testId}
      lit={lit}
      selected={selected}
      disabled={disabled}
      label={
        <span className="firstrun-cardhead">
          <span className="firstrun-card-title">{title}</span>
          {state ? <span className="firstrun-cardstate">{state}</span> : null}
        </span>
      }
    >
      {children ? <div className="firstrun-card-body">{children}</div> : null}
    </ChoiceCardShell>
  );
}

/** An optional card's Skip (owner ruling 2026-10-06). */
export interface SkipProps {
  skipped: boolean;
  busy: boolean;
  error: string;
  onSkip: () => void;
}

/** SKIPPED, as the card's state token. */
export function SkippedChip() {
  return <StateChip state="idle" label="SKIPPED" />;
}

/** The Skip verb at the card's foot, and NOT SAVED when the write failed. */
export function SkipFoot({ title, skip }: { title: string; skip: SkipProps }) {
  return (
    <>
      {skip.error ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="failure" label="NOT SAVED" />
          <span className="firstrun-reason">{skip.error}</span>
        </div>
      ) : null}
      <div className="firstrun-card-foot">
        <Button
          dense
          variant="ghost"
          className="firstrun-skip"
          aria-label={`Skip ${title}`}
          loading={skip.busy}
          disabled={skip.busy}
          onClick={skip.onSkip}
        >
          Skip
        </Button>
      </div>
    </>
  );
}
