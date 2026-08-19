import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FirstWords } from "./FirstWords";
import {
  clearFirstValueKeepNoteId,
  takeFirstValueNoteOpen,
} from "../firstValue";
import { readDurableDraft } from "../../lib/durableDraft";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  retryPendingTranscription: vi.fn(),
  startStreamSession: vi.fn(),
  refresh: vi.fn(),
  loadPendingVoice: vi.fn(),
  openSurfaceOr: vi.fn(),
  speakSupported: true,
  streamSupported: true,
}));

vi.mock("../store", () => ({
  useDesk: (selector: (state: { refresh: typeof mocks.refresh }) => unknown) =>
    selector({ refresh: mocks.refresh }),
}));

vi.mock("../../lib/api", () => {
  class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
    ) {
      super(message);
    }
  }
  return {
    ApiError,
    apiFetch: mocks.apiFetch,
    readableError: (error: unknown) =>
      error instanceof Error ? error.message : "Request failed",
  };
});

vi.mock("../../lib/speakToFill", () => ({
  speakToFillSupported: () => mocks.speakSupported,
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn(),
  cancelCapture: vi.fn(),
  retryPendingTranscription: mocks.retryPendingTranscription,
}));

vi.mock("../../lib/micStreamSession", () => ({
  micStreamSupported: () => mocks.streamSupported,
  startStreamSession: mocks.startStreamSession,
  subscribeCaptureLevel: () => () => undefined,
}));

vi.mock("../../lib/pendingVoice", () => ({
  loadPendingVoice: mocks.loadPendingVoice,
}));

vi.mock("../shell", () => ({
  openSurfaceOr: mocks.openSurfaceOr,
}));

describe("FirstWords", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    clearFirstValueKeepNoteId();
    takeFirstValueNoteOpen();
    mocks.apiFetch.mockImplementation((path: string) => {
      if (path.endsWith("/start"))
        return Promise.resolve({ attempt: { id: "a1" } });
      return Promise.resolve({ success: true });
    });
    const stopFn = vi.fn().mockResolvedValue("A sentence that stays editable.");
    mocks.startStreamSession.mockResolvedValue({
      stop: stopFn,
      cancel: vi.fn(),
      retained: vi.fn().mockResolvedValue(false),
    });
    mocks.retryPendingTranscription.mockResolvedValue(null);
    mocks.loadPendingVoice.mockResolvedValue(null);
    mocks.speakSupported = true;
    mocks.streamSupported = true;
    mocks.refresh.mockResolvedValue(undefined);
  });

  it("captures one local step, retains editable text, and records no phrase", async () => {
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    const talk = screen.getByRole("button", { name: "Click to dictate" });
    fireEvent.click(talk);
    await screen.findByText("Listening… click to stop");
    fireEvent.click(talk);

    const editor = await screen.findByRole("textbox", {
      name: "Your dictated text",
    });
    expect(editor).toHaveValue("A sentence that stays editable.");
    fireEvent.change(editor, { target: { value: "Edited after dictation." } });
    expect(editor).toHaveValue("Edited after dictation.");

    await waitFor(() =>
      expect(mocks.apiFetch).toHaveBeenCalledWith(
        "/api/setup/first-value/a1/event",
        expect.objectContaining({
          json: {
            event_id: "a1:3:transcript_received",
            kind: "transcript_received",
          },
        }),
      ),
    );
    const telemetry = mocks.apiFetch.mock.calls.filter(([path]) =>
      String(path).includes("/first-value/"),
    );
    expect(JSON.stringify(telemetry)).not.toContain(
      "A sentence that stays editable",
    );
    expect(mocks.apiFetch.mock.calls.some(([path]) => String(path).includes("/finish"))).toBe(false);
  });

  it("names browser or OS microphone repair and offers one Retry after permission denial", async () => {
    mocks.startStreamSession.mockRejectedValue(
      new DOMException("denied", "NotAllowedError"),
    );
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Click to dictate" }),
    );
    expect(
      await screen.findByText(/Microphone access is blocked/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Click to retry dictation" }),
    ).toBeEnabled();
    expect(screen.getByRole("button", { name: "Copy" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Keep as Note" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Setup" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();
  });

  it("offers the one honest Setup action when local transcription is unavailable", async () => {
    let streamEvent!: (event: { type: "error"; error: string; failure_category: string }) => void;
    mocks.startStreamSession.mockImplementation(async (onEvent) => {
      streamEvent = onEvent;
      return { stop: vi.fn(), cancel: vi.fn(), retained: vi.fn().mockResolvedValue(false) };
    });
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Click to dictate" }));
    await waitFor(() => expect(streamEvent).toBeTypeOf("function"));
    streamEvent({
      type: "error",
      error: "Local transcription unavailable.",
      failure_category: "transcription_unavailable",
    });

    expect(await screen.findByText(/Local transcription is unavailable/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Setup" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Voice typing unavailable" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Setup" }));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-setup", "/setup");
  });

  it("keeps typed fallback and one Retry for no speech and a timeout", async () => {
    const noSpeech = vi.fn().mockResolvedValue("");
    mocks.startStreamSession.mockResolvedValue({
      stop: noSpeech,
      cancel: vi.fn(),
      retained: vi.fn().mockResolvedValue(false),
    });
    const view = render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Click to dictate" }));
    await screen.findByText("Listening… click to stop");
    fireEvent.click(screen.getByRole("button", { name: "Stop listening" }));
    expect(await screen.findByText(/No speech was detected/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Click to retry dictation" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Your dictated text" }), {
      target: { value: "Typed instead." },
    });
    expect(screen.getByDisplayValue("Typed instead.")).toBeInTheDocument();

    view.unmount();
    const timeout = vi.fn().mockRejectedValue(new DOMException("slow", "TimeoutError"));
    mocks.startStreamSession.mockResolvedValue({
      stop: timeout,
      cancel: vi.fn(),
      retained: vi.fn().mockResolvedValue(false),
    });
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Click to dictate" }));
    await screen.findByText("Listening… click to stop");
    fireEvent.click(screen.getByRole("button", { name: "Stop listening" }));
    expect(await screen.findByText(/Transcription timed out/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Click to retry dictation" })).toBeEnabled();
  });

  it("retries retained stream audio after reload without recording again", async () => {
    let streamEvent!: (event: { type: "error"; error: string; failure_category: string }) => void;
    let finishRetention!: (retained: boolean) => void;
    const retention = new Promise<boolean>((resolve) => {
      finishRetention = resolve;
    });
    const cancel = vi.fn();
    mocks.startStreamSession.mockImplementation(async (onEvent) => {
      streamEvent = onEvent;
      return {
        stop: vi.fn().mockResolvedValue(""),
        cancel,
        retained: vi.fn().mockReturnValue(retention),
      };
    });
    const first = render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Click to dictate" }));
    await waitFor(() => expect(streamEvent).toBeTypeOf("function"));
    streamEvent({
      type: "error",
      error: "Transcription failed.",
      failure_category: "transcription_failed",
    });
    const savingAudio = await screen.findByRole("button", {
      name: "Saving audio for Retry",
    });
    expect(savingAudio).toBeDisabled();
    finishRetention(true);
    expect(await screen.findByText(/Captured audio is retained/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Click to retry dictation" }),
    ).toBeEnabled();
    expect(cancel).toHaveBeenCalledOnce();
    expect(mocks.startStreamSession).toHaveBeenCalledWith(
      expect.any(Function),
      { retainScope: "first-words" },
    );

    first.unmount();
    mocks.retryPendingTranscription.mockResolvedValue("Recovered retained words.");
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Click to dictate" }));
    expect(await screen.findByDisplayValue("Recovered retained words.")).toBeInTheDocument();
    expect(mocks.retryPendingTranscription).toHaveBeenLastCalledWith("first-words");
    expect(mocks.startStreamSession).toHaveBeenCalledTimes(1);
  });

  it("retries recovered audio even when this browser cannot start a fresh capture", async () => {
    mocks.speakSupported = false;
    mocks.streamSupported = false;
    mocks.loadPendingVoice.mockResolvedValue(new ArrayBuffer(8));
    mocks.retryPendingTranscription.mockResolvedValue("Recovered without recording.");
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/Captured audio was recovered/)).toBeInTheDocument();
    expect(
      screen.queryByText(/Microphone capture is unavailable/),
    ).not.toBeInTheDocument();
    const retry = screen.getByRole("button", { name: "Click to retry dictation" });
    expect(retry).toBeEnabled();
    fireEvent.click(retry);
    expect(await screen.findByDisplayValue("Recovered without recording.")).toBeInTheDocument();
    expect(
      screen.queryByText(/Microphone capture is unavailable/),
    ).not.toBeInTheDocument();
    expect(mocks.retryPendingTranscription).toHaveBeenCalledWith("first-words");
    expect(mocks.startStreamSession).not.toHaveBeenCalled();
  });

  it("does not let late recovered-audio lookup replace a new capture", async () => {
    let resolveRecovered!: (audio: ArrayBuffer | null) => void;
    mocks.loadPendingVoice.mockReturnValue(
      new Promise<ArrayBuffer | null>((resolve) => {
        resolveRecovered = resolve;
      }),
    );
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Click to dictate" }));
    await screen.findByText("Listening… click to stop");
    resolveRecovered(new ArrayBuffer(8));
    await Promise.resolve();

    expect(screen.getByText("Listening… click to stop")).toBeInTheDocument();
    expect(screen.queryByText(/Captured audio was recovered/)).not.toBeInTheDocument();
  });

  it("keeps idle first value free of setup administration", () => {
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );

    expect(screen.queryByRole("button", { name: "Setup" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Configure rewrite destination" }),
    ).not.toBeInTheDocument();
  });

  it("transcribes one capture exactly once when toggle is repeated", async () => {
    const stopFn = vi.fn().mockResolvedValue("A sentence that stays editable.");
    mocks.startStreamSession.mockResolvedValue({ stop: stopFn, cancel: vi.fn() });
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    const talk = screen.getByRole("button", { name: "Click to dictate" });
    fireEvent.click(talk);
    await screen.findByText("Listening… click to stop");

    fireEvent.click(talk);

    await screen.findByDisplayValue("A sentence that stays editable.");
    expect(stopFn).toHaveBeenCalledOnce();
    expect(
      screen.queryByRole("button", { name: "Configure rewrite destination" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Setup" })).not.toBeInTheDocument();
  });

  it("persists Continue later independently of first success", async () => {
    const dismissed = vi.fn();
    render(
      <MemoryRouter>
        <FirstWords onDismiss={dismissed} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Continue later" }));
    await waitFor(() => expect(dismissed).toHaveBeenCalledOnce());
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/setup/onboarding", {
      method: "PUT",
      json: { disposition: "dismissed" },
    });
  });

  it("recovers an editable local draft after remount without sending it to metrics", async () => {
    localStorage.setItem(
      "hs.draft.v1.first-words",
      JSON.stringify({
        version: 1,
        text: "A draft retained through relaunch.",
        updatedAt: "2026-07-11T00:00:00Z",
      }),
    );

    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("textbox", { name: "Your dictated text" }),
    ).toHaveValue("A draft retained through relaunch.");
    expect(screen.getByText(/Recovered your local draft/)).toBeInTheDocument();
    expect(JSON.stringify(mocks.apiFetch.mock.calls)).not.toContain(
      "A draft retained through relaunch",
    );
  });

  it("copies the edited value and names a clipboard refusal", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    const editor = screen.getByRole("textbox", { name: "Your dictated text" });
    fireEvent.change(editor, { target: { value: "Edited copy value." } });
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("Edited copy value."));
    expect(screen.getByRole("status")).toHaveTextContent("Copied to your clipboard.");

    writeText.mockRejectedValueOnce(new Error("blocked"));
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Clipboard access was blocked. Select your text and copy it manually.",
    );
  });

  it("retries Keep with one client note id, refreshes, and stages its future open", async () => {
    const notePosts: Array<Record<string, unknown>> = [];
    mocks.apiFetch.mockImplementation((path: string, init?: { json?: Record<string, unknown> }) => {
      if (path === "/api/notes") {
        notePosts.push(init?.json || {});
        if (notePosts.length === 1) return Promise.reject(new Error("Response lost"));
        return Promise.resolve({ note: { id: notePosts[1].id } });
      }
      return Promise.resolve({ success: true });
    });
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByRole("textbox", { name: "Your dictated text" }), {
      target: { value: "Keep this edited value." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Keep as Note" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Could not keep as a note");
    fireEvent.click(screen.getByRole("button", { name: "Keep as Note" }));
    await waitFor(() => expect(mocks.refresh).toHaveBeenCalledOnce());
    expect(notePosts).toHaveLength(2);
    expect(notePosts[0].id).toMatch(/^note_/);
    expect(notePosts[1].id).toBe(notePosts[0].id);
    expect(notePosts[1].body_markdown).toBe("Keep this edited value.");
    expect(screen.getByRole("status")).toHaveTextContent(
      "Kept as a note. It will open when your Desk is ready.",
    );
  });

  it("keeps the durable draft and stable id when refresh fails after a confirmed write", async () => {
    const notePosts: Array<Record<string, unknown>> = [];
    mocks.apiFetch.mockImplementation((path: string, init?: { json?: Record<string, unknown> }) => {
      if (path === "/api/notes") {
        notePosts.push(init?.json || {});
        return Promise.resolve({ note: { id: notePosts.at(-1)?.id } });
      }
      return Promise.resolve({ success: true });
    });
    mocks.refresh
      .mockRejectedValueOnce(new Error("Desk refresh failed"))
      .mockResolvedValueOnce(undefined);
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByRole("textbox", { name: "Your dictated text" }), {
      target: { value: "Keep this through refresh failure." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Keep as Note" }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Kept as a note, but the Desk could not refresh. Retry Keep as Note to open it.",
    );
    expect(readDurableDraft("first-words")?.text).toBe("Keep this through refresh failure.");
    expect(localStorage.getItem("hs.first-value.keep-note-id")).toBe(notePosts[0].id);
    expect(takeFirstValueNoteOpen()).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Keep as Note" }));
    await waitFor(() => expect(mocks.refresh).toHaveBeenCalledTimes(2));
    expect(notePosts.map((post) => post.id)).toEqual([notePosts[0].id, notePosts[0].id]);
    expect(takeFirstValueNoteOpen()).toBe(`note:${notePosts[0].id}`);
    expect(takeFirstValueNoteOpen()).toBeNull();
  });
});
