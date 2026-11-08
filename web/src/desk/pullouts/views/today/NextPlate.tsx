/** Today's first plate (the language, 2026-11-08): the one thing first,
 *  raised over the day. The next meeting: its sprite, its name, its time
 *  and countdown in mono, its four steps as one spine (the current one
 *  brass) and its verbs: Prep (the brass Button while prep is the step that
 *  waits on him) and Record, or Record when it starts. */
import type { ReactNode } from "react";
import { Button } from "../../../../components/signal/Signal";
import { DotWord } from "../../../surface/kit";
import { Spine, type SpineSegment } from "../../../surface/patterns/Spine";
import { spriteUrl } from "../../../sprites";
import { calendarOpener } from "../../../openObject";
import { clock, countdown, currentStep, SHORT_DAYS, startOfDay, when, type DayEvent } from "./time";

export const PLATE_STEPS = ["prep", "record", "summary", "follow-up"] as const;

/** The steps as spine parts: moss done, brass the current, idle ahead. */
export function stepSegments(step: number): SpineSegment[] {
  return PLATE_STEPS.map((_, index) => ({ tone: index < step ? "moss" : index === step ? "brass" : "idle", share: 1 }));
}

export function eventTitle(event: DayEvent): string {
  return event.title || event.event_title || "Meeting";
}

export function NextPlate({ next, now, recordLead, busy, error, onRecord, onArm }: {
  next: DayEvent;
  now: Date;
  recordLead: boolean;
  busy: boolean;
  error: string | null;
  onRecord(): void;
  onArm(): void;
}) {
  const start = when(next.starts_at)!;
  const open = calendarOpener(next);
  const started = start.getTime() <= now.getTime();
  const armed = Boolean(next.armed || next.source === "scheduled_recording");
  const armsAt = when(next.armed?.arms_at ?? next.starts_at);
  const step = currentStep(next, now);
  const kind = next.person_relationship_id ? "person" : "meeting";
  const facts: ReactNode[] = [
    startOfDay(start) === startOfDay(now) ? clock(start) : `${SHORT_DAYS[start.getDay()]} ${clock(start)}`,
    <span key="in" className="today-next-in" data-testid="today-countdown">{countdown(start, now)}</span>,
    next.person_label ?? null,
    next.project_name ?? null,
  ].filter(Boolean);
  return (
    <section className="today-plate" aria-label={`Next: ${eventTitle(next)}`} data-testid="today-next">
      <h3 className="today-plate-label">Next</h3>
      <div className="today-plate-row">
        <img className="today-plate-glyph" src={spriteUrl(kind, next.person_relationship_id ?? next.id, "rest", null, 32)}
          width={32} height={32} alt="" draggable={false} />
        <div className="today-plate-words">
          <span className="today-plate-title">{eventTitle(next)}</span>
          <span className="today-plate-facts">
            {facts.map((fact, index) => <span key={index}>{index ? " · " : ""}{fact}</span>)}
            {armed ? (
              <DotWord tone="info" className="today-armed" data-testid="today-armed">
                {armsAt ? `Armed for ${clock(armsAt)}` : "Armed"}
              </DotWord>
            ) : null}
          </span>
        </div>
        <div className="today-plate-verbs">
          {open ? <Button dense variant={step === 0 ? "brass" : "secondary"} onClick={open} data-testid="today-open-prep">Prep</Button> : null}
          {started || armed ? (
            <Button dense variant={recordLead ? "primary" : "secondary"} onClick={onRecord} data-testid="today-record">Record</Button>
          ) : next.source === "calendar_event" ? (
            <Button dense variant="secondary" loading={busy} data-testid="today-arm" onClick={onArm}>Record when it starts</Button>
          ) : null}
          {error ? <span role="status" data-testid="today-arm-failed"><DotWord tone="fail">{error}</DotWord></span> : null}
        </div>
      </div>
      <div className="today-plate-steps">
        <ol className="today-plate-stepwords" aria-label="Meeting steps">
          {PLATE_STEPS.map((word, index) => (
            <li key={word} aria-current={index === step ? "step" : undefined} data-state={index < step ? "done" : index === step ? "now" : "later"}>{word}</li>
          ))}
        </ol>
        <Spine segments={stepSegments(step)} className="today-plate-spine" />
      </div>
    </section>
  );
}
