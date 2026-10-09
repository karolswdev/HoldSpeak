// PHILO-16 (C) — five state words, never eleven (§12 rule 6).
import { describe, expect, it } from "vitest";
import { STATE_WORDS, stateWord } from "../stateWord";

describe("stateWord", () => {
  it("maps every backend word to one of the five", () => {
    const table: Record<string, string> = {
      // concierge detect / propose (concierge_service.py STATE_*)
      READY: "READY",
      WAITING: "WAITING",
      NOT_SET: "OFF",
      UNREACHABLE: "BROKEN",
      CHECKING: "WAITING",
      LIMITED: "LIMITED",
      INCOMPATIBLE: "BROKEN",
      UNKNOWN: "WAITING",
      NOT_SUPPORTED: "BROKEN",
      // the roster (inference_assignment_service.assignment_summary)
      assigned: "READY",
      no_assignment: "OFF",
      no_compatible_assignment: "BROKEN",
      // a binding's readiness
      ready: "READY",
      missing: "BROKEN",
      disabled: "OFF",
      unknown: "WAITING",
      // an acquisition
      downloading: "WAITING",
      failed: "BROKEN",
      cancelled: "OFF",
      // the summary row and the task probe
      attention: "BROKEN",
      REFUSED: "BROKEN",
      off: "OFF",
    };
    for (const [raw, word] of Object.entries(table)) expect(stateWord(raw), raw).toBe(word);
  });

  it("never answers a word outside the five, and never READY for what it cannot read", () => {
    for (const raw of ["", null, undefined, "SOMETHING_NEW", "not set", "no-assignment"]) {
      expect(STATE_WORDS).toContain(stateWord(raw));
    }
    expect(stateWord("SOMETHING_NEW")).toBe("WAITING");
    expect(stateWord(undefined)).toBe("WAITING");
    expect(stateWord("not set")).toBe("OFF");
  });
});
