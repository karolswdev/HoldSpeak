/* The first-run card: ChoiceCardShell with a title and one state slot. */
import type { ReactNode } from "react";
import { ChoiceCardShell } from "../surface";

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
      <div className="firstrun-card-body">{children}</div>
    </ChoiceCardShell>
  );
}
