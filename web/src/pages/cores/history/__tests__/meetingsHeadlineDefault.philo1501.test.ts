// PHILO-15 01 — a Default for AI work clears "No engine for summaries" on
// the Meetings headline too. The headline reads the hub's `planned_route`
// (HistoryCore: `Boolean(faceRoute) && !routeReady(faceRoute)`), which the
// hub resolves through the meeting-intel queue's own principal and route
// policy (`meeting_route_projection.project_route`). With only a global
// default that route is ready (tests/unit/test_philo15_01_summaries_blocker.py
// `test_meetings_route_is_ready_on_the_default_alone`), so the headline
// gives the all-clear.
import { describe, expect, it } from "vitest";
import { meetingsHeadline } from "../helpers";
import { readPlannedRoute, routeOff, routeReady } from "../../../../meetings/summaryRoute";

function headline(rows: Record<string, unknown>[]) {
  const faceRoute = readPlannedRoute(rows.find((row) => readPlannedRoute(row)));
  // The same derivation as HistoryCore's headline.
  return meetingsHeadline(
    rows, false,
    Boolean(faceRoute) && !routeReady(faceRoute) && !routeOff(faceRoute),
    routeOff(faceRoute),
  );
}

const SUMMARISED = { id: "m1", title: "Standup", has_summary: true, intel_status: "complete" };

describe("PHILO-15 01 — the Meetings headline on a default-only desk", () => {
  it("reads the all-clear when the queue route resolves on the default", () => {
    const row = {
      ...SUMMARISED,
      planned_route: {
        status: "ready",
        reason_code: null,
        selection_hash: "sha256:default",
        legs: [{ ordinal: 1, host: "192.168.1.43", boundary: "private_network", profile_id: "lan-qwen", profile_revision: 1 }],
      },
    };
    expect(headline([row])).toEqual({ text: "All summaries done", accent: false });
  });

  it("names the missing engine only when the queue route is unavailable", () => {
    const row = {
      ...SUMMARISED,
      planned_route: { status: "unavailable", reason_code: "no assignment", selection_hash: null, legs: [] },
    };
    expect(headline([row]).text).toBe("No engine for summaries");
  });

  it("reads OFF, not 'No engine', when the owner turned summaries off", () => {
    // meeting_route_projection.project_route: unavailable("summaries_off").
    const row = {
      ...SUMMARISED,
      planned_route: { status: "unavailable", reason_code: "summaries off", selection_hash: null, legs: [] },
    };
    expect(headline([row])).toEqual({ text: "Summaries off", accent: false });
  });
});
