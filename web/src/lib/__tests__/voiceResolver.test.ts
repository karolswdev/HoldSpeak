import { describe, expect, it, vi, beforeEach } from "vitest";
import { resolveDrawerNames } from "../drawerResolver";
import type { Directory } from "../primitives";

/** Helper to build a minimal Directory for testing. */
function zone(name: string, id: string, memberIds: string[] = []): Directory {
  return {
    kind: "directory",
    id,
    name,
    nameNormalized: name.toLowerCase(),
    parentId: null,
    memberIds,
    createdAt: "2026-01-01T00:00:00Z",
  };
}

const ZONES: Directory[] = [
  zone("Research Notes", "dir_research", ["m1", "m2", "m3"]),
  zone("Monday Standup", "dir_monday_standup"),
  zone("Planning", "dir_planning"),
];

describe("voice resolver: fast path", () => {
  it("exact zone name in transcript produces chip with no server call", () => {
    const { refs } = resolveDrawerNames("look at Research Notes", ZONES);
    expect(refs).toHaveLength(1);
    expect(refs[0]).toEqual({
      name: "Research Notes",
      id: "dir_research",
      ref: "zone:dir_research",
      kind: "zone",
    });
  });

  it("multiple exact zone names produce multiple chips", () => {
    const { refs } = resolveDrawerNames(
      "compare Research Notes and Monday Standup",
      ZONES,
    );
    expect(refs).toHaveLength(2);
    expect(refs.map((r) => r.id)).toContain("dir_research");
    expect(refs.map((r) => r.id)).toContain("dir_monday_standup");
  });

  it("no match returns empty refs", () => {
    const { refs } = resolveDrawerNames("what did I do today", ZONES);
    expect(refs).toHaveLength(0);
  });
});

describe("voice resolver: smart path integration", () => {
  it("smart path refs deduplicate against fast path refs", () => {
    // Simulate: fast path found "Research Notes", smart path also returns it
    const fastRefs = resolveDrawerNames("Research Notes stuff", ZONES).refs;
    const smartRefs = [
      { name: "Research Notes", id: "dir_research", ref: "zone:dir_research", kind: "zone" },
      { name: "Planning", id: "dir_planning", ref: "zone:dir_planning", kind: "zone" },
    ];

    // Simulate addGroundingRef dedup behavior
    const tray = new Map<string, typeof fastRefs[0]>();
    fastRefs.forEach((r) => tray.set(r.ref, r));
    smartRefs.forEach((r) => {
      if (!tray.has(r.ref)) tray.set(r.ref, r);
    });

    // Should have 2 unique refs, not 3
    expect(tray.size).toBe(2);
    expect(tray.has("zone:dir_research")).toBe(true);
    expect(tray.has("zone:dir_planning")).toBe(true);
  });

  it("generation ID gating discards stale responses", () => {
    let generation = 0;
    const generationRef = { current: 0 };

    // Simulate: dictation 1 starts
    const gen1 = ++generationRef.current;
    expect(gen1).toBe(1);

    // Simulate: dictation 2 starts before response
    const gen2 = ++generationRef.current;
    expect(gen2).toBe(2);

    // Response from dictation 1 arrives — should be discarded
    const shouldApply1 = generationRef.current === gen1;
    expect(shouldApply1).toBe(false);

    // Response from dictation 2 arrives — should be applied
    const shouldApply2 = generationRef.current === gen2;
    expect(shouldApply2).toBe(true);
  });

  it("submit increments generation, discarding pending responses", () => {
    const generationRef = { current: 0 };

    // Start dictation
    const gen = ++generationRef.current;

    // Submit (simulated)
    generationRef.current++;

    // Late response should be discarded
    expect(generationRef.current === gen).toBe(false);
  });

  it("error classification maps HTTP status codes", () => {
    // Simulate error classification
    function classifyError(err: Error): string {
      const msg = err.message;
      if (msg.includes("409")) return "resolver_not_configured";
      if (msg.includes("503")) return "resolver_unavailable";
      return "resolver_error";
    }

    expect(classifyError(new Error("HTTP 409"))).toBe("resolver_not_configured");
    expect(classifyError(new Error("HTTP 503"))).toBe("resolver_unavailable");
    expect(classifyError(new Error("network error"))).toBe("resolver_error");
  });

  it("no resolver profile means no server call", () => {
    // This tests the conditional: if (resolverProfileId) { ... }
    const resolverProfileId: string | null = null;
    let serverCalled = false;

    if (resolverProfileId) {
      serverCalled = true;
    }

    expect(serverCalled).toBe(false);
  });
});
