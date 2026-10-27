/* The Live meeting app (W2-LIVE, 2026-10-27; canvas
 * docs/internal/betterment/canvases/live-direction-2026-10-27.html,
 * direction A "the transcript is the page").
 *
 * The rig cannot record, so DURING replays the hub's own `segment` frames
 * (web/src/test/wire/live.segments.wire.json, fenced by
 * tests/integration/test_face_wire_fences.py::test_live_segment_frames) and the
 * hub's recorded /api/settings/hub answers, and drives them to the rendered
 * window: a time mark from `start_time`, the speaker's name when the speaker
 * changes, the bookmark mark, the live state once in the status bar, Stop as
 * the danger verb, Bookmark and Settings in the toolbar, and no gear wing.
 */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import segmentsWire from "../../test/wire/live.segments.wire.json";
import hubNoEngine from "./fixtures/settings-wire/hub.json";
import needsYouRecorded from "./fixtures/needsYou.recorded.json";
import { recordedGet, type Gets } from "../../test/recordedHub";
import { WingSlotContext } from "../surface/wings";
import { useDesk } from "../store";

type Frame = { type: string; data: unknown };

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
  openSurfaceOr: vi.fn(),
}));

function subscribe(type: string, listener: (frame: Frame) => void) {
  const set = mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
  set.add(listener);
  mocks.listeners.set(type, set);
  return () => set.delete(listener);
}

function emit(type: string, data: unknown) {
  act(() => {
    for (const listener of [...(mocks.listeners.get(type) ?? [])]) listener({ type, data });
    for (const listener of [...(mocks.listeners.get("*") ?? [])]) listener({ type, data });
  });
}

vi.mock("../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useOptionalRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));

vi.mock("../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shell")>()),
  openSurfaceOr: mocks.openSurfaceOr,
}));

import { LiveCore } from "../../pages/cores/LiveCore";
import { LiveMeetingTools } from "../../pages/cores/LiveMeetingTools";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const recorded = needsYouRecorded as any;
const hubWithEngine = recorded.calendar.none.gets["/api/settings/hub"];
const SEGMENTS = (segmentsWire as { wire: Record<string, unknown>[] }).wire;

function answer(gets: Gets) {
  mocks.apiFetch.mockImplementation(async (path: string) => {
    const got = recordedGet(gets, path);
    return got ?? {};
  });
}

function WindowHost({ children }: { children: ReactNode }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <WingSlotContext.Provider value={setWings}>
      <div data-testid="window-head">{wings}</div>
      {children}
    </WingSlotContext.Provider>
  );
}

async function mount(meetingId?: string) {
  const view = render(
    <WindowHost>
      <LiveCore meetingId={meetingId} />
    </WindowHost>,
  );
  await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  return view;
}

describe("Live meeting: during, the transcript is the page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    useDesk.setState({ recording: "recording", liveMeetingId: "m-live" });
    answer({
      "/api/settings/hub": hubWithEngine,
      "/api/state": { active: true, meeting_active: true, meeting_id: "m-live", title: "Ledger cutover sync" },
    });
  });

  it("draws each recorded segment frame as a line with its time mark and its speaker once per run", async () => {
    await mount("m-live");
    for (const frame of SEGMENTS) emit("segment", frame);

    const lines = await screen.findAllByTestId("live-transcript-line");
    expect(lines).toHaveLength(4);
    const marks = lines.map((line) => line.querySelector(".live-doc-when")?.textContent);
    expect(marks).toEqual(["0:04", "0:19", "0:41", "1:02"]);
    // The speaker heads a run: Priya's second line carries no name.
    const who = lines.map((line) => line.querySelector(".live-doc-who")?.textContent ?? "");
    expect(who).toEqual(["Me", "Priya", "", "Me"]);
    expect(lines[1]).toHaveTextContent("It holds if the backup job moves to 22:00.");
    // The bookmarked frame wears the mark; the others do not.
    expect(lines.map((line) => line.hasAttribute("data-flagged"))).toEqual([false, false, false, true]);
    // A document, not a counted stream: no count head, no "segments".
    expect(document.querySelector(".surface-stream-head")).toBeNull();
    expect(document.body.textContent ?? "").not.toMatch(/segments?\b/i);
    expect(screen.getByTestId("live-listening")).toHaveTextContent("Listening");
  });

  it("says the live state once in the status bar: Recording, the clock, the summary engine by name", async () => {
    await mount("m-live");
    emit("duration", "12:04");
    const bar = screen.getByTestId("live-statusbar");
    await waitFor(() => expect(within(bar).getByTestId("live-capture-state")).toHaveTextContent(/Recording\s*12:04/));
    expect(within(bar).getByTestId("live-summary-engine")).toHaveTextContent("Summaries on Hs201 Meeting Engine");
    // The clock stands once on the face.
    expect((document.body.textContent ?? "").split("12:04")).toHaveLength(2);
    // No host or scope chip in the status bar (UX-CANON A.9 as amended).
    expect(bar.querySelector(".egress-chip, [data-egress]")).toBeNull();
  });

  it("keeps Stop as the danger verb and Bookmark and Settings in the toolbar; no gear wing", async () => {
    await mount("m-live");
    const toolbar = screen.getByTestId("live-toolbar");
    const stop = within(toolbar).getByRole("button", { name: "Stop meeting" });
    expect(stop.className).toContain("btn--danger");
    expect(within(toolbar).getByRole("button", { name: "Bookmark" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Configure meeting" })).toBeNull();
    expect(screen.getByTestId("window-head")).toBeEmptyDOMElement();
    // The steps band is the before face; while it records the transcript leads.
    expect(screen.queryByTestId("live-steps")).toBeNull();

    fireEvent.click(within(toolbar).getByRole("button", { name: "Settings" }));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "meetings");
  });

  it("names a bookmark from the toolbar and sends it to the hub", async () => {
    await mount("m-live");
    fireEvent.click(within(screen.getByTestId("live-toolbar")).getByRole("button", { name: "Bookmark" }));
    const field = screen.getByRole("textbox", { name: "Name this moment" });
    fireEvent.change(field, { target: { value: "the decision" } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() =>
      expect(mocks.apiFetch).toHaveBeenCalledWith("/api/bookmark", { method: "POST", json: { label: "the decision" } }),
    );
  });
});

describe("Live meeting: before, the honest summary word", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    useDesk.setState({ recording: "idle", liveMeetingId: null });
  });

  it("says No engine for summaries on the hub that has none, and keeps the four steps", async () => {
    answer({ "/api/settings/hub": hubNoEngine });
    await mount();
    const engine = await screen.findByTestId("live-summary-engine");
    expect(engine).toHaveTextContent("No engine for summaries");
    expect(engine.querySelector(".kit-dot")?.getAttribute("data-tone")).toBe("warn");
    expect(screen.getByTestId("live-steps")).toBeInTheDocument();
    expect(within(screen.getByTestId("live-toolbar")).getByRole("button", { name: "Start meeting" }).className).toContain(
      "btn--primary",
    );
    expect(within(screen.getByTestId("live-toolbar")).queryByRole("button", { name: "Bookmark" })).toBeNull();
  });
});

describe("Settings ▸ Meetings ▸ Live meeting holds the old gear wing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
  });

  it("says the true word on an idle hub: no devices, no jobs, and tries a phrase", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/plugin-jobs/summary")
        return { total_jobs: 0, queued_jobs: 0, running_jobs: 0, failed_jobs: 0, next_retry_at: null };
      if (path === "/api/devices/health") return { devices: [] };
      if (path === "/api/intents/control") return { profile: "balanced" };
      if (path === "/api/intents/preview") return { route: "architecture", intent: "decision", confidence: 0.82 };
      return {};
    });
    render(<LiveMeetingTools />);
    expect(await screen.findByText("No jobs waiting")).toBeInTheDocument();
    expect(await screen.findByText("None attached")).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toMatch(/\b0\b/);
    expect(screen.queryByRole("button", { name: "Process pending" })).toBeNull();

    fireEvent.change(screen.getByRole("textbox", { name: "Preview route" }), { target: { value: "we decided to freeze" } });
    fireEvent.click(screen.getByRole("button", { name: "Preview route" }));
    expect(await screen.findByText("architecture")).toBeInTheDocument();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/intents/preview", {
      method: "POST",
      json: { text: "we decided to freeze" },
    });
  });

  it("offers Process pending only when work waits", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) =>
      path === "/api/plugin-jobs/summary" ? { total_jobs: 2, failed_jobs: 1 } : {},
    );
    render(<LiveMeetingTools />);
    const jobs = await screen.findByTestId("settings-live-jobs");
    await waitFor(() => expect(jobs).toHaveTextContent("Total jobs 2 · Failed jobs 1"));
    fireEvent.click(screen.getByRole("button", { name: "Process pending" }));
    await waitFor(() =>
      expect(mocks.apiFetch).toHaveBeenCalledWith("/api/plugin-jobs/process", { method: "POST", json: {} }),
    );
  });
});
