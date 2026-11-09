// HS-170-04 -- CatalogRail tests: the run-summary verb appears only
// on OFF rows with a transcript, never on no-transcript rows. The language
// (2026-11-08): the verb is the picked meeting's plate (meetingPlate); the
// rail says the state.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail } from "../CatalogRail";
import { meetingPlate } from "../plate";

function baseProps(rows: Record<string, unknown>[]) {
  return {
    meetingRows: rows,
    meetings: { loading: false, error: "", reload: vi.fn(async () => ({})) },
    picked: null,
    onPick: vi.fn(),
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
    render(<CatalogRail {...baseProps(rows)} />);
    expect(meetingPlate(rows[0], {}).title).toBe("Run intelligence");
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
    render(<CatalogRail {...baseProps(rows)} />);
    expect(meetingPlate(rows[0], {}).kind).toBe("transcribe");
    expect(screen.getByText("No transcript")).toBeInTheDocument();
  });

  it("a summarised row offers no run verb; its plate is the follow-up", () => {
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
    render(<CatalogRail {...baseProps(rows)} />);
    expect(meetingPlate(rows[0], {}).kind).toBe("send");
    expect(screen.getByTestId("state-token").textContent).toBe("Ran");
  });
});
