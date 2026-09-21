/* HS-202-02 job 2 — the meeting record refreshes on assignment and on run,
 * with no browser reload.
 *
 * 04-sober-eye.md Job 2 and rank 2: "Setting the engine did not make
 * **Run summary** appear; a page reload did. Clicking **Run summary** did
 * not show the result; a second reload did. The work took two seconds
 * (`Processed 1 deferred intel job(s)`) and the screen stayed silent for
 * sixty-five. Between those two silences sits the whole meeting job."
 *
 * The cause is a face that subscribes to nothing that names those two
 * events: `HistoryCore` read only the `runtime_queue` frame, and the open
 * record is a plain object snapshot that only a click ever replaced, so
 * even a ledger reload could not repaint it.
 *
 * The two signals that actually carry the news (audited on the hub):
 *  - an assignment write publishes NO server frame at all
 *    (`holdspeak/services/inference_assignment_service.py` has no
 *    broadcast), so the honest signal is the client's own
 *    `holdspeak:settings-updated` return event, exactly as ChairHome uses
 *    it since HS-201-01 (`desk/chair/ChairHome.tsx:503`);
 *  - a deferred intel job's completion publishes `aftercare_ready`
 *    (`holdspeak/intel_queue_conductor.py:96`), never `desk_changed` and
 *    never `intel_complete` (that one is live-session only).
 * `desk_changed` and window focus are subscribed too, for everything else
 * that moves the desk.
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { announceTaskReturn } from "../../../desk/returnToTask";
import { HistoryCore } from "../HistoryCore";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));

const frameListeners = new Map<string, Set<(frame: { data: unknown }) => void>>();
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, listener: (frame: { data: unknown }) => void) => {
      const set = frameListeners.get(type) ?? new Set();
      set.add(listener);
      frameListeners.set(type, set);
      return () => set.delete(listener);
    },
  }),
  useRuntimeFrame: () => null,
}));

function emit(type: string) {
  for (const listener of frameListeners.get(type) ?? []) listener({ data: {} });
}

const NO_ROUTE = {
  status: "no_assignment",
  reason_code: "no_assignment",
  selection_hash: "",
  legs: [],
};
const READY_ROUTE = {
  status: "ready",
  reason_code: null,
  selection_hash: "sha256:ready",
  legs: [{ ordinal: 1, host: "192.168.1.43", boundary: "lan" }],
};

/** The record the hub would answer right now. The engine repair flips it. */
let route: Record<string, unknown> = NO_ROUTE;
let detailReads = 0;

const detail = () => ({
  id: "m-1",
  title: "Imported meeting",
  started_at: "2026-09-20T09:00:00Z",
  duration_seconds: 60,
  capture_status: "finalized",
  intel_status: { state: "disabled" },
  transcriptWords: 9,
  segments: [],
  planned_route: route,
  run_receipt: null,
});

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    const url = String(path);
    if (url.startsWith("/api/meetings?"))
      return { meetings: [detail()] } as never;
    if (url === "/api/meetings/m-1") {
      detailReads += 1;
      return detail() as never;
    }
    return {} as never;
  });
}

describe("the open meeting record re-reads itself (HS-202-02)", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    frameListeners.clear();
    route = NO_ROUTE;
    detailReads = 0;
    wire();
  });

  it("shows the run verb after the engine is assigned, with no reload", async () => {
    render(<HistoryCore scope="meeting:m-1" />);

    // Cold: the hub has no assignment, so the face states that and offers
    // no run verb.
    await screen.findByTestId("detail-route-unavailable");
    expect(screen.queryByTestId("detail-run-intelligence-btn")).toBeNull();

    // The owner repairs the engine in the Concierge; its Apply announces
    // the return to this task.
    route = READY_ROUTE;
    act(() => {
      announceTaskReturn();
    });

    expect(
      await screen.findByTestId("detail-run-intelligence-btn"),
    ).toBeVisible();
  });

  it("re-reads the record when the hub says a run finished", async () => {
    render(<HistoryCore scope="meeting:m-1" />);
    await screen.findByTestId("detail-route-unavailable");
    const before = detailReads;

    route = READY_ROUTE;
    act(() => {
      emit("aftercare_ready");
    });

    await waitFor(() => expect(detailReads).toBeGreaterThan(before));
    expect(
      await screen.findByTestId("detail-run-intelligence-btn"),
    ).toBeVisible();
  });

  it("re-reads the record on the desk_changed frame", async () => {
    render(<HistoryCore scope="meeting:m-1" />);
    await screen.findByTestId("detail-route-unavailable");
    const before = detailReads;

    act(() => {
      emit("desk_changed");
    });

    await waitFor(() => expect(detailReads).toBeGreaterThan(before));
  });
});
