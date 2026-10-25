// HS-170-04 -- CatalogRail tests: the run-summary verb appears only
// on OFF rows with a transcript, never on no-transcript rows. Window grammar
// (2026-10-24): the verb is the selected row's, in the status bar
// (MeetingSelectionVerbs); the list view says the state.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail, MeetingSelectionVerbs } from "../CatalogRail";

function selection(row: Record<string, unknown>) {
  return <MeetingSelectionVerbs row={row} primary onRunIntelligence={vi.fn()} runningId={null} />;
}

function baseProps(rows: Record<string, unknown>[]) {
  return {
    meetingRows: rows,
    meetings: { loading: false, error: "", reload: vi.fn(async () => ({})) },
    selected: null,
    setSelected: vi.fn(),
    onRunIntelligence: vi.fn(),
    runningId: null,
  };
}

describe("CatalogRail Run summary verb (HS-170-04)", () => {
  it("shows Run summary on OFF row with transcript", () => {
    const rows = [
      {
        id: "m-off-words",
        title: "Census standup",
        started_at: "2026-09-04T09:00:00Z",
        duration_seconds: 1800,
        capture_status: "finalized",
        intel_status: "disabled",
        transcriptWords: 1204,
        // HS-201-04: a run verb needs a disclosed route to run on; the
        // hub serves one on every row of this read model.
        planned_route: {
          status: "ready",
          reason_code: null,
          selection_hash: "sha256:rail",
          legs: [{ ordinal: 1, host: "local", boundary: "local" }],
        },
      },
    ];
    render(<><CatalogRail {...baseProps(rows)} />{selection(rows[0])}</>);
    expect(screen.getByText("Run summary")).toBeInTheDocument();
    expect(screen.getByTestId("state-token").textContent).toBe("Not run");
  });

  it("does not show Run summary on no-transcript row", () => {
    const rows = [
      {
        id: "m-no-transcript",
        title: "Vendor call",
        started_at: "2026-08-26T10:00:00Z",
        duration_seconds: 720,
        capture_status: "finalized",
        intel_status: "disabled",
        transcriptWords: null,
      },
    ];
    render(<><CatalogRail {...baseProps(rows)} />{selection(rows[0])}</>);
    expect(screen.queryByText("Run summary")).not.toBeInTheDocument();
    expect(screen.getByText("No transcript")).toBeInTheDocument();
  });

  it("a summarised row offers no run verb; the toolbar's Open opens it", () => {
    const rows = [
      {
        id: "m-saved",
        title: "1:1 Ania",
        started_at: "2026-08-28T10:00:00Z",
        duration_seconds: 1500,
        capture_status: "finalized",
        intel_status: "complete",
        transcriptWords: 800,
      },
    ];
    render(<><CatalogRail {...baseProps(rows)} />{selection(rows[0])}</>);
    expect(screen.queryByText("Run summary")).not.toBeInTheDocument();
    expect(screen.getByTestId("state-token").textContent).toBe("Ran");
  });
});
