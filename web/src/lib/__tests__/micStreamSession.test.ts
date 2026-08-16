// HS-132-04 — the streaming socket declares WHAT KIND of utterance it carries.
//
// A speak-to-fill (every desk field mic) is the user typing with their voice:
// the socket opens with {"type":"start","pipeline":false} and the server's
// final pass is verbatim — no intent routing, no enrichment, no rewriting, no
// journal row. The Speak room's TALK key is the dictate-for-delivery surface;
// it asks for the pipeline, and that is the utterance's ONE pass.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../auth", () => ({
  websocketUrl: (path: string) => `ws://desk.test${path}`,
  websocketProtocols: () => ["holdspeak"],
}));

const mic = vi.hoisted(() => ({
  beginHold: vi.fn().mockResolvedValue(undefined),
  endHold: vi.fn().mockReturnValue(null),
  drainHold: vi.fn().mockReturnValue(null),
  abortHold: vi.fn(),
}));

vi.mock("../micSession", () => ({
  beginHold: mic.beginHold,
  endHold: mic.endHold,
  drainHold: mic.drainHold,
  abortHold: mic.abortHold,
  micCaptureSupported: vi.fn().mockReturnValue(true),
  subscribeCaptureLevel: vi.fn().mockReturnValue(() => {}),
}));

/* A 1-sample "capture": 44 header bytes + 2 PCM bytes. */
const CAPTURED = { chunks: [new Float32Array(1)], rate: 16_000 };

vi.mock("../speakToFill", () => ({
  toWav16kMono: vi.fn(() => new ArrayBuffer(46)),
  wavFromPcm16: vi.fn(
    (pcm: Int16Array) => new ArrayBuffer(44 + pcm.length * 2),
  ),
}));

const store = vi.hoisted(() => ({
  savePendingVoice: vi.fn().mockResolvedValue(undefined),
  clearPendingVoice: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../pendingVoice", () => ({
  savePendingVoice: store.savePendingVoice,
  clearPendingVoice: store.clearPendingVoice,
}));

import { startStreamSession } from "../micStreamSession";
import { toWav16kMono } from "../speakToFill";

type Listener = (event: unknown) => void;

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  sent: unknown[] = [];
  private listeners: Record<string, Listener[]> = {};

  constructor(
    public url: string,
    public protocols?: string | string[],
  ) {
    FakeWebSocket.instances.push(this);
  }

  addEventListener(type: string, fn: Listener) {
    (this.listeners[type] ??= []).push(fn);
  }

  send(data: unknown) {
    this.sent.push(data);
  }

  close() {
    this.emit("close", {});
  }

  emit(type: string, event: unknown) {
    (this.listeners[type] ?? []).forEach((fn) => fn(event));
  }

  /** What the client said in JSON text frames, parsed. */
  frames(): Record<string, unknown>[] {
    return this.sent
      .filter((item): item is string => typeof item === "string")
      .map((item) => JSON.parse(item) as Record<string, unknown>);
  }
}

beforeEach(() => {
  FakeWebSocket.instances = [];
  mic.beginHold.mockClear();
  mic.endHold.mockReset().mockReturnValue(null);
  mic.drainHold.mockReset().mockReturnValue(null);
  mic.abortHold.mockClear();
  store.savePendingVoice.mockClear();
  store.clearPendingVoice.mockClear();
  vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function openSocket(options?: { pipeline?: boolean }) {
  const session = await startStreamSession(() => undefined, options);
  const ws = FakeWebSocket.instances[0];
  ws.emit("open", {});
  return { session, ws };
}

describe("startStreamSession declares its pipeline mode (HS-132-04)", () => {
  it("asks for NO pipeline by default (a speak-to-fill)", async () => {
    const { ws } = await openSocket();

    expect(ws.frames()[0]).toEqual({ type: "start", pipeline: false });
  });

  it("asks for the pipeline when the caller is a delivery surface", async () => {
    const { ws } = await openSocket({ pipeline: true });

    expect(ws.frames()[0]).toEqual({ type: "start", pipeline: true });
  });

  it("surfaces the fired command on the final event, with no text", async () => {
    const events: unknown[] = [];
    const session = await startStreamSession((event) => events.push(event), {
      pipeline: true,
    });
    const ws = FakeWebSocket.instances[0];
    ws.emit("open", {});

    const stopped = session.stop();
    ws.emit("message", {
      data: JSON.stringify({
        type: "final",
        text: "",
        fired: { keyword: "standup", kind: "type_text", preview: "types: ## Standup", ok: true },
      }),
    });

    expect(await stopped).toBe("");
    expect(events).toEqual([
      {
        type: "final",
        text: "",
        fired: {
          keyword: "standup",
          kind: "type_text",
          preview: "types: ## Standup",
          ok: true,
        },
      },
    ]);
  });

  it("declares before any audio and before the end frame", async () => {
    const { session, ws } = await openSocket({ pipeline: false });

    const stopped = session.stop();
    ws.emit("message", {
      data: JSON.stringify({ type: "final", text: "verbatim words" }),
    });

    expect(await stopped).toBe("verbatim words");
    const frames = ws.frames().map((frame) => frame.type);
    expect(frames[0]).toBe("start");
    expect(frames).toEqual(["start", "end"]);
  });
});

/* HS-132-05 — the streaming mic is honest.
   The hold is HELD for the whole capture (the lamp and the level meter told
   the truth only between chunks before), a refusal arrives with the server's
   own names attached, and the audio the socket shipped is retained on this
   device so the Retry the UI promises has something behind it. */
describe("the capture holds the floor for the whole utterance (HS-132-05)", () => {
  it("drains the hold per chunk instead of ending and re-beginning it", async () => {
    mic.drainHold.mockReturnValue(CAPTURED);
    vi.useFakeTimers();
    try {
      const { ws } = await openSocket();

      vi.advanceTimersByTime(1_800); // three chunk ticks

      expect(mic.drainHold).toHaveBeenCalledTimes(3);
      // The lamp lied because each tick suspended the graph: never again.
      expect(mic.endHold).not.toHaveBeenCalled();
      expect(mic.beginHold).toHaveBeenCalledTimes(1);
      expect(mic.abortHold).not.toHaveBeenCalled();
      expect(
        ws.sent.filter((item) => typeof item !== "string"),
      ).toHaveLength(3);
    } finally {
      vi.useRealTimers();
    }
  });

  it("ends the hold exactly once, on stop", async () => {
    mic.endHold.mockReturnValue(CAPTURED);
    const { session, ws } = await openSocket();

    const stopped = session.stop();
    ws.emit("message", { data: JSON.stringify({ type: "final", text: "hi" }) });
    await stopped;

    expect(mic.endHold).toHaveBeenCalledTimes(1);
  });
});

describe("a refusal keeps the server's names (HS-132-05)", () => {
  it("carries reason, failure_category and mic_interval to the consumer", async () => {
    const events: unknown[] = [];
    const session = await startStreamSession((event) => events.push(event));
    const ws = FakeWebSocket.instances[0];
    ws.emit("open", {});

    ws.emit("message", {
      data: JSON.stringify({
        type: "error",
        error: "The microphone session closed.",
        reason: "speech_child_budget_exhausted",
        failure_category: "speech_session_refused",
        mic_interval: "closed",
      }),
    });

    expect(events).toEqual([
      {
        type: "error",
        error: "The microphone session closed.",
        reason: "speech_child_budget_exhausted",
        failure_category: "speech_session_refused",
        mic_interval: "closed",
      },
    ]);
    session.cancel();
  });

  it("never overwrites a named refusal with 'Connection lost.'", async () => {
    const events: { type: string; error?: string }[] = [];
    await startStreamSession((event) => events.push(event));
    const ws = FakeWebSocket.instances[0];
    ws.emit("open", {});

    ws.emit("message", {
      data: JSON.stringify({
        type: "error",
        error: "The microphone session closed.",
        reason: "speech_session_cancelled",
        mic_interval: "closed",
      }),
    });
    ws.close(); // the server always closes right behind its refusal

    expect(events.map((event) => event.error)).toEqual([
      "The microphone session closed.",
    ]);
  });
});

describe("retained audio is real on the streaming path (HS-132-05)", () => {
  it("persists what it sent at the final send, and clears it on a final", async () => {
    mic.drainHold.mockReturnValue(CAPTURED);
    mic.endHold.mockReturnValue(CAPTURED);
    const session = await startStreamSession(() => undefined, {
      retainScope: "desk-ask",
    });
    const ws = FakeWebSocket.instances[0];
    ws.emit("open", {});

    const stopped = session.stop();
    expect(store.savePendingVoice).toHaveBeenCalledTimes(1);
    expect(store.savePendingVoice.mock.calls[0][0]).toBe("desk-ask");
    ws.emit("message", {
      data: JSON.stringify({ type: "final", text: "kept nothing back" }),
    });
    await stopped;

    // The server answered: there is nothing left to retry.
    expect(store.clearPendingVoice).toHaveBeenCalledWith("desk-ask");
    expect(await session.retained()).toBe(false);
  });

  it("keeps the audio when the utterance failed, and says so", async () => {
    mic.drainHold.mockReturnValue(CAPTURED);
    const session = await startStreamSession(() => undefined, {
      retainScope: "desk-ask",
    });
    const ws = FakeWebSocket.instances[0];
    ws.emit("open", {});

    ws.emit("message", {
      data: JSON.stringify({
        type: "error",
        error: "Transcription failed.",
        failure_category: "transcription_failed",
      }),
    });

    expect(await session.retained()).toBe(true);
    expect(store.savePendingVoice).toHaveBeenCalledWith(
      "desk-ask",
      expect.any(ArrayBuffer),
    );
    expect(store.clearPendingVoice).not.toHaveBeenCalled();
  });

  it("retains nothing past the store's 16 MB cap, and claims nothing", async () => {
    // ~8 minutes of 16 kHz mono 16-bit is where BOTH pendingVoice's store and
    // /api/dictation/transcribe stop accepting audio (16_000_000 bytes).
    // Retaining more would be a Retry button that 413s.
    vi.mocked(toWav16kMono).mockReturnValueOnce(new ArrayBuffer(44 + 17_000_000));
    mic.drainHold.mockReturnValue(CAPTURED);
    const session = await startStreamSession(() => undefined, {
      retainScope: "desk-ask",
    });
    const ws = FakeWebSocket.instances[0];
    ws.emit("open", {});

    ws.emit("message", {
      data: JSON.stringify({ type: "error", error: "Transcription failed." }),
    });

    expect(store.savePendingVoice).not.toHaveBeenCalled();
    expect(await session.retained()).toBe(false);
  });

  it("retains nothing, and claims nothing, without a scope", async () => {
    mic.drainHold.mockReturnValue(CAPTURED);
    const session = await startStreamSession(() => undefined);
    const ws = FakeWebSocket.instances[0];
    ws.emit("open", {});

    ws.emit("message", {
      data: JSON.stringify({ type: "error", error: "Transcription failed." }),
    });

    expect(store.savePendingVoice).not.toHaveBeenCalled();
    expect(await session.retained()).toBe(false);
  });
});
