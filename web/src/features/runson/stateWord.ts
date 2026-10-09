// PHILO-16 (C) — five state words, and never eleven (COMPOSITOR.md §12 rule 6).
//
// The backend says READY · WAITING · NOT_SET · UNREACHABLE · CHECKING ·
// LIMITED · INCOMPATIBLE · UNKNOWN · NOT_SUPPORTED (concierge detect and
// propose), the roster says assigned · no_assignment · no_compatible_assignment,
// a binding says ready · missing · disabled · unknown, an acquisition says
// requested · downloading · ... · failed. This one function is the only place
// any of them becomes a word on the face. A limitation is never a state: it
// is a token on the wire or the job (`WITHOUT VISION`).

export type StateWord = "READY" | "LIMITED" | "BROKEN" | "WAITING" | "OFF";

export const STATE_WORDS: readonly StateWord[] = ["READY", "LIMITED", "BROKEN", "WAITING", "OFF"];

const MAP: Record<string, StateWord> = {
  READY: "READY",
  ASSIGNED: "READY",
  OK: "READY",
  SUCCEEDED: "READY",

  LIMITED: "LIMITED",

  WAITING: "WAITING",
  CHECKING: "WAITING",
  // The hub cannot say yet: never READY.
  UNKNOWN: "WAITING",
  REQUESTED: "WAITING",
  RESOLVING_SOURCE: "WAITING",
  DOWNLOADING: "WAITING",
  VERIFYING: "WAITING",
  INSTALLING: "WAITING",

  NOT_SET: "OFF",
  NO_ASSIGNMENT: "OFF",
  UNASSIGNED: "OFF",
  OFF: "OFF",
  DISABLED: "OFF",
  CANCELLED: "OFF",

  UNREACHABLE: "BROKEN",
  INCOMPATIBLE: "BROKEN",
  NOT_SUPPORTED: "BROKEN",
  NO_COMPATIBLE_ASSIGNMENT: "BROKEN",
  MISSING: "BROKEN",
  FAILED: "BROKEN",
  REFUSED: "BROKEN",
  ATTENTION: "BROKEN",
  INDETERMINATE: "BROKEN",
};

/** Any backend state, as one of the five words. Unknown input is WAITING. */
export function stateWord(raw: string | null | undefined): StateWord {
  const key = String(raw ?? "")
    .trim()
    .toUpperCase()
    .replace(/[\s-]+/g, "_");
  return MAP[key] ?? "WAITING";
}

/** The Switchboard's class for a word. */
export function stateClass(word: StateWord): "ready" | "limited" | "broken" | "waiting" | "off" {
  return word.toLowerCase() as "ready" | "limited" | "broken" | "waiting" | "off";
}
