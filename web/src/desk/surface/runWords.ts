export type RunFailureReason =
  | "no_engine"
  | "engine_busy"
  | "did_not_answer"
  | "refused"
  | "too_long"
  | "not_usable"
  | "timed_out"
  | "stopped"
  | "";

export function reasonWords(
  reason: string | undefined,
  model = "Engine",
  elapsedSeconds?: number,
): string {
  switch (reason as RunFailureReason) {
    case "no_engine": return "No engine for answers";
    case "engine_busy": return "Engine busy";
    case "did_not_answer": return `${model || "Engine"} did not answer`;
    case "refused": return `${model || "Engine"} refused it`;
    case "too_long": return `Too long for ${model || "the engine"}`;
    case "not_usable": return "The answer was not usable";
    case "timed_out": return `Timed out after ${Math.max(0, Math.round(elapsedSeconds || 0))} s`;
    case "stopped": return "Stopped";
    default: return "Not answered";
  }
}

export function reasonVerb(reason: string | undefined): string {
  switch (reason as RunFailureReason) {
    case "no_engine": return "Choose an engine";
    case "too_long": return "";
    case "refused":
    case "stopped": return "Ask again";
    default: return "Try again";
  }
}
