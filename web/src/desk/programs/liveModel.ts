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
    step_id: stepId,
    revision: program.revision,
    checkpoint_id: Math.max(
      0,
      ...program.checkpoints.map((row) => Number(row.id)),
    ),
  };
}
export function bindingId(program: Program, stepId = "") {
  return `${program.id}:${stepId}:${program.revision}:${answerBinding(program).checkpoint_id}`;
}
export function currentStep(program: Program): ProgramStep | null {
  const asked = program.your_turn_items.find((item) => item.step_id);
  return (
    program.steps.find((step) => step.id === asked?.step_id) ??
    program.steps.find((step) =>
      ["briefed", "working", "checking", "review", "pr_open"].includes(
        step.state,
      ),
    ) ??
    program.steps.find((step) => !["done", "merged"].includes(step.state)) ??
    program.steps.at(-1) ??
    null
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
  const tonight = row.id === nightId && row.state !== "done";
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
    return "This program changed · Your answer was not applied · Read it again";
  return `The change was not saved · ${plainReason(cause)} · Your input is kept · Try again`;
}
export function staleAnswer(cause: unknown): boolean {
  return (
    cause instanceof ApiError &&
    (cause.payload as { code?: string })?.code === "answer_stale"
  );
}
