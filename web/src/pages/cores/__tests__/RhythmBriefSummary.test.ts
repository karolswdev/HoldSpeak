import { describe, expect, it } from "vitest";
import { briefSummaryLine } from "../CadenceCore";

// HS-175 counsel C9(a) / H10-3: the Rhythm summary line pluralizes honestly
// and names ARMED as ARMED (never folded into WATCH ITEMS).
describe("briefSummaryLine", () => {
  it("is singular at one and names every part", () => {
    expect(briefSummaryLine([
      { source_ref: "calendar:week", text: "1 meeting this week" },
      { source_ref: "calendar:armed", text: "1 armed" },
      { source_ref: "meeting_watch:decisions", text: "1 decision" },
      { source_ref: "meeting_watch:commitments_due", text: "1 commitment due" },
    ])).toBe("1 meeting · 1 armed · 1 watch item · 1 commitment due");
  });

  it("pluralizes above one", () => {
    expect(briefSummaryLine([
      { source_ref: "calendar:week", text: "3 meetings this week" },
      { source_ref: "calendar:armed", text: "2 armed" },
      { source_ref: "meeting_watch:commitments_due", text: "2 commitments due" },
    ])).toBe("3 meetings · 2 armed · 2 commitments due");
  });

  it("omits zero parts and is absent when nothing counts (A.8)", () => {
    expect(briefSummaryLine([
      { source_ref: "calendar:week", text: "2 meetings this week" },
      { text: "Next: Standup at 10:00" },
    ])).toBe("2 meetings");
    expect(briefSummaryLine([])).toBeNull();
    expect(briefSummaryLine(undefined)).toBeNull();
    expect(briefSummaryLine([{ text: "Next: Standup at 10:00" }])).toBeNull();
  });
});
