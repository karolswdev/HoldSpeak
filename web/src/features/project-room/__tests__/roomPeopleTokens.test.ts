// HS-172-07 — monogram + person token resolver tests.
//
// Covers: monogram derivation, absent-at-zero, no pronoun/first-name
// derivation from the display name.

import { describe, it, expect } from "vitest";
import { monogram, buildPersonTokens } from "../RoomPeopleSection";
import type { RoomPersonItem } from "../api";

describe("monogram", () => {
  it("takes the first letter of the first two words", () => {
    expect(monogram("Ania Kowalska")).toBe("AK");
    expect(monogram("Marek Kubiak")).toBe("MK");
  });

  it("takes two letters from a single word", () => {
    expect(monogram("Ania")).toBe("AN");
  });

  it("handles empty string", () => {
    expect(monogram("")).toBe("");
  });

  it("handles extra whitespace", () => {
    expect(monogram("  Ania   Kowalska  ")).toBe("AK");
  });

  it("uppercases the result", () => {
    expect(monogram("ania kowalska")).toBe("AK");
  });

  it("handles three or more words by taking first two", () => {
    expect(monogram("Jan Maria Rokita")).toBe("JM");
  });

  it("never derives a first name or pronoun", () => {
    // The monogram is purely visual; no semantic derivation
    const mono = monogram("Dr. Smith");
    expect(mono).toBe("DS");
    // It does NOT try to extract "Smith" or any pronoun
  });
});

describe("buildPersonTokens", () => {
  it("returns null for zero counts (absent at zero)", () => {
    const person: RoomPersonItem = {
      relationship_id: "r1",
      display_name: "Test",
    };
    const tokens = buildPersonTokens(person);
    expect(tokens.prsWaiting).toBeNull();
    expect(tokens.assignmentsOverdue).toBeNull();
  });

  it("returns PR waiting token for non-zero", () => {
    const person: RoomPersonItem = {
      relationship_id: "r1",
      display_name: "Test",
      prs_waiting: 2,
    };
    const tokens = buildPersonTokens(person);
    expect(tokens.prsWaiting).toBe("2 PRS WAITING");
  });

  it("returns singular PR WAITING for 1", () => {
    const person: RoomPersonItem = {
      relationship_id: "r1",
      display_name: "Test",
      prs_waiting: 1,
    };
    const tokens = buildPersonTokens(person);
    expect(tokens.prsWaiting).toBe("1 PR WAITING");
  });

  it("returns overdue token for non-zero", () => {
    const person: RoomPersonItem = {
      relationship_id: "r1",
      display_name: "Test",
      assignments_overdue: 1,
    };
    const tokens = buildPersonTokens(person);
    expect(tokens.assignmentsOverdue).toBe("1 ASSIGNMENT OVERDUE");
  });

  it("returns plural overdue for > 1", () => {
    const person: RoomPersonItem = {
      relationship_id: "r1",
      display_name: "Test",
      assignments_overdue: 3,
    };
    const tokens = buildPersonTokens(person);
    expect(tokens.assignmentsOverdue).toBe("3 ASSIGNMENTS OVERDUE");
  });

  it("returns both tokens when both non-zero", () => {
    const person: RoomPersonItem = {
      relationship_id: "r1",
      display_name: "Test",
      prs_waiting: 2,
      assignments_overdue: 1,
    };
    const tokens = buildPersonTokens(person);
    expect(tokens.prsWaiting).toBe("2 PRS WAITING");
    expect(tokens.assignmentsOverdue).toBe("1 ASSIGNMENT OVERDUE");
  });
});
