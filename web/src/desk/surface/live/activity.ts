/** Accept the producer's state words. Unknown/future states stay quiet. */
export function activity(state: string): "working" | "waiting" | "done" | "parked" | "planned" {
  if (["briefed", "working", "checking", "review", "pr_open", "running"].includes(state)) return "working";
  if (["waiting", "findings", "merge_ask"].includes(state)) return "waiting";
  if (["merged", "done"].includes(state)) return "done";
  if (["parked", "limited", "failed", "check_failed"].includes(state)) return "parked";
  return "planned";
}
