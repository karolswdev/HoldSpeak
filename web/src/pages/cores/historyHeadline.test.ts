// HS-201-01 — the Meetings window headline never reads the all-clear
// over a FAILED meeting (audits/face-walk-opus.md defect 8).
import { describe, expect, it } from "vitest";
import { meetingsHeadline } from "./history";

const FAILED = { id: "m1", intel_status: { state: "error" }, transcriptWords: 0 };
const RAN = { id: "m2", intel_status: { state: "ready" }, transcriptWords: 120 };
const OFF_WITH_WORDS = { id: "m3", intel_status: { state: "disabled" }, transcriptWords: 120 };

describe("meetingsHeadline", () => {
  it("never says the all-clear over a FAILED row", () => {
    expect(meetingsHeadline([FAILED], false)).toEqual({ text: "1 meeting failed", accent: true });
    expect(meetingsHeadline([FAILED, { ...FAILED, id: "m4" }], false))
      .toEqual({ text: "2 meetings failed", accent: true });
  });

  it("keeps the existing grammar", () => {
    expect(meetingsHeadline([], false)).toEqual({ text: "No meetings yet", accent: false });
    expect(meetingsHeadline([RAN], false)).toEqual({ text: "Nothing needs you", accent: false });
    expect(meetingsHeadline([OFF_WITH_WORDS], false))
      .toEqual({ text: "1 meeting needs a summary", accent: true });
    expect(meetingsHeadline([RAN], true)).toEqual({ text: "", accent: false });
  });
});
