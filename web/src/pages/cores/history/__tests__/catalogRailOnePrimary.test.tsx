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
import { CatalogRail } from "../CatalogRail";

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
      onRunIntelligence={vi.fn()}
      runningId={null}
    />,
  );
  return document.querySelectorAll<HTMLElement>(".meetings-stream .btn--primary");
}

describe("HS-201-04 one filled primary in the meetings rail", () => {
  beforeEach(() => forgetExecutedReceipts());

  it("gives the filled verb to the TOP-MOST summary-ready row only", () => {
    const primaries = rail();
    expect([...primaries].map((b) => b.textContent)).toEqual(["Run summary"]);
    // Both rows still offer the verb — the second one just is not filled.
    expect(screen.getAllByText("Run summary")).toHaveLength(2);
  });

  it("moves the filled verb to the SELECTED row when it can run", () => {
    const primaries = rail(ROWS[1]);
    // The selected row's record is open, and the record carries the filled
    // verb — so the rail itself holds none.
    expect(primaries).toHaveLength(0);
  });

  it("keeps the lead on the first runnable row when the selection cannot run", () => {
    const primaries = rail(ROWS[2]);
    expect([...primaries].map((b) => b.textContent)).toEqual(["Run summary"]);
  });

  it("draws no filled verb when no row can run", () => {
    const stalled = ROWS.map((row) => ({
      ...row,
      planned_route: {
        status: "unavailable",
        reason_code: "no assignment",
        selection_hash: null,
        legs: [],
      },
    }));
    render(
      <CatalogRail
        meetingRows={stalled}
        meetings={{ loading: false, error: "", reload: vi.fn(async () => ({})) }}
        selected={null}
        setSelected={vi.fn()}
        onRunIntelligence={vi.fn()}
        runningId={null}
      />,
    );
    expect(
      document.querySelectorAll(".meetings-stream .btn--primary"),
    ).toHaveLength(0);
  });
});
