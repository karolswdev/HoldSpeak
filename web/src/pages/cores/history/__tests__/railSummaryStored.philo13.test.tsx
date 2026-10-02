// PHILO-13-04 A3-W — the Meetings list rail names the STORED fact.
//
// H-A3 (#729) gives each `/api/meetings` row `has_summary`, read from the
// latest persisted summary, apart from the config switch and the run status.
// The rail said `OFF` beside a meeting that stores a summary
// (story-04-shots/meetings-stored-1440.png). These rows have the wire's shape:
// snake_case `intel_status`, `has_summary`, `transcriptWords`.
import { render, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail } from "../CatalogRail";
import { meetingRowState, meetingsHeadline, stateToken } from "../helpers";

function row(id: string, intel_status: unknown, has_summary: boolean) {
  return {
    id,
    title: `Meeting ${id}`,
    started_at: "2026-10-01T10:00:00Z",
    duration_seconds: 2700,
    capture_status: "finalized",
    intel_status,
    has_summary,
    transcriptWords: 12,
  };
}

function rail(rows: Record<string, unknown>[]) {
  return render(
    <CatalogRail
      meetingRows={rows}
      meetings={{ loading: false, error: "", reload: vi.fn(async () => ({})) }}
      selected={null}
      setSelected={vi.fn()}
      onRunIntelligence={vi.fn()}
      runningId={null}
    />,
  );
}

function token(id: string): string {
  const el = document.querySelector(`[data-testid="meeting-row-${id}"]`) as HTMLElement;
  return within(el).getByTestId("state-token").textContent ?? "";
}

describe("PHILO-13-04 A3-W — the rail names a stored summary", () => {
  it("says SUMMARY STORED, never OFF, when the run status is disabled", () => {
    rail([row("stored", "disabled", true), row("none", "disabled", false)]);
    expect(token("stored")).toBe("SUMMARY STORED");
    expect(token("none")).toBe("OFF");
  });

  it("names the stored fact when no run is active", () => {
    for (const status of ["disabled", "skipped", "ready", "complete", { state: "disabled" }, null]) {
      expect(stateToken(row("s", status, true))).toEqual({ axis: "SUMMARY", label: "STORED" });
    }
  });

  // Coordinator ruling: an ACTIVE run is the live fact, so it shows first.
  it("shows an active run before the stored summary", () => {
    expect(stateToken(row("r", "running", true)).label).toBe("RUNNING");
    expect(stateToken(row("q", "queued", true)).label).toBe("QUEUED");
    expect(stateToken(row("p", { state: "pending" }, true)).label).toBe("QUEUED");
  });

  it("shows a failed re-run as FAILED with Retry, not SUMMARY STORED", () => {
    expect(stateToken(row("f", "error", true)).label).toBe("FAILED");
    rail([row("failed", "error", true)]);
    const el = document.querySelector('[data-testid="meeting-row-failed"]') as HTMLElement;
    expect(within(el).getByTestId("state-token").textContent).toBe("FAILED");
    expect(meetingRowState(row("failed", "error", true)).verb).toBe("Retry");
  });

  it("keeps the honest states when no summary is stored", () => {
    expect(stateToken(row("a", "disabled", false)).label).toBe("OFF");
    expect(stateToken(row("b", "ready", false)).label).toBe("RAN");
    expect(stateToken(row("c", "error", false)).label).toBe("FAILED");
  });

  it("offers Open, not Run summary, on a stored summary", () => {
    rail([row("stored", "disabled", true)]);
    const el = document.querySelector('[data-testid="meeting-row-stored"]') as HTMLElement;
    expect(within(el).queryByTestId("run-intelligence-btn")).toBeNull();
    expect(within(el).getByRole("button", { name: "Open" })).toBeTruthy();
  });

  it("does not count a stored summary as one that needs a summary", () => {
    const rows = [row("stored", "disabled", true), row("none", "disabled", false)];
    expect(meetingsHeadline(rows, false).text).toBe("1 meeting needs a summary");
  });
});
