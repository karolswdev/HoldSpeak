// PHILO-15-07 — B01: a transcript with honest gaps carries a WARN lamp with
// its count, never a bare word count. B15: the footer receipt follows the
// summary run to its final state (`RAN · hh:mm`), never `QUEUED` after it ran.
import { describe, expect, it } from "vitest";
import { finishedRunReceipt, unclearLampLabel } from "../helpers";
import { mastFacts } from "../plate";

function meeting(unclearSpans: number) {
  return {
    id: "m1",
    title: "Philo3 architect meeting",
    started_at: "2026-10-07T10:52:00",
    duration_seconds: 35,
    capture_status: "finalized",
    intel_status: "disabled",
    transcriptWords: 98,
    unclearSpans,
  };
}

describe("PHILO-15-07 the transcript never lies", () => {
  it("says the count beside the words when a span is unclear (the meeting's mast)", () => {
    const facts = mastFacts(meeting(1));
    expect(facts).toContain("98 words");
    expect(facts).toContain("1 unclear span");
  });

  it("says no gap (no counter of zero) on a clean transcript", () => {
    expect(mastFacts(meeting(0))).not.toMatch(/unclear/);
  });

  it("says the plural and reads either wire spelling", () => {
    expect(unclearLampLabel({ unclearSpans: 3 })).toBe("WARN · 3 UNCLEAR SPANS");
    expect(unclearLampLabel({ unclear_spans: 1 })).toBe("WARN · 1 UNCLEAR SPAN");
    expect(unclearLampLabel({})).toBeNull();
  });

  it("turns the QUEUED receipt into the run's final state", () => {
    const at = "2026-10-07T11:02:00";
    expect(finishedRunReceipt("ready", at).text).toMatch(/^Ran at \d{1,2}:\d{2}/);
    expect(finishedRunReceipt("complete", at).text).toMatch(/^Ran at /);
    expect(finishedRunReceipt("error", at)).toMatchObject({ tone: "danger" });
    expect(finishedRunReceipt("error", at).text).toMatch(/^Summary failed at \d\d:\d\d · The transcript stays · Run it again$/);
    expect(finishedRunReceipt("skipped", at).text).toMatch(/^Skipped at /);
  });
});
