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
  // HS-201-06 (Constitution tenet 4, ASD-STE100): a state word is not a
  // counted noun. The Models face said `7 WAITINGS` because the default
  // plural appended an S to "WAITING" (audits/face-walk-opus.md, row 6).
  it("never pluralises a state word", () => {
    expect(countToken(7, "WAITING")).toBe("7 WAITING");
    expect(countToken(2, "FAILED")).toBe("2 FAILED");
    expect(countToken(4, "waiting")).toBe("4 waiting");
    expect(countToken(3, "THING WAITING")).toBe("3 THING WAITING");
  });
  it("still pluralises a real noun that ends in -ing", () => {
    expect(countToken(3, "MEETING")).toBe("3 MEETINGS");
    expect(countToken(1, "MEETING")).toBe("1 MEETING");
  });
  it("an explicit plural always wins", () => {
    expect(countToken(3, "GROUP SET", "GROUPS SET")).toBe("3 GROUPS SET");
  });
  it("countLabel omits the zero", () => {
    expect(countLabel("NEEDS YOU", 0)).toBe("NEEDS YOU");
    expect(countLabel("NEEDS YOU", 3)).toBe("NEEDS YOU 3");
  });
});
