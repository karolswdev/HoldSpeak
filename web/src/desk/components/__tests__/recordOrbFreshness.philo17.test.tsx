// PHILO-17 meetingwin, Astra r2 on #1082: ONE freshness rule for the
// recording state, with the Record orb mounted. The orb's first `/api/state`
// read is asked at a recording epoch; a Start or a Stop while it is in flight
// makes it stale, and it never moves the desk (nor, through it, the meeting's
// window).
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, apiRequest } from "../../../lib/api";
import { useDesk } from "../../store";
import { RecordOrb } from "../RecordOrb";

const shell = vi.hoisted(() => ({ openSurfaceOr: vi.fn() }));
vi.mock("../../shell", () => ({ openSurfaceOr: shell.openSurfaceOr }));

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

  it("a long press opens Meetings Record without starting a meeting", async () => {
    vi.useFakeTimers();
    try {
      render(<RecordOrb />);
      const orb = screen.getByRole("button", { name: "Record a meeting" });
      fireEvent.pointerDown(orb);
      await act(async () => { vi.advanceTimersByTime(500); });
      expect(shell.openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", "record");
      fireEvent.pointerUp(orb);
      fireEvent.click(orb);
      expect(apiRequest).not.toHaveBeenCalledWith("/api/meeting/start", expect.anything());
    } finally {
      vi.useRealTimers();
    }
  });
});

// W7 (canvas 2026-10-28 (b), direction A "The ring and the clock").
describe("the Record tile while it records: the ring and the clock", () => {
  it("recording with a start time: the ring state and a clock with the elapsed time", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    try {
      vi.setSystemTime(new Date("2026-10-28T10:00:00Z"));
      useDesk.setState({ recording: "recording", recordingStartedAt: Date.now() - (12 * 60 + 4) * 1000 });
      render(<RecordOrb />);
      const orb = screen.getByRole("button", { name: "Stop recording, 12:04" });
      expect(orb.className).toContain("is-recording");
      const clock = screen.getByTestId("desk-orb-clock");
      expect(clock.textContent).toBe("12:04");
      expect(clock).toHaveAttribute("aria-hidden", "true");
      await act(async () => { vi.advanceTimersByTime(1000); });
      expect(screen.getByTestId("desk-orb-clock").textContent).toBe("12:05");
    } finally {
      vi.useRealTimers();
    }
  });

  it("idle: no clock and no ring state", () => {
    render(<RecordOrb />);
    expect(screen.queryByTestId("desk-orb-clock")).toBeNull();
    expect(screen.getByRole("button", { name: "Record a meeting" }).className).not.toContain("is-recording");
  });

  it("recording with no start time from the hub: no clock (never 0:00)", () => {
    useDesk.setState({ recording: "recording", recordingStartedAt: null });
    render(<RecordOrb />);
    expect(screen.getByRole("button", { name: "Stop recording" }).className).toContain("is-recording");
    expect(screen.queryByTestId("desk-orb-clock")).toBeNull();
  });
});
