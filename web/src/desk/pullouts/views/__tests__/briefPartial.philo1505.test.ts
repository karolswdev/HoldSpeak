// PHILO-15 05 (Astra r1 P1): a source the producer could not read is a NOT
// READ row (`source_ref` `not_read:<source>`); the Brief's receipt then reads
// GENERATED · PARTIAL (ChairHome BriefDate, BriefView's generated label).
import { describe, expect, it } from "vitest";
import { briefIsPartial } from "../BriefView";

describe("briefIsPartial", () => {
  it("is true when any section holds a NOT READ row", () => {
    expect(briefIsPartial({
      waiting: [
        { source_ref: "not_read:assignments" },
        { source_ref: "blocker:engines" },
      ],
    })).toBe(true);
  });

  it("is false for a whole brief, an empty one, or a missing one", () => {
    expect(briefIsPartial({ waiting: [{ source_ref: "blocker:engines" }], decisions: [] })).toBe(false);
    expect(briefIsPartial({ waiting: undefined })).toBe(false);
    expect(briefIsPartial({})).toBe(false);
    expect(briefIsPartial(null)).toBe(false);
  });

  it("a coverage gap (Not observed) is not PARTIAL: it is a watch source, not the producer's read", () => {
    expect(briefIsPartial({ waiting: [{ source_ref: "coverage:github" }] })).toBe(false);
  });
});
