// HS-112-06 — ONE grant, ONE stream, and an OFF that is real.
//
// The invariants the owner asked for, pinned at the module level: the
// Desk asks the browser for the microphone once and never re-requests
// it (call-count on getUserMedia); between utterances the session is
// suspended, not torn down; a push-to-talk hold takes the floor from
// the open mic; and CLOSED means `MediaStreamTrack.stop()` was called —
// verified on track state, never on a lamp.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  IDLE_RELEASE_MS,
  abortHold,
  beginHold,
  closeMicSession,
  endHold,
  micCaptureReason,
  micCaptureSupported,
  micPhase,
  micSessionLive,
  startOpenMic,
  stopOpenMic,
  subscribeCaptureLevel,
} from "../micSession";

const RATE = 16_000;
const FRAME = 1024;

type FakeTrack = {
  enabled: boolean;
  readyState: string;
  stop: ReturnType<typeof vi.fn>;
};

const workletNodes: FakeWorkletNode[] = [];

class FakeWorkletNode {
  port: { onmessage: ((event: { data: Float32Array }) => void) | null } = {
    onmessage: null,
  };
  connect = vi.fn();
  disconnect = vi.fn();
  constructor() {
    workletNodes.push(this);
  }
}

class FakeAudioContext {
  sampleRate = RATE;
  state = "running";
  destination = {};
  audioWorklet = { addModule: vi.fn(async () => undefined) };
  createMediaStreamSource = vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
  }));
  createScriptProcessor = vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    onaudioprocess: null,
  }));
  suspend = vi.fn(async () => {
    this.state = "suspended";
  });
  resume = vi.fn(async () => {
    this.state = "running";
  });
  close = vi.fn(async () => {
    this.state = "closed";
  });
}

class TrackedContext extends FakeAudioContext {
  constructor() {
    super();
    contexts.push(this);
  }
}

/** A browser (or a jsdom) with no AudioWorklet at all. */
class WorkletlessContext extends TrackedContext {
  audioWorklet = undefined as unknown as FakeAudioContext["audioWorklet"];
}

const contexts: FakeAudioContext[] = [];
const tracks: FakeTrack[] = [];
let getUserMedia: ReturnType<typeof vi.fn>;

function makeStream(): MediaStream {
  const track: FakeTrack = {
    enabled: true,
    readyState: "live",
    stop: vi.fn(function stop(this: void) {
      track.readyState = "ended";
    }),
  };
  tracks.push(track);
  return {
    getTracks: () => [track],
    getAudioTracks: () => [track],
  } as unknown as MediaStream;
}

/** One frame at a given RMS, as the worklet would post it. */
function frame(rms: number): Float32Array {
  const samples = new Float32Array(FRAME);
  for (let index = 0; index < FRAME; index += 1)
    samples[index] = index % 2 ? rms : -rms;
  return samples;
}

/** Push frames through the live worklet node — the real audio path. */
function speak(rms: number, count: number): void {
  const node = workletNodes[workletNodes.length - 1];
  for (let index = 0; index < count; index += 1)
    node.port.onmessage?.({ data: frame(rms) });
}

const LOUD = 0.2;
const QUIET = 0.001;

beforeEach(() => {
  workletNodes.length = 0;
  contexts.length = 0;
  tracks.length = 0;
  getUserMedia = vi.fn(async () => makeStream());
  vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });
  vi.stubGlobal("AudioContext", TrackedContext);
  vi.stubGlobal("AudioWorkletNode", FakeWorkletNode);
  Object.assign(URL, {
    createObjectURL: () => "blob:holdspeak-capture",
    revokeObjectURL: () => undefined,
  });
});

afterEach(() => {
  closeMicSession();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("one grant, one stream (HS-112-06)", () => {
  it("asks for the microphone ONCE across many utterances", async () => {
    for (let utterance = 0; utterance < 5; utterance += 1) {
      await beginHold();
      speak(LOUD, 3);
      expect(endHold()).toBeTruthy();
    }
    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(tracks).toHaveLength(1);
    expect(tracks[0].stop).not.toHaveBeenCalled();
  });

  it("suspends between utterances instead of tearing the device down", async () => {
    await beginHold();
    endHold();
    expect(micPhase()).toBe("suspended");
    expect(contexts[0].suspend).toHaveBeenCalled();
    expect(tracks[0].enabled).toBe(false);
    expect(tracks[0].readyState).toBe("live");

    await beginHold();
    expect(contexts[0].resume).toHaveBeenCalled();
    expect(tracks[0].enabled).toBe(true);
    expect(getUserMedia).toHaveBeenCalledTimes(1);
  });

  it("runs on an AudioWorklet, never the deprecated ScriptProcessor", async () => {
    await beginHold();
    expect(contexts[0].audioWorklet.addModule).toHaveBeenCalled();
    expect(contexts[0].createScriptProcessor).not.toHaveBeenCalled();
    expect(workletNodes).toHaveLength(1);
  });

  it("refuses where AudioWorklet is absent — no deprecated fallback", async () => {
    closeMicSession();
    vi.stubGlobal("AudioWorkletNode", undefined);
    vi.stubGlobal("AudioContext", WorkletlessContext);
    // the browser is honestly unsupported, and it says so before opening.
    expect(micCaptureSupported()).toBe(false);
    expect(micCaptureReason()).toBe(
      "This browser cannot capture microphone audio.",
    );
    await expect(beginHold()).rejects.toThrow(/cannot capture/);
    expect(micSessionLive()).toBe(false);
  });

  it("closing stops the tracks for real — CLOSED is not muted", async () => {
    await beginHold();
    endHold();
    expect(micSessionLive()).toBe(true);
    closeMicSession();
    expect(tracks[0].stop).toHaveBeenCalled();
    expect(tracks[0].readyState).toBe("ended");
    expect(micPhase()).toBe("closed");
    expect(micSessionLive()).toBe(false);
  });

  it("releases the device when the pause outlasts the idle window", async () => {
    vi.useFakeTimers();
    await beginHold();
    endHold();
    expect(tracks[0].stop).not.toHaveBeenCalled();
    vi.advanceTimersByTime(IDLE_RELEASE_MS + 1);
    expect(tracks[0].stop).toHaveBeenCalled();
    expect(micPhase()).toBe("closed");
  });

  it("reports the capture level from the one frame path", async () => {
    const levels: number[] = [];
    const stop = subscribeCaptureLevel((level) => levels.push(level));
    await beginHold();
    speak(LOUD, 1);
    expect(levels[0]).toBeCloseTo(0.8, 3);
    endHold();
    expect(levels[levels.length - 1]).toBe(0);
    stop();
  });
});

describe("the open mic (HS-112-06)", () => {
  it("segments continuous audio into utterances with no key touched", async () => {
    const segments: { chunks: Float32Array[]; rate: number }[] = [];
    await startOpenMic((segment) => segments.push(segment));
    expect(micPhase()).toBe("open");

    speak(LOUD, 8);
    expect(micPhase()).toBe("segmenting");
    speak(QUIET, 12);
    speak(LOUD, 8);
    speak(QUIET, 12);

    expect(segments).toHaveLength(2);
    expect(segments[0].rate).toBe(RATE);
    expect(micPhase()).toBe("open");
    expect(getUserMedia).toHaveBeenCalledTimes(1);
  });

  it("a hold takes the floor: the open mic captures nothing while held", async () => {
    const segments: unknown[] = [];
    await startOpenMic((segment) => segments.push(segment));
    speak(LOUD, 4); // mid-utterance when the key goes down

    await beginHold();
    expect(micPhase()).toBe("held");
    speak(LOUD, 8);
    speak(QUIET, 12);
    // every frame went to the hold; the open mic delivered nothing.
    expect(segments).toHaveLength(0);
    const captured = endHold();
    expect(captured?.chunks).toHaveLength(20);
    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(micPhase()).toBe("open");

    // and the open mic is listening again the moment the key comes up.
    speak(LOUD, 8);
    speak(QUIET, 12);
    expect(segments).toHaveLength(1);
  });

  it("a cancelled hold hands the floor back without dropping the grant", async () => {
    const segments: unknown[] = [];
    await startOpenMic((segment) => segments.push(segment));
    await beginHold();
    abortHold();
    expect(micPhase()).toBe("open");
    speak(LOUD, 8);
    speak(QUIET, 12);
    expect(segments).toHaveLength(1);
    expect(getUserMedia).toHaveBeenCalledTimes(1);
  });

  it("one verb drops the stream entirely", async () => {
    await startOpenMic(() => undefined);
    stopOpenMic();
    expect(tracks[0].stop).toHaveBeenCalled();
    expect(micPhase()).toBe("closed");
    expect(micSessionLive()).toBe(false);
  });

  it("dropping the open mic mid-hold keeps the hold's own capture", async () => {
    await startOpenMic(() => undefined);
    await beginHold();
    stopOpenMic();
    expect(micPhase()).toBe("held");
    expect(tracks[0].stop).not.toHaveBeenCalled();
    speak(LOUD, 2);
    expect(endHold()?.chunks).toHaveLength(2);
  });

  it("refuses honestly when the browser withholds the microphone", async () => {
    closeMicSession();
    getUserMedia.mockRejectedValueOnce(new Error("Permission denied"));
    await expect(startOpenMic(() => undefined)).rejects.toThrow(
      /Permission denied/,
    );
    expect(micPhase()).toBe("closed");
    expect(micSessionLive()).toBe(false);
  });
});
