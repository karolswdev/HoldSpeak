import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import statusDisabled from "./fixtures/status-disabled.json";
import statusEnabled from "./fixtures/status-enabled.json";
import saveSuccess from "./fixtures/save-success.json";
import transcribeSuccess from "./fixtures/transcribe-success.json";
import transcribeFailed from "./fixtures/transcribe-failed.json";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  captureWindowPng: vi.fn(),
  startFeedbackAudio: vi.fn(),
  canonicalWindowRow: vi.fn(),
  abortHold: vi.fn(),
  beginHold: vi.fn(),
  endHold: vi.fn(),
  holdOwnsFloor: vi.fn(),
  micPhase: vi.fn(),
  openMicRunning: vi.fn(),
  claimAudioFloor: vi.fn(),
  releaseAudioFloor: vi.fn(),
  renewAudioFloor: vi.fn(),
  toWav16kMono: vi.fn(),
}));

vi.mock("../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) =>
    error instanceof Error ? error.message : "Request failed",
}));

vi.mock("../store", () => ({
  useDesk: Object.assign(() => undefined, {
    subscribe: () => () => undefined,
    getState: () => ({
      windowsById: { "window-1": { id: "window-1", title: "Platform" } },
      panelRects: { "window-1": { x: 10, y: 20, width: 500, height: 300 } },
      panelOrder: ["window-1"],
      panelDepth: { "window-1": 7 },
      panelMin: [],
      panelMax: [],
      panelZoom: {},
      drafts: { "window-1": "An unsaved draft" },
    }),
  }),
}));

vi.mock("../../lib/micSession", async () => {
  const actual = await vi.importActual<typeof import("../../lib/micSession")>(
    "../../lib/micSession",
  );
  return {
    ...actual,
    abortHold: mocks.abortHold,
    beginHold: mocks.beginHold,
    endHold: mocks.endHold,
    holdOwnsFloor: mocks.holdOwnsFloor,
    micPhase: mocks.micPhase,
    openMicRunning: mocks.openMicRunning,
  };
});

vi.mock("../../lib/audioFloor", async () => {
  const actual = await vi.importActual<typeof import("../../lib/audioFloor")>(
    "../../lib/audioFloor",
  );
  return {
    ...actual,
    FLOOR_RENEW_MS: 60_000,
    claimAudioFloor: mocks.claimAudioFloor,
    releaseAudioFloor: mocks.releaseAudioFloor,
    renewAudioFloor: mocks.renewAudioFloor,
  };
});

vi.mock("../../lib/speakToFill", async () => {
  const actual = await vi.importActual<typeof import("../../lib/speakToFill")>(
    "../../lib/speakToFill",
  );
  return { ...actual, toWav16kMono: mocks.toWav16kMono };
});

const captureHolder = vi.hoisted(() => ({
  current: undefined as typeof import("./capture") | undefined,
}));
vi.mock("./capture", async () => {
  const actual = await vi.importActual<typeof import("./capture")>("./capture");
  captureHolder.current = actual;
  return {
    ...actual,
    captureWindowPng: (...args: unknown[]) => mocks.captureWindowPng(...args),
    canonicalWindowRow: (...args: unknown[]) =>
      mocks.canonicalWindowRow(...args),
    startFeedbackAudio: (...args: unknown[]) =>
      mocks.startFeedbackAudio(...args),
  };
});

import { UiFeedbackHost } from "./UiFeedbackHost";
import { TALK_STOP_EVENT } from "../components/MicButton";
import {
  hydrateUiFeedback,
  requestUiFeedback,
  resetUiFeedbackRuntimeForTests,
  uiFeedbackState,
} from "./runtime";
import { menuVerbs, offeredHere, verbById } from "../verbRegistry";

const feedbackContext = { selectedRef: null };

function session() {
  return {
    stop: vi.fn(() => ({ wav: new ArrayBuffer(8), durationMs: 240 })),
    cancel: vi.fn(),
    lost: vi.fn(() => false),
    onFloorLost: vi.fn(),
  };
}

function deskFace(onClick = vi.fn()) {
  const view = render(
    <>
      <div id="window-1" data-layer="window" aria-label="Platform">
        <h1 className="desk-window-title">Platform</h1>
        <button type="button" onClick={onClick}>
          Apply draft
        </button>
      </div>
      <UiFeedbackHost />
    </>,
  );
  return {
    ...view,
    action: screen.getByRole("button", { name: "Apply draft" }),
    onClick,
  };
}

async function startPicker() {
  await waitFor(() => expect(uiFeedbackState().enabled).toBe(true));
  act(() => verbById("desk.give-feedback")?.run(feedbackContext));
  await screen.findByText("Select a part");
}

async function selectAction(action: HTMLElement) {
  fireEvent.pointerDown(action, { pointerId: 1, buttons: 1 });
  fireEvent.pointerUp(action, { pointerId: 1 });
  fireEvent.click(action);
  await screen.findByRole("button", { name: "Record" });
}

beforeEach(() => {
  cleanup();
  resetUiFeedbackRuntimeForTests();
  mocks.apiFetch.mockReset().mockResolvedValue(statusEnabled);
  mocks.captureWindowPng.mockReset().mockResolvedValue("PNG_BYTES");
  mocks.canonicalWindowRow
    .mockReset()
    .mockResolvedValue({ id: "window-1", app: "surface" });
  mocks.startFeedbackAudio.mockReset().mockResolvedValue(session());
  mocks.claimAudioFloor.mockReset().mockResolvedValue(undefined);
  mocks.releaseAudioFloor.mockReset().mockResolvedValue(undefined);
  mocks.renewAudioFloor.mockReset().mockResolvedValue(true);
  mocks.toWav16kMono.mockReset().mockReturnValue(new ArrayBuffer(8));
  mocks.abortHold.mockReset();
  mocks.beginHold.mockReset().mockResolvedValue(11);
  mocks.endHold.mockReset().mockReturnValue(null);
  mocks.holdOwnsFloor.mockReset().mockReturnValue(false);
  mocks.micPhase.mockReset().mockReturnValue("closed");
  mocks.openMicRunning.mockReset().mockReturnValue(false);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Window feedback capture", () => {
  it("keeps the flag and the one registry verb", async () => {
    mocks.apiFetch.mockResolvedValueOnce(statusDisabled);
    render(<UiFeedbackHost />);
    await waitFor(() => expect(uiFeedbackState().loading).toBe(false));
    expect(verbById("desk.give-feedback")!.ghost(feedbackContext)).toBeTruthy();
    expect(menuVerbs("help").map((row) => row.id)).toContain(
      "desk.give-feedback",
    );
    expect(menuVerbs("desk").map((row) => row.id)).not.toContain(
      "desk.give-feedback",
    );
    act(() => requestUiFeedback(document.body));
    expect(screen.queryByLabelText("Feedback words")).toBeNull();
  });
  it("selects without activating, freezes the window before capture, and permits typed words without audio", async () => {
    const { action, onClick } = deskFace();
    await startPicker();
    await selectAction(action);
    expect(onClick).not.toHaveBeenCalled();
    expect(mocks.captureWindowPng).toHaveBeenCalledWith(
      action.closest('[data-layer="window"]'),
      expect.any(AbortSignal),
    );
    expect(mocks.startFeedbackAudio).not.toHaveBeenCalled();
    mocks.apiFetch.mockResolvedValueOnce({
      ...saveSuccess,
      transcript_status: "complete",
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Feedback words" }), {
      target: { value: "These buttons touch." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText("Saved.");
    const save = mocks.apiFetch.mock.calls.find(
      (call) => call[0] === "/api/ui-feedback",
    );
    expect(save![1].json).toMatchObject({
      words: "These buttons touch.",
      audio_base64: null,
      screenshot_base64: "PNG_BYTES",
    });
    expect(
      mocks.apiFetch.mock.calls.filter((call) =>
        String(call[0]).includes("transcribe"),
      ),
    ).toHaveLength(0);
    expect(mocks.canonicalWindowRow).not.toHaveBeenCalled();
  });
  it("records on request, stops before Save and posts the same audio bundle and transcript", async () => {
    const recording = session();
    mocks.startFeedbackAudio.mockResolvedValue(recording);
    const { action } = deskFace();
    await startPicker();
    await selectAction(action);
    fireEvent.click(screen.getByRole("button", { name: "Record" }));
    await screen.findByText("Recording");
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    expect(recording.stop).toHaveBeenCalledOnce();
    expect(
      mocks.apiFetch.mock.calls.some((call) => call[0] === "/api/ui-feedback"),
    ).toBe(false);
    mocks.apiFetch
      .mockResolvedValueOnce(saveSuccess)
      .mockResolvedValueOnce(transcribeSuccess);
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText("Saved.");
    expect(
      mocks.apiFetch.mock.calls.some((call) =>
        String(call[0]).endsWith("/transcribe"),
      ),
    ).toBe(true);
  });
  it("retains words, image and identity after a failed Save for an exact retry", async () => {
    const { action } = deskFace();
    await startPicker();
    await selectAction(action);
    fireEvent.change(screen.getByRole("textbox", { name: "Feedback words" }), {
      target: { value: "Keep this draft" },
    });
    mocks.apiFetch
      .mockRejectedValueOnce(new Error("Hub unavailable"))
      .mockResolvedValueOnce({ ...saveSuccess, transcript_status: "complete" });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText("Hub unavailable");
    expect(screen.getByRole("textbox", { name: "Feedback words" })).toHaveValue(
      "Keep this draft",
    );
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText("Saved.");
    const posts = mocks.apiFetch.mock.calls.filter(
      (call) => call[0] === "/api/ui-feedback",
    );
    expect(posts[0][1].json).toEqual(posts[1][1].json);
    expect(mocks.captureWindowPng).toHaveBeenCalledOnce();
  });
  it("adds guide context and resumes on Save or Cancel", async () => {
    const { action } = deskFace();
    await waitFor(() => expect(uiFeedbackState().enabled).toBe(true));
    const mount = document.createElement("div");
    document.body.appendChild(mount);
    const finish = vi.fn();
    const guide = {
      app: "Decisions",
      step: 2,
      of: 3,
      target: "decide",
      words: "Decide records your answer.",
    };
    act(() => requestUiFeedback(action, { guide, mount, onFinish: finish }));
    await screen.findByRole("button", { name: "Record" });
    mocks.apiFetch.mockResolvedValueOnce({
      ...saveSuccess,
      transcript_status: "complete",
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Feedback words" }), {
      target: { value: "The action is cut." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(finish).toHaveBeenCalledWith(true));
    expect(
      mocks.apiFetch.mock.calls.find(
        (call) => call[0] === "/api/ui-feedback",
      )![1].json.context.guide,
    ).toEqual(guide);
    act(() => requestUiFeedback(action, { guide, mount, onFinish: finish }));
    await screen.findByRole("button", { name: "Record" });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(finish).toHaveBeenLastCalledWith(false);
    mount.remove();
  });
  it("ignores a late image after Cancel", async () => {
    let resolve!: (image: string) => void;
    mocks.captureWindowPng.mockReturnValueOnce(
      new Promise<string>((done) => {
        resolve = done;
      }),
    );
    const { action } = deskFace();
    await startPicker();
    fireEvent.pointerDown(action);
    await screen.findByText("Capturing");
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    await act(async () => resolve("LATE_IMAGE"));
    expect(screen.queryByRole("button", { name: "Record" })).toBeNull();
    expect(mocks.startFeedbackAudio).not.toHaveBeenCalled();
  });
  it("redacts typed credentials and retains the full ordinary draft", () => {
    const root = document.createElement("div");
    root.innerHTML =
      '<textarea aria-label="Draft">A full draft</textarea><input aria-label="API key" value="SECRET">';
    document.body.appendChild(root);
    const context = captureHolder.current!.snapshotContext(
      root.querySelector("textarea")!,
      root,
      null,
    );
    expect(JSON.stringify(context)).toContain("A full draft");
    expect(JSON.stringify(context)).not.toContain("SECRET");
    root.remove();
  });
});

it("a guide recording uses the shared local mic without a hub floor call", async () => {
  const { startFeedbackAudio } = captureHolder.current!;
  const session = await startFeedbackAudio(new AbortController().signal, {
    local: true,
  });
  expect(mocks.beginHold).toHaveBeenCalledOnce();
  expect(mocks.claimAudioFloor).not.toHaveBeenCalled();
  session.cancel();
  expect(mocks.abortHold).toHaveBeenCalledWith(11);
  expect(mocks.releaseAudioFloor).not.toHaveBeenCalled();
  expect(mocks.renewAudioFloor).not.toHaveBeenCalled();
});

it("keeps a saved recording after a transcript failure and retries only the transcript", async () => {
  const { action } = deskFace();
  await startPicker();
  await selectAction(action);
  fireEvent.click(screen.getByRole("button", { name: "Record" }));
  await screen.findByText("Recording");
  fireEvent.click(screen.getByRole("button", { name: "Stop" }));
  mocks.apiFetch
    .mockResolvedValueOnce(saveSuccess)
    .mockResolvedValueOnce(transcribeFailed)
    .mockResolvedValueOnce(transcribeSuccess);
  fireEvent.click(screen.getByRole("button", { name: "Save" }));
  await screen.findByRole("button", { name: "Retry transcription" });
  fireEvent.click(screen.getByRole("button", { name: "Retry transcription" }));
  await waitFor(() =>
    expect(
      screen.queryByRole("button", { name: "Retry transcription" }),
    ).toBeNull(),
  );
  expect(
    mocks.apiFetch.mock.calls.filter((call) => call[0] === "/api/ui-feedback"),
  ).toHaveLength(1);
  expect(
    mocks.apiFetch.mock.calls.filter((call) =>
      String(call[0]).endsWith("/transcribe"),
    ),
  ).toHaveLength(2);
  expect(mocks.captureWindowPng).toHaveBeenCalledOnce();
});
