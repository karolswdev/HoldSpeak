// HS-136-03 -- scheduled recording slice tests: event application,
// arming state, outcome state, CRUD actions.

import { describe, expect, it, vi, beforeEach } from "vitest";
import { createScheduledRecordingSlice } from "../scheduledRecordingSlice";
import type { DeskState } from "../types";

const apiFetchMock = vi.hoisted(() => vi.fn());
vi.mock("../../../lib/api", () => ({ apiFetch: apiFetchMock }));

// ---------------------------------------------------------------------------
// minimal slice harness (same pattern as the existing store tests)
// ---------------------------------------------------------------------------

function makeSlice() {
  let state: Record<string, unknown> = {};
  const set = (partial: Partial<DeskState> | ((s: DeskState) => Partial<DeskState>)) => {
    if (typeof partial === "function") {
      Object.assign(state, partial(state as unknown as DeskState));
    } else {
      Object.assign(state, partial);
    }
  };
  const get = () => state as unknown as DeskState;
  const api = { setState: set as (p: Partial<DeskState>) => void, getState: get };
  const slice = createScheduledRecordingSlice(set, get, api);
  Object.assign(state, slice);
  return { state: state as ReturnType<typeof createScheduledRecordingSlice>, get, set };
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("scheduledRecordingSlice", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("initializes with empty schedules and null arming", () => {
    const { state } = makeSlice();
    expect(state.scheduledRecordings).toEqual([]);
    expect(state.scheduledArming).toBeNull();
    expect(state.scheduleCreateWindow).toBeNull();
  });

  describe("applyScheduledRecordingEvent", () => {
    it("arming sets the arming state", () => {
      const { state } = makeSlice();
      state.applyScheduledRecordingEvent("scheduled_recording.arming", {
        schedule_id: "s1",
        title: "Daily standup",
        countdown_seconds: 10,
        fire_at: Date.now() / 1000 + 10,
        at: new Date().toISOString(),
      });
      expect(state.scheduledArming).not.toBeNull();
      expect(state.scheduledArming!.scheduleId).toBe("s1");
      expect(state.scheduledArming!.title).toBe("Daily standup");
      expect(state.scheduledArming!.outcome).toBeNull();
    });

    it("cancelled sets outcome on matching arming", () => {
      const { state } = makeSlice();
      // Set up arming first.
      state.applyScheduledRecordingEvent("scheduled_recording.arming", {
        schedule_id: "s1", title: "Test", countdown_seconds: 10,
        fire_at: Date.now() / 1000 + 10, at: new Date().toISOString(),
      });
      state.applyScheduledRecordingEvent("scheduled_recording.cancelled", {
        schedule_id: "s1", title: "Test", receipt_id: "r1",
        at: new Date().toISOString(),
      });
      expect(state.scheduledArming!.outcome).toBe("cancelled");
    });

    it("refused sets outcome with reason", () => {
      const { state } = makeSlice();
      state.applyScheduledRecordingEvent("scheduled_recording.arming", {
        schedule_id: "s1", title: "Test", countdown_seconds: 10,
        fire_at: Date.now() / 1000 + 10, at: new Date().toISOString(),
      });
      state.applyScheduledRecordingEvent("scheduled_recording.refused", {
        schedule_id: "s1", title: "Test", reason: "mic floor held",
        receipt_id: "r1", at: new Date().toISOString(),
      });
      expect(state.scheduledArming!.outcome).toBe("refused");
      expect(state.scheduledArming!.outcomeReason).toBe("mic floor held");
    });

    it("started sets outcome on matching arming", () => {
      const { state } = makeSlice();
      state.applyScheduledRecordingEvent("scheduled_recording.arming", {
        schedule_id: "s1", title: "Test", countdown_seconds: 10,
        fire_at: Date.now() / 1000 + 10, at: new Date().toISOString(),
      });
      state.applyScheduledRecordingEvent("scheduled_recording.started", {
        schedule_id: "s1", title: "Test", duration_minutes: 60,
        deadline_at: Date.now() / 1000 + 3600,
        receipt_id: "r1", at: new Date().toISOString(),
      });
      expect(state.scheduledArming!.outcome).toBe("started");
    });

    it("missed creates arming state even without prior arming", () => {
      const { state } = makeSlice();
      state.applyScheduledRecordingEvent("scheduled_recording.missed", {
        schedule_id: "s1", title: "Missed one",
        receipt_id: "r1", at: new Date().toISOString(),
      });
      expect(state.scheduledArming).not.toBeNull();
      expect(state.scheduledArming!.outcome).toBe("missed");
      expect(state.scheduledArming!.title).toBe("Missed one");
    });

    it("refused creates arming state even without prior arming", () => {
      const { state } = makeSlice();
      state.applyScheduledRecordingEvent("scheduled_recording.refused", {
        schedule_id: "s1", title: "Refused one",
        reason: "mic floor held", receipt_id: "r1",
        at: new Date().toISOString(),
      });
      expect(state.scheduledArming).not.toBeNull();
      expect(state.scheduledArming!.outcome).toBe("refused");
    });
  });

  describe("armEventRecording (HS-147-02)", () => {
    it("posts calendar_event_id and reloads schedules on success", async () => {
      apiFetchMock.mockImplementation((path: string, opts?: { method?: string }) => {
        if (path === "/api/scheduled-recordings" && opts?.method === "POST") {
          return Promise.resolve({ success: true, schedule: { id: "sched-new" } });
        }
        if (path === "/api/scheduled-recordings") {
          return Promise.resolve({ success: true, schedules: [{ id: "sched-new" }] });
        }
        return Promise.resolve({});
      });
      const { state } = makeSlice();

      const result = await state.armEventRecording("event-123");
      expect(result).toBe(true);
      expect(apiFetchMock).toHaveBeenCalledWith("/api/scheduled-recordings", {
        method: "POST",
        json: { calendar_event_id: "event-123" },
      });
      // loadSchedules is called after arm.
      expect(apiFetchMock).toHaveBeenCalledWith("/api/scheduled-recordings");
    });

    it("returns false on failure", async () => {
      apiFetchMock.mockImplementation((path: string, opts?: { method?: string }) => {
        if (path === "/api/scheduled-recordings" && opts?.method === "POST") {
          return Promise.reject(new Error("conflict"));
        }
        return Promise.resolve({});
      });
      const { state } = makeSlice();

      const result = await state.armEventRecording("event-bad");
      expect(result).toBe(false);
    });
  });

  describe("window lifecycle", () => {
    it("openScheduleCreate sets the window state", () => {
      const { state } = makeSlice();
      state.openScheduleCreate({ x: 100, y: 200 });
      expect(state.scheduleCreateWindow).toEqual({ origin: { x: 100, y: 200 } });
    });

    it("closeScheduleCreate clears the window state", () => {
      const { state } = makeSlice();
      state.openScheduleCreate();
      state.closeScheduleCreate();
      expect(state.scheduleCreateWindow).toBeNull();
    });

    it("openScheduleCreate with no origin sets null origin", () => {
      const { state } = makeSlice();
      state.openScheduleCreate();
      expect(state.scheduleCreateWindow).toEqual({ origin: null });
    });
  });
});
