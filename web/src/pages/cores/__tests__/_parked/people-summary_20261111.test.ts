// PARKED 2026-11-11: Tests of the retired summary label-width and inline-token caps.
import {describe,expect,it} from "vitest";
import {prsSummaryLabel,capTokens} from "../../_parked/peopleSummary_20261111";

describe("prsSummaryLabel", () => {
  it("includes the name when short enough", () => {
    expect(prsSummaryLabel(2, "Ania")).toBe("2 PRs waiting on Ania");
  });

  it("uses singular PR for count 1", () => {
    expect(prsSummaryLabel(1, "Ania")).toBe("1 PR waiting on Ania");
  });

  it("drops the name when the label is too long", () => {
    const longName = "Aleksandra Magdalena Kowalski";
    const label = prsSummaryLabel(2, longName);
    expect(label).toBe("2 PRs waiting");
  });

  it("never contains her/him/she/he", () => {
    for (const name of ["Hermione", "Sheila", "Hershey", "Shelby"]) {
      const label = prsSummaryLabel(1, name);
      // The label should NOT contain pronoun words separated by spaces.
      expect(label).not.toMatch(/\b(her|him|she|he)\b/i);
    }
  });
});

describe("capTokens", () => {
  it("returns empty string for empty array", () => {
    expect(capTokens([])).toBe("");
  });

  it("joins up to three tokens", () => {
    expect(capTokens(["#1", "#2", "#3"])).toBe("#1 · #2 · #3");
  });

  it("caps at three then +N", () => {
    expect(capTokens(["#1", "#2", "#3", "#4", "#5"])).toBe("#1 · #2 · #3 +2");
  });

  it("respects custom max", () => {
    expect(capTokens(["a", "b", "c", "d"], 2)).toBe("a · b +2");
  });

  it("single token", () => {
    expect(capTokens(["#612"])).toBe("#612");
  });
});

