// Conductor K3: R5 in the browser twin of the one needs-you rule
// (`holdspeak/services/needs_you_membership.py` `coder_items`, held by
// `tests/unit/test_conductor_k3_coder_needs_you.py`).
import { describe, expect, it } from "vitest";
import { attentionClass } from "./attention";
import { coderItems, computeNeedsYou, isBlockedCoder, type NeedsYouCoder } from "./needsYou";

const NOW = new Date("2026-10-05T12:00:00Z");

function session(overrides: Partial<NeedsYouCoder> & { minutesAgo?: number } = {}): NeedsYouCoder {
  const { minutesAgo = 2, ...rest } = overrides;
  return {
    agent: "claude",
    session_id: "s1",
    cwd: "/work/holdspeak",
    project_name: "holdspeak",
    repo_root: "/work/holdspeak",
    updated_at: new Date(NOW.getTime() - minutesAgo * 60_000).toISOString(),
    awaiting_response: true,
    lifecycle: "waiting",
    question: "Should I keep the old migration or drop it?",
    ...rest,
  };
}

describe("R5: a coding agent that waits for the owner", () => {
  it("is a member when fresh, awaiting and asking", () => {
    const rows = coderItems([session({ agent: "codex" })], NOW);
    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      id: "coder:codex:s1",
      ref: "coder:codex:s1",
      kind: "coder",
      sessionKey: "codex:s1",
      agent: "codex",
      cwd: "/work/holdspeak",
      projectName: "holdspeak",
      question: "Should I keep the old migration or drop it?",
      ageSeconds: 120,
      why: "TO ANSWER",
    });
    const result = computeNeedsYou({ coders: [session()], now: NOW });
    expect(result.members.map((m) => m.ref)).toEqual(["coder:claude:s1"]);
    expect(result.count).toBe(1);
  });

  it("is not a member when stale (past 30 minutes)", () => {
    expect(coderItems([session({ minutesAgo: 31 })], NOW)).toEqual([]);
    expect(coderItems([session({ minutesAgo: 29 })], NOW)).toHaveLength(1);
  });

  it("is not a member when answered or ended", () => {
    expect(coderItems([session({ awaiting_response: false, question: null })], NOW)).toEqual([]);
    expect(coderItems([session({ question: null })], NOW)).toEqual([]);
    expect(coderItems([session({ lifecycle: "ended" })], NOW)).toEqual([]);
  });

  it("reads the Notification subtype: permission is TO APPROVE, input is TO ANSWER", () => {
    const prompt = session({
      awaiting_response: false, hook_event_name: "Notification",
      notification_type: "permission_prompt",
      question: "Claude needs your permission to use Bash",
    });
    const rows = coderItems([prompt], NOW);
    expect(rows.map((row) => [row.ref, row.why])).toEqual([["coder:claude:s1", "TO APPROVE"]]);
    expect(attentionClass(rows[0], NOW)).toBe("due_today");
    const idle = { ...prompt, notification_type: "idle_prompt", question: "Claude is waiting for your input" };
    expect(coderItems([idle], NOW)[0].why).toBe("TO ANSWER");
    expect(coderItems([session()], NOW)[0].why).toBe("TO ANSWER");
    expect(coderItems([{ ...prompt, notification_type: "auth_success" }], NOW)).toEqual([]);
    expect(coderItems([{ ...prompt, lifecycle: "ended" }], NOW)).toEqual([]);
    expect(coderItems([{ ...prompt, question: null }], NOW)).toEqual([]);
    expect(coderItems([{ ...prompt, hook_event_name: "PreToolUse" }], NOW)).toEqual([]);
  });

  it("never blocks on a non-prompt Notification, even with a surviving flag", () => {
    // Round 2 (B): the subtype decides before awaiting_response.
    const auth = session({
      awaiting_response: true, hook_event_name: "Notification",
      notification_type: "auth_success", question: "Authenticated",
    });
    expect(isBlockedCoder(auth)).toBe(false);
    expect(coderItems([auth], NOW)).toEqual([]);
    expect(isBlockedCoder({ ...auth, notification_type: "some_future_subtype" })).toBe(false);
    expect(isBlockedCoder({ ...auth, notification_type: "elicitation_dialog" })).toBe(true);
    expect(isBlockedCoder({ ...auth, notification_type: null })).toBe(true);
  });

  it("shares the blocked predicate: a surviving awaiting flag without a question is not blocked", () => {
    const worked = session({ awaiting_response: true, question: null, hook_event_name: "PostToolUse", lifecycle: "working" });
    expect(isBlockedCoder(worked)).toBe(false);
    expect(coderItems([worked], NOW)).toEqual([]);
  });

  it("ranks by the wait's start, and names the wait episode for notifications", () => {
    const start = new Date(NOW.getTime() - 20 * 60_000).toISOString();
    const reported = session({ session_id: "first", minutesAgo: 1, wait_started_at: start, wait_id: "w1" });
    const later = session({ session_id: "second", minutesAgo: 5, wait_id: "w2",
      wait_started_at: new Date(NOW.getTime() - 5 * 60_000).toISOString() });
    const result = computeNeedsYou({ coders: [later, reported], now: NOW });
    expect(result.unmutedItems.map((row) => row.ref)).toEqual(["coder:claude:first", "coder:claude:second"]);
    const [row] = coderItems([reported], NOW);
    expect(row.since).toBe(start);
    expect(row.ageSeconds).toBe(20 * 60);
    expect(row.notifyKey).toBe("coder:claude:first#w1");
    expect(row.ref).toBe("coder:claude:first");
  });

  it("ranks with the due-today rows, oldest wait first", () => {
    const [coder] = coderItems([session()], NOW);
    expect(attentionClass(coder, NOW)).toBe("due_today");
    const result = computeNeedsYou({
      coders: [session({ session_id: "new", minutesAgo: 1 }), session({ session_id: "old", minutesAgo: 20 })],
      roomItems: [{
        id: "p1:github:old", ref: "old-row", projectId: "p1", title: "No due date row",
        why: "CI RED", since: new Date(NOW.getTime() - 86_400_000).toISOString(),
        source: "github", severity: "danger",
      }],
      now: NOW,
    });
    expect(result.unmutedItems.map((row) => row.ref)).toEqual([
      "coder:claude:old", "coder:claude:new", "old-row",
    ]);
  });
});
