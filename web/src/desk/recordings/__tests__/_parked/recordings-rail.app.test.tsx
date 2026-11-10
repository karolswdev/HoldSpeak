/* Parked: assertions for the retired rail/card face; selection and capture tests remain live. */
/* The Recordings app (T2; RECORDINGS-DESIGN-2026-10-28, canvas
 * docs/internal/betterment/canvases/recordings-2026-10-28.html).
 *
 * The answers are recorded through the real /api/recordings routes
 * (scripts/record_recordings_fixtures.py: fake ffmpeg, a recorded Tailscale
 * Serve answer). Each case drives a press to the rendered outcome: the window
 * in its states (empty, the list, encoding 42 %, ready with both links,
 * failed and Retry), the dock tile with a fake getDisplayMedia and
 * MediaRecorder (start, a chunk, stop), the menu-bar lamp, and another view's
 * recording from the `recording_state` frame. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { frameEncoding } from "../../__fixtures__/frame.encoding";
import { frameReady } from "../../__fixtures__/frame.ready";
import { frameRemoteStarted } from "../../__fixtures__/frame.remoteStarted";
import { recordingFailed } from "../../__fixtures__/recording.failed";
import { recordingLive } from "../../__fixtures__/recording.recording";
import { recordingReady } from "../../__fixtures__/recording.ready";
import { recordingStopped } from "../../__fixtures__/recording.stopped";
import { recordingsEmpty } from "../../__fixtures__/recordings.empty";
import { recordingsList } from "../../__fixtures__/recordings.list";

type Frame = { type: string; data: unknown };
type Answer = unknown | ((init?: { method?: string; json?: unknown; body?: unknown }) => unknown);

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
  openSurfaceOr: vi.fn(),
  openRef: vi.fn(),
}));

vi.mock("../../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useOptionalRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../shell")>()),
  openSurfaceOr: mocks.openSurfaceOr,
}));
vi.mock("../../../openObject", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../openObject")>()),
  openRef: mocks.openRef,
}));

import { ApiError } from "../../../../lib/api";
import { DESK_APPLICATIONS, goRows } from "../../../applications";
import { RecordingsCore } from "../../_parked/RecordingsWindow_20261110";
import { ScreenRecordLamp, ScreenRecordTile } from "../../ScreenRecord";
import { RecordingsSettings } from "../../RecordingsSettings";
import { appWalk } from "../../../walk/appWalks";
import { CHUNK_MS, VIEW_ID, captureState, resetCaptureForTests } from "../../capture";

function subscribe(type: string, listener: (frame: Frame) => void) {
  const set = mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
  set.add(listener);
  mocks.listeners.set(type, set);
  return () => set.delete(listener);
}
function emit(type: string, data: unknown) {
  act(() => {
    for (const listener of [...(mocks.listeners.get(type) ?? [])]) listener({ type, data });
  });
}

const clone = <T,>(value: T): T => structuredClone(value);
let calls: string[];
let bodies: unknown[];

function hub(table: Record<string, Answer>) {
  mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: unknown; body?: unknown }) => {
    const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
    calls.push(init?.json !== undefined ? `${key} ${JSON.stringify(init.json)}` : key);
    if (init?.body !== undefined) bodies.push(init.body);
    if (!(key in table)) throw new ApiError(404, "Not Found", { detail: "Not Found" });
    const answer = table[key];
    return clone(typeof answer === "function" ? (answer as (i?: typeof init) => unknown)(init) : answer);
  });
}

/* ── a fake screen and recorder (jsdom has neither) ─────────────────── */

class FakeTrack {
  kind: string;
  stopped = false;
  private ended: Array<() => void> = [];
  constructor(kind: string) { this.kind = kind; }
  stop() { this.stopped = true; }
  getSettings() { return { width: 2880, height: 1800 }; }
  addEventListener(name: string, fn: () => void) { if (name === "ended") this.ended.push(fn); }
  end() { this.ended.forEach((fn) => fn()); }
}
class FakeStream {
  tracks: FakeTrack[];
  constructor(tracks: FakeTrack[] = []) { this.tracks = tracks; }
  getTracks() { return this.tracks; }
  getVideoTracks() { return this.tracks.filter((t) => t.kind === "video"); }
  getAudioTracks() { return this.tracks.filter((t) => t.kind === "audio"); }
}
class FakeRecorder {
  static last: FakeRecorder | null = null;
  static isTypeSupported(type: string) { return type === "video/webm;codecs=vp9"; }
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  options: { mimeType?: string; videoBitsPerSecond?: number };
  timeslice = 0;
  constructor(_stream: unknown, options: { mimeType?: string; videoBitsPerSecond?: number }) {
    this.options = options;
    FakeRecorder.last = this;
  }
  start(timeslice: number) { this.timeslice = timeslice; }
  chunk(text: string) { this.ondataavailable?.({ data: new Blob([text], { type: "video/webm" }) }); }
  stop() { this.chunk("last"); this.onstop?.(); }
}

let screenTrack: FakeTrack;
const getDisplayMedia = vi.fn();

beforeEach(() => {
  calls = [];
  bodies = [];
  mocks.listeners.clear();
  mocks.apiFetch.mockReset();
  mocks.openSurfaceOr.mockReset();
  mocks.openRef.mockReset();
  resetCaptureForTests();
  screenTrack = new FakeTrack("video");
  getDisplayMedia.mockReset();
  getDisplayMedia.mockImplementation(async () => new FakeStream([screenTrack]));
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getDisplayMedia },
  });
  vi.stubGlobal("MediaRecorder", FakeRecorder);
  vi.stubGlobal("MediaStream", FakeStream);
  FakeRecorder.last = null;
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const status = () => screen.getByTestId("recordings-status").textContent ?? "";

describe("the window", () => {
  it("empty: one true line and Record screen as the primary", async () => {
    hub({ "GET /api/recordings": recordingsEmpty });
    render(<RecordingsCore />);
    expect(await screen.findByText("No recordings yet")).toBeTruthy();
    fireEvent.click(screen.getByTestId("recordings-capture-open"));
    const record = screen.getByTestId("recordings-record");
    expect(record.textContent).toContain("Record screen");
    expect(record.className).toContain("primary");
  });

  it("the list: a dense row per recording, its length, size and state as a dot and a word", async () => {
    hub({ "GET /api/recordings": recordingsList });
    render(<RecordingsCore />);
    const rows = await screen.findAllByTestId("recordings-row");
    expect(rows).toHaveLength(2);
    const states = rows.map((row) => within(row).getByTestId("recordings-state").textContent);
    expect(states).toEqual(expect.arrayContaining([expect.stringContaining("Ready"), expect.stringContaining("Failed")]));
    expect(status().trim()).toMatch(/^2 recordings/);
    expect(status()).toMatch(/\d+ (B|KB|MB) used/);
  });

  it("encoding 42 %: the frame moves the row in place", async () => {
    const stopped = { ...recordingsList, recordings: [clone(recordingStopped)] };
    hub({ "GET /api/recordings": stopped });
    render(<RecordingsCore />);
    const row = await screen.findByTestId("recordings-row");
    expect(within(row).getByTestId("recordings-state").textContent).toContain("Encoding 0 %");
    emit("recording_state", frameEncoding);
    await waitFor(() => expect(within(screen.getByTestId("recordings-row")).getByTestId("recordings-state").textContent).toContain("Encoding 42 %"));
    emit("recording_state", frameReady);
    await waitFor(() => expect(within(screen.getByTestId("recordings-row")).getByTestId("recordings-state").textContent).toContain("Ready"));
  });

  it("ready: the video plays from the hub, both links show (Tailscale first) with Copy, and Stop sharing hides them", async () => {
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    const unshared = { ...clone(recordingReady), shared: false, links: { tailnet: null, local: null } };
    hub({
      "GET /api/recordings": { ...recordingsList, recordings: [clone(recordingReady)] },
      [`POST /api/recordings/${recordingReady.id}/unshare`]: unshared,
    });
    render(<RecordingsCore />);
    fireEvent.click(within(await screen.findByTestId("recordings-row")).getByRole("option"));
    const video = await screen.findByTestId("recordings-video");
    expect(video.getAttribute("src")).toContain(`/api/recordings/${recordingReady.id}/video`);
    const links = screen.getByTestId("recordings-links");
    const shown = [...links.querySelectorAll(".recordings-link-url")].map((a) => a.textContent);
    expect(shown).toEqual([recordingReady.links.tailnet, recordingReady.links.local]);
    expect(shown[0]).toMatch(/^https:\/\/karols-macbook-pro\.tailad9943\.ts\.net\/r\//);
    expect(shown[1]).toMatch(/^http:\/\/127\.0\.0\.1:8765\/r\//);
    fireEvent.click(screen.getByTestId("recordings-link-tailnet-copy"));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(recordingReady.links.tailnet));
    expect(await screen.findByText("Copied")).toBeTruthy();
    fireEvent.click(screen.getByTestId("recordings-open-note"));
    expect(mocks.openRef).toHaveBeenCalledWith("note:n-rec-1");
    fireEvent.click(screen.getByTestId("recordings-share"));
    await waitFor(() => expect(screen.queryByTestId("recordings-links")).toBeNull());
    expect(screen.getByTestId("recordings-share").textContent).toContain("Share");
  });

  it("failed: the row says why and Retry encodes again", async () => {
    hub({
      "GET /api/recordings": { ...recordingsList, recordings: [clone(recordingFailed)] },
      [`POST /api/recordings/${recordingFailed.id}/retry`]: { ...clone(recordingFailed), state: "encoding", progress: 0, error: "" },
    });
    render(<RecordingsCore />);
    fireEvent.click(within(await screen.findByTestId("recordings-row")).getByRole("option"));
    expect(screen.getByTestId("recordings-wait").textContent).toContain("ffmpeg stopped");
    fireEvent.click(screen.getByTestId("recordings-retry"));
    await waitFor(() => expect(screen.getByTestId("recordings-wait").textContent).toContain("Encoding 0 %"));
    expect(calls).toContain(`POST /api/recordings/${recordingFailed.id}/retry {}`);
  });
});

describe("native Recordings presses", () => {
  it("picks a recording into the Mast, and removes it only after confirmation", async () => {
    hub({ "GET /api/recordings": recordingsList,
      [`POST /api/recordings/${recordingReady.id}/park`]: { id: recordingReady.id, parked: true } });
    render(<RecordingsCore />);
    const row = (await screen.findAllByTestId("recordings-row")).find((r) => r.dataset.recording === recordingReady.id)!;
    fireEvent.click(within(row).getByRole("option"));
    expect(screen.getByTestId("recordings-mast").textContent).toContain(recordingReady.title.replace(/^Recording · /, ""));
    expect(screen.getByTestId("recordings-rail")).toHaveAttribute("data-pane-open", "true");
    fireEvent.click(screen.getByTestId("recordings-park"));
    expect(calls.some((call) => call.includes("/park"))).toBe(false);
    fireEvent.click(screen.getByTestId("recordings-park"));
    await waitFor(() => expect(screen.queryByTestId("recordings-video")).toBeNull());
    expect(screen.getByTestId("recordings-status").textContent).toContain("Recording moved to the parked folder");
    expect(screen.queryAllByTestId("recordings-row").some((r) => r.dataset.recording === recordingReady.id)).toBe(false);
  });

  it("a failed remove keeps the selected recording and allows retry", async () => {
    hub({ "GET /api/recordings": { ...recordingsList, recordings: [recordingReady] },
      [`POST /api/recordings/${recordingReady.id}/park`]: () => { throw new Error("Disk is busy"); } });
    render(<RecordingsCore />);
    await screen.findByTestId("recordings-video");
    fireEvent.click(screen.getByTestId("recordings-park"));
    fireEvent.click(screen.getByTestId("recordings-park"));
    await waitFor(() => expect(status()).toContain("Disk is busy"));
    expect(screen.getByTestId("recordings-video")).toBeTruthy();
    expect(screen.getByTestId("recordings-park")).not.toBeDisabled();
  });

  it("a view without screen capture shows the reason instead of a Start verb", async () => {
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: {} });
    hub({ "GET /api/recordings": recordingsEmpty }); render(<RecordingsCore />);
    await screen.findByText("No recordings yet");
    fireEvent.click(screen.getByTestId("recordings-capture-open"));
    expect(screen.getByText("Record from your computer")).toBeTruthy();
    expect(screen.queryByTestId("recordings-record")).toBeNull();
  });

  it("a late list answer cannot replace a newer recording frame", async () => {
    let finish!: (value: unknown) => void;
    mocks.apiFetch.mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
    render(<RecordingsCore />);
    emit("recording_state", frameReady);
    await act(async () => { finish({ ...recordingsList, recordings: [recordingStopped] }); });
    expect(await screen.findByTestId("recordings-video")).toBeTruthy();
    expect(screen.getByTestId("recordings-mast")).toHaveTextContent("Ready");
  });

  it("a missing recordings route is a failure, and Retry reads again", async () => {
    hub({}); render(<RecordingsCore />);
    fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
    await waitFor(() => expect(calls.filter((call) => call === "GET /api/recordings")).toHaveLength(2));
    expect(screen.queryByText("No recordings yet")).toBeNull();
  });

  it("carries its walk and shares the app's storage read", async () => {
    hub({ "GET /api/recordings": recordingsList });
    render(<RecordingsCore />);
    await screen.findAllByTestId("recordings-row");
    expect(appWalk("open-recordings")?.open.app).toBe("surface-recordings");
    fireEvent.click(within(screen.getByTestId("recordings-storage")).getByRole("button"));
    expect(await screen.findByTestId("settings-recordings-usage")).toHaveTextContent("30 days");
    expect(calls.filter((call) => call === "GET /api/recordings")).toHaveLength(1);
  });
});

