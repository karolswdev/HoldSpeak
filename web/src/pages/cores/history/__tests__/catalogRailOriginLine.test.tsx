// HS-170-04 -- CatalogRail tests: Run intelligence verb appears only
// on OFF rows with a transcript, never on no-transcript rows.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail } from "../CatalogRail";

function baseProps(rows: Record<string, unknown>[]) {
  return {
    meetingRows: rows,
    meetings: { loading: false, error: "", reload: vi.fn(async () => ({})) },
    selected: null,
    setSelected: vi.fn(),
    onRunIntelligence: vi.fn(),
    runningId: null,
    runHost: null,
  };
}

describe("CatalogRail Run intelligence verb (HS-170-04)", () => {
  it("shows Run intelligence on OFF row with transcript", () => {
    const rows = [
      {
        id: "m-off-words",
        title: "Census standup",
        started_at: "2026-09-04T09:00:00Z",
        duration_seconds: 1800,
        capture_status: "finalized",
        intel_status: "disabled",
        transcriptWords: 1204,
      },
    ];
    render(<CatalogRail {...baseProps(rows)} />);
    expect(screen.getByText("Run intelligence")).toBeInTheDocument();
  });

  it("does not show Run intelligence on no-transcript row", () => {
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
    expect(screen.queryByText("Run intelligence")).not.toBeInTheDocument();
    expect(screen.getByText("NO TRANSCRIPT")).toBeInTheDocument();
  });

  it("shows Open on SAVED row", () => {
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
    expect(screen.getByText("Open")).toBeInTheDocument();
  });
});
