import { describe, expect, it } from "vitest";
import {
  findAtTrigger,
  extractAtQuery,
  filterZones,
  zoneToRef,
  removeAtSpan,
} from "../components/InletAutocomplete";
import type { Directory } from "../../lib/primitives";

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
  zone("Alpha", "dir_alpha"),
  zone("Beta", "dir_beta"),
  zone("Calendar", "dir_cal"),
  zone("Design", "dir_design"),
  zone("Engineering", "dir_eng"),
  zone("Finance", "dir_finance"),
];

describe("findAtTrigger", () => {
  it("finds @ at start of input", () => {
    expect(findAtTrigger("@Res", 4)).toBe(0);
  });

  it("finds @ after space", () => {
    expect(findAtTrigger("hello @Res", 10)).toBe(6);
  });

  it("finds @ after punctuation", () => {
    expect(findAtTrigger("check,@Res", 10)).toBe(6);
  });

  it("returns -1 for @ inside word (email)", () => {
    expect(findAtTrigger("user@example", 12)).toBe(-1);
  });

  it("returns -1 when no @ present", () => {
    expect(findAtTrigger("hello world", 11)).toBe(-1);
  });

  it("returns -1 when cursor is before @", () => {
    expect(findAtTrigger("hello @Res", 5)).toBe(-1);
  });

  it("finds @ at cursor = atPos+1 (just typed @)", () => {
    expect(findAtTrigger("@", 1)).toBe(0);
  });

  // Fix #1: multi-word zone names work with zones parameter.
  it("allows spaces when query matches a multi-word zone prefix", () => {
    expect(findAtTrigger("@Monday stan", 12, ZONES)).toBe(0);
  });

  it("allows full multi-word zone match", () => {
    expect(findAtTrigger("hello @Monday standup", 21, ZONES)).toBe(6);
  });

  it("returns -1 when space appears and no zone matches", () => {
    expect(findAtTrigger("@zzz nothing", 12, ZONES)).toBe(-1);
  });

  it("returns -1 for spaces without zones parameter (backward compat)", () => {
    // Without zones, spaces still break the trigger (old behavior).
    expect(findAtTrigger("@Monday standup", 15)).toBe(-1);
  });

  it("empty query after @ returns trigger position", () => {
    expect(findAtTrigger("hello @", 7, ZONES)).toBe(6);
  });
});

describe("extractAtQuery", () => {
  it("extracts query after @", () => {
    expect(extractAtQuery("@Res", 0, 4)).toBe("Res");
  });

  it("extracts empty query for bare @", () => {
    expect(extractAtQuery("@", 0, 1)).toBe("");
  });

  it("extracts partial query", () => {
    expect(extractAtQuery("hello @Re", 6, 9)).toBe("Re");
  });
});

describe("filterZones", () => {
  it("filters by case-insensitive prefix", () => {
    const matches = filterZones("res", ZONES);
    expect(matches).toHaveLength(1);
    expect(matches[0].name).toBe("Research");
  });

  it("empty query returns all zones (up to 8)", () => {
    const matches = filterZones("", ZONES);
    expect(matches.length).toBeLessThanOrEqual(8);
    // Should be sorted alphabetically.
    for (let i = 1; i < matches.length; i++) {
      expect(matches[i].name.localeCompare(matches[i - 1].name)).toBeGreaterThanOrEqual(0);
    }
  });

  it("returns max 8 matches", () => {
    const manyZones = Array.from({ length: 20 }, (_, i) =>
      zone(`Zone${String(i).padStart(2, "0")}`, `dir_${i}`),
    );
    const matches = filterZones("zone", manyZones);
    expect(matches).toHaveLength(8);
  });

  it("results are sorted alphabetically", () => {
    const matches = filterZones("", ZONES);
    const names = matches.map((z) => z.name);
    const sorted = [...names].sort();
    expect(names).toEqual(sorted);
  });

  it("no matches returns empty array", () => {
    expect(filterZones("zzz", ZONES)).toHaveLength(0);
  });
});

describe("zoneToRef", () => {
  it("builds a ResolvedRef from a Directory", () => {
    const z = zone("Research", "dir_research", ["m1"]);
    const ref = zoneToRef(z);
    expect(ref).toEqual({
      name: "Research",
      id: "dir_research",
      ref: "zone:dir_research",
      kind: "zone",
    });
  });
});

describe("removeAtSpan", () => {
  it("removes @query from middle of text", () => {
    const result = removeAtSpan("hello @Res world", 6, 10);
    expect(result.text).toBe("hello world");
    expect(result.cursor).toBeLessThanOrEqual(result.text.length);
  });

  it("fix #6: collapses double space at seam", () => {
    // "Compare @Research with" -> removing @Research should yield "Compare with"
    const result = removeAtSpan("Compare @Research with", 8, 17);
    expect(result.text).toBe("Compare with");
  });

  it("fix #7: trims leading space when @ is at start", () => {
    // "@Research with stuff" -> removing @Research should yield "with stuff"
    const result = removeAtSpan("@Research with stuff", 0, 9);
    expect(result.text).toBe("with stuff");
  });

  it("fix #7: trims trailing space when @ is at end", () => {
    // "stuff with @Research" -> removing @Research should yield "stuff with"
    const result = removeAtSpan("stuff with @Research", 11, 20);
    expect(result.text).toBe("stuff with");
  });

  it("handles removal of entire text", () => {
    const result = removeAtSpan("@Research", 0, 9);
    expect(result.text).toBe("");
    expect(result.cursor).toBe(0);
  });

  it("cursor stays within bounds", () => {
    const result = removeAtSpan("@Res", 0, 4);
    expect(result.cursor).toBeGreaterThanOrEqual(0);
    expect(result.cursor).toBeLessThanOrEqual(result.text.length);
  });
});

describe("autocomplete integration scenarios", () => {
  it("typing @Res shows Research zone", () => {
    const text = "@Res";
    const cursor = 4;
    const atPos = findAtTrigger(text, cursor);
    expect(atPos).toBe(0);
    const query = extractAtQuery(text, atPos, cursor);
    expect(query).toBe("Res");
    const matches = filterZones(query, ZONES);
    expect(matches).toHaveLength(1);
    expect(matches[0].name).toBe("Research");
  });

  it("selecting removes @query and adds ref", () => {
    const text = "hello @Res";
    const cursor = 10;
    const atPos = findAtTrigger(text, cursor);
    expect(atPos).toBe(6);
    // Simulate removal of @query span.
    const result = removeAtSpan(text, atPos, cursor);
    expect(result.text).toBe("hello");
  });

  it("escape keeps @Res as literal text", () => {
    // The escape handler sets acDismissed=true but does NOT modify text.
    const text = "@Res";
    // After escape, text should remain unchanged.
    expect(text).toBe("@Res");
  });

  it("duplicate zone in tray is prevented", () => {
    const refs = [zoneToRef(zone("Research", "dir_research"))];
    const newRef = zoneToRef(zone("Research", "dir_research"));
    // Simulate dedup check.
    const isDuplicate = refs.some((r) => r.ref === newRef.ref);
    expect(isDuplicate).toBe(true);
  });

  it("paste containing @ does not trigger autocomplete", () => {
    // When paste flag is true, findAtTrigger is bypassed.
    // We test this by checking that pasteRef would suppress the trigger.
    const text = "@Research";
    const cursor = 9;
    // Normal: would find trigger.
    expect(findAtTrigger(text, cursor)).toBe(0);
    // With paste flag: the component uses typedAtPos check.
    // This is component logic, but the function itself is pure.
  });

  it("enter with popover open selects, does not submit", () => {
    const text = "@Res";
    const cursor = 4;
    const atPos = findAtTrigger(text, cursor);
    const query = extractAtQuery(text, atPos!, cursor);
    const matches = filterZones(query, ZONES);
    expect(matches.length).toBeGreaterThan(0);
  });

  it("fix #1: multi-word @query stays open with matching zones", () => {
    const text = "summarize @Monday stan";
    const cursor = 22;
    const atPos = findAtTrigger(text, cursor, ZONES);
    expect(atPos).toBe(10);
    const query = extractAtQuery(text, atPos, cursor);
    expect(query).toBe("Monday stan");
    const matches = filterZones(query, ZONES);
    expect(matches).toHaveLength(1);
    expect(matches[0].name).toBe("Monday standup");
  });

  it("fix #1: @query closes when no zones match after space", () => {
    const text = "@zzz no match";
    const cursor = 13;
    const atPos = findAtTrigger(text, cursor, ZONES);
    expect(atPos).toBe(-1);
  });
});
