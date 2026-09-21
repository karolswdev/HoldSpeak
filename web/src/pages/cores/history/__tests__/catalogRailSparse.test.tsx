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
  };
}

describe("CatalogRail stream (HS-170-04)", () => {
  it("renders meeting rows with titles", () => {
    render(<CatalogRail {...baseProps(3)} />);
    expect(screen.getByText("Meeting 0")).toBeInTheDocument();
    expect(screen.getByText("Meeting 1")).toBeInTheDocument();
    expect(screen.getByText("Meeting 2")).toBeInTheDocument();
  });

  /* HS-202-04 (M6) re-points this rig, which pinned the OLD label.
   * `No meetings yet` is the Meetings face's display headline
   * (`history/helpers.ts:223`); the rail printed the very same words
   * beneath it, so the cold face said its all-clear twice on one screen
   * (`01-measured-walk.md`, leg `wing-meetings-outcomes`). UX-CANON A.7
   * and A.3: the headline keeps the state, the rail states the next move.
   * The assertion still proves the empty state renders — it now proves it
   * renders the ONE line the face is allowed to draw here. */
  it("shows empty state when there are zero meetings", () => {
    render(<CatalogRail {...baseProps(0)} />);
    expect(screen.getByText("Record or import a meeting")).toBeInTheDocument();
    expect(screen.queryByText("No meetings yet")).toBeNull();
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
    />);
    expect(screen.getByText("NO TRANSCRIPT")).toBeInTheDocument();
  });
});
