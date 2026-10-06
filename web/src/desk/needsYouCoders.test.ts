// Conductor K3: R5 in the browser twin of the one needs-you rule
// (`holdspeak/services/needs_you_membership.py` `coder_items`, held by
// `tests/unit/test_conductor_k3_coder_needs_you.py`).
import { describe, expect, it } from "vitest";
import { attentionClass } from "./attention";
import { coderItems, computeNeedsYou, type NeedsYouCoder } from "./needsYou";

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
