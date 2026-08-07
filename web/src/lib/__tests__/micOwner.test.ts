// HS-95-05 — one mic authority (Constitution, Article IV.3): never two
// live captures.
//
// HS-112-06 changed HOW that holds. The rule used to be enforced by
// takeover — a second `startCapture` tore the first stream down. Now
// there is only ever ONE stream on the Desk (lib/micSession): a second
// start joins the session it already has, so two live captures are
// impossible by construction and the microphone is requested once.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cancelCapture, startCapture, stopAndTranscribe } from "../speakToFill";
import { closeMicSession } from "../micSession";

vi.mock("../api", () => ({
  apiFetch: vi.fn().mockResolvedValue({}),
  apiBlob: vi.fn(),
}));

function fakeStream() {
  const track = { enabled: true, readyState: "live", stop: vi.fn() };
  return {
    stream: {
      getTracks: () => [track],
      getAudioTracks: () => [track],
    } as unknown as MediaStream,
    track,
  };
}

class FakeAudioContext {
  sampleRate = 16000;
  destination = {};
  audioWorklet = { addModule: async () => undefined };
  createMediaStreamSource = () => ({ connect: vi.fn(), disconnect: vi.fn() });
  createScriptProcessor = () => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    onaudioprocess: null,
  });
  suspend = async () => undefined;
  resume = async () => undefined;
  close = async () => undefined;
}

class FakeWorkletNode {
  port: { onmessage: ((event: { data: Float32Array }) => void) | null } = {
    onmessage: null,
  };
  connect = vi.fn();
  disconnect = vi.fn();
}

describe("speak-to-fill mic arbitration", () => {
  beforeEach(() => {
    Object.assign(URL, {
      createObjectURL: () => "blob:holdspeak-capture",
      revokeObjectURL: () => undefined,
    });
  });

  afterEach(() => {
    closeMicSession();
    vi.unstubAllGlobals();
  });

  it("a second start joins the one session — one grant, never two streams", async () => {
    const first = fakeStream();
    const second = fakeStream();
    const getUserMedia = vi
      .fn()
      .mockResolvedValueOnce(first.stream)
      .mockResolvedValueOnce(second.stream);
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });
    vi.stubGlobal("AudioContext", FakeAudioContext);
    vi.stubGlobal("AudioWorkletNode", FakeWorkletNode);

    await startCapture();
    await startCapture();
    // The second capture never opened a second device.
    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(second.track.stop).not.toHaveBeenCalled();
    expect(first.track.readyState).toBe("live");

    await cancelCapture();
    // …and the grant survives the release for the next utterance.
    expect(first.track.stop).not.toHaveBeenCalled();
    expect(first.track.enabled).toBe(false);
  });

  it("a hold with nothing captured transcribes nothing", async () => {
    const only = fakeStream();
    const getUserMedia = vi.fn().mockResolvedValue(only.stream);
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });
    vi.stubGlobal("AudioContext", FakeAudioContext);
    vi.stubGlobal("AudioWorkletNode", FakeWorkletNode);

    await startCapture();
    expect(await stopAndTranscribe()).toBe("");
  });
});
