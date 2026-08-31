// HS-154-02 — call loop vitest: the energy VAD hands-free utterance loop.
//
// A synthetic utterance (mocked micSession/VAD events + mocked fetch)
// yields EXACTLY ONE onSubmit with the transcript; empty transcript →
// zero submits; stop() closes the session (spy) and cancels in-flight
// work; a transcribe error emits onError and the loop survives to the
// next utterance.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ── mocks ───────────────────────────────────────────────────────────

// Capture the segment handler that startOpenMic receives
let capturedSegmentHandler: ((segment: { chunks: Float32Array[]; rate: number }) => void) | null = null;

const mockStartOpenMic = vi.fn().mockImplementation(async (handler: (segment: { chunks: Float32Array[]; rate: number }) => void) => {
  capturedSegmentHandler = handler;
});
const mockStopOpenMic = vi.fn().mockImplementation(() => {
  capturedSegmentHandler = null;
});

vi.mock("../micSession", () => ({
  startOpenMic: (...args: unknown[]) => mockStartOpenMic(...args),
  stopOpenMic: (...args: unknown[]) => mockStopOpenMic(...args),
}));

const mockTranscribeWav = vi.fn();
const mockToWav16kMono = vi.fn().mockReturnValue(new ArrayBuffer(44));

vi.mock("../speakToFill", () => ({
  transcribeWav: (...args: unknown[]) => mockTranscribeWav(...args),
  toWav16kMono: (...args: unknown[]) => mockToWav16kMono(...args),
}));

vi.mock("../dictationRecovery", () => ({
  dictationFailure: (err: unknown) => {
    if (err instanceof Error && err.message.includes("permission"))
      return "permission_denied";
    return "transcription_failed";
  },
}));

import {
  startCallLoop,
  stopCallLoop,
  callLoopState,
  type CallLoopCallbacks,
} from "../callLoop";

// ── helpers ─────────────────────────────────────────────────────────

function fakeSegment(): { chunks: Float32Array[]; rate: number } {
  return {
    chunks: [new Float32Array([0.1, 0.2, 0.3])],
    rate: 48000,
  };
}

function makeCallbacks(overrides: Partial<CallLoopCallbacks> = {}): CallLoopCallbacks & {
  submitSpy: ReturnType<typeof vi.fn>;
  errorSpy: ReturnType<typeof vi.fn>;
  stateSpy: ReturnType<typeof vi.fn>;
} {
  const submitSpy = vi.fn();
  const errorSpy = vi.fn();
  const stateSpy = vi.fn();
  return {
    onSubmit: overrides.onSubmit ?? submitSpy,
    onError: overrides.onError ?? errorSpy,
    onStateChange: overrides.onStateChange ?? stateSpy,
    submitSpy,
    errorSpy,
    stateSpy,
  };
}

/** Flush microtasks so async handlers settle. */
async function flush(): Promise<void> {
  await new Promise<void>((r) => setTimeout(r, 0));
  await new Promise<void>((r) => setTimeout(r, 0));
}

// ── tests ───────────────────────────────────────────────────────────

describe("callLoop", () => {
  beforeEach(() => {
    mockStartOpenMic.mockClear();
    mockStopOpenMic.mockClear();
    mockTranscribeWav.mockClear();
    mockToWav16kMono.mockClear();
    capturedSegmentHandler = null;

    // Default: transcribe returns text
    mockTranscribeWav.mockResolvedValue("Hello world");
  });

  afterEach(() => {
    // Ensure clean state between tests
    stopCallLoop();
  });

  // ── start / utterance / submit ──────────────────────────────────

  it("opens the mic session on start and reports listening state", async () => {
    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    expect(mockStartOpenMic).toHaveBeenCalledOnce();
    expect(callLoopState()).toBe("listening");
    expect(cbs.stateSpy).toHaveBeenCalledWith("listening");
  });

  it("a synthetic utterance yields exactly one onSubmit with the transcript", async () => {
    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    // Simulate VAD delivering an utterance segment
    capturedSegmentHandler!(fakeSegment());
    await flush();

    expect(mockToWav16kMono).toHaveBeenCalledOnce();
    expect(mockTranscribeWav).toHaveBeenCalledOnce();
    expect(cbs.submitSpy).toHaveBeenCalledOnce();
    expect(cbs.submitSpy).toHaveBeenCalledWith("Hello world");
  });

  it("transitions through transcribing and back to listening", async () => {
    const cbs = makeCallbacks();
    await startCallLoop(cbs);
    cbs.stateSpy.mockClear();

    capturedSegmentHandler!(fakeSegment());
    // Should enter transcribing
    expect(cbs.stateSpy).toHaveBeenCalledWith("transcribing");

    await flush();
    // Should return to listening
    expect(cbs.stateSpy).toHaveBeenCalledWith("listening");
  });

  // ── empty transcript ────────────────────────────────────────────

  it("drops empty transcripts (zero submits)", async () => {
    mockTranscribeWav.mockResolvedValue("");
    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    capturedSegmentHandler!(fakeSegment());
    await flush();

    expect(cbs.submitSpy).not.toHaveBeenCalled();
    expect(callLoopState()).toBe("listening");
  });

  it("drops whitespace-only transcripts (zero submits)", async () => {
    mockTranscribeWav.mockResolvedValue("   \n  ");
    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    capturedSegmentHandler!(fakeSegment());
    await flush();

    expect(cbs.submitSpy).not.toHaveBeenCalled();
    expect(callLoopState()).toBe("listening");
  });

  // ── stop ────────────────────────────────────────────────────────

  it("stop() closes the mic session and returns to idle", async () => {
    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    stopCallLoop();

    expect(mockStopOpenMic).toHaveBeenCalledOnce();
    expect(callLoopState()).toBe("idle");
    expect(cbs.stateSpy).toHaveBeenCalledWith("idle");
  });

  it("stop() cancels in-flight transcription", async () => {
    // Set up a transcribe that hangs
    let resolveTranscribe!: (value: string) => void;
    mockTranscribeWav.mockReturnValue(
      new Promise<string>((resolve) => {
        resolveTranscribe = resolve;
      }),
    );

    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    // Start an utterance
    capturedSegmentHandler!(fakeSegment());
    // transcribe is now in-flight

    // Stop mid-flight
    stopCallLoop();

    // Resolve the transcribe (late) — should NOT fire onSubmit
    resolveTranscribe("Late text");
    await flush();

    expect(cbs.submitSpy).not.toHaveBeenCalled();
    expect(callLoopState()).toBe("idle");
  });

  // ── error handling ──────────────────────────────────────────────

  it("a transcribe error emits onError and the loop survives", async () => {
    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    // First utterance: transcribe fails
    mockTranscribeWav.mockRejectedValueOnce(new Error("server down"));
    capturedSegmentHandler!(fakeSegment());
    await flush();

    expect(cbs.errorSpy).toHaveBeenCalledOnce();
    expect(cbs.errorSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        failure: "transcription_failed",
        message: "server down",
      }),
    );
    expect(cbs.submitSpy).not.toHaveBeenCalled();
    // Loop survives — still listening
    expect(callLoopState()).toBe("listening");

    // Second utterance: transcribe succeeds
    mockTranscribeWav.mockResolvedValueOnce("Recovery text");
    capturedSegmentHandler!(fakeSegment());
    await flush();

    expect(cbs.submitSpy).toHaveBeenCalledOnce();
    expect(cbs.submitSpy).toHaveBeenCalledWith("Recovery text");
  });

  it("mic permission denied emits onError and goes idle", async () => {
    mockStartOpenMic.mockRejectedValueOnce(
      new Error("Microphone permission denied"),
    );

    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    expect(cbs.errorSpy).toHaveBeenCalledOnce();
    expect(cbs.errorSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        failure: "permission_denied",
        message: "Microphone permission denied",
      }),
    );
    expect(callLoopState()).toBe("idle");
  });

  // ── double-fire guard ───────────────────────────────────────────

  it("guards against double-fires from rapid VAD events", async () => {
    // Transcribe takes a moment
    let resolveTranscribe!: (value: string) => void;
    mockTranscribeWav.mockReturnValueOnce(
      new Promise<string>((resolve) => {
        resolveTranscribe = resolve;
      }),
    );

    const cbs = makeCallbacks();
    await startCallLoop(cbs);

    // Two rapid segments
    capturedSegmentHandler!(fakeSegment());
    capturedSegmentHandler!(fakeSegment());

    // Only one toWav call (the second was guarded out)
    expect(mockToWav16kMono).toHaveBeenCalledOnce();

    resolveTranscribe("First text");
    await flush();

    expect(cbs.submitSpy).toHaveBeenCalledOnce();
    expect(cbs.submitSpy).toHaveBeenCalledWith("First text");
  });

  // ── idempotent start ────────────────────────────────────────────

  it("does not double-start when already listening", async () => {
    const cbs = makeCallbacks();
    await startCallLoop(cbs);
    await startCallLoop(cbs); // second call is a no-op

    expect(mockStartOpenMic).toHaveBeenCalledOnce();
  });
});
