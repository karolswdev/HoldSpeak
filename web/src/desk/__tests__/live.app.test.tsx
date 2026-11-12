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
import liveActions from "../../test/wire/live.actions.wire.json";
import nativeState from "../../test/wire/live.native-state.wire.json";
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
import { MastSlotContext, type MastDeclaration } from "../surface/patterns/Mast";
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
const ACTIONS = liveActions.wire;
const SEGMENTS = (segmentsWire as { wire: Record<string, unknown>[] }).wire;
const MIC_HEARING = (micHearingWire as { wire: Record<string, unknown> }).wire;
const MIC_REFUSED = (micRefusedWire as { wire: Record<string, unknown> }).wire;
const PASS = (passWire as { wire: { type: string; data: unknown }[] }).wire;
const LEVELS = (levelWire as { wire: { type: string; data: unknown }[] }).wire;

function answer(gets: Gets) {
  mocks.apiFetch.mockImplementation(async (path: string, options?: { method?: string; json?: Record<string, unknown> }) => {
    if (path === "/api/meeting/start") return ACTIONS.start;
    if (path === "/api/meeting/stop") return ACTIONS.stop;
    if (path === "/api/bookmark") return ACTIONS.bookmarks["The freeze date"];
    if (path === "/api/meeting" && options?.method === "PATCH") return ACTIONS.updates[String(options.json?.title) as keyof typeof ACTIONS.updates] ?? ACTIONS.updates["Ledger cutover sync"];
    const got = recordedGet(gets, path);
    return got ?? {};
  });
}

function WindowHost({ children }: { children: ReactNode }) {
  const [wings, setWings] = useState<ReactNode>(null);
  const [mast, setMast] = useState<MastDeclaration | null>(null);
  return (
    <MastSlotContext.Provider value={setMast}><div data-testid="window-mast">{mast?.line}{mast?.figures?.map(figure => <span key={figure.label}>{figure.value}</span>)}</div><WingSlotContext.Provider value={setWings}>
      <div data-testid="window-head">{wings}</div>
      {children}
    </WingSlotContext.Provider></MastSlotContext.Provider>
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

  it("reopens the recorded live transcript and caught task in one body", async () => {
    answer({ "/api/state": nativeState.wire, "/api/settings/hub": hubWithEngine });
    await mount("m-caught");
    expect(await screen.findByTestId("live-transcript")).toHaveTextContent(nativeState.wire.segments[0].text);
    expect(screen.getByTestId("live-caught")).toHaveTextContent(nativeState.wire.intel.action_items[0].task);
    expect(screen.getByTestId("live-caught")).toHaveTextContent("Priya");
    expect(within(screen.getByTestId("live-toolbar")).getByRole("button", { name: "Stop meeting" })).toBeInTheDocument();
  });

  it("keeps the transcript in the shared bounded well and the figures in the inspector", async () => {
    answer({ "/api/state": nativeState.wire, "/api/settings/hub": hubWithEngine });
    await mount("m-caught");
    expect(screen.getByTestId("live-transcript")).toHaveClass("surface-transcript-well");
    expect(screen.getByTestId("live-transcript")).toHaveAttribute("data-feedback-redact", "true");
    expect(document.querySelector(".surface-mast, .live-ready-plate, .live-native-body")).toBeNull();
    expect(screen.getByTestId("live-caught").querySelector(".surface-inspector-figures")).not.toBeNull();
    expect(screen.getByRole("combobox", { name: "Microphone" })).toBeEnabled();
    expect(within(screen.getByTestId("live-caught")).queryByRole("columnheader", { name: "At" })).toBeNull();
    fireEvent.click(within(screen.getByTestId("live-caught")).getByRole("button", { name: "Done" }));
    expect(screen.queryByTestId("live-caught")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Caught so far" }));
    expect(screen.getByTestId("live-caught")).toBeInTheDocument();
  });

  it("keeps the Stop snapshot and reads only its saved meeting after another recording starts", async () => {
    answer({
      "/api/state": { ...ACTIONS.state, segments: ACTIONS.state.segments.slice(0, -1) },
      "/api/settings/hub": hubWithEngine,
      "/api/meetings/m-caught?include_parked=true": ACTIONS.saved,
    });
    await mount("m-caught");
    emit("duration", nativeState.wire.formatted_duration);
    fireEvent.click(screen.getByRole("button", { name: "Stop meeting" }));
    const last = ACTIONS.stop.meeting.segments.at(-1)!;
    await waitFor(() => expect(screen.getByTestId("live-transcript")).toHaveTextContent(last.text));
    expect(screen.getByTestId("live-statusbar")).toHaveTextContent(ACTIONS.stop.meeting.formatted_duration);
    emit("meeting_started", ACTIONS.next_start.meeting);
    emit("segment", ACTIONS.next_state.segments[0]);
    emit("duration", ACTIONS.next_state.formatted_duration);
    expect(screen.getByTestId("live-transcript")).not.toHaveTextContent(ACTIONS.next_state.segments[0].text);
    expect(screen.getByTestId("live-statusbar")).toHaveTextContent("Stopped");
    emit("desk_changed", ACTIONS.changed);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/meetings/m-caught?include_parked=true"));
    expect(screen.getByTestId("live-transcript")).toHaveTextContent(last.text);
  });

  it.each([
    ["Edit details", "Title", "Save"],
    ["Name this moment", "Name this moment", "Bookmark"],
  ])("retains an open %s draft when capture stops", async (verb, label, completion) => {
    answer({ "/api/state": ACTIONS.state, "/api/settings/hub": hubWithEngine });
    await mount("m-caught");
    fireEvent.click(screen.getByRole("button", { name: verb }));
    const field = screen.getByRole("textbox", { name: label });
    fireEvent.change(field, { target: { value: "Keep this draft" } });
    emit("stopped", ACTIONS.stop);
    expect(field).toHaveValue("Keep this draft");
    expect(screen.getByRole("button", { name: completion })).toBeDisabled();
  });

  it("keeps a moment name after refusal and closes only after retry succeeds", async () => {
    answer({ "/api/state": nativeState.wire, "/api/settings/hub": hubWithEngine });
    const read = mocks.apiFetch.getMockImplementation()!;
    let refused = true;
    mocks.apiFetch.mockImplementation((path, ...args) => {
      if (path === "/api/bookmark" && refused) return Promise.reject(new Error("Moment not saved"));
      return read(path, ...args);
    });
    await mount("m-caught");
    fireEvent.click(screen.getByRole("button", { name: "Name this moment" }));
    const field = screen.getByRole("textbox", { name: "Name this moment" });
    fireEvent.change(field, { target: { value: "The freeze date" } });
    fireEvent.click(screen.getByRole("button", { name: "Bookmark" }));
    await screen.findByText("Moment not saved");
    expect(field).toHaveValue("The freeze date");
    refused = false;
    fireEvent.click(screen.getByRole("button", { name: "Bookmark" }));
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Name this moment" })).toBeNull());
  });

  it("keeps a newer details edit when an older save finishes", async () => {
    answer({ "/api/state": nativeState.wire, "/api/settings/hub": hubWithEngine });
    const read = mocks.apiFetch.getMockImplementation()!;
    let saved!: (answer: unknown) => void;
    mocks.apiFetch.mockImplementation((path, ...args) => path === "/api/meeting" ? new Promise(resolve => { saved = resolve; }) : read(path, ...args));
    await mount("m-caught");
    fireEvent.click(screen.getByRole("button", { name: "Edit details" }));
    const field = screen.getByRole("textbox", { name: "Title" });
    fireEvent.change(field, { target: { value: "First name" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    fireEvent.change(field, { target: { value: "Newer name" } });
    await act(async () => saved(ACTIONS.updates["First name"]));
    expect(field).toHaveValue("Newer name");
    expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
  });

  it("shows the running summary and its strip meter from the producer state", async () => {
    answer({ "/api/state": nativeState.wire, "/api/settings/hub": hubNoEngine });
    await mount("m-caught");
    emit("intel_status", { state: "running", meeting_id: "m-caught" });
    expect(screen.getByTestId("live-summary-engine")).toHaveTextContent("Summary running");
    expect(within(screen.getByTestId("live-statusbar")).getByRole("img", { name: "Summary running" })).toBeInTheDocument();
  });

  it("draws each recorded segment frame as a line with its time mark and its speaker once per run", async () => {
    await mount("m-live");
    for (const frame of SEGMENTS) emit("segment", frame);

    const lines = await screen.findAllByTestId("live-transcript-line");
    expect(lines).toHaveLength(4);
    const marks = lines.map((line) => line.querySelector("time")?.textContent);
    expect(marks).toEqual(["0:04", "0:19", "0:41", "1:02"]);
    // The speaker heads a run: Priya's second line carries no name.
    const who = lines.map((line) => line.querySelector(".transcript-speaker")?.textContent ?? "");
    expect(who).toEqual(["Me", "Priya", "Priya", "Me"]);
    expect(lines[1]).toHaveTextContent("It holds if the backup job moves to 22:00.");
    // The bookmarked frame wears the mark; the others do not.
    expect(lines.map((line) => line.hasAttribute("data-mark"))).toEqual([false, false, false, true]);
    // A document, not a counted stream: no count head, no "segments".
    expect(document.querySelector(".surface-stream-head")).toBeNull();
    expect(document.body.textContent ?? "").not.toMatch(/segments?\b/i);
    expect(screen.getByTestId("live-listening")).toHaveTextContent("Listening");
  });

  it("says the live state once in the status bar: Recording, the clock, the summary engine by name", async () => {
    await mount("m-live");
    emit("duration", "12:04");
    const bar = screen.getByTestId("live-statusbar");
    await waitFor(() => expect(within(bar).getByTestId("live-capture-state")).toHaveTextContent("Recording"));
    expect(within(bar).getByTestId("live-summary-engine")).toHaveTextContent("Summaries on Hs201 Meeting Engine");
    // The same hub counter fills the Mast and the strip (the compact Mast yields its figure).
    expect(bar).toHaveTextContent("12:04");
    expect(screen.getByTestId("window-mast")).toHaveTextContent("12:04");
    // No host or scope chip in the status bar (UX-CANON A.9 as amended).
    expect(bar.querySelector(".egress-chip, [data-egress]")).toBeNull();
  });

  it("keeps Stop as the danger verb and Bookmark and Settings in the toolbar; no gear wing", async () => {
    await mount("m-live");
    const toolbar = screen.getByTestId("live-toolbar");
    const stop = within(screen.getByTestId("live-toolbar")).getByRole("button", { name: "Stop meeting" });
    expect(stop.className).toContain("btn--danger");
    expect(within(toolbar).getByRole("button", { name: "Name this moment" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Configure meeting" })).toBeNull();
    expect(screen.getByTestId("window-head")).toBeEmptyDOMElement();
    // The steps band is the before face; while it records the transcript leads.
    expect(screen.queryByTestId("live-steps")).toBeNull();

    fireEvent.click(within(screen.getByTestId("live-toolbar")).getByRole("button", { name: "Settings" }));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "meetings");
  });

  it("names a bookmark from the toolbar and sends it to the hub", async () => {
    await mount("m-live");
    fireEvent.click(within(screen.getByTestId("live-toolbar")).getByRole("button", { name: "Name this moment" }));
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
    const plate = within(sheet).getByTestId("live-ready-mic");
    await waitFor(() => expect(plate).toHaveTextContent("Hearing"));
    expect(within(plate).getByRole("meter", { name: "Microphone level" })).toHaveAttribute("aria-valuenow", String(MIC_HEARING.level));
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/meeting/mic-check", { method: "POST" });
    expect(screen.getByRole("button", { name: "Start meeting" })).toBeInTheDocument();
    expect(screen.getByTestId("live-summary-engine")).toHaveTextContent("No engine for summaries");
    expect(screen.getByTestId("live-capture-state")).toHaveTextContent("Speech not set up");
    expect(screen.getByRole("button", { name: "Set up speech · 144 MB" })).toBeInTheDocument();
    expect(screen.queryByText("It will hear")).toBeNull();
    expect(screen.queryByTestId("live-steps")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Settings" }));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "meetings");
  });

  it("keeps the speech row while its first read is pending, then fills that row with setup", async () => {
    answer({
      "/api/settings/hub": hubNoEngine,
      "/api/settings": recorded.calendar.none.gets["/api/settings"],
      "/api/meeting/mic-check": MIC_HEARING,
    });
    const base = mocks.apiFetch.getMockImplementation()!;
    let release!: (value: unknown) => void;
    const reading = new Promise((resolve) => { release = resolve; });
    mocks.apiFetch.mockImplementation((path, ...args) => path === "/api/setup/local-ai" ? reading : base(path, ...args));
    await mount();
    const row = screen.getByTestId("live-ready-transcript");
    expect(row).toHaveAttribute("aria-busy", "true");
    expect(row).toHaveTextContent("Reading speech…");
    await act(async () => { release((localAiCold as { wire: unknown }).wire); });
    expect(screen.getByTestId("live-ready-transcript")).toBe(row);
    expect(row).not.toHaveAttribute("aria-busy");
    expect(within(row).getByRole("button", { name: "Set up speech · 144 MB" })).toBeEnabled();
  });

  it("a ready meeting has one start plate and no settings form", async () => {
    answer({
      "/api/settings/hub": hubWithEngine,
      "/api/settings": recorded.calendar.none.gets["/api/settings"],
      "/api/setup/local-ai": (meetingsHubReady as Record<string, unknown>)["/api/setup/local-ai"],
      "/api/meeting/mic-check": MIC_HEARING,
    });
    await mount();
    await screen.findByTestId("live-ready-mic");
    expect(within(screen.getByTestId("live-toolbar")).getByRole("button", { name: "Start meeting" })).toBeEnabled();
    expect(screen.queryByText("Your next meeting")).toBeNull();
    expect(screen.getByRole("combobox", { name: "Microphone" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Set up speech/ })).toBeNull();
    expect(screen.queryByTestId("live-ready-summary")).toBeNull();
  });

  it("sends the name he typed before Start to the live meeting", async () => {
    answer({ "/api/settings/hub": hubWithEngine, "/api/settings": recorded.calendar.none.gets["/api/settings"] });
    await mount();
    fireEvent.change(screen.getByRole("textbox", { name: "Meeting name" }), { target: { value: "Ledger cutover sync" } });
    fireEvent.click(screen.getByRole("button", { name: "Start meeting" }));
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
    fireEvent.click(within(row).getByRole("button", { name: "Retry" }));
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
      await waitFor(() => expect(within(bar).getByTestId("live-capture-state")).toHaveTextContent("Recording"));
      expect(screen.getByTestId("live-capture-state")).toHaveTextContent("Recording 12:04");
      expect(screen.getByTestId("live-summary-engine")).toHaveTextContent("Summaries on Hs201 Meeting Engine");
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
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/plugin-jobs/summary"));
    expect(screen.queryByTestId("settings-live-jobs")).toBeNull();
    expect(await screen.findByText("None attached")).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toMatch(/\b0\b/);
    expect(screen.queryByRole("button", { name: "Process pending" })).toBeNull();

    expect(screen.queryByRole("textbox", {name: "Preview route"})).toBeNull();
    expect(screen.queryByRole("combobox", {name: "Routing profile"})).toBeNull();
    expect(mocks.apiFetch.mock.calls.some(([path]) => String(path).startsWith("/api/intents/"))).toBe(false);
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
