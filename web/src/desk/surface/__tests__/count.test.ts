import { describe, expect, it } from "vitest";
import { countToken, countLabel } from "../count";

describe("countToken (UX-CANON A8: no counters of zero)", () => {
  it("returns null at zero, null, undefined, NaN and negatives", () => {
    for (const v of [0, null, undefined, NaN, -2]) expect(countToken(v as number, "OPEN PR")).toBeNull();
  });
  it("pluralizes by count with the default S", () => {
    expect(countToken(1, "OPEN PR")).toBe("1 OPEN PR");
    expect(countToken(3, "OPEN PR")).toBe("3 OPEN PRS");
  });
  it("honours an explicit plural", () => {
    expect(countToken(2, "MEETING", "MEETINGS")).toBe("2 MEETINGS");
  });
  it("countLabel omits the zero", () => {
    expect(countLabel("NEEDS YOU", 0)).toBe("NEEDS YOU");
    expect(countLabel("NEEDS YOU", 3)).toBe("NEEDS YOU 3");
  });
});
