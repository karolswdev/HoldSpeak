// PHILO-17 meetingwin, Astra r1 on #1082 — three fences on the meeting's own
// window (history/MeetingRecord.tsx, desk/pullouts/MeetingWindow.tsx):
//  1. a proposal confirmed elsewhere (an agent) leaves Outcomes on the next
//     signal, though the meeting row itself did not change;
//  2. the window adopts the durable summary run (QUEUED) and settles it (RAN)
//     when the meeting's own state goes final;
//  3. a Stop is final: a slow first `/api/state` that answers after recording
//     went idle never brings the live room back.
import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { useDesk } from "../../../../desk/store";
import { MeetingRecord } from "../MeetingRecord";
import { useRecordingHere } from "../../../../desk/pullouts/MeetingWindow";

vi.mock("../../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
const listeners = new Map<string, Set<(frame?: { type: string; data: unknown }) => void>>();
const subscribe = (type: string, listener: (frame?: { type: string; data: unknown }) => void) => {
  const set = listeners.get(type) ?? new Set();
  set.add(listener);
  listeners.set(type, set);
  return () => set.delete(listener);
};
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));
const emit = (type: string) => listeners.get(type)?.forEach((l) => l({
  type: "desk_changed",
  data: { kind: "meeting", id: "m-1", op: "update", origin: "agent", changes: [{ kind: "meeting", id: "m-1", op: "update" }] },
}));
const isDetail = (url: string) => url.split("?")[0] === "/api/meetings/m-1";

const meeting = (intel: string) => ({
  id: "m-1", title: "Platform sync", started_at: "2026-10-10T09:00:00Z", duration_seconds: 60,
  capture_status: "finalized", intel_status: intel, segments: [], planned_route: null, run_receipt: null,
});

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  listeners.clear();
});

describe("Astra r1: the meeting window's own records follow the hub", () => {
  it("a proposal confirmed elsewhere updates the Outcomes row on the next signal (the meeting row unchanged)", async () => {
    let state = "proposed";
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const url = String(path);
      if (isDetail(url)) return meeting("ready") as never;
      if (url.endsWith("/follow-through-proposals")) {
        return { proposals: [{ id: "p1", kind: "decision", text: "Freeze the old ledger", state }] } as never;
      }
      return {} as never;
    });
    render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    fireEvent.click(await screen.findByRole("tab", { name: "Decisions" }));
    await screen.findByText("Freeze the old ledger");
    fireEvent.click(screen.getByText("Freeze the old ledger"));
    state = "confirmed";
    await act(async () => {
      emit("desk_changed");
      await new Promise((r) => setTimeout(r, 400));
    });
    await waitFor(() => expect(screen.queryByText("Decided")).toBeTruthy());
    expect(screen.getByRole("grid")).toHaveTextContent("Freeze the old ledger");
  });

  it("Astra r2: an older first read that lands last never brings TO DECIDE back", async () => {
    let releaseFirst: (value: unknown) => void = () => undefined;
    let reads = 0;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const url = String(path);
      if (isDetail(url)) return meeting("ready") as never;
      if (url.endsWith("/follow-through-proposals")) {
        reads += 1;
        if (reads === 1) {
          // The first read stalls; it holds the state from before the confirm.
          return new Promise((resolve) => { releaseFirst = resolve; }) as never;
        }
        return { proposals: [{ id: "p1", kind: "decision", text: "Freeze the old ledger", state: "confirmed" }] } as never;
      }
      return {} as never;
    });
    render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    await waitFor(() => expect(reads).toBe(1));
    await act(async () => {
      emit("desk_changed");
      await new Promise((r) => setTimeout(r, 400));
    });
    fireEvent.click(await screen.findByRole("tab", { name: "Decisions" }));
    await screen.findByText("Freeze the old ledger");
    fireEvent.click(screen.getByText("Freeze the old ledger"));
    await act(async () => {
      releaseFirst({ proposals: [{ id: "p1", kind: "decision", text: "Freeze the old ledger", state: "proposed" }] });
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();
  });

  it("adopts a durable run as QUEUED and settles it when the meeting goes final", async () => {
    let intel = "running";
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      (isDetail(String(path)) ? meeting(intel) : {}) as never);
    render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    const receipt = await screen.findByTestId("meetings-run-receipt");
    expect(receipt.textContent).toMatch(/^Queued at \d/);
    intel = "ready";
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
    });
    await waitFor(() => expect(screen.getByTestId("meetings-run-receipt").textContent).toMatch(/^Ran at \d/));
  });
});

describe("Astra r1: a Stop is final for the meeting's window", () => {
  it("a slow first state read that answers after Stop never brings the live room back", async () => {
    let answer: (value: unknown) => void = () => undefined;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path) === "/api/state") return new Promise((resolve) => { answer = resolve; }) as never;
      return {} as never;
    });
    useDesk.setState({ recording: "recording", liveMeetingId: "m-1" });
    const { result } = renderHook(() => useRecordingHere("m-1"));
    expect(result.current[0]).toBe(true);
    act(() => {
      useDesk.setState({ recording: "idle", liveMeetingId: null });
    });
    expect(result.current[0]).toBe(false);
    // The read asked before the Stop answers now, from the live moment.
    await act(async () => {
      answer({ meeting_active: true, meeting_id: "m-1", id: "m-1" });
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(result.current[0]).toBe(false);
  });
});

it("keeps action and contents chrome while the meeting row is pending or failed", async () => {
  let reject: (reason: Error) => void = () => undefined;
  vi.mocked(apiFetch).mockImplementation(async path => isDetail(String(path)) ? new Promise((_resolve, fail) => { reject = fail; }) as never : {} as never);
  render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
  expect(screen.getByTestId("meeting-toolbar")).toBeVisible();
  expect(screen.getByRole("tab", { name: "Transcript" })).toBeVisible();
  expect(screen.getByTestId("meeting-status")).toHaveTextContent("Reading meeting");
  await act(async () => reject(new Error("offline")));
  expect(await screen.findByRole("alert")).toHaveTextContent("offline");
  expect(screen.getByTestId("meeting-toolbar")).toBeVisible();
  expect(screen.getByRole("tab", { name: "Transcript" })).toBeVisible();
  expect(screen.getByTestId("meeting-status")).toHaveTextContent("Meeting not read");
});

describe("daily work: Send opens on request", () => {
  it("does not mount Send or Decide on first open; More opens the existing title form", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      (isDetail(String(path)) ? { ...meeting("ready"), intel: { summary: "Move the cutover to Friday." }, has_summary: true } : {}) as never);
    render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    await screen.findByTestId("meeting-send");
    expect(screen.queryByTestId("meeting-send-well")).toBeNull();
    expect(screen.queryByTestId("meeting-decide-well")).toBeNull();
    const toolbar = screen.getByTestId("meeting-toolbar");
    expect(within(toolbar).getByRole("button", { name: "Send to…" })).toBeEnabled();
    fireEvent.click(within(toolbar).getByRole("button", { name: "Actions ▾" }));
    expect(screen.getByRole("menuitem", { name: "Export MD" })).toBeVisible();
    expect(screen.getByRole("menuitem", { name: "Export SRT" })).toBeVisible();
    expect(screen.getByRole("menuitem", { name: "Settings" })).toBeVisible();
    fireEvent.click(screen.getByRole("menuitem", { name: "Decide" }));
    expect(await screen.findByPlaceholderText("Decision title")).toBeTruthy();
  });
});

  it("requested Send mounts the shared seat and retries an unreadable sends list", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/channels/sends")) throw new Error("offline");
      return (isDetail(String(path)) ? { ...meeting("ready"), has_summary: true } : {}) as never;
    });
    render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    await waitFor(() => expect(screen.getByTestId("meeting-send")).toBeEnabled());
    fireEvent.click(screen.getByTestId("meeting-send"));
    expect(await screen.findByTestId("sends-unreadable")).toHaveTextContent("Cannot read sends");
    expect(screen.getByTestId("sends-unreadable-retry")).toBeEnabled();
  });
