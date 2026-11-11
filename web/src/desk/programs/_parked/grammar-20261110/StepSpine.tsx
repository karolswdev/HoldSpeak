/* Parked: the live kit owns the Programs window grammar. */
/* The step spine (the language, 2026-11-08; ProgramsBold canvas): the
 * Program's steps as one numbered row of 6 px bars, "01 Read the fold"
 * under each. A done step is steel; the step that waits on him is brass
 * with a brass tint ring; a running step is steel and breathes; a red step
 * is coral; a parked step graphite; a step ahead is idle grey. It is a picture: the plate under it
 * and the step list are what he presses. At 393 the names fold away and
 * the numbers stay (a container query in programs.css). */
import type { Program, ProgramStep } from "./types";

const RUNNING = new Set(["briefed", "working", "checking", "review", "pr_open"]);

export type SpineMark = "done" | "here" | "running" | "red" | "parked" | "ahead";

export type SpineStep = { id: string; number: string; name: string; mark: SpineMark };

/** Two digits: "01". */
export const stepNumber = (ordinal: number): string => String(ordinal).padStart(2, "0");

function markOf(step: ProgramStep, held: Set<string>): SpineMark {
  if (step.state === "merged" || step.state === "done") return "done";
  if (held.has(step.id)) return "here";
  if (RUNNING.has(step.state)) return "running";
  if (step.state === "check_failed" || step.state === "failed") return "red";
  if (step.state === "parked") return "parked";
  return "ahead";
}

export function spineSteps(program: Program): SpineStep[] {
  const held = new Set((program.your_turn_items ?? []).map((item) => item.step_id).filter(Boolean));
  return program.steps.filter((step) => !step.race_of)
    .map((step) => ({ id: step.id, number: stepNumber(step.ordinal), name: step.title, mark: markOf(step, held) }));
}

/** The words a screen reader hears: "5 steps, 2 done, step 03 Merge waits on you". */
function spineLabel(steps: readonly SpineStep[]): string {
  const done = steps.filter((step) => step.mark === "done").length;
  const parts = [steps.length === 1 ? "1 step" : `${steps.length} steps`];
  if (done) parts.push(`${done} done`);
  const here = steps.find((step) => step.mark === "here");
  const run = steps.find((step) => step.mark === "running");
  if (here) parts.push(`step ${here.number} ${here.name} waits on you`);
  else if (run) parts.push(`step ${run.number} ${run.name} runs`);
  return parts.join(", ");
}

export function StepSpine({ program, current }: { program: Program; current?: string | null }) {
  const steps = spineSteps(program);
  if (!steps.length) return null;
  return (
    <ol className="pg-spine" aria-label={spineLabel(steps)} data-testid="programs-spine"
      style={{ gridTemplateColumns: `repeat(${steps.length}, minmax(0, 1fr))` }}>
      {steps.map((step) => (
        <li key={step.id} className="pg-spine-step" data-mark={step.mark} data-step={step.id}
          data-current={step.id === current ? "" : undefined} data-testid="programs-spine-step">
          <i className="pg-spine-bar" aria-hidden="true" />
          <span className="pg-spine-words">
            <span className="pg-spine-number">{step.number}</span>
            <span className="pg-spine-name" title={step.name}>{step.name}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}
