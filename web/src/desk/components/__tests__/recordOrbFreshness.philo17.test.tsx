// PHILO-17 meetingwin, Astra r2 on #1082: ONE freshness rule for the
// recording state, with the Record orb mounted. The orb's first `/api/state`
// read is asked at a recording epoch; a Start or a Stop while it is in flight
// makes it stale, and it never moves the desk (nor, through it, the meeting's
// window).
import { act, render } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, apiRequest } from "../../../lib/api";
import { useDesk } from "../../store";
import { RecordOrb } from "../RecordOrb";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
  apiRequest: vi.fn(),
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

let answerState: (value: unknown) => void = () => undefined;

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (String(path) === "/api/state") return new Promise((resolve) => { answerState = resolve; }) as never;
    return {} as never;
  });
  vi.mocked(apiRequest).mockImplementation(async (path: string) => {
    if (String(path) === "/api/meeting/start") {
      return new Response(JSON.stringify({ success: true, meeting: { id: "m-live" } }), { status: 200 });
    }
    return new Response(JSON.stringify({ status: "stopped" }), { status: 200 });
  });
  useDesk.setState({
    recording: "idle", recordingExternal: false, recordingStartedAt: null, liveMeetingId: null,
    pullouts: [], refresh: vi.fn(async () => undefined) as never,
  });
});

describe("Astra r2: the orb's first state read never undoes a newer Start or Stop", () => {
  it("a stale IDLE snapshot after Start leaves the meeting live", async () => {
    render(<RecordOrb />);
    await act(async () => {
      await useDesk.getState().startRecording();
    });
    expect(useDesk.getState().recording).toBe("recording");
    expect(useDesk.getState().liveMeetingId).toBe("m-live");
    // The read asked before the Start answers now: idle.
    await act(async () => {
      answerState({ meeting_active: false, meeting_id: null, activity: { state: "idle" } });
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(useDesk.getState().recording).toBe("recording");
    expect(useDesk.getState().liveMeetingId).toBe("m-live");
  });

  it("a stale LIVE snapshot after Stop leaves the meeting stopped", async () => {
    render(<RecordOrb />);
    await act(async () => {
      await useDesk.getState().startRecording();
      await useDesk.getState().stopRecording();
    });
    expect(useDesk.getState().recording).toBe("idle");
    await act(async () => {
      answerState({ meeting_active: true, meeting_id: "m-live", activity: { state: "meeting_live" } });
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(useDesk.getState().recording).toBe("idle");
    expect(useDesk.getState().liveMeetingId).toBeNull();
  });
});
