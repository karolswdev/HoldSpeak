// HS-201-04 — the Chair's Run verb and the Chair's Open.
//
//   1. Run POSTs `expected_selection_hash` from the route the row
//      disclosed (the lane A interlock; the HS-170 browser probe measured
//      a POST with NO hash);
//   2. the planned host is beside the verb BEFORE the click, and the
//      verb is withheld when no route resolves;
//   3. a 409 is a refusal with its plain reason;
//   4. Open passes `meeting:<id>` — the grammar HistoryCore parses
//      (`HistoryCore.tsx:33`); a bare id opened no meeting.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../lib/api";
import { openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { ChairHome } from "./ChairHome";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));
vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openSurfaceOr: vi.fn(),
}));

const mockedApiFetch = vi.mocked(apiFetch);
const mockedOpen = vi.mocked(openSurfaceOr);

const ROUTE = {
  status: "ready",
  reason_code: null,
  selection_hash: "sha256:chair",
  legs: [{ ordinal: 1, host: "192.168.1.43", boundary: "lan" }],
};
const NO_ROUTE = {
  status: "unavailable",
  reason_code: "no assignment",
  selection_hash: null,
  legs: [],
};

function seatMeeting(overrides: Record<string, unknown> = {}) {
  useDesk.setState({
    items: {
      meeting: [
        {
          kind: "meeting",
          id: "m-1",
          title: "Census standup",
          startedAt: "2026-09-19T09:00:00Z",
          endedAt: "2026-09-19T09:30:00Z",
          durationSeconds: 1800,
          intelStatus: "disabled",
          transcriptWords: 1204,
          plannedRoute: ROUTE,
          runReceipt: null,
          ...overrides,
        },
      ],
    } as never,
  });
}

/** The wire row the hub serves for the seated meeting, so the desk's own
 *  refresh (which a refusal triggers) does not empty the Chair. */
function wireMeeting(route: unknown) {
  return {
    id: "m-1",
    title: "Census standup",
    started_at: "2026-09-19T09:00:00Z",
    ended_at: "2026-09-19T09:30:00Z",
    duration_seconds: 1800,
    intel_status: "disabled",
    transcriptWords: 1204,
    planned_route: route,
  };
}

function wire(route: unknown = ROUTE) {
  mockedApiFetch.mockImplementation(async (path: string) => {
    if (String(path).startsWith("/api/meetings?"))
      return { meetings: [wireMeeting(route)] } as never;
    if (String(path) === "/api/inference/assignments")
      return {
        schema: "InferenceAssignmentSummary@1",
        rows: [],
        task_overrides: [],
        issue_count: 0,
      } as never;
    if (String(path).startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    if (String(path) === "/api/door") return { board: {}, upcoming: [] } as never;
    return null as never;
  });
}

describe("HS-201-04 the Chair's summary run", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
    mockedOpen.mockReset();
  });

  it("sends the disclosed selection hash, and shows the host first", async () => {
    wire();
    seatMeeting();
    render(<ChairHome />);
    const verb = await screen.findByTestId("arrival-run-intel");
    // The host is disclosed BEFORE the click (Article III).
    expect(screen.getByTestId("arrival-route").textContent).toContain(
      "192.168.1.43 · LAN",
    );
    fireEvent.click(verb);
    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/api/meetings/m-1/intelligence/run",
        { method: "POST", json: { expected_selection_hash: "sha256:chair" } },
      ),
    );
  });

  it("withholds Run and says the reason when no route resolves", async () => {
    wire();
    seatMeeting({ plannedRoute: NO_ROUTE });
    render(<ChairHome />);
    await screen.findByTestId("arrival-route-unavailable");
    expect(screen.queryByTestId("arrival-run-intel")).toBeNull();
    expect(screen.getByTestId("arrival-route-unavailable").textContent).toContain(
      "NO ASSIGNMENT",
    );
  });

  it("shows a 409 as ONE short refusal fact, the reason on its title", async () => {
    wire();
    seatMeeting();
    const quiet = mockedApiFetch.getMockImplementation()!;
    mockedApiFetch.mockImplementation(async (path: string, init?: unknown) => {
      if (String(path).endsWith("/intelligence/run")) {
        throw new ApiError(409, "conflict", {
          code: "selection_drift",
          plainReason: "The summary route changed. Check it, then try again.",
          planned_route: ROUTE,
          run_receipt: null,
        });
      }
      return quiet(path, init as never);
    });
    render(<ChairHome />);
    fireEvent.click(await screen.findByTestId("arrival-run-intel"));
    const refusal = await screen.findByTestId("arrival-refusal");
    // UX-CANON A.3 (Astra's counsel finding 5): a fact line, not the hub's
    // two-sentence instruction. The full sentence stays on the title.
    expect(refusal.textContent).toBe("REFUSED · ROUTE CHANGED");
    expect(refusal.getAttribute("title")).toContain("The summary route changed");
  });

  it("opens the meeting with the `meeting:<id>` grammar History parses", async () => {
    wire();
    seatMeeting({ intelStatus: "complete" });
    render(<ChairHome />);
    const open = await screen.findByRole("button", { name: "Open" });
    fireEvent.click(open);
    expect(mockedOpen).toHaveBeenCalledWith(
      "review-meetings",
      "/meetings",
      "meeting:m-1",
    );
  });
});
