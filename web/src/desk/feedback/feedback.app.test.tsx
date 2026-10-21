import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
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
  const actual = await vi.importActual<typeof import("../../lib/micSession")>("../../lib/micSession");
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
  const actual = await vi.importActual<typeof import("../../lib/audioFloor")>("../../lib/audioFloor");
  return {
    ...actual,
    FLOOR_RENEW_MS: 60_000,
    claimAudioFloor: mocks.claimAudioFloor,
    releaseAudioFloor: mocks.releaseAudioFloor,
    renewAudioFloor: mocks.renewAudioFloor,
  };
});

vi.mock("../../lib/speakToFill", async () => {
  const actual = await vi.importActual<typeof import("../../lib/speakToFill")>("../../lib/speakToFill");
  return { ...actual, toWav16kMono: mocks.toWav16kMono };
});

const captureHolder = vi.hoisted(() => ({ current: undefined as typeof import("./capture") | undefined }));
vi.mock("./capture", async () => {
  const actual = await vi.importActual<typeof import("./capture")>("./capture");
  captureHolder.current = actual;
  return {
    ...actual,
    captureWindowPng: (...args: unknown[]) => mocks.captureWindowPng(...args),
    canonicalWindowRow: (...args: unknown[]) => mocks.canonicalWindowRow(...args),
    startFeedbackAudio: (...args: unknown[]) => mocks.startFeedbackAudio(...args),
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
        <button type="button" onClick={onClick}>Apply draft</button>
      </div>
      <UiFeedbackHost />
    </>,
  );
  return { ...view, action: screen.getByRole("button", { name: "Apply draft" }), onClick };
}

async function startPicker() {
  await waitFor(() => expect(uiFeedbackState().enabled).toBe(true));
  act(() => verbById("desk.give-feedback")?.run(feedbackContext));
  await screen.findByText("Select an element");
}

async function selectAction(action: HTMLElement) {
  fireEvent.pointerDown(action, { pointerId: 1, buttons: 1 });
  fireEvent.pointerUp(action, { pointerId: 1 });
  fireEvent.click(action);
  await screen.findByRole("button", { name: "Stop and save" });
}

beforeEach(() => {
  cleanup();
  resetUiFeedbackRuntimeForTests();
  mocks.apiFetch.mockReset().mockResolvedValue(statusEnabled);
  mocks.captureWindowPng.mockReset().mockResolvedValue("PNG_BYTES");
  mocks.canonicalWindowRow.mockReset().mockResolvedValue({ id: "window-1", app: "surface" });
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

describe("local UI feedback", () => {
  it("marks the registry verb unavailable when disabled and exposes the launcher when enabled", async () => {
    const verb = verbById("desk.give-feedback")!;
    mocks.apiFetch.mockResolvedValueOnce(statusDisabled);
    await hydrateUiFeedback();
    expect(verb.ghost(feedbackContext)).toBe("Feedback is unavailable");
    expect(offeredHere(verb)).toBe(false);
    expect(menuVerbs("desk").map((entry) => entry.id)).toContain("desk.give-feedback");

    resetUiFeedbackRuntimeForTests();
    mocks.apiFetch.mockResolvedValueOnce(statusEnabled);
    render(<UiFeedbackHost />);
    await startPicker();
    expect(screen.getByText("Select an element")).toBeTruthy();
    expect(verb.ghost(feedbackContext)).toBeNull();
    expect(offeredHere(verb)).toBe(true);
  });

  it("freezes full textarea drafts and excludes a plain-text credential field", () => {
    const root = document.createElement("div");
    root.id = "window-1";
    root.dataset.layer = "window";
    root.innerHTML = `
      <h1 class="desk-window-title">Platform</h1>
      <label for="draft">Draft</label><textarea id="draft"></textarea>
      <label for="credential">API token</label><input id="credential" type="password">
      <button id="target" type="button">Apply</button>
    `;
    document.body.appendChild(root);
    const draft = root.querySelector<HTMLTextAreaElement>("#draft")!;
    const credential = root.querySelector<HTMLInputElement>("#credential")!;
    draft.value = "x".repeat(1_201);
    credential.type = "text";
    credential.value = "secret-before-freeze";

    const context = captureHolder.current!.snapshotContext(root.querySelector("#target")!, root, null);
    const draftField = context.fields.find((field) => field.id === "draft");
    expect(draftField?.value).toHaveLength(1_201);
    expect(context.fields.some((field) => field.id === "credential")).toBe(false);
    expect(context.owner.window_text).not.toContain("secret-before-freeze");

    draft.value = "mutated-after-freeze";
    credential.value = "secret-after-freeze";
    expect(draftField?.value).toBe("x".repeat(1_201));
    expect(context.owner.window_text).not.toContain("secret-after-freeze");
    root.remove();
  });

  it("consumes the selected press before activation and starts audio after the PNG", async () => {
    const onClick = vi.fn();
    const view = deskFace(onClick);
    await startPicker();
    await selectAction(view.action);

    expect(onClick).not.toHaveBeenCalled();
    expect(mocks.captureWindowPng.mock.invocationCallOrder[0]).toBeLessThan(
      mocks.startFeedbackAudio.mock.invocationCallOrder[0],
    );
    view.unmount();
  });

  it("captures the frame root passed by a direct launcher, including that root's draft", async () => {
    const view = render(
      <>
        <div id="window-front" data-layer="window" aria-label="Front">
          <textarea aria-label="Front draft" defaultValue="front draft" />
        </div>
        <div id="window-clicked" data-layer="window" aria-label="Clicked">
          <textarea aria-label="Clicked draft" defaultValue="clicked draft" />
        </div>
        <UiFeedbackHost />
      </>,
    );
    await waitFor(() => expect(uiFeedbackState().enabled).toBe(true));
    const clicked = document.getElementById("window-clicked")!;
    act(() => requestUiFeedback(clicked));
    await screen.findByRole("button", { name: "Stop and save" });

    expect(mocks.captureWindowPng).toHaveBeenCalledWith(clicked);
    expect(mocks.canonicalWindowRow).toHaveBeenCalledWith("window-clicked");
    expect(screen.getByText("Clicked")).toBeTruthy();
    act(() => window.dispatchEvent(new Event(TALK_STOP_EVENT)));
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/ui-feedback", expect.anything()));
    const post = mocks.apiFetch.mock.calls.find(([path]) => path === "/api/ui-feedback")?.[1] as { json?: { context?: { owner?: { window_id?: string }; fields?: Array<{ value?: string }> } } };
    expect(post.json?.context?.owner?.window_id).toBe("window-clicked");
    expect(post.json?.context?.fields?.some((field) => field.value === "clicked draft")).toBe(true);
    view.unmount();
  });

  it("stops and saves the feedback recording through the desk Stop event", async () => {
    const recording = session();
    mocks.startFeedbackAudio.mockResolvedValueOnce(recording);
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/ui-feedback/status") return statusEnabled;
      if (path.endsWith("/transcribe")) {
        return transcribeSuccess;
      }
      return saveSuccess;
    });
    const view = deskFace();
    await startPicker();
    await selectAction(view.action);
    act(() => window.dispatchEvent(new Event(TALK_STOP_EVENT)));
    await screen.findByText("SAVED");

    expect(recording.stop).toHaveBeenCalledTimes(1);
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/ui-feedback", expect.objectContaining({
      method: "POST",
      json: expect.objectContaining({
        id: expect.stringMatching(/^[a-f0-9]{32}$/),
        screenshot_base64: "PNG_BYTES",
        audio_base64: expect.any(String),
      }),
    }));
    view.unmount();
  });

  it("retries the same frozen report after a failed POST", async () => {
    const posts: Array<{ id?: string; captured_at?: string; context?: unknown; audio_base64?: string; screenshot_base64?: string }> = [];
    let postAttempt = 0;
    mocks.apiFetch.mockImplementation(async (path: string, init?: { json?: typeof posts[number] }) => {
      if (path === "/api/ui-feedback/status") return statusEnabled;
      if (path === "/api/ui-feedback") {
        posts.push(init?.json ?? {});
        postAttempt += 1;
        if (postAttempt === 1) throw new Error("save failed");
        return saveSuccess;
      }
      if (path.endsWith("/transcribe")) return transcribeSuccess;
      return {};
    });
    const view = deskFace();
    await startPicker();
    await selectAction(view.action);
    fireEvent.click(screen.getByRole("button", { name: "Stop and save" }));
    await screen.findByRole("button", { name: "Retry" });
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByText("SAVED");

    expect(posts).toHaveLength(2);
    expect(posts[1]).toEqual(posts[0]);
    expect(mocks.captureWindowPng).toHaveBeenCalledTimes(1);
    view.unmount();
  });

  it("keeps the saved bundle when ASR fails and retries only the transcript", async () => {
    const recording = session();
    let saveCalls = 0;
    let transcribeCalls = 0;
    mocks.startFeedbackAudio.mockResolvedValueOnce(recording);
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/ui-feedback/status") return statusEnabled;
      if (path === "/api/ui-feedback") {
        saveCalls += 1;
        return saveSuccess;
      }
      if (path.endsWith("/transcribe")) {
        transcribeCalls += 1;
        return transcribeCalls === 1
          ? transcribeFailed
          : transcribeSuccess;
      }
      return {};
    });
    const view = deskFace();
    await startPicker();
    await selectAction(view.action);
    fireEvent.click(screen.getByRole("button", { name: "Stop and save" }));
    await screen.findByRole("button", { name: "Retry transcription" });
    expect(screen.getByText("Speech is not set up.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Retry transcription" }));
    await screen.findByText("SAVED");
    expect(saveCalls).toBe(1);
    expect(transcribeCalls).toBe(2);
    expect(recording.stop).toHaveBeenCalledTimes(1);
    expect(screen.getByText("SPEECH · PRIVATE NETWORK")).toBeTruthy();
    view.unmount();
  });

  it("aborts a pending grant on cancel and cancels a late-resolved session", async () => {
    let signal: AbortSignal | undefined;
    let resolveAudio: ((value: ReturnType<typeof session>) => void) | undefined;
    mocks.startFeedbackAudio.mockImplementation((candidate: AbortSignal) => {
      signal = candidate;
      return new Promise<ReturnType<typeof session>>((resolve) => { resolveAudio = resolve; });
    });
    const view = deskFace();
    await startPicker();
    fireEvent.pointerDown(view.action, { pointerId: 1 });
    await waitFor(() => expect(mocks.startFeedbackAudio).toHaveBeenCalled());
    expect(signal?.aborted).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(signal?.aborted).toBe(true);

    const late = session();
    await act(async () => { resolveAudio?.(late); });
    await waitFor(() => expect(late.cancel).toHaveBeenCalled());
    view.unmount();
  });

  it("aborts a pending grant when the feedback host unmounts", async () => {
    let signal: AbortSignal | undefined;
    let resolveAudio: ((value: ReturnType<typeof session>) => void) | undefined;
    mocks.startFeedbackAudio.mockImplementation((candidate: AbortSignal) => {
      signal = candidate;
      return new Promise<ReturnType<typeof session>>((resolve) => { resolveAudio = resolve; });
    });
    const view = deskFace();
    await startPicker();
    fireEvent.pointerDown(view.action, { pointerId: 1 });
    await waitFor(() => expect(mocks.startFeedbackAudio).toHaveBeenCalled());
    view.unmount();
    expect(signal?.aborted).toBe(true);

    const late = session();
    await act(async () => { resolveAudio?.(late); });
    await waitFor(() => expect(late.cancel).toHaveBeenCalled());
  });

  it("does not release the floor when a successor hold owns it", async () => {
    const feedback = captureHolder.current!.startFeedbackAudio();
    const held = await feedback;
    mocks.holdOwnsFloor.mockReturnValue(true);
    held.cancel();
    expect(mocks.abortHold).toHaveBeenCalledWith(11);
    expect(mocks.releaseAudioFloor).not.toHaveBeenCalled();
  });
});
