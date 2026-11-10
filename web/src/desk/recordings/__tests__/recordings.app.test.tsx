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
import { frameEncoding } from "../__fixtures__/frame.encoding";
import { frameReady } from "../__fixtures__/frame.ready";
import { frameRemoteStarted } from "../__fixtures__/frame.remoteStarted";
import { recordingFailed } from "../__fixtures__/recording.failed";
import { recordingLive } from "../__fixtures__/recording.recording";
import { recordingReady } from "../__fixtures__/recording.ready";
import { recordingStopped } from "../__fixtures__/recording.stopped";
import { recordingsEmpty } from "../__fixtures__/recordings.empty";
import { recordingsList } from "../__fixtures__/recordings.list";

type Frame = { type: string; data: unknown };
type Answer = unknown | ((init?: { method?: string; json?: unknown; body?: unknown }) => unknown);

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
  openSurfaceOr: vi.fn(),
  openRef: vi.fn(),
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useOptionalRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../shell")>()),
  openSurfaceOr: mocks.openSurfaceOr,
}));
vi.mock("../../openObject", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../openObject")>()),
  openRef: mocks.openRef,
}));

import { ApiError } from "../../../lib/api";
import { DESK_APPLICATIONS, goRows } from "../../applications";
import { RecordingsCore } from "../RecordingsWindow";
import { ScreenRecordLamp, ScreenRecordTile } from "../ScreenRecord";
import { RecordingsSettings } from "../RecordingsSettings";
import { appWalk } from "../../walk/appWalks";
import { CHUNK_MS, VIEW_ID, captureState, resetCaptureForTests } from "../capture";

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

describe("the Recordings window is in the manifest, and its frame is registered", () => {
  it("Go ▸ Work ▸ Recordings opens surface-recordings at 1000 x 680", () => {
    const app = DESK_APPLICATIONS.find((entry) => entry.action === "open-recordings");
    expect(app?.windowId).toBe("surface-recordings");
    expect(app?.surface).toMatchObject({ defaultW: 1000, defaultH: 680, sprite: "system:dock-screen-record" });
    expect(goRows("work").some((row) => row.kind === "app" && row.app.action === "open-recordings")).toBe(true);
  });
});

const pick = async (id = recordingReady.id) => {
  const rows = await screen.findAllByTestId("recordings-row");
  const row = rows.find((entry) => entry.dataset.recording === id)!;
  fireEvent.click(row);
  return row;
};
const more = () =>
  fireEvent.click(screen.getByRole("button", { name: "More" }));
const chooseMore = (name: string) => {
  more();
  fireEvent.click(screen.getByRole("menuitem", { name }));
};
const video = () =>
  fireEvent.click(screen.getByRole("tab", { name: "Video" }));

describe("the window selection grammar", () => {
  it("selects in one list, opens the Note with Return, and finds without dispatching", async () => {
    hub({ "GET /api/recordings": recordingsList });
    render(<RecordingsCore />);
    const grid = await screen.findByRole("grid", { name: "Recordings" });
    expect(screen.getByText("Select a recording.")).toBeTruthy();
    expect(within(grid).getByRole("columnheader", { name: "Kept until" })).toBeTruthy();
    const row = await pick();
    expect(row.querySelector("button")).toBeNull();
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(mocks.openRef).not.toHaveBeenCalled();
    expect(screen.getByTestId("recordings-document")).toHaveTextContent(
      new Date(
        (recordingReady.started_ts + 30 * 86400) * 1000,
      ).toLocaleDateString(undefined, {
        day: "numeric",
        month: "short",
        year: "numeric",
      }),
    );
    fireEvent.keyDown(row, { key: "Enter" });
    expect(mocks.openRef).toHaveBeenCalledWith("note:n-rec-1");
    expect(screen.queryByRole("button", {name:"Done"})).toBeNull();
    expect(row).toHaveAttribute("aria-selected", "true");
    fireEvent.change(
      screen.getByRole("textbox", { name: "Find a recording" }),
      { target: { value: "not-here" } },
    );
    expect(screen.queryAllByTestId("recordings-row")).toHaveLength(0);
    expect(screen.getByText("No recordings found")).toBeTruthy();
    expect(calls.filter((call) => call.startsWith("POST"))).toHaveLength(0);
  });

  it("empty: New recording opens the Voice and Record screen form", async () => {
    hub({ "GET /api/recordings": recordingsEmpty });
    render(<RecordingsCore />);
    expect(await screen.findByText("No recordings yet")).toBeTruthy();
    fireEvent.click(screen.getByTestId("recordings-capture-open"));
    expect(screen.getByRole("checkbox", { name: "Voice" })).toBeTruthy();
    expect(screen.getByTestId("recordings-record")).toHaveTextContent(
      "Record screen",
    );
    expect(
      screen.getByRole("button", { name: "Cancel" }),
    ).toBeTruthy();
  });

  it("Stop selects the recording made in this window", async () => {
    hub({
      "GET /api/recordings": recordingsEmpty,
      "POST /api/recordings": recordingLive,
      [`POST /api/recordings/${recordingLive.id}/chunks`]: { id: recordingLive.id, bytes_in: 1, chunks: 1, state: "recording" },
      [`POST /api/recordings/${recordingLive.id}/stop`]: recordingStopped,
    });
    render(<RecordingsCore />);
    await screen.findByText("No recordings yet");
    fireEvent.click(screen.getByTestId("recordings-capture-open"));
    await act(async () => { fireEvent.click(screen.getByTestId("recordings-record")); });
    await waitFor(() => expect(captureState().phase).toBe("recording"));
    emit("recording_state", { reason: "started", recording: recordingLive });
    fireEvent.click(screen.getByTestId("recordings-stop"));
    await waitFor(() => expect(captureState().phase).toBe("idle"));
    emit("recording_state", frameReady);
    expect(screen.getByTestId("recordings-row")).toHaveAttribute("aria-selected", "true");
    video();
    expect(screen.getByTestId("recordings-video")).toBeTruthy();
  });

  it("normal rows are quiet; only failed recordings ask for the owner", async () => {
    hub({ "GET /api/recordings": recordingsList });
    render(<RecordingsCore />);
    const rows = await screen.findAllByTestId("recordings-row");
    expect(
      rows.find((row) => row.dataset.recording === recordingReady.id),
    ).not.toHaveTextContent("Ready");
    expect(
      rows.find((row) => row.dataset.recording === recordingFailed.id),
    ).toHaveTextContent("Failed");
    expect(status()).toContain("2 recordings");
    expect(status()).toContain("1 needs you");
    expect(screen.getByRole("grid").querySelector(".surface-spine")).toBeNull();
  });

  it("encoding frames replace the row, then expose the ready video", async () => {
    hub({
      "GET /api/recordings": {
        ...recordingsList,
        recordings: [recordingStopped],
      },
    });
    render(<RecordingsCore />);
    await pick(recordingStopped.id);
    expect(
      screen.queryByRole("tab", { name: "Video" }),
    ).toBeNull();
    emit("recording_state", frameEncoding);
    expect(screen.getByTestId("recordings-row")).not.toHaveTextContent(
      "Encoding",
    );
    emit("recording_state", frameReady);
    video();
    expect(
      screen.getByTestId("recordings-video").getAttribute("src"),
    ).toContain(`/api/recordings/${recordingReady.id}/video`);
  });

  it("keeps playback, both links and Copy, and hides links after Stop sharing", async () => {
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    const unshared = {
      ...recordingReady,
      shared: false,
      links: { tailnet: null, local: null },
    };
    hub({
      "GET /api/recordings": {
        ...recordingsList,
        recordings: [recordingReady],
      },
      [`POST /api/recordings/${recordingReady.id}/unshare`]: unshared,
    });
    render(<RecordingsCore />);
    await pick();
    video();
    expect(
      screen.getByTestId("recordings-video").getAttribute("poster"),
    ).toContain(`/api/recordings/${recordingReady.id}/poster`);
    fireEvent.click(screen.getByRole("tab", { name: "Links" }));
    expect(screen.getByTestId("recordings-links")).toHaveTextContent(
      recordingReady.links.tailnet!,
    );
    expect(screen.getByTestId("recordings-links")).toHaveTextContent(
      recordingReady.links.local!,
    );
    chooseMore("Copy phone link");
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(recordingReady.links.tailnet),
    );
    expect(status()).toContain("Copied");
    chooseMore("Copy Mac link");
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(recordingReady.links.local),
    );
    fireEvent.click(screen.getByTestId("recordings-share"));
    await waitFor(() =>
      expect(screen.queryByTestId("recordings-links")).toBeNull(),
    );
    expect(screen.getByTestId("recordings-share")).toHaveTextContent("Share");
  });

  it("a failed share keeps the links and retries the same selected object", async () => {
    hub({
      "GET /api/recordings": {
        ...recordingsList,
        recordings: [recordingReady, recordingFailed],
      },
      [`POST /api/recordings/${recordingReady.id}/unshare`]: () => {
        throw new Error("Disk is busy");
      },
    });
    render(<RecordingsCore />);
    await pick();
    fireEvent.click(screen.getByRole("tab", { name: "Links" }));
    fireEvent.click(screen.getByTestId("recordings-share"));
    await waitFor(() => expect(status()).toContain("Disk is busy"));
    const required = [...screen.getByTestId("recordings-status").querySelectorAll("[data-required]")].map(part => part.textContent);
    expect(required.some(text => text?.includes("needs you"))).toBe(true);
    expect(required.some(text => text?.includes("Disk is busy"))).toBe(true);
    expect(screen.getByTestId("recordings-links")).toBeTruthy();
    expect(screen.getByTestId("recordings-share")).not.toBeDisabled();
    fireEvent.click(screen.getByTestId("recordings-share"));
    await waitFor(() =>
      expect(calls.filter((call) => call.includes("/unshare"))).toHaveLength(2),
    );
  });

  it("failed: the selected facts say why and Retry keeps the row", async () => {
    hub({
      "GET /api/recordings": {
        ...recordingsList,
        recordings: [recordingFailed],
      },
      [`POST /api/recordings/${recordingFailed.id}/retry`]: {
        ...recordingFailed,
        state: "encoding",
        progress: 0,
        error: "",
      },
    });
    render(<RecordingsCore />);
    await pick(recordingFailed.id);
    expect(screen.getByTestId("recordings-wait")).toHaveTextContent(
      "ffmpeg stopped",
    );
    fireEvent.click(screen.getByTestId("recordings-retry"));
    await waitFor(() =>
      expect(screen.queryByTestId("recordings-wait")).toBeNull(),
    );
    expect(calls).toContain(
      `POST /api/recordings/${recordingFailed.id}/retry {}`,
    );
    expect(screen.getByTestId("recordings-row")).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("Delete asks in the window, Cancel preserves the object, Remove parks only after confirmation", async () => {
    hub({
      "GET /api/recordings": recordingsList,
      [`POST /api/recordings/${recordingReady.id}/park`]: {
        id: recordingReady.id,
        parked: true,
      },
    });
    render(<RecordingsCore />);
    const row = await pick();
    fireEvent.keyDown(row, { key: "Delete" });
    expect(
      screen.getByRole("region", { name: "Remove recording?" }),
    ).toBeTruthy();
    expect(calls.some((call) => call.includes("/park"))).toBe(false);
    fireEvent.click(
      screen.getByRole("button", { name: "Cancel" }),
    );
    expect(screen.getAllByTestId("recordings-row")).toHaveLength(2);
    fireEvent.click(screen.getByTestId("recordings-park"));
    fireEvent.click(screen.getByTestId("recordings-remove-confirm"));
    await waitFor(() =>
      expect(status()).toContain("Recording moved to the parked folder"),
    );
    expect(
      screen
        .queryAllByTestId("recordings-row")
        .some((entry) => entry.dataset.recording === recordingReady.id),
    ).toBe(false);
  });

  it("failed removal keeps the question and selection for retry", async () => {
    hub({
      "GET /api/recordings": {
        ...recordingsList,
        recordings: [recordingReady],
      },
      [`POST /api/recordings/${recordingReady.id}/park`]: () => {
        throw new Error("Disk is busy");
      },
    });
    render(<RecordingsCore />);
    await pick();
    fireEvent.click(screen.getByTestId("recordings-park"));
    fireEvent.click(screen.getByTestId("recordings-remove-confirm"));
    await waitFor(() => expect(status()).toContain("Disk is busy"));
    expect(screen.getByTestId("recordings-row")).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByTestId("recordings-remove-confirm")).not.toBeDisabled();
  });

  it("a completed remove keeps a newer selection", async () => {
    hub({ "GET /api/recordings": recordingsList });
    render(<RecordingsCore />);
    await pick();
    let finish!: (answer: unknown) => void;
    mocks.apiFetch.mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
    fireEvent.click(screen.getByTestId("recordings-park"));
    fireEvent.click(screen.getByTestId("recordings-remove-confirm"));
    const newer = await pick(recordingFailed.id);
    await act(async () => { finish({ id: recordingReady.id, parked: true }); });
    expect(newer).toHaveAttribute("aria-selected", "true");
    expect(screen.getByTestId("recordings-wait")).toHaveTextContent("ffmpeg stopped");
    expect(screen.queryAllByTestId("recordings-row").some((row) => row.dataset.recording === recordingReady.id)).toBe(false);
  });

  it("a browser without capture keeps the reason in the same window", async () => {
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: {},
    });
    hub({ "GET /api/recordings": recordingsEmpty });
    render(<RecordingsCore />);
    await screen.findByText("No recordings yet");
    fireEvent.click(screen.getByTestId("recordings-capture-open"));
    expect(screen.getByText("Record from your computer")).toBeTruthy();
    expect(screen.queryByTestId("recordings-record")).toBeNull();
  });

  it("a late list cannot replace a newer recording frame", async () => {
    let finish!: (value: unknown) => void;
    mocks.apiFetch.mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    render(<RecordingsCore />);
    emit("recording_state", frameReady);
    await act(async () => {
      finish({ ...recordingsList, recordings: [recordingStopped] });
    });
    await pick();
    video();
    expect(screen.getByTestId("recordings-video")).toBeTruthy();
  });

  it("a missing route is a failure, and Try again reads it again", async () => {
    hub({});
    render(<RecordingsCore />);
    fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
    await waitFor(() =>
      expect(
        calls.filter((call) => call === "GET /api/recordings"),
      ).toHaveLength(2),
    );
    expect(screen.queryByText("No recordings yet")).toBeNull();
  });

  it("carries the walk, reads storage once, and opens the folder through its declared action", async () => {
    hub({
      "GET /api/recordings": recordingsList,
      "POST /api/recordings/folder/open": { opened: true },
    });
    render(<RecordingsCore />);
    await screen.findAllByTestId("recordings-row");
    expect(appWalk("open-recordings")?.open.app).toBe("surface-recordings");
    chooseMore("Storage");
    expect(screen.getByTestId("settings-recordings-usage")).toHaveTextContent(
      "30 days",
    );
    expect(calls.filter((call) => call === "GET /api/recordings")).toHaveLength(
      1,
    );
    chooseMore("Open folder");
    await waitFor(() => expect(status()).toContain("Folder opened"));
  });
});

describe("the dock tile and the lamp", () => {
  it("a press opens the picker, starts the hub's row, posts each chunk, and a second press stops", async () => {
    hub({
      "GET /api/recordings": recordingsEmpty,
      "POST /api/recordings": recordingLive,
      [`POST /api/recordings/${recordingLive.id}/chunks`]: { id: recordingLive.id, bytes_in: 1, chunks: 1, state: "recording" },
      [`POST /api/recordings/${recordingLive.id}/stop`]: recordingStopped,
    });
    render(<><ScreenRecordLamp /><ScreenRecordTile /></>);
    const tile = screen.getByTestId("desk-dock-screen-record");
    expect(tile.getAttribute("aria-label")).toBe("Record screen");
    expect(tile.hasAttribute("data-recording")).toBe(false);
    expect(screen.queryByTestId("desk-screen-lamp")).toBeNull();
    await act(async () => { fireEvent.click(tile); });
    await waitFor(() => expect(captureState().phase).toBe("recording"));
    expect(getDisplayMedia).toHaveBeenCalledWith(expect.objectContaining({
      video: { frameRate: 15 }, audio: false, preferCurrentTab: true, selfBrowserSurface: "include",
    }));
    const start = calls.find((line) => line.startsWith("POST /api/recordings {"));
    expect(JSON.parse(start!.slice("POST /api/recordings ".length))).toMatchObject({ width: 2880, height: 1800, voice: false, view: VIEW_ID });
    const recorder = FakeRecorder.last!;
    expect(recorder.timeslice).toBe(CHUNK_MS);
    expect(recorder.options).toEqual({ mimeType: "video/webm;codecs=vp9", videoBitsPerSecond: 2_500_000 });
    expect(screen.getByTestId("desk-dock-screen-record").hasAttribute("data-recording")).toBe(true);
    expect(screen.getByTestId("desk-dock-screen-record").getAttribute("aria-label")).toMatch(/^Stop screen recording, 0:0\d$/);
    expect(screen.getByTestId("desk-screen-lamp").textContent).toMatch(/Recording 0:0\d/);
    await act(async () => { recorder.chunk("one"); });
    await waitFor(() => expect(calls).toContain(`POST /api/recordings/${recordingLive.id}/chunks`));
    expect(bodies[0]).toBeInstanceOf(Blob);
    await act(async () => { fireEvent.click(screen.getByTestId("desk-dock-screen-record")); });
    await waitFor(() => expect(calls).toContain(`POST /api/recordings/${recordingLive.id}/stop {}`));
    expect(calls.filter((line) => line === `POST /api/recordings/${recordingLive.id}/chunks`)).toHaveLength(2);
    await waitFor(() => expect(captureState().phase).toBe("idle"));
    expect(screenTrack.stopped).toBe(true);
    expect(screen.queryByTestId("desk-screen-lamp")).toBeNull();
    expect(screen.getByTestId("desk-dock-screen-record").hasAttribute("data-recording")).toBe(false);
  });

  it("the browser's own Stop sharing ends the recording", async () => {
    hub({
      "GET /api/recordings": recordingsEmpty,
      "POST /api/recordings": recordingLive,
      [`POST /api/recordings/${recordingLive.id}/chunks`]: { id: recordingLive.id, bytes_in: 1, chunks: 1, state: "recording" },
      [`POST /api/recordings/${recordingLive.id}/stop`]: recordingStopped,
    });
    render(<ScreenRecordTile />);
    await act(async () => { fireEvent.click(screen.getByTestId("desk-dock-screen-record")); });
    await waitFor(() => expect(captureState().phase).toBe("recording"));
    await act(async () => { screenTrack.end(); });
    await waitFor(() => expect(calls).toContain(`POST /api/recordings/${recordingLive.id}/stop {}`));
  });

  it("a closed picker changes nothing", async () => {
    getDisplayMedia.mockImplementation(async () => { throw new DOMException("denied", "NotAllowedError"); });
    hub({ "GET /api/recordings": recordingsEmpty });
    render(<ScreenRecordTile />);
    await act(async () => { fireEvent.click(screen.getByTestId("desk-dock-screen-record")); });
    expect(captureState()).toMatchObject({ phase: "idle", error: "" });
    expect(calls.some((line) => line.startsWith("POST"))).toBe(false);
  });

  it("another view's recording lights the lamp and the tile, and Stop here stops it there", async () => {
    hub({
      "GET /api/recordings": recordingsEmpty,
      [`POST /api/recordings/${frameRemoteStarted.recording.id}/stop`]: recordingStopped,
    });
    render(<><ScreenRecordLamp /><ScreenRecordTile compact /></>);
    expect(screen.queryByTestId("desk-dock-screen-record")).toBeNull();
    emit("recording_state", frameRemoteStarted);
    expect(screen.getByTestId("desk-screen-lamp").textContent).toContain("Recording on another view");
    expect(screen.getByTestId("desk-dock-screen-record").hasAttribute("data-recording")).toBe(true);
    fireEvent.click(screen.getByTestId("desk-screen-lamp-stop"));
    await waitFor(() => expect(calls).toContain(`POST /api/recordings/${frameRemoteStarted.recording.id}/stop {}`));
    expect(screen.queryByTestId("desk-screen-lamp")).toBeNull();
    expect(getDisplayMedia).not.toHaveBeenCalled();
  });
});

/* PHONE-APNS-HOST (2026-10-30): the lamp read RECORDING ON ANOTHER VIEW: the
 * lamp species' mono caps (gadgets.css .gadget-lamp) beat the sentence-case
 * word. LAMPS-WORDS (2026-10-30): the species itself draws sentence case
 * (lampWords.test.tsx), so recordings.css carries no override. */
import gadgetsCss from "../../surface/gadgets.css?raw";
import { stateWords } from "../../surface/words";

describe("The Record lamp says its word in sentence case", () => {
  it("the menu-bar lamp's text is sentence case and its CSS does not uppercase it", () => {
    hub({ "GET /api/recordings": recordingsEmpty });
    render(<ScreenRecordLamp />);
    emit("recording_state", frameRemoteStarted);
    const lamp = screen.getByTestId("desk-screen-lamp").querySelector(".gadget-lamp");
    expect(lamp?.textContent).toBe("Recording on another view");
    expect(lamp?.textContent).toBe(stateWords(lamp?.textContent ?? ""));
    expect(lamp?.textContent).not.toBe(lamp?.textContent?.toUpperCase());
    const rule = /\n\.gadget-lamp \{([^}]*)\}/.exec(gadgetsCss)?.[1] ?? "";
    expect(rule).not.toBe("");
    expect(rule).not.toMatch(/text-transform:\s*uppercase/);
    expect(rule).toMatch(/letter-spacing:\s*0/);
  });
});

describe("Settings ▸ Desk ▸ Recordings", () => {
  it("says the keep and the space used, and Open folder asks the hub", async () => {
    hub({ "GET /api/recordings": recordingsList, "POST /api/recordings/folder/open": { opened: true } });
    render(<RecordingsSettings />);
    await waitFor(() => expect(screen.getByTestId("settings-recordings-usage").textContent).toMatch(/^30 days · \d+ (B|KB) used$/));
    fireEvent.click(screen.getByTestId("settings-recordings-open-folder"));
    await waitFor(() => expect(calls).toContain("POST /api/recordings/folder/open {}"));
  });
});
