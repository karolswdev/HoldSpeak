// HS-154-04 — autoSpeak unit tests.
//
// - Streaming deltas produce sentence-boundary enqueues BEFORE turn_done
// - Barge-in stops and blocks further enqueues for that turn
// - Auto-speak fires only when call mode is ON
// - Replay works with call OFF
// - No double-speak: auto-spoken turns are not re-spoken
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";

// ---- mock the TTS seam ----
//
// autoSpeak.ts calls onStateChange at module top level, so the mock
// factory runs before any `let`/`const` in this file is initialized.
// vi.hoisted() lifts the declaration above the mock factory.

const {
  _tts, mockEnqueueSentence, mockStop, mockSpeak,
} = vi.hoisted(() => ({
  _tts: { callback: null as ((s: string) => void) | null },
  mockEnqueueSentence: vi.fn(),
  mockStop: vi.fn(),
  mockSpeak: vi.fn(),
}));

vi.mock("../../lib/tts", () => ({
  enqueueSentence: (...args: unknown[]) => mockEnqueueSentence(...args),
  stop: (...args: unknown[]) => mockStop(...args),
  speak: (...args: unknown[]) => mockSpeak(...args),
  onStateChange: (cb: (s: string) => void) => {
    _tts.callback = cb;
    return () => { _tts.callback = null; };
  },
}));

import {
  feedDelta,
  flushTurn,
  setCallActive,
  bargeIn,
  wasAutoSpoken,
  replayMessage,
  stopReplay,
  getActiveSpeakerId,
  isCallActive,
  _resetForTest,
  _getBuffer,
  _splitSentences,
} from "../autoSpeak";

// ---- setup ----

beforeEach(() => {
  _resetForTest();
  mockEnqueueSentence.mockClear();
  mockStop.mockClear();
  mockSpeak.mockClear();
});

afterEach(() => {
  _resetForTest();
});

// ---- sentence boundary splitting ----

describe("_splitSentences", () => {
  it("splits on period + space", () => {
    const [sentences, rest] = _splitSentences(
      "This is a long enough sentence. And more text here",
    );
    expect(sentences).toEqual(["This is a long enough sentence."]);
    expect(rest).toBe("And more text here");
  });

  it("splits on exclamation + space", () => {
    const [sentences, rest] = _splitSentences(
      "This is exciting enough text! More follows",
    );
    expect(sentences).toEqual(["This is exciting enough text!"]);
    expect(rest).toBe("More follows");
  });

  it("splits on question mark + space", () => {
    const [sentences, rest] = _splitSentences(
      "Is this long enough for us? Yes it is",
    );
    expect(sentences).toEqual(["Is this long enough for us?"]);
    expect(rest).toBe("Yes it is");
  });

  it("does NOT split short fragments (min length floor)", () => {
    const [sentences, rest] = _splitSentences("Hi. More text");
    expect(sentences).toEqual([]);
    expect(rest).toBe("Hi. More text");
  });

  it("splits multiple sentences", () => {
    const text =
      "First sentence is long enough. Second sentence is also long. Tail";
    const [sentences, rest] = _splitSentences(text);
    expect(sentences).toEqual([
      "First sentence is long enough.",
      "Second sentence is also long.",
    ]);
    expect(rest).toBe("Tail");
  });

  it("returns empty array when no boundary found", () => {
    const [sentences, rest] = _splitSentences("no boundary here yet");
    expect(sentences).toEqual([]);
    expect(rest).toBe("no boundary here yet");
  });
});

// ---- auto-speak (call mode ON) ----

describe("feedDelta + flushTurn", () => {
  it("enqueues sentences BEFORE turn_done", () => {
    setCallActive(true);

    // Simulate streaming deltas
    feedDelta("msg-1", "This is a sentence that is ");
    feedDelta("msg-1", "long enough to pass. ");
    feedDelta("msg-1", "And here is the tail");

    // The first sentence should have been enqueued before turn_done
    expect(mockEnqueueSentence).toHaveBeenCalledTimes(1);
    expect(mockEnqueueSentence).toHaveBeenCalledWith(
      "This is a sentence that is long enough to pass.",
    );

    // The tail should still be in the buffer
    expect(_getBuffer()).toBe("And here is the tail");

    // Now flush at turn_done
    flushTurn("msg-1");
    expect(mockEnqueueSentence).toHaveBeenCalledTimes(2);
    expect(mockEnqueueSentence).toHaveBeenCalledWith(
      "And here is the tail",
    );
  });

  it("enqueues multiple sentences from deltas", () => {
    setCallActive(true);

    feedDelta(
      "msg-1",
      "First sentence is long enough. Second sentence is also long enough. Tail",
    );

    expect(mockEnqueueSentence).toHaveBeenCalledTimes(2);
    expect(mockEnqueueSentence).toHaveBeenNthCalledWith(
      1,
      "First sentence is long enough.",
    );
    expect(mockEnqueueSentence).toHaveBeenNthCalledWith(
      2,
      "Second sentence is also long enough.",
    );

    expect(_getBuffer()).toBe("Tail");
  });

  it("marks turn as auto-spoken", () => {
    setCallActive(true);

    feedDelta("msg-1", "A sentence that is long enough. ");
    expect(wasAutoSpoken("msg-1")).toBe(true);
    expect(wasAutoSpoken("msg-2")).toBe(false);
  });

  it("sets activeSpeakerId during auto-speak", () => {
    setCallActive(true);

    feedDelta("msg-1", "Sentence that is long enough to go. ");
    expect(getActiveSpeakerId()).toBe("msg-1");
  });
});

// ---- call mode gate ----

describe("call mode gate", () => {
  it("does NOT enqueue when call mode is OFF", () => {
    setCallActive(false);

    feedDelta("msg-1", "This is a sentence long enough. More");
    expect(mockEnqueueSentence).not.toHaveBeenCalled();
    expect(_getBuffer()).toBe("");
  });

  it("does NOT flush when call mode is OFF", () => {
    setCallActive(false);

    feedDelta("msg-1", "Some text");
    flushTurn("msg-1");
    expect(mockEnqueueSentence).not.toHaveBeenCalled();
  });

  it("stops accumulating when call mode is turned OFF mid-stream", () => {
    setCallActive(true);

    feedDelta("msg-1", "Some text");
    expect(_getBuffer()).toBe("Some text");

    setCallActive(false);
    expect(_getBuffer()).toBe(""); // buffer cleared
  });
});

// ---- barge-in ----

describe("barge-in", () => {
  it("calls stop() and blocks further enqueues for the current turn", () => {
    setCallActive(true);

    feedDelta("msg-1", "Beginning of ");

    // Barge-in
    bargeIn();
    expect(mockStop).toHaveBeenCalled();
    expect(_getBuffer()).toBe("");

    // Further deltas for the same turn are blocked
    mockEnqueueSentence.mockClear();
    feedDelta("msg-1", "More text that is long enough. And more after that.");
    expect(mockEnqueueSentence).not.toHaveBeenCalled();
  });

  it("does NOT block a NEW turn after barge-in", () => {
    setCallActive(true);

    feedDelta("msg-1", "Some text");
    bargeIn();
    mockEnqueueSentence.mockClear();

    // A new message should NOT be blocked
    feedDelta("msg-2", "A new sentence that is long enough. ");
    expect(mockEnqueueSentence).toHaveBeenCalledTimes(1);
  });

  it("clears activeSpeakerId", () => {
    setCallActive(true);

    feedDelta("msg-1", "Sentence that is long enough to go. ");
    expect(getActiveSpeakerId()).toBe("msg-1");

    bargeIn();
    expect(getActiveSpeakerId()).toBeNull();
  });
});

// ---- replay (works with call OFF) ----

describe("replayMessage", () => {
  it("calls speak() with the message text", () => {
    replayMessage("msg-1", "Hello world");
    expect(mockSpeak).toHaveBeenCalledWith("Hello world");
    expect(getActiveSpeakerId()).toBe("msg-1");
  });

  it("works when call mode is OFF", () => {
    setCallActive(false);
    replayMessage("msg-1", "Test replay");
    expect(mockSpeak).toHaveBeenCalledWith("Test replay");
    expect(getActiveSpeakerId()).toBe("msg-1");
  });
});

// ---- stopReplay ----

describe("stopReplay", () => {
  it("calls stop() and clears activeSpeakerId", () => {
    replayMessage("msg-1", "Hello");
    stopReplay();
    expect(mockStop).toHaveBeenCalled();
    expect(getActiveSpeakerId()).toBeNull();
  });
});

// ---- TTS state listener ----

describe("TTS state listener", () => {
  it("clears activeSpeakerId when TTS goes idle", () => {
    replayMessage("msg-1", "Hello");
    expect(getActiveSpeakerId()).toBe("msg-1");

    // Simulate TTS going idle
    _tts.callback?.("idle");
    expect(getActiveSpeakerId()).toBeNull();
  });
});

// ---- isCallActive ----

describe("isCallActive", () => {
  it("reflects the current call-active state", () => {
    expect(isCallActive()).toBe(false);
    setCallActive(true);
    expect(isCallActive()).toBe(true);
    setCallActive(false);
    expect(isCallActive()).toBe(false);
  });
});
