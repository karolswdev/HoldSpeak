// HS-95-05 — one mic authority (Constitution, Article IV.3): a second
// capture takes the microphone over and the first is torn down — never
// two live captures.
import { afterEach, describe, expect, it, vi } from "vitest";
import { cancelCapture, startCapture } from "../speakToFill";

function fakeStream() {
  const track = { stop: vi.fn() };
  return {
    stream: { getTracks: () => [track] } as unknown as MediaStream,
    track,
  };
}

function fakeAudioContext() {
  return {
    sampleRate: 16000,
    createMediaStreamSource: () => ({ connect: vi.fn(), disconnect: vi.fn() }),
    createScriptProcessor: () => ({
      connect: vi.fn(),
      disconnect: vi.fn(),
      set onaudioprocess(_h: unknown) {},
    }),
    destination: {},
    close: () => Promise.resolve(),
  } as unknown as AudioContext;
}

describe("speak-to-fill mic arbitration", () => {
  afterEach(async () => {
    await cancelCapture();
    vi.unstubAllGlobals();
  });

  it("a second start takes over and stops the first capture's tracks", async () => {
    const first = fakeStream();
    const second = fakeStream();
    const getUserMedia = vi
      .fn()
      .mockResolvedValueOnce(first.stream)
      .mockResolvedValueOnce(second.stream);
    vi.stubGlobal("navigator", {
      mediaDevices: { getUserMedia },
    });
    vi.stubGlobal("AudioContext", vi.fn(fakeAudioContext));

    await startCapture();
    expect(first.track.stop).not.toHaveBeenCalled();
    await startCapture();
    // The first owner lost the mic the moment the second took it.
    expect(first.track.stop).toHaveBeenCalled();
    expect(second.track.stop).not.toHaveBeenCalled();
    expect(getUserMedia).toHaveBeenCalledTimes(2);
  });
});
