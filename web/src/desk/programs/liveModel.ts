import { ApiError } from "../../lib/api";
import { plainReason } from "../surface/plainFailure";
import type { LampState, ObjectListRow } from "../surface";
import type {
  AnswerBinding,
  Program,
  ProgramStep,
  ProgramSummary,
} from "./types";

export function answerBinding(program: Program, stepId = ""): AnswerBinding {
  return {
    program_id: program.id,
    step_id: stepId,
    step_revision:
      allSteps(program).find((row) => row.id === stepId)?.updated_at || "",
    revision: program.revision,
    checkpoint_id: Math.max(
      0,
      ...program.checkpoints
        .filter((row) => !stepId || !row.step_id || row.step_id === stepId)
        .map((row) => Number(row.id)),
    ),
  };
}
export function boundId(
  binding: AnswerBinding,
  programId = binding.program_id ?? "",
) {
  return `${programId}:${binding.step_id}:${binding.revision}:${binding.step_revision || ""}:${binding.checkpoint_id}`;
}
export function bindingId(program: Program, stepId = "") {
  return boundId(answerBinding(program, stepId), program.id);
}

const WORKING_STEPS = new Set([
  "briefed",
  "working",
  "checking",
  "review",
  "pr_open",
]);
const FINISHED_STEPS = new Set(["done", "merged"]);
export function allSteps(program: Program): ProgramStep[] {
  return program.steps.flatMap((step) => [step, ...(step.contenders ?? [])]);
}
export function stepResult(step: ProgramStep): ProgramStep {
  const group = [step, ...(step.contenders ?? [])];
  return (
    group.find((s) => FINISHED_STEPS.has(s.state)) ??
    group.find((s) => WORKING_STEPS.has(s.state)) ??
    step
  );
}
export function currentStep(program: Program): ProgramStep | null {
  const steps = allSteps(program),
    asked = program.your_turn_items.find((item) => item.step_id);
  return (
    steps.find((step) => step.id === asked?.step_id) ??
    steps.find((step) => WORKING_STEPS.has(step.state)) ??
    program.steps.find((step) => !FINISHED_STEPS.has(stepResult(step).state)) ??
    (program.steps.at(-1) ? stepResult(program.steps.at(-1)!) : null)
  );
}

export function liveLamp(state: string): LampState {
  return ["waiting", "merge_ask", "findings"].includes(state)
    ? "waiting"
    : [
          "running",
          "briefed",
          "working",
          "checking",
          "review",
          "pr_open",
        ].includes(state)
      ? "working"
      : ["done", "merged"].includes(state)
        ? "done"
        : "off";
}
export function programRow(
  row: Pick<
    ProgramSummary,
    "id" | "title" | "state" | "state_word" | "done" | "total" | "your_turn"
  > &
    Partial<ProgramSummary>,
  nightId?: string | null,
): ObjectListRow {
  const tonight =
    (row.night_queued ?? row.id === nightId) &&
    !["done", "parked", "failed", "drafting"].includes(row.state);
  return {
    id: row.id,
    kind: "program",
    name: row.title,
    detail: row.line || `${row.done} of ${row.total} steps · ${row.state_word}`,
    group: row.your_turn ? 0 : tonight ? 2 : row.state === "running" ? 1 : 3,
    leadingLamp: {
      state: row.your_turn
        ? "waiting"
        : tonight
          ? "tonight"
          : liveLamp(row.state),
      label: row.state_word,
    },
    meter: { current: row.done, total: row.total, state: row.state },
  };
}
export const choiceWord = (word: string) =>
  ({
    go_on: "Go on",
    not_yet: "Not yet",
    fix_now: "Fix now",
    not_now: "Not now",
    send_back: "Send back",
    cant: "Cannot do",
    fix_program: "Make program",
  })[word] ?? word.replaceAll("_", " ").replace(/^./, (s) => s.toUpperCase());

export function programFailure(cause: unknown): string {
  if (
    cause instanceof ApiError &&
    (cause.payload as { code?: string })?.code === "answer_stale"
  )
    return "This question changed. Read it again.";
  return `The change was not saved · ${plainReason(cause)} · Your input is kept · Try again`;
}
export function staleAnswer(cause: unknown): boolean {
  return (
    cause instanceof ApiError &&
    (cause.payload as { code?: string })?.code === "answer_stale"
  );
}

/** Daily automation runs occupy one master row: the newest run. */
export function latestRuns(
  programs: readonly ProgramSummary[],
): ProgramSummary[] {
  const newest = new Map<string, ProgramSummary>();
  for (const row of programs) {
    if (row.automation_id) {
      const seen = newest.get(row.automation_id);
      if (!seen || row.created_at > seen.created_at)
        newest.set(row.automation_id, row);
    }
  }
  return programs.filter(
    (row) => !row.automation_id || newest.get(row.automation_id) === row,
  );
}
