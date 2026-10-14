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
 *
 * PHILO-17 ("A meeting opens in one window"): the record lives in the
 * meeting's own window (history/MeetingRecord.tsx); the fences below follow
 * it there. The list-side races (a click inside a debounce, a list read that
 * lands after a click) have no seat: the window reads its own meeting when it
 * opens and on every signal.
 */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { announceTaskReturn } from "../../../desk/returnToTask";
import { HistoryCore } from "../HistoryCore";
import { MeetingRecord } from "../history/MeetingRecord";
import { openPrimitive, openSurfaceOr } from "../../../desk/shell";
import { TitleSlotContext } from "../../../desk/surface/title";

vi.mock("../../../desk/shell", async (original) => ({
  ...(await original<typeof import("../../../desk/shell")>()),
  openPrimitive: vi.fn(),
  openSurfaceOr: vi.fn(),
}));
vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));

const frameListeners = new Map<string, Set<(frame: { data: unknown }) => void>>();
/* The real bus hands out ONE `subscribe` for the life of the provider
 * (`runtime/RuntimeBus.tsx:31` — `useCallback([])`). A mock that minted a
 * fresh function per render made every subscriber's effect re-run on
 * every render, which hid the debounce-cancelling defect this file
 * catches below. */
const subscribe = (type: string, listener: (frame: { data: unknown }) => void) => {
  const set = frameListeners.get(type) ?? new Set();
  set.add(listener);
  frameListeners.set(type, set);
  return () => set.delete(listener);
};
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
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

/** Answers the detail read (the window asks `?include_parked=true`). */
const isDetail = (url: string, id = "m-1") => url.split("?")[0] === `/api/meetings/${id}`;

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    const url = String(path);
    if (url.startsWith("/api/meetings?"))
      return { meetings: [detail()] } as never;
    if (isDetail(url)) {
      detailReads += 1;
      return detail() as never;
    }
    return {} as never;
  });
}

const openRecord = (id = "m-1") => {
  const windowTitle = { value: "" };
  const view = render(
    <TitleSlotContext.Provider value={(title) => { windowTitle.value = title ?? ""; }}>
      <MeetingRecord meetingId={id} onClose={() => undefined} />
    </TitleSlotContext.Provider>,
  );
  return { ...view, windowTitle };
};

describe("the open meeting record re-reads itself (HS-202-02)", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    frameListeners.clear();
    route = NO_ROUTE;
    detailReads = 0;
    vi.mocked(openPrimitive).mockReset();
    vi.mocked(openSurfaceOr).mockReset();
    wire();
  });

  it("shows the run verb after the engine is assigned, with no reload", async () => {
    openRecord();
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
    // PHILO-17 (the desk sweep): the record's body is drawn once its first
    // reads end, so the verb is mounted at once and visible after.
    await waitFor(() => expect(screen.getByTestId("detail-run-intelligence-btn")).toBeVisible());
  });

  it("re-reads the record when the hub says a run finished", async () => {
    openRecord();
    await screen.findByTestId("detail-route-unavailable");
    const before = detailReads;
    route = READY_ROUTE;
    act(() => {
      emit("aftercare_ready");
    });
    await waitFor(() => expect(detailReads).toBeGreaterThan(before));
    // PHILO-17 (the desk sweep): the record's body is drawn once its first
    // reads end, so the verb is mounted at once and visible after.
    await waitFor(() => expect(screen.getByTestId("detail-run-intelligence-btn")).toBeVisible());
  });

  it("re-reads the record on the desk_changed frame", async () => {
    openRecord();
    await screen.findByTestId("detail-route-unavailable");
    const before = detailReads;
    act(() => {
      emit("desk_changed");
    });
    await waitFor(() => expect(detailReads).toBeGreaterThan(before));
  });
});

/* ── Astra's counsel finding 3 on PR #595, in the one-window world ──
 * A slow read for meeting A never lands on meeting B: each window reads
 * its own meeting. */
describe("a slow refresh never restores a record the owner left", () => {
  it("a stalled read of one meeting never lands in another meeting's window", async () => {
    let releaseA: ((value: unknown) => void) | null = null;
    let stall = false;
    const titleA = { value: "" };
    const titleB = { value: "" };
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const url = String(path);
      if (isDetail(url) && stall)
        return new Promise((resolve) => {
          releaseA = resolve;
        }) as never;
      if (isDetail(url)) return detail() as never;
      if (isDetail(url, "m-2")) return { ...detail(), id: "m-2", title: "The other meeting" } as never;
      return {} as never;
    });
    render(
      <>
        <TitleSlotContext.Provider value={(title) => { titleA.value = title ?? ""; }}>
          <MeetingRecord meetingId="m-1" onClose={() => undefined} />
        </TitleSlotContext.Provider>
        <TitleSlotContext.Provider value={(title) => { titleB.value = title ?? ""; }}>
          <MeetingRecord meetingId="m-2" onClose={() => undefined} />
        </TitleSlotContext.Provider>
      </>,
    );
    const bodyFacts = () => [...document.querySelectorAll(".meetings-detail-head .surface-display")].map((e) => e.textContent);
    await waitFor(() => expect([titleA.value, titleB.value]).toEqual(["Imported meeting", "The other meeting"]));
    await waitFor(() => expect(bodyFacts()).toEqual(["SUMMARY OFF", "SUMMARY OFF"]));
    // A refresh for A starts and stalls.
    stall = true;
    act(() => {
      emit("desk_changed");
    });
    await waitFor(() => expect(releaseA).not.toBeNull());
    await act(async () => {
      releaseA?.({ ...detail(), title: "Imported meeting, read again" });
    });
    await waitFor(() => expect([titleA.value, titleB.value]).toEqual(["Imported meeting, read again", "The other meeting"]));
    expect(bodyFacts()).toEqual(["SUMMARY OFF", "SUMMARY OFF"]);
  });
});

/* ── coordinator item 9 / the first-use smoke's `import-refresh` leg ──
 * The refresh must not COST the record anything: a detail payload with no
 * `transcriptWords` never withdraws `Run summary`. */
describe("a refresh never withdraws what the record had", () => {
  it("keeps Run summary when the detail payload omits transcriptWords", async () => {
    const segments = [{ text: "The quick brown fox.", speaker: "Me", start_time: 0, end_time: 1 }];
    const transcribed = { ...detail(), transcriptWords: 9, segments, planned_route: READY_ROUTE };
    let first = true;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const url = String(path);
      if (isDetail(url)) {
        detailReads += 1;
        if (first) {
          first = false;
          return transcribed as never;
        }
        // The detail path carries raw dicts: NO transcriptWords.
        const { transcriptWords: _drop, ...raw } = transcribed;
        return raw as never;
      }
      return {} as never;
    });
    openRecord();
    // PHILO-17 (the desk sweep): the record's body is drawn once its first
    // reads end, so the verb is mounted at once and visible after.
    await waitFor(() => expect(screen.getByTestId("detail-run-intelligence-btn")).toBeVisible());
    act(() => {
      emit("desk_changed");
    });
    await waitFor(() => expect(detailReads).toBeGreaterThan(1));
    expect(screen.getByTestId("detail-run-intelligence-btn")).toBeVisible();
  });
});

/* ── the first-use smoke's `import-refresh` leg ──
 * The import worker announces the desk change the INSTANT the transcript
 * lands, which can be before the owner opens the meeting. The window reads
 * the meeting when it opens, so it is current whatever came first. */
describe("the announced refresh survives the owner opening a record", () => {
  it("catches the record up when the frame arrived before the open", async () => {
    const transcribed = {
      ...detail(),
      intel_status: "disabled",
      transcriptWords: 9,
      planned_route: READY_ROUTE,
      segments: [{ text: "The quick brown fox.", speaker: "Me", start_time: 0, end_time: 1 }],
    };
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      (isDetail(String(path)) ? transcribed : {}) as never);
    act(() => {
      emit("desk_changed");
    });
    openRecord();
    await waitFor(() => expect(screen.getByTestId("detail-run-intelligence-btn")).toBeVisible(), { timeout: 4000 });
  });
});

/* ── the residual race, in the one-window world ──
 * The open record never keeps a snapshot the hub has replaced: a window
 * focus (no frame behind it) reads the meeting again. */
describe("the open record follows the hub", () => {
  it("takes the new fields when the meeting changes under it", async () => {
    let current: Record<string, unknown> = {
      ...detail(), title: "Still importing", intel_status: "importing", transcriptWords: null, planned_route: READY_ROUTE,
    };
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      (isDetail(String(path)) ? current : {}) as never);
    const { windowTitle } = openRecord();
    const bodyFact = () => document.querySelector(".meetings-detail-head .surface-display")?.textContent ?? "";
    await waitFor(() => expect(windowTitle.value).toBe("Still importing"));
    expect(bodyFact()).toBe("Still importing");
    current = {
      ...detail(), title: "The transcribed meeting", intel_status: "disabled", transcriptWords: 9, planned_route: READY_ROUTE,
      segments: [{ text: "The quick brown fox.", speaker: "Me", start_time: 0, end_time: 1 }],
    };
    act(() => {
      window.dispatchEvent(new Event("focus"));
    });
    await waitFor(() => expect(windowTitle.value).toBe("The transcribed meeting"));
    expect(bodyFact()).toBe("SUMMARY OFF");
    await waitFor(() => expect(screen.getByTestId("detail-run-intelligence-btn")).toBeVisible(), { timeout: 4000 });
  });
});

describe("C1 readiness acknowledgement", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    frameListeners.clear();
    route = NO_ROUTE;
    detailReads = 0;
    wire();
  });

  it("a real Meetings row opens the meeting's own window", async () => {
    render(<HistoryCore />);
    const rowBody = await waitFor(() => {
      const found = document.querySelector(
        '[data-testid="meeting-row-m-1"] .meetings-stream-row-body',
      );
      expect(found, "the real Meetings ledger draws the row").toBeTruthy();
      return found as Element;
    });
    fireEvent.click(rowBody);
    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", "meeting:m-1");
  });

  it("ACKs readiness when the meeting's window opens (every door)", async () => {
    openRecord();
    await waitFor(() =>
      expect(document.querySelector(".meetings-detail-head")).toBeTruthy(),
    );
    expect(apiFetch).toHaveBeenCalledWith("/api/meetings/m-1/ready/read", {
      method: "POST",
    });
  });
});
