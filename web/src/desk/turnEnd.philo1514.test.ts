// PHILO-15 lane 14 (B48): a turn end is ASKS only when a real question waits.
// The same cases as `tests/unit/test_philo15_codex_launch_truth.py`
// (`agent_context.models.asks_a_question`): the hub and the client agree.
import { describe, expect, it } from "vitest";
import { asksAQuestion, coderItems, coderTurnEnd } from "./needsYou";
import { fromWireFlight, fromWireSessionRow } from "./agentFlights";
import { flightWord } from "./drawer/members";
import { agentState } from "./screen/compose";

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

describe("IDLE is a lamp, never a Needs you row (the A5 law)", () => {
  const now = new Date("2026-10-07T17:00:00Z");
  const base = { agent: "codex", hook_event_name: "Stop", awaiting_response: true, lifecycle: "waiting",
    updated_at: "2026-10-07T16:59:00Z", wait_started_at: "2026-10-07T16:59:00Z" };

  it("Needs you lists a real question and drops a turn end with no question", () => {
    const rows = coderItems([
      { ...base, session_id: "asks", question: "Shall I open the PR?" },
      { ...base, session_id: "idle", question: "Done. PR #2 is open." },
    ], now);
    expect(rows.map((r) => r.sessionKey)).toEqual(["codex:asks"]);
  });

  it("the Conductor lamp and the drawer say IDLE for it, ASKS for a question", () => {
    const idleRow = fromWireSessionRow({ session: { ...base, session_id: "idle", question: "Done. PR #2 is open." } });
    const askRow = fromWireSessionRow({ session: { ...base, session_id: "asks", question: "Shall I open the PR?" } });
    expect(agentState(idleRow)).toBe("idle");
    expect(agentState(askRow)).toBe("ask");
    const idleFlight = fromWireFlight({ origin_ref: "action:a", state: "waiting", turn_end: "idle", agent: "codex" });
    expect(flightWord(idleFlight)).toEqual({ label: "IDLE", tone: "info" });
    expect(flightWord(fromWireFlight({ origin_ref: "action:a", state: "waiting", turn_end: "asks", agent: "codex" }))).toEqual({ label: "ASKS", tone: "ask" });
  });
});
