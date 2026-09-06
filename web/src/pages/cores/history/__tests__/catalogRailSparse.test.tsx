// HS-170-04 — CatalogRail tests: the stream renders meetings,
// shows empty state, and uses the new prop interface.
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail } from "../CatalogRail";

function baseProps(rowCount: number) {
  const meetingRows = Array.from({ length: rowCount }, (_, i) => ({
    id: `m${i}`,
    title: `Meeting ${i}`,
    started_at: "2026-08-16T10:00:00Z",
    segment_count: 2,
    duration_seconds: 300,
    capture_status: "done",
    transcriptWords: 100,
  }));
  return {
    meetingRows,
    meetings: { loading: false, error: "", reload: vi.fn(async () => ({})) },
    selected: null,
    setSelected: vi.fn(),
    onRunIntelligence: vi.fn(),
    runningId: null,
    runHost: null,
  };
}

describe("CatalogRail stream (HS-170-04)", () => {
  it("renders meeting rows with titles", () => {
    render(<CatalogRail {...baseProps(3)} />);
    expect(screen.getByText("Meeting 0")).toBeInTheDocument();
    expect(screen.getByText("Meeting 1")).toBeInTheDocument();
    expect(screen.getByText("Meeting 2")).toBeInTheDocument();
  });

  it("shows empty state when there are zero meetings", () => {
    render(<CatalogRail {...baseProps(0)} />);
    expect(screen.getByText("No meetings yet")).toBeInTheDocument();
  });

  it("renders NO TRANSCRIPT token when transcriptWords is null", () => {
    const rows = [{
      id: "m-no-transcript",
      title: "Vendor call",
      started_at: "2026-08-26T10:00:00Z",
      duration_seconds: 720,
      capture_status: "finalized",
      intel_status: "disabled",
      transcriptWords: null,
    }];
    render(<CatalogRail
      meetingRows={rows}
      meetings={{ loading: false, error: "", reload: vi.fn(async () => ({})) }}
      selected={null}
      setSelected={vi.fn()}
      onRunIntelligence={vi.fn()}
      runningId={null}
      runHost={null}
    />);
    expect(screen.getByText("NO TRANSCRIPT")).toBeInTheDocument();
  });
});
