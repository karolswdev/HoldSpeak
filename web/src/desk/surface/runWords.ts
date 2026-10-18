export type RunFailureReason =
  | "no_engine"
  | "engine_busy"
  | "did_not_answer"
  | "refused"
  | "too_long"
  | "not_usable"
  | "timed_out"
  | "stopped"
  | "not_reachable"
  | "source_gone"
  | "not_sent"
  | "still_running"
  | "";

export function reasonWords(
  reason: string | undefined,
  model = "Engine",
  elapsedSeconds?: number,
): string {
  switch (reason as RunFailureReason) {
    case "no_engine": return "No engine for answers";
    case "engine_busy": return `${model || "Engine"} was busy and did not answer`;
    case "did_not_answer": return `${model || "Engine"} did not answer`;
    case "refused": return `${model || "Engine"} refused it`;
    case "too_long": return `Too long for ${model || "the engine"}`;
    case "not_usable": return "The answer was not usable";
    case "timed_out": return elapsedSeconds
      ? `Timed out after ${Math.max(0, Math.round(elapsedSeconds))} s`
      : `${model || "Engine"} did not answer in time`;
    case "stopped": return "Stopped";
    case "not_reachable": return `${model || "Engine"} not reachable`;
    case "source_gone": return "A source was deleted";
    case "not_sent": return "The question was not sent";
    case "still_running": return "Still working on it";
    default: return "Not answered";
  }
}

export function reasonVerb(reason: string | undefined): string {
  switch (reason as RunFailureReason) {
    case "no_engine": return "Choose an engine";
    case "too_long":
    case "still_running": return "";
    case "source_gone":
    case "refused":
    case "stopped": return "Ask again";
    default: return "Try again";
  }
}

const REASONS = new Set<string>([
  "no_engine", "engine_busy", "did_not_answer", "refused", "too_long", "not_usable",
  "timed_out", "stopped", "not_reachable", "source_gone", "not_sent", "still_running",
]);

/** True when `code` is one of the hub's face reason tokens (Betterment Q1). */
export function isRunFailureReason(code: string | undefined): code is RunFailureReason {
  return Boolean(code) && REASONS.has(String(code));
}
