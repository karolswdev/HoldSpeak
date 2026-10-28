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
    expect(await screen.findByText("Freeze the old ledger")).toBeTruthy();
    state = "confirmed";
    await act(async () => {
      emit("desk_changed");
      await new Promise((r) => setTimeout(r, 400));
    });
    await waitFor(() => expect(screen.queryByText("DECIDED")).toBeTruthy());
    expect(screen.getByText("Freeze the old ledger")).toBeTruthy();
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
    await waitFor(() => expect(screen.getByText("Freeze the old ledger")).toBeTruthy());
    await act(async () => {
      releaseFirst({ proposals: [{ id: "p1", kind: "decision", text: "Freeze the old ledger", state: "proposed" }] });
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(screen.queryByText("TO DECIDE")).toBeNull();
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

describe("PHILO-17 desk sweep: the record holds still while its first reads land", () => {
  it("draws the body once the first reads end, never row by row", async () => {
    let release: (value: unknown) => void = () => undefined;
    let details = 0;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const url = String(path);
      // The window reads the meeting row first; the record's own first
      // reads (useMeetingData) follow, and the detail one stalls.
      if (isDetail(url) && ++details > 1) return new Promise((resolve) => { release = resolve; }) as never;
      if (isDetail(url)) return meeting("ready") as never;
      return {} as never;
    });
    const { container } = render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    // Mounted (its wells start their reads) but not drawn: the body is busy.
    await waitFor(() => expect(container.querySelector("[aria-busy='true'][data-settling]")).toBeTruthy());
    expect(container.querySelector("[data-testid='meeting-decide']")).toBeNull();
    await act(async () => {
      release(meeting("ready"));
      await new Promise((r) => setTimeout(r, 0));
    });
    await waitFor(() => expect(container.querySelector("[data-settling]")).toBeNull());
    expect(screen.queryByTestId("meeting-decide")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "More actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Decide" }));
    expect(await screen.findByTestId("meeting-decide-well")).toBeTruthy();
    expect(container.querySelector("[aria-busy='true']:not(button)")).toBeNull();
  });
});

describe("PHILO-17 (Astra r1 on #1108): each first read ends on its own", () => {
  it("a failed detail read does not draw the body while another first read is out", async () => {
    let releaseDecisions: (value: unknown) => void = () => undefined;
    let details = 0;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const url = String(path);
      if (isDetail(url) && ++details > 1) throw new Error("detail down");
      if (isDetail(url)) return meeting("ready") as never;
      if (url.startsWith("/api/decisions")) return new Promise((resolve) => { releaseDecisions = resolve; }) as never;
      return {} as never;
    });
    const { container } = render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    await waitFor(() => expect(details).toBeGreaterThan(1));
    await act(async () => { await new Promise((r) => setTimeout(r, 50)); });
    expect(container.querySelector("[data-settling]")).toBeTruthy();
    await act(async () => {
      releaseDecisions({ decisions: [] });
      await new Promise((r) => setTimeout(r, 0));
    });
    await waitFor(() => expect(container.querySelector("[data-settling]")).toBeNull());
  });

  it("a revision read of the records never ends the detail's first read", async () => {
    let releaseDetail: (value: unknown) => void = () => undefined;
    let details = 0;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const url = String(path);
      if (isDetail(url) && ++details === 2) return new Promise((resolve) => { releaseDetail = resolve; }) as never;
      if (isDetail(url)) return meeting("ready") as never;
      return {} as never;
    });
    const { container } = render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    await waitFor(() => expect(details).toBeGreaterThan(1));
    await act(async () => {
      emit("desk_changed");
      await new Promise((r) => setTimeout(r, 400));
    });
    // The records read again and ended; the detail read is still out.
    expect(container.querySelector("[data-settling]")).toBeTruthy();
    await act(async () => {
      releaseDetail(meeting("ready"));
      await new Promise((r) => setTimeout(r, 0));
    });
    await waitFor(() => expect(container.querySelector("[data-settling]")).toBeNull());
  });
});


describe("daily work: Send opens on request", () => {
  it("does not mount Send or Decide on first open; More opens the existing title form", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      (isDetail(String(path)) ? { ...meeting("ready"), intel: { summary: "Move the cutover to Friday." }, has_summary: true } : {}) as never);
    render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    await screen.findByTestId("meeting-send");
    expect(screen.queryByTestId("meeting-send-well")).toBeNull();
    expect(screen.queryByTestId("meeting-decide-well")).toBeNull();
    // Window grammar: Send, Export and More are the toolbar's verbs.
    const toolbar = screen.getByRole("toolbar", { name: "Meeting" });
    expect(within(toolbar).getByTestId("meeting-send")).toBeTruthy();
    // W2-LIVE-2 (canvas A, After): Send follow-up… is the primary, Settings
    // the trailing verb; with a summary and nothing to review the rail is at
    // Send follow-up (Summary done).
    expect(within(toolbar).getByTestId("meeting-send")).toHaveTextContent("Send follow-up…");
    expect(within(toolbar).getByTestId("meeting-send").className).toContain("btn--primary");
    expect(within(toolbar).getByRole("button", { name: "Settings" })).toBeTruthy();
    const rail = screen.getByTestId("meeting-steps");
    expect(rail.querySelector("[aria-current=step]")?.textContent).toContain("Send follow-up");
    expect(rail.querySelector('[data-state="done"]:nth-child(3)')?.textContent).toContain("Summary");
    fireEvent.click(within(toolbar).getByRole("button", { name: "Export" }));
    expect(screen.getByRole("menuitem", { name: "Export MD" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: "Export SRT" })).toBeTruthy();
    fireEvent.click(within(toolbar).getByRole("button", { name: "Export" }));
    fireEvent.click(within(toolbar).getByRole("button", { name: "More actions" }));
    expect(screen.queryByRole("menuitem", { name: "Export MD" })).toBeNull();
    fireEvent.click(screen.getByRole("menuitem", { name: "Decide" }));
    expect(await screen.findByPlaceholderText("Decision title")).toBeTruthy();
  });
});

  it("requested Send mounts its well and names an unavailable stored summary with Retry", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      (isDetail(String(path)) ? { ...meeting("ready"), has_summary: true } : {}) as never);
    render(<MeetingRecord meetingId="m-1" onClose={() => undefined} />);
    fireEvent.click(await screen.findByTestId("meeting-send"));
    expect(await screen.findByText("Summary unavailable")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
  });
