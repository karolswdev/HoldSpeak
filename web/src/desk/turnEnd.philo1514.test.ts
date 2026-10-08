// PHILO-15 lane 14 (B48): a turn end is ASKS only when a real question waits.
// The same cases as `tests/unit/test_philo15_codex_launch_truth.py`
// (`agent_context.models.asks_a_question`): the hub and the client agree.
import { describe, expect, it } from "vitest";
import { asksAQuestion, coderItems, coderTurnEnd, reportsAProblem } from "./needsYou";
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
    ["Should I deploy to production?\n\nThe change is done and all tests pass.", true],
    ["Hi! Thanks for the brief. Which branch should I push to? Everything else is done.", true],
    ["Should I push the branch? " + "I wrote SECURITY.md and its test, ran both tests, and committed. ".repeat(5), true],
    ["Should I deploy to production. The change is done.", true],
    ["Want me to open the PR now", true],
    ["I can push it next. The change is done.", false],
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

// PHILO-15 20 (B68): the finished report of rehearsal 2 (shot 49, its exact
// words) is no question and no problem: the turn end is DONE, not ASKS. The
// same text is fenced in `tests/unit/test_philo15_20_yolo_reads.py`.
describe("B68: a confirmation with no question reads done", () => {
  const REPORT =
    "Confirmed — already conforming to the re-brief: - No files written outside the worktree. Only " +
    "`CODEOWNERS` and `tests/codeowners_test.sh` were created, both inside the worktree. (The earlier " +
    "`/tmp` write attempts were blocked, so nothing landed outside.) - PR opened via `gh pr create` with " +
    "the body passed inline through `--body`. **Current state** - Worktree clean; branch " +
    "`hs/action-action_8ea0eb39eb080881760399af` pushed, not on main. - PR " +
    "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/4 — `OPEN`, `MERGEABLE`, body " +
    "names `action:action_8ea0eb39eb080881760399af` and its test `tests/codeowners_test.sh`. - " +
    "`CODEOWNERS` maps `*` → Kiraal Swedeva; test passes. Item meets the done criteria (PR open, tests " +
    "pass). I left the merge to you per the Squash-Merge-only decision.";

  it("is no question, no problem, and no Needs row", () => {
    expect(asksAQuestion(REPORT)).toBe(false);
    expect(reportsAProblem(REPORT)).toBe(false);
    expect(coderTurnEnd({ hook_event_name: "Stop", question: REPORT })).toBe("idle");
  });

  it.each([
    ["The earlier /tmp write attempts were blocked, so nothing landed outside.", false],
    ["The push was denied by the gate; the branch stays local.", false],
    ["The lint check failed on PR #3.", true],
    ["The build is blocked on a missing secret.", true],
    ["Tests failed after the write attempts were blocked.", true],
    ["The write was blocked by the desk.", false],
    ["The call was denied from the desk.", false],
    ["The API call was blocked by a firewall.", true],
    ["The push was blocked by branch protection.", true],
    ["The merge attempts were blocked by a failing check.", true],
    ["The deploy was blocked by the hook.", true],
  ])("%j → problem %s", (text, problem) => {
    expect(reportsAProblem(text)).toBe(problem);
  });
});
