import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest } from "../../../lib/api";
import { currentWriteFailure, clearWriteFailure } from "../../hooks/useWriteReceipt";
import { createRecordingSlice } from "../recordingSlice";
import type { DeskState } from "../types";

vi.mock("../../../lib/api", () => ({ apiRequest: vi.fn() }));

const request = vi.mocked(apiRequest);

function makeSlice() {
  const state: Record<string, unknown> = {
    items: { meeting: [] },
    refresh: vi.fn().mockResolvedValue(undefined),
  };
  const set = (partial: Partial<DeskState> | ((s: DeskState) => Partial<DeskState>)) => {
    Object.assign(
      state,
      typeof partial === "function"
        ? partial(state as unknown as DeskState)
        : partial,
    );
  };
  const get = () => state as unknown as DeskState;
  Object.assign(
    state,
    createRecordingSlice(set, get, { setState: set, getState: get } as never),
  );
  return state as unknown as ReturnType<typeof createRecordingSlice> & {
    refresh: ReturnType<typeof vi.fn>;
  };
}

describe("recordingSlice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearWriteFailure();
  });

  it("leaves a refused stop retryable, then idles only after the retry lands", async () => {
    request.mockRejectedValueOnce(new TypeError("offline")).mockResolvedValueOnce(new Response());
    const state = makeSlice();
    (state as unknown as { recording: string }).recording = "recording";

    await state.stopRecording();

    expect(state.recording).toBe("recording");
    expect(state.refresh).not.toHaveBeenCalled();
    const refusal = currentWriteFailure();
    expect(refusal?.verb).toBe("STOP RECORDING");
    expect(refusal?.retry).toEqual(expect.any(Function));

    refusal?.retry?.();
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    expect(request).toHaveBeenCalledTimes(2);
    expect(state.recording).toBe("idle");
    expect(state.refresh).toHaveBeenCalledOnce();
  });

  it("returns a refused start to idle and retries the same start into recording", async () => {
    request.mockRejectedValueOnce(new TypeError("offline")).mockResolvedValueOnce(new Response());
    const state = makeSlice();

    await state.startRecording();

    expect(state.recording).toBe("idle");
    const refusal = currentWriteFailure();
    expect(refusal?.verb).toBe("START RECORDING");
    expect(refusal?.retry).toEqual(expect.any(Function));

    refusal?.retry?.();
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    expect(request).toHaveBeenCalledTimes(2);
    expect(state.recording).toBe("recording");
  });

  it("keeps the calendar event context on an explicit retry", async () => {
    request.mockRejectedValueOnce(new TypeError("offline")).mockResolvedValueOnce(new Response());
    const state = makeSlice();
    const context = { calendarEventId: "event-1" };

    await state.startRecording(context);

    expect(request).toHaveBeenNthCalledWith(1, "/api/meeting/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ calendar_event_id: "event-1" }),
    });
    const refusal = currentWriteFailure();
    expect(refusal?.retry).toEqual(expect.any(Function));

    refusal?.retry?.();
    await new Promise<void>((resolve) => setTimeout(resolve, 0));

    expect(request).toHaveBeenNthCalledWith(2, "/api/meeting/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ calendar_event_id: "event-1" }),
    });
    expect(state.recording).toBe("recording");
  });

  // PHILO-13-04 (A3) — a refused start is not a recording. The hub answers
  // 501 when it has no recorder (holdspeak/web/routes/meetings/live.py); the
  // fetch resolves, so the slice must read `res.ok`.
  // replaces (the face half): tests/e2e/test_philo13_04_faces_glass.py::TestFacesDoNotLie::test_a_refused_start_says_not_recording
  // (the hub half: tests/integration/test_desk_capture.py)
  it("a refused start (501) stays idle, starts no timer and says Not recording", async () => {
    request.mockResolvedValueOnce(
      new Response(JSON.stringify({ success: false, error: "Meeting start control not supported" }), { status: 501 }),
    );
    const state = makeSlice();

    await state.startRecording();

    expect(state.recording).toBe("idle");
    expect(state.recordingStartedAt).toBeNull();
    const refusal = currentWriteFailure();
    expect(refusal?.label).toBe("NOT RECORDING · NO RECORDER ON THIS HUB");
    // A Retry cannot add a recorder: the verb that does nothing is withheld (A.11).
    expect(refusal?.retry).toBeNull();
    // Never the hub's raw words on the face.
    expect(refusal?.label).not.toMatch(/control not supported/i);
  });

  it("a failed start (500) stays idle and keeps Retry", async () => {
    request.mockResolvedValueOnce(new Response("{}", { status: 500 }));
    const state = makeSlice();

    await state.startRecording();

    expect(state.recording).toBe("idle");
    expect(currentWriteFailure()?.label).toBe("NOT RECORDING · THE HUB DID NOT START IT");
    expect(currentWriteFailure()?.retry).toEqual(expect.any(Function));
  });

  it("a stale calendar context stays idle without a retry", async () => {
    request.mockResolvedValueOnce(new Response("{}", { status: 409 }));
    const state = makeSlice();

    await state.startRecording({ calendarEventId: "event-gone" });

    expect(state.recording).toBe("idle");
    expect(currentWriteFailure()?.label).toBe("NOT RECORDING · MEETING CONTEXT EXPIRED");
    expect(currentWriteFailure()?.retry).toBeNull();
  });

  it("a network failure says Not recording + Hub unreachable", async () => {
    request.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    const state = makeSlice();

    await state.startRecording();

    expect(state.recording).toBe("idle");
    expect(currentWriteFailure()?.label).toBe("NOT RECORDING · HUB UNREACHABLE");
  });

  it("a refused stop (500) keeps the recording and its Retry", async () => {
    request.mockResolvedValueOnce(new Response("{}", { status: 500 }));
    const state = makeSlice();
    (state as unknown as { recording: string }).recording = "recording";

    await state.stopRecording();

    expect(state.recording).toBe("recording");
    expect(currentWriteFailure()?.verb).toBe("STOP RECORDING");
    expect(currentWriteFailure()?.label).toBe("STILL RECORDING · THE HUB DID NOT STOP IT");
    expect(currentWriteFailure()?.retry).toEqual(expect.any(Function));
  });

  it("stopped capture idles on a partial save and keeps the retained Meeting without fake recovery", async () => {
    request.mockResolvedValueOnce(new Response(JSON.stringify({
      success: true,
      status: "stopped",
      meeting: { id: "meeting-same-id" },
      save: { database_saved: true, json_saved: false },
      save_error: "JSON export failed",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const state = makeSlice();
    (state as unknown as { recording: string; liveMeetingId: string }).recording = "recording";
    (state as unknown as { liveMeetingId: string }).liveMeetingId = "meeting-same-id";

    await state.stopRecording();

    expect(state.recording).toBe("idle");
    expect(currentWriteFailure()?.label).toBe("STOPPED · PARTLY SAVED");
    expect(currentWriteFailure()?.detail).toBe("JSON export failed");
    expect(currentWriteFailure()?.retry).toBeNull();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("recovers a failed database save only from an explicit recoverable checkpoint", async () => {
    request.mockResolvedValueOnce(new Response(JSON.stringify({
      success: true,
      status: "stopped",
      meeting: { id: "meeting-recoverable", capture_status: "recoverable" },
      save: { database_saved: false, json_saved: true },
      save_error: "database unavailable",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    request.mockResolvedValueOnce(new Response(JSON.stringify({ recovered: true }), { status: 200 }));
    const state = makeSlice();
    (state as unknown as { recording: string }).recording = "recording";

    await state.stopRecording();

    expect(state.recording).toBe("idle");
    expect(currentWriteFailure()?.retry).toEqual(expect.any(Function));
    currentWriteFailure()?.retry?.();
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    expect(request).toHaveBeenNthCalledWith(2, "/api/meetings/meeting-recoverable/capture/recover", { method: "POST" });
    expect(currentWriteFailure()).toBeNull();
  });

  it("keeps recording active when the Stop response explicitly says capture continues", async () => {
    request.mockResolvedValueOnce(new Response(JSON.stringify({
      success: true,
      status: "recording",
      meeting: { id: "meeting-still-live" },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const state = makeSlice();
    (state as unknown as { recording: string }).recording = "recording";

    await state.stopRecording();

    expect(state.recording).toBe("recording");
    expect(currentWriteFailure()?.label).toBe("STILL RECORDING · THE HUB DID NOT STOP IT");
  });

  it("stopped capture reports save failure without inventing a Stop retry", async () => {
    request.mockResolvedValueOnce(new Response(JSON.stringify({
      success: true,
      status: "stopped",
      meeting: { id: "meeting-save-failed" },
      save: { database_saved: false, json_saved: false },
      save_error: "disk full",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const state = makeSlice();
    (state as unknown as { recording: string }).recording = "recording";

    await state.stopRecording();

    expect(state.recording).toBe("idle");
    expect(currentWriteFailure()?.label).toBe("STOPPED · SAVE FAILED");
    expect(currentWriteFailure()?.retry).toBeNull();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("keeps a clean save stopped while naming device cleanup failure", async () => {
    request.mockResolvedValueOnce(new Response(JSON.stringify({
      success: true,
      status: "stopped",
      meeting: { id: "meeting-cleanup" },
      save: { database_saved: true, json_saved: true },
      save_error: null,
      device_cleanup_error: "Mic audio device did not close.",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const state = makeSlice();
    (state as unknown as { recording: string }).recording = "recording";

    await state.stopRecording();

    expect(state.recording).toBe("idle");
    expect(currentWriteFailure()?.label).toBe("STOPPED · SAVED · AUDIO DEVICE CLEANUP FAILED");
    expect(currentWriteFailure()?.detail).toBe("Mic audio device did not close.");
    expect(currentWriteFailure()?.retry).toBeNull();
  });
});
