// PHILO-15-07 — B01: a transcript with honest gaps carries a WARN lamp with
// its count, never a bare word count. B15: the footer receipt follows the
// summary run to its final state (`RAN · hh:mm`), never `QUEUED` after it ran.
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail } from "../CatalogRail";
import { finishedRunReceipt, unclearLampLabel } from "../helpers";

function props(unclearSpans: number) {
  return {
    meetingRows: [{
      id: "m1",
      title: "Philo3 architect meeting",
      started_at: "2026-10-07T10:52:00",
      duration_seconds: 35,
      capture_status: "finalized",
      intel_status: "disabled",
      transcriptWords: 98,
      unclearSpans,
    }],
    meetings: { loading: false, error: "", reload: vi.fn(async () => ({})) },
    selected: null,
    setSelected: vi.fn(),
    onRunIntelligence: vi.fn(),
    runningId: null,
  };
}

describe("PHILO-15-07 the transcript never lies", () => {
  it("lamps WARN with the count beside the words when a span is unclear", () => {
    render(<CatalogRail {...props(1)} />);
    expect(screen.getByText("98 WORDS")).toBeInTheDocument();
    expect(screen.getByTestId("unclear-lamp")).toHaveTextContent("WARN · 1 UNCLEAR SPAN");
  });

  it("draws no lamp (no counter of zero) on a clean transcript", () => {
    render(<CatalogRail {...props(0)} />);
    expect(screen.queryByTestId("unclear-lamp")).toBeNull();
  });

  it("says the plural and reads either wire spelling", () => {
    expect(unclearLampLabel({ unclearSpans: 3 })).toBe("WARN · 3 UNCLEAR SPANS");
    expect(unclearLampLabel({ unclear_spans: 1 })).toBe("WARN · 1 UNCLEAR SPAN");
    expect(unclearLampLabel({})).toBeNull();
  });

  it("turns the QUEUED receipt into the run's final state", () => {
    const at = "2026-10-07T11:02:00";
    expect(finishedRunReceipt("ready", at).text).toMatch(/^RAN · \d{1,2}:\d{2}/);
    expect(finishedRunReceipt("complete", at).text).toMatch(/^RAN · /);
    expect(finishedRunReceipt("error", at)).toMatchObject({ tone: "danger" });
    expect(finishedRunReceipt("error", at).text).toMatch(/^FAILED · /);
    expect(finishedRunReceipt("skipped", at).text).toMatch(/^SKIPPED · /);
  });
});
