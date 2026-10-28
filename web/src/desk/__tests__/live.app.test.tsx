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
import micHearingWire from "../../test/wire/live.mic-check.hearing.wire.json";
import micRefusedWire from "../../test/wire/live.mic-check.not-allowed.wire.json";
import passWire from "../../test/wire/live.pass.frames.wire.json";
import levelWire from "../../test/wire/live.level.frames.wire.json";
import hubNoEngine from "./fixtures/settings-wire/hub.json";
import localAiCold from "../../test/wire/setup-local-ai.wire.json";
import meetingsHubReady from "./fixtures/meetings-hub/p17t-ready.json";
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
const MIC_HEARING = (micHearingWire as { wire: Record<string, unknown> }).wire;
const MIC_REFUSED = (micRefusedWire as { wire: Record<string, unknown> }).wire;
const PASS = (passWire as { wire: { type: string; data: unknown }[] }).wire;
const LEVELS = (levelWire as { wire: { type: string; data: unknown }[] }).wire;

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

describe("Live meeting: before, the ready sheet (W2-LIVE-2)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    useDesk.setState({ recording: "idle", liveMeetingId: null });
  });

  it("on a hub with no speech and no engine: each row says its state and carries its one verb", async () => {
    answer({
      "/api/settings/hub": hubNoEngine,
      "/api/settings": recorded.calendar.none.gets["/api/settings"],
      "/api/setup/local-ai": (localAiCold as { wire: unknown }).wire,
      "/api/meeting/mic-check": MIC_HEARING,
    });
    await mount();
    const sheet = await screen.findByTestId("live-ready");
    expect(within(sheet).getByText("It will hear")).toBeInTheDocument();
    expect(within(sheet).getByText("It will write")).toBeInTheDocument();
    // Live slice 3: the hub's mic check (one short sample) — the bars and Hearing.
    await waitFor(() => expect(screen.getByTestId("live-ready-mic")).toHaveTextContent(/Microphone\s*System default\s*Hearing/));
    expect(within(screen.getByTestId("live-ready-mic")).getByRole("meter", { name: "Microphone level" })).toHaveAttribute("aria-valuenow", String(MIC_HEARING.level));
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/meeting/mic-check", { method: "POST" });
    expect(screen.getByTestId("live-ready-system")).toHaveTextContent(/System audio\s*Auto\s*Ready/);
    const transcript = screen.getByTestId("live-ready-transcript");
    await waitFor(() => expect(within(transcript).getByTestId("live-ready-transcript-state")).toHaveTextContent("Not set up"));
    expect(transcript).toHaveTextContent("Whisper base, on this Mac");
    // Set up speech is the Transcript row's verb, not a toolbar item.
    expect(within(transcript).getByRole("button", { name: "Set up speech · 144 MB" })).toBeInTheDocument();
    expect(within(screen.getByTestId("live-toolbar")).queryByRole("button", { name: /Set up speech/ })).toBeNull();
    const summary = screen.getByTestId("live-ready-summary");
    expect(within(summary).getByTestId("live-ready-summary-state")).toHaveTextContent("No engine");
    expect(within(summary).getByTestId("live-ready-summary-state").getAttribute("data-tone")).toBe("warn");
    fireEvent.click(within(summary).getByRole("button", { name: "Choose engine" }));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("open-concierge", "/models", "meetings");

    // The status bar keeps the honest words; the steps band stays.
    expect(screen.getByTestId("live-summary-engine")).toHaveTextContent("No engine for summaries");
    expect(screen.getByTestId("live-capture-state")).toHaveTextContent("Speech not set up");
    expect(screen.getByTestId("live-steps")).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toContain("Start a meeting to begin");
    const toolbar = screen.getByTestId("live-toolbar");
    expect(within(toolbar).getByRole("button", { name: "Start meeting" }).className).toContain("btn--primary");
    expect(within(toolbar).queryByRole("button", { name: "Bookmark" })).toBeNull();
  });

  it("on a hub with speech on this Mac and an engine: every row is Ready, no fixing verb", async () => {
    answer({
      "/api/settings/hub": hubWithEngine,
      "/api/settings": recorded.calendar.none.gets["/api/settings"],
      "/api/setup/local-ai": (meetingsHubReady as Record<string, unknown>)["/api/setup/local-ai"],
    });
    await mount();
    const transcript = await screen.findByTestId("live-ready-transcript");
    await waitFor(() => expect(within(transcript).getByTestId("live-ready-transcript-state")).toHaveTextContent("Ready"));
    expect(transcript).toHaveTextContent("Whisper base, on this Mac");
    expect(screen.getByTestId("live-ready-summary")).toHaveTextContent(/Hs201 Meeting Engine, after the meeting\s*Ready/);
    expect(screen.queryByRole("button", { name: /Set up speech/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Choose engine" })).toBeNull();
    expect(screen.getByTestId("live-capture-state")).toHaveTextContent("Ready");
  });

  it("sends the name he typed before Start to the live meeting", async () => {
    answer({ "/api/settings/hub": hubWithEngine, "/api/settings": recorded.calendar.none.gets["/api/settings"] });
    await mount();
    fireEvent.change(screen.getByRole("textbox", { name: "Meeting name" }), { target: { value: "Ledger cutover sync" } });
    fireEvent.click(within(screen.getByTestId("live-toolbar")).getByRole("button", { name: "Start meeting" }));
    await waitFor(() =>
      expect(mocks.apiFetch).toHaveBeenCalledWith("/api/meeting", { method: "PATCH", json: { title: "Ledger cutover sync" } }),
    );
    const order = mocks.apiFetch.mock.calls.map(([path]) => path);
    expect(order.indexOf("/api/meeting/start")).toBeLessThan(order.indexOf("/api/meeting"));
  });
});

describe("Live meeting: what the hub hears (Live slice 3)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
  });

  it("before: a refused grant says Not allowed with Allow, and no level", async () => {
    useDesk.setState({ recording: "idle", liveMeetingId: null });
    answer({
      "/api/settings/hub": hubWithEngine,
      "/api/settings": recorded.calendar.none.gets["/api/settings"],
      "/api/meeting/mic-check": MIC_REFUSED,
    });
    await mount();
    const row = await screen.findByTestId("live-ready-mic");
    await waitFor(() => expect(within(row).getByTestId("live-ready-mic-state")).toHaveTextContent("Not allowed"));
    expect(within(row).getByTestId("live-ready-mic-state").getAttribute("data-tone")).toBe("fail");
    expect(within(row).queryByRole("meter")).toBeNull();
    expect(within(row).getByRole("button", { name: "Allow…" })).toBeInTheDocument();
  });

  it("before: digital silence says Quiet and Check again listens once more", async () => {
    useDesk.setState({ recording: "idle", liveMeetingId: null });
    answer({
      "/api/settings/hub": hubWithEngine,
      "/api/settings": recorded.calendar.none.gets["/api/settings"],
      "/api/meeting/mic-check": { ...MIC_HEARING, state: "quiet", level: 0 },
    });
    await mount();
    const row = await screen.findByTestId("live-ready-mic");
    await waitFor(() => expect(row).toHaveTextContent("Quiet"));
    fireEvent.click(within(row).getByRole("button", { name: "Check again" }));
    await waitFor(() =>
      expect(mocks.apiFetch.mock.calls.filter(([path]) => path === "/api/meeting/mic-check")).toHaveLength(2),
    );
  });

  it("during: the foot shows the level, who the hub hears, Writing while a pass runs, and the saved reach", async () => {
    useDesk.setState({ recording: "recording", liveMeetingId: "m-live" });
    answer({
      "/api/settings/hub": hubWithEngine,
      "/api/state": { active: true, meeting_active: true, id: "m-live", meeting_id: "m-live", title: "Ledger cutover sync",
        mic_label: "Me", remote_label: "Remote" },
    });
    await mount("m-live");
    for (const frame of SEGMENTS) emit("segment", frame);
    const foot = await screen.findByTestId("live-listening");
    expect(foot).toHaveTextContent("Listening");
    expect(screen.queryByTestId("live-saved-through")).toBeNull();

    // The meeting's own level frames: the microphone is the louder source.
    for (const frame of LEVELS) emit(frame.type, frame.data);
    await waitFor(() => expect(screen.getByTestId("live-listening-who")).toHaveTextContent("Me"));
    expect(within(foot).getByRole("meter", { name: "Meeting level" })).toHaveAttribute("aria-valuenow", "0.62");

    // A pass hands its audio to the engine, then the saved transcript reaches 1:06.
    emit(PASS[0].type, PASS[0].data);
    await waitFor(() => expect(screen.getByTestId("live-listening")).toHaveAttribute("data-state", "writing"));
    expect(screen.getByTestId("live-listening")).toHaveTextContent("Writing");
    emit(PASS[1].type, PASS[1].data);
    await waitFor(() => expect(screen.getByTestId("live-listening")).toHaveAttribute("data-state", "listening"));
    expect(screen.getByTestId("live-saved-through")).toHaveTextContent("Saved up to 1:06");
    // Before Start only: no mic check while it records.
    expect(mocks.apiFetch).not.toHaveBeenCalledWith("/api/meeting/mic-check", { method: "POST" });
  });

  it("during: another meeting's pass is not this one's", async () => {
    useDesk.setState({ recording: "recording", liveMeetingId: "m-live" });
    answer({
      "/api/settings/hub": hubWithEngine,
      "/api/state": { active: true, meeting_active: true, id: "m-live", meeting_id: "m-live" },
    });
    await mount("m-live");
    for (const frame of SEGMENTS) emit("segment", frame);
    emit("transcript_pass", { ...(PASS[0].data as Record<string, unknown>), meeting_id: "m-other" });
    expect(screen.getByTestId("live-listening")).toHaveAttribute("data-state", "listening");
  });
});

describe("Live meeting: the phone status bar while it records is one line (W2-LIVE-2)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    useDesk.setState({ recording: "recording", liveMeetingId: "m-live" });
    answer({
      "/api/settings/hub": hubWithEngine,
      "/api/state": { active: true, meeting_active: true, meeting_id: "m-live", title: "Ledger cutover sync" },
    });
  });

  it("drops the title (the title bar has it) and, on the phone, the connected link", async () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: query === "(max-width: 720px)", media: query, onchange: null,
      addEventListener: () => undefined, removeEventListener: () => undefined,
      addListener: () => undefined, removeListener: () => undefined, dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      await mount();
      emit("duration", "12:04");
      const bar = screen.getByTestId("live-statusbar");
      await waitFor(() => expect(within(bar).getByTestId("live-capture-state")).toHaveTextContent(/Recording\s*12:04/));
      const items = [...bar.querySelectorAll(".kit-statusbar-item")].map((item) => item.textContent);
      expect(items).toEqual(["Recording 12:04", "Summaries on Hs201 Meeting Engine"]);
      expect(bar).not.toHaveTextContent("Ledger cutover sync");
    } finally {
      window.matchMedia = original;
    }
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
