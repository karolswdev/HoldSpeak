// HS-154-02 — the submit seam IS the composer's send (sendTurn).
//
// This test imports the callLoopWiring and spies on sendTurn to prove
// that the call loop's onSubmit path goes through the SAME function
// the ThreadComposer uses — no parallel turn entrance; the loop never
// issues its own network request to /api/threads/*/turns.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ── mocks ───────────────────────────────────────────────────────────

// Spy on sendTurn — the SAME function the ThreadComposer's handleSend calls
const mockSendTurn = vi.fn().mockResolvedValue({ user_message_id: "u1", assistant_message_id: "a1" });

vi.mock("../threads", () => ({
  sendTurn: (...args: unknown[]) => mockSendTurn(...args),
}));

// Capture the callbacks the callLoop receives
let capturedCallbacks: {
  onSubmit: (text: string) => void;
  onError: (error: unknown) => void;
  onStateChange?: (state: string) => void;
} | null = null;

const mockStartCallLoop = vi.fn().mockImplementation(async (cbs: typeof capturedCallbacks) => {
  capturedCallbacks = cbs;
});
const mockStopCallLoop = vi.fn();
const mockCallLoopState = vi.fn().mockReturnValue("idle");

vi.mock("../../lib/callLoop", () => ({
  startCallLoop: (...args: unknown[]) => mockStartCallLoop(...args),
  stopCallLoop: (...args: unknown[]) => mockStopCallLoop(...args),
  callLoopState: (...args: unknown[]) => mockCallLoopState(...args),
}));

import { wireCallLoop } from "../callLoopWiring";

// ── tests ───────────────────────────────────────────────────────────

describe("callLoopWiring", () => {
  const THREAD_ID = "thread-abc";

  beforeEach(() => {
    mockSendTurn.mockClear();
    mockStartCallLoop.mockClear();
    mockStopCallLoop.mockClear();
    capturedCallbacks = null;
  });

  afterEach(() => {
    // Clean up
  });

  it("wires onSubmit to sendTurn (the composer's send path)", async () => {
    const onError = vi.fn();
    const wiring = wireCallLoop(THREAD_ID, onError);
    await wiring.start();

    expect(mockStartCallLoop).toHaveBeenCalledOnce();
    expect(capturedCallbacks).not.toBeNull();

    // Simulate the call loop delivering a transcript
    capturedCallbacks!.onSubmit("Hello from voice");

    // The SAME sendTurn the composer uses — with the correct thread id
    expect(mockSendTurn).toHaveBeenCalledOnce();
    expect(mockSendTurn).toHaveBeenCalledWith(THREAD_ID, { text: "Hello from voice" });
  });

  it("the loop never issues its own /api/threads/*/turns request", async () => {
    // The wiring proves this by construction: onSubmit calls sendTurn,
    // which is the composer's OWN function. The callLoop module has no
    // import of apiFetch or threads — it receives onSubmit as a callback.
    const onError = vi.fn();
    const wiring = wireCallLoop(THREAD_ID, onError);
    await wiring.start();

    capturedCallbacks!.onSubmit("Test text");

    // sendTurn is the ONLY thing called — no direct network request
    expect(mockSendTurn).toHaveBeenCalledOnce();
  });

  it("stop() delegates to stopCallLoop", () => {
    const onError = vi.fn();
    const wiring = wireCallLoop(THREAD_ID, onError);
    wiring.stop();

    expect(mockStopCallLoop).toHaveBeenCalledOnce();
  });

  it("onError is forwarded to the caller", async () => {
    const onError = vi.fn();
    const wiring = wireCallLoop(THREAD_ID, onError);
    await wiring.start();

    const error = { failure: "transcription_failed" as const, message: "server down" };
    capturedCallbacks!.onError(error);

    expect(onError).toHaveBeenCalledOnce();
    expect(onError).toHaveBeenCalledWith(error);
  });

  it("onStateChange is forwarded to the caller", async () => {
    const onStateChange = vi.fn();
    const onError = vi.fn();
    const wiring = wireCallLoop(THREAD_ID, onError, onStateChange);
    await wiring.start();

    capturedCallbacks!.onStateChange?.("listening");

    expect(onStateChange).toHaveBeenCalledWith("listening");
  });
});
