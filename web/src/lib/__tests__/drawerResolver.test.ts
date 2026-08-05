import { describe, expect, it } from "vitest";
import { resolveDrawerName, resolveDrawerNames } from "../drawerResolver";
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
  zone("Research", "dir_research", ["m1", "m2", "m3"]),
  zone("Planning", "dir_planning"),
  zone("Monday standup", "dir_monday_standup"),
  zone("Mon", "dir_mon"),
  zone("Now", "dir_now"),
  zone("Plan", "dir_plan"),
];

describe("resolveDrawerName", () => {
  it("exact match", () => {
    const result = resolveDrawerName("Research", ZONES);
    expect(result).toEqual({
      name: "Research",
      id: "dir_research",
      ref: "zone:dir_research",
      kind: "zone",
    });
  });

  it("case-insensitive match", () => {
    const result = resolveDrawerName("research", ZONES);
    expect(result).not.toBeNull();
    expect(result!.name).toBe("Research");
    expect(result!.id).toBe("dir_research");
  });

  it("nonexistent returns null", () => {
    expect(resolveDrawerName("nonexistent", ZONES)).toBeNull();
  });

  it("partial name does not match", () => {
    expect(resolveDrawerName("Res", ZONES)).toBeNull();
  });
});

describe("resolveDrawerNames", () => {
  it("resolves two zones from text", () => {
    const { refs, cleanText } = resolveDrawerNames(
      "summarize Research and Planning",
      ZONES,
    );
    expect(refs).toHaveLength(2);
    expect(refs.map((r) => r.name).sort()).toEqual(["Planning", "Research"]);
    expect(cleanText).toBe("summarize and");
  });

  it("longest-match-first: 'Monday standup' wins over 'Mon'", () => {
    const { refs } = resolveDrawerNames("Monday standup", ZONES);
    expect(refs).toHaveLength(1);
    expect(refs[0].name).toBe("Monday standup");
  });

  it("word boundary: 'Plan' does NOT match 'planning session'", () => {
    // "Plan" followed by "n" is not a boundary.
    const { refs } = resolveDrawerNames("planning session", ZONES);
    const planRef = refs.find((r) => r.name === "Plan");
    expect(planRef).toBeUndefined();
  });

  it("word boundary: 'Now' matches 'do this now' (space before, end of string)", () => {
    const { refs } = resolveDrawerNames("do this now", ZONES);
    expect(refs).toHaveLength(1);
    expect(refs[0].name).toBe("Now");
  });

  it("word boundary: 'Now' matches 'do this now!' (space before, punctuation after)", () => {
    const { refs } = resolveDrawerNames("do this now!", ZONES);
    expect(refs).toHaveLength(1);
    expect(refs[0].name).toBe("Now");
  });

  it("word boundary: 'Now' does NOT match inside 'know'", () => {
    const { refs } = resolveDrawerNames("I don't know", ZONES);
    const nowRef = refs.find((r) => r.name === "Now");
    expect(nowRef).toBeUndefined();
  });

  it("word boundary: zone at start of string matches", () => {
    const zonesWithResearch = [zone("Research", "dir_research")];
    const { refs } = resolveDrawerNames(
      "Research-notes are ready",
      zonesWithResearch,
    );
    expect(refs).toHaveLength(1);
    expect(refs[0].name).toBe("Research");
  });

  it("dedup: same zone appearing twice produces one ref", () => {
    const { refs, cleanText } = resolveDrawerNames(
      "Research plus more Research",
      ZONES,
    );
    expect(refs).toHaveLength(1);
    expect(refs[0].name).toBe("Research");
    // Both occurrences removed from cleanText.
    expect(cleanText).toBe("plus more");
  });

  it("unicode: zone 'Cafe notes' matches 'cafe notes'", () => {
    const cafeZones = [zone("Cafe notes", "dir_cafe")];
    const { refs } = resolveDrawerNames("cafe notes", cafeZones);
    expect(refs).toHaveLength(1);
    expect(refs[0].name).toBe("Cafe notes");
  });

  it("empty text returns empty", () => {
    const { refs, cleanText } = resolveDrawerNames("", ZONES);
    expect(refs).toHaveLength(0);
    expect(cleanText).toBe("");
  });

  it("no zones returns empty", () => {
    const { refs, cleanText } = resolveDrawerNames("some text", []);
    expect(refs).toHaveLength(0);
    expect(cleanText).toBe("some text");
  });

  it("cleanText collapses whitespace", () => {
    const { cleanText } = resolveDrawerNames(
      "check Research today",
      [zone("Research", "dir_research")],
    );
    expect(cleanText).toBe("check today");
  });
});
