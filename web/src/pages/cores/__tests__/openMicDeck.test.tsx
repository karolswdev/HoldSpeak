// HS-112-06 — the Speak deck with the mic left open.
//
// One latch opens the microphone for the session; from then on spoken
// utterances arrive with no key touched, and each one travels the exact
// HS-112-02 road: the same AIM, the same `/api/dictation/remote`, one
// fresh `delivery_id` per utterance, the same in-flow refusals. Silence
// misread as speech spends nothing. Pressing the latch again drops the
// stream — and the lamp reports the session's own phase, never a guess.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DictationCore } from "../DictationCore";
import { ApiError } from "../../../lib/api";
import type { MicPhase } from "../../../lib/micSession";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  startOpenMic: vi.fn(),
  stopOpenMic: vi.fn(),
  transcribeWav: vi.fn(),
  openMicInterval: vi.fn(),
  closeMicInterval: vi.fn(),
  segment: null as
    | ((segment: { chunks: Float32Array[]; rate: number }) => void)
    | null,
  phase: null as ((phase: MicPhase) => void) | null,
}));

vi.mock("../../../lib/api", () => {
  class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
      public payload: unknown = {},
    ) {
      super(message);
      this.name = "ApiError";
    }
  }
  return {
    ApiError,
    apiFetch: mocks.apiFetch,
    readableError: (error: unknown) =>
      error instanceof Error ? error.message : "Request failed",
  };
});

vi.mock("../../../lib/pendingVoice", () => ({
  loadPendingVoice: vi.fn().mockResolvedValue(null),
  savePendingVoice: vi.fn(),
  clearPendingVoice: vi.fn(),
}));

vi.mock("../../../lib/speakToFill", () => ({
  cancelCapture: vi.fn(),
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => null,
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn().mockResolvedValue(""),
  retryPendingTranscription: vi.fn().mockResolvedValue(null),
  subscribeCaptureLevel: () => () => undefined,
  toWav16kMono: () => new ArrayBuffer(8),
  transcribeWav: mocks.transcribeWav,
  // HS-131-09: the open mic now opens ONE admitted server-side interval and
  // honors its one terminal status.
  openMicInterval: mocks.openMicInterval,
  closeMicInterval: mocks.closeMicInterval,
  micIntervalClosed: (error: unknown) =>
    !!(error as { payload?: { mic_interval?: string } })?.payload
      ?.mic_interval,
}));

vi.mock("../../../lib/micSession", () => ({
  micCaptureSupported: () => true,
  micCaptureReason: () => null,
  startOpenMic: mocks.startOpenMic,
  stopOpenMic: mocks.stopOpenMic,
  subscribeMicPhase: (listener: (phase: MicPhase) => void) => {
    mocks.phase = listener;
    listener("closed");
    return () => {
      mocks.phase = null;
    };
  },
  micPhase: () => "closed",
}));

type Route = (init?: { method?: string; json?: unknown }) => Promise<unknown>;

function mockRoutes(routes: Record<string, Route> = {}) {
  mocks.apiFetch.mockImplementation(
    (path: string, init?: { method?: string; json?: unknown }) => {
      for (const [prefix, handler] of Object.entries(routes))
        if (path === prefix || path.startsWith(prefix)) return handler(init);
      return Promise.resolve({});
    },
  );
}

function callsTo(path: string): { method?: string; json?: any }[] {
  return mocks.apiFetch.mock.calls
    .filter((call: unknown[]) => String(call[0]).startsWith(path))
    .map(
      (call: unknown[]) => (call[1] ?? {}) as { method?: string; json?: any },
    );
}

/** One utterance heard by the VAD, handed over as the session would. */
async function utterance(text: string) {
  mocks.transcribeWav.mockResolvedValueOnce(text);
  await mocks.segment?.({ chunks: [new Float32Array(1024)], rate: 16_000 });
}

async function openDeck() {
  render(
    <MemoryRouter>
      <DictationCore />
    </MemoryRouter>,
  );
  return screen.findByRole("button", { name: "Open mic" });
}

async function latchOpen() {
  const latch = await openDeck();
  fireEvent.click(latch);
  await waitFor(() => expect(latch).toHaveAttribute("aria-pressed", "true"));
  return latch;
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  mocks.segment = null;
  mocks.openMicInterval.mockResolvedValue(undefined);
  mocks.closeMicInterval.mockResolvedValue(undefined);
  mocks.startOpenMic.mockImplementation(
    async (handler: (segment: { chunks: Float32Array[]; rate: number }) => void) => {
      mocks.segment = handler;
    },
  );
  mockRoutes({
    "/api/dictation/remote": () =>
      Promise.resolve({ success: true, delivered: true }),
  });
});

describe("the open mic on the Speak deck (HS-112-06)", () => {
  it("opens the session once and lands utterances with no key touched", async () => {
    await latchOpen();
    expect(mocks.startOpenMic).toHaveBeenCalledTimes(1);

    await utterance("ship it friday");
    await waitFor(() =>
      expect(callsTo("/api/dictation/remote")).toHaveLength(1),
    );
    await utterance("and tell the team");
    await waitFor(() =>
      expect(callsTo("/api/dictation/remote")).toHaveLength(2),
    );

    const [first, second] = callsTo("/api/dictation/remote");
    expect(first.json.text).toBe("ship it friday");
    expect(first.json.target_mode).toBe("focused");
    expect(String(first.json.delivery_id)).toMatch(/^speak:/);
    // one fresh claim per utterance — never a replayed id.
    expect(first.json.delivery_id).not.toBe(second.json.delivery_id);
    // one grant covered both: the mic was never re-requested.
    expect(mocks.startOpenMic).toHaveBeenCalledTimes(1);
  });

  it("obeys the deck's aim like a released TALK does", async () => {
    await latchOpen();
    fireEvent.change(screen.getByRole("combobox", { name: "Aim" }), {
      target: { value: "agent" },
    });

    await utterance("summarise the thread");

    await waitFor(() =>
      expect(callsTo("/api/dictation/remote")).toHaveLength(1),
    );
    const [call] = callsTo("/api/dictation/remote");
    expect(call.json.target_mode).toBe("agent");
    expect(call.json.require_agent).toBe(true);
  });

  it("rehearses instead of delivering while REHEARSE is latched", async () => {
    await latchOpen();
    fireEvent.click(screen.getByRole("checkbox", { name: "Rehearse" }));

    await utterance("ship it friday");

    await waitFor(() =>
      expect(callsTo("/api/dictation/dry-run")).toHaveLength(1),
    );
    expect(callsTo("/api/dictation/remote")).toHaveLength(0);
  });

  it("drops an empty transcript silently — silence spends nothing", async () => {
    await latchOpen();

    await utterance("   ");

    expect(callsTo("/api/dictation/remote")).toHaveLength(0);
    expect(callsTo("/api/dictation/dry-run")).toHaveLength(0);
  });

  it("renders a transcription failure in flow, never as an overlay", async () => {
    await latchOpen();
    mocks.transcribeWav.mockRejectedValueOnce(new Error("Failed to fetch"));

    await mocks.segment?.({ chunks: [new Float32Array(8)], rate: 16_000 });

    await waitFor(() =>
      expect(screen.getByLabelText("Dictation state")).toBeInTheDocument(),
    );
    const register = screen.getByLabelText("Dictation state");
    const refused = Array.from(
      register.querySelectorAll(".speak-register-token"),
    ).find((token) => token.textContent === "Refused");
    expect(refused).toHaveAttribute("data-active");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("the latch drops the stream and the lamp follows the session", async () => {
    const latch = await latchOpen();
    expect(screen.getByLabelText("Mic session").textContent).toBe("CLOSED");

    mocks.phase?.("open");
    await waitFor(() =>
      expect(screen.getByLabelText("Mic session").textContent).toBe("OPEN"),
    );
    mocks.phase?.("segmenting");
    await waitFor(() =>
      expect(screen.getByLabelText("Mic session").textContent).toBe(
        "SEGMENTING",
      ),
    );
    mocks.phase?.("held");
    await waitFor(() =>
      expect(screen.getByLabelText("Mic session").textContent).toBe("HELD"),
    );

    fireEvent.click(latch);
    await waitFor(() => expect(latch).not.toHaveAttribute("aria-pressed"));
    expect(mocks.stopOpenMic).toHaveBeenCalled();
    mocks.phase?.("closed");
    await waitFor(() =>
      expect(screen.getByLabelText("Mic session").textContent).toBe("CLOSED"),
    );
  });

  it("refuses in flow when the browser withholds the microphone", async () => {
    mocks.startOpenMic.mockRejectedValueOnce(new Error("Permission denied"));
    const latch = await openDeck();

    fireEvent.click(latch);

    await waitFor(() => expect(latch).not.toHaveAttribute("aria-pressed"));
    const register = screen.getByLabelText("Dictation state");
    const refused = Array.from(
      register.querySelectorAll(".speak-register-token"),
    ).find((token) => token.textContent === "Refused");
    expect(refused).toHaveAttribute("data-active");
  });

  it("takes the audio floor before the device opens", async () => {
    await latchOpen();
    const claim = mocks.apiFetch.mock.calls.findIndex(
      (call: unknown[]) => call[0] === "/api/dictation/floor/claim",
    );
    expect(claim).toBeGreaterThanOrEqual(0);
    expect(mocks.startOpenMic).toHaveBeenCalledTimes(1);
  });

  it("refuses BY NAME when a meeting holds the floor, and never opens", async () => {
    mockRoutes({
      "/api/dictation/floor/claim": () =>
        Promise.reject(new ApiError(409, "conflict", { owner: "meeting" })),
    });
    const latch = await openDeck();

    fireEvent.click(latch);

    await waitFor(() =>
      expect(screen.getByLabelText("Landed latency").textContent).toBe(
        "FLOOR HELD MEETING",
      ),
    );
    expect(latch).not.toHaveAttribute("aria-pressed");
    // the device was never opened under a held floor.
    expect(mocks.startOpenMic).not.toHaveBeenCalled();
  });

  it("releases the floor when the latch drops the stream", async () => {
    const latch = await latchOpen();
    fireEvent.click(latch);
    await waitFor(() =>
      expect(
        mocks.apiFetch.mock.calls.some(
          (call: unknown[]) => call[0] === "/api/dictation/floor/release",
        ),
      ).toBe(true),
    );
  });

  it("admits ONE interval before the device opens (HS-131-09)", async () => {
    await latchOpen();
    expect(mocks.openMicInterval).toHaveBeenCalledTimes(1);
    await utterance("one");
    await utterance("two");
    // Two utterances, still ONE interval: the mic is one authority lifetime.
    expect(mocks.openMicInterval).toHaveBeenCalledTimes(1);
  });

  it("closes the interval and requires a fresh click when the server fences it", async () => {
    const latch = await latchOpen();
    mocks.transcribeWav.mockRejectedValueOnce(
      new ApiError(409, "The microphone session closed.", {
        mic_interval: "closed",
        reason: "browser_mic_inactivity_lapsed",
      }),
    );

    await mocks.segment?.({ chunks: [new Float32Array(8)], rate: 16_000 });

    // Sol Amendment 3: one visible interval never crosses authority epochs.
    await waitFor(() => expect(mocks.stopOpenMic).toHaveBeenCalled());
    await waitFor(() => expect(latch).not.toHaveAttribute("aria-pressed"));
    expect(callsTo("/api/dictation/remote")).toHaveLength(0);
  });

  it("drops the stream when the room closes", async () => {
    const view = render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    await screen.findByRole("button", { name: "Open mic" });
    view.unmount();
    expect(mocks.stopOpenMic).toHaveBeenCalled();
  });
});
