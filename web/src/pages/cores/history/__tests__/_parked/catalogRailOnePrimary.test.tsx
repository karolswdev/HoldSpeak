// HS-201-04, Astra's counsel round 2 — ONE filled primary in the rail.
//
// The first fix demoted only the SELECTED row's verb, so a desk with two
// summary-ready meetings drew two filled `Run summary` primaries side by
// side and the face had no lead action. The rule now: only the LEAD row
// (the selected row when it can start a run, else the top-most that can)
// wears the filled species; every other run verb is the default one.
//
// The fence counts `.btn--primary` in the rendered rail — the species on
// the glass, not a prop.
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { forgetExecutedReceipts } from "../../../../meetings/summaryRoute";
import { CatalogRail, MeetingSelectionVerbs } from "../CatalogRail";

const ROUTE = {
  status: "ready",
  reason_code: null,
  selection_hash: "sha256:rail",
  legs: [{ ordinal: 1, host: "local", boundary: "local" }],
};

function meeting(over: Record<string, unknown>) {
  return {
    title: "Meeting",
    started_at: "2026-09-19T09:00:00Z",
    duration_seconds: 1800,
    capture_status: "finalized",
    transcriptWords: 1204,
    planned_route: ROUTE,
    ...over,
  };
}

/** Two summary-ready meetings and one that already ran. */
const ROWS = [
  meeting({ id: "m-ready-1", intel_status: "disabled" }),
  meeting({ id: "m-ready-2", intel_status: "disabled" }),
  meeting({ id: "m-done", intel_status: "ready" }),
];

function rail(selected: Record<string, unknown> | null = null) {
  render(
    <CatalogRail
      meetingRows={ROWS}
      meetings={{ loading: false, error: "", reload: vi.fn(async () => ({})) }}
      selected={selected}
      setSelected={vi.fn()}
      runningId={null}
    />,
  );
  return document.querySelectorAll<HTMLElement>(".meetings-stream .btn--primary");
}

// Window grammar (2026-10-24): the rail is a list view and carries no verb;
// the selected row's run verb sits at the status bar's right; the
// window's ONE primary is decided (HistoryCore: Choose engine, else the
// selection's run verb, else Record meeting).
describe("HS-201-04 one filled primary, window grammar", () => {
  beforeEach(() => forgetExecutedReceipts());

  it("the list view itself draws no verb, filled or not", () => {
    const primaries = rail(ROWS[1]);
    expect(primaries).toHaveLength(0);
    expect(screen.queryAllByText("Run summary")).toHaveLength(0);
    expect(screen.getAllByRole("row").length).toBe(ROWS.length + 1);
  });

  it("the selection's run verb wears the primary only when the window gives it", () => {
    const { unmount } = render(<MeetingSelectionVerbs row={ROWS[0]} primary onRunIntelligence={vi.fn()} runningId={null} />);
    expect(screen.getByTestId("run-intelligence-btn")).toHaveClass("btn--primary");
    unmount();
    render(<MeetingSelectionVerbs row={ROWS[1]} primary={false} onRunIntelligence={vi.fn()} runningId={null} />);
    expect(screen.getByTestId("run-intelligence-btn")).not.toHaveClass("btn--primary");
  });

  it("a meeting that already ran offers no run verb", () => {
    render(<MeetingSelectionVerbs row={ROWS[2]} primary onRunIntelligence={vi.fn()} runningId={null} />);
    expect(screen.queryByTestId("run-intelligence-btn")).toBeNull();
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(0);
  });

  it("draws no run verb when no route resolves", () => {
    const stalled = {
      ...ROWS[0],
      planned_route: { status: "unavailable", reason_code: "no assignment", selection_hash: null, legs: [] },
    };
    render(<MeetingSelectionVerbs row={stalled} primary onRunIntelligence={vi.fn()} runningId={null} />);
    expect(screen.queryByTestId("run-intelligence-btn")).toBeNull();
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(0);
  });
});
