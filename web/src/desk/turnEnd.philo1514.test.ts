// PHILO-15 lane 14 (B48): a turn end is ASKS only when a real question waits.
// The same cases as `tests/unit/test_philo15_codex_launch_truth.py`
// (`agent_context.models.asks_a_question`): the hub and the client agree.
import { describe, expect, it } from "vitest";
import { asksAQuestion, coderTurnEnd } from "./needsYou";

describe("asksAQuestion (the hub's rule)", () => {
  it.each([
    ["Understood — stopping here … Good luck with the merge!", false],
    ["PR #1 is open and the test passes.", false],
    ["You're welcome — take care!", false],
    ["Should I push the branch?", true],
    ["I made the change.\n\nWhich file should hold the test (a or b)?", true],
    ["Is it **ok?**", true],
    ["See https://x.test/?q=1 for the run.", false],
    ["Is the test needed? I checked: yes. " + "Then I wrote the file and ran it. ".repeat(12), false],
    ["", false],
  ])("%j → %s", (text, asks) => {
    expect(asksAQuestion(text)).toBe(asks);
  });

  it("a permission prompt always asks; a turn end with no question is idle", () => {
    expect(coderTurnEnd({ hook_event_name: "Notification", notification_type: "permission_prompt", question: "Run ls" })).toBe("asks");
    expect(coderTurnEnd({ hook_event_name: "Stop", question: "Done. PR #2 is open." })).toBe("idle");
    expect(coderTurnEnd({ hook_event_name: "Stop", question: "May I push?" })).toBe("asks");
  });
});
