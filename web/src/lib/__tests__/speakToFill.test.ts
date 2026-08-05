// HS-118-08 -- transcribeWav sends pipeline=true by default.
//
// Pinned behaviour: the browser mic path requests the full dictation
// pipeline (corrections, learning, journaling) by default. The
// pipeline=false path is unchanged (backward compatible).
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock the api module before importing speakToFill
const mockApiFetch = vi.fn();
vi.mock("../api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

// Mock micSession to avoid real AudioContext usage
vi.mock("../micSession", () => ({
  beginHold: vi.fn().mockResolvedValue(undefined),
  endHold: vi.fn().mockReturnValue(null),
  abortHold: vi.fn(),
  micCaptureReason: vi.fn().mockReturnValue(null),
  micCaptureSupported: vi.fn().mockReturnValue(true),
  subscribeCaptureLevel: vi.fn().mockReturnValue(() => {}),
}));

// Mock pendingVoice
vi.mock("../pendingVoice", () => ({
  clearPendingVoice: vi.fn().mockResolvedValue(undefined),
  loadPendingVoice: vi.fn().mockResolvedValue(null),
  savePendingVoice: vi.fn().mockResolvedValue(undefined),
}));

import { transcribeWav } from "../speakToFill";

// Minimal WAV header for a 16 kHz mono 16-bit PCM file with 0 samples.
function emptyWav(): ArrayBuffer {
  const buffer = new ArrayBuffer(44);
  const view = new DataView(buffer);
  const word = (at: number, value: string) =>
    [...value].forEach((c, i) => view.setUint8(at + i, c.charCodeAt(0)));
  word(0, "RIFF");
  view.setUint32(4, 36, true);
  word(8, "WAVE");
  word(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, 16_000, true);
  view.setUint32(28, 32_000, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  word(36, "data");
  view.setUint32(40, 0, true);
  return buffer;
}

describe("transcribeWav", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
    mockApiFetch.mockResolvedValue({ success: true, text: "hello" });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends pipeline=true by default", async () => {
    const audio = emptyWav();
    await transcribeWav(audio);

    expect(mockApiFetch).toHaveBeenCalledTimes(1);
    const [url] = mockApiFetch.mock.calls[0];
    expect(url).toBe("/api/dictation/transcribe?pipeline=true");
  });

  it("sends pipeline=true when explicitly set", async () => {
    const audio = emptyWav();
    await transcribeWav(audio, { pipeline: true });

    const [url] = mockApiFetch.mock.calls[0];
    expect(url).toBe("/api/dictation/transcribe?pipeline=true");
  });

  it("sends without pipeline param when pipeline=false", async () => {
    const audio = emptyWav();
    await transcribeWav(audio, { pipeline: false });

    const [url] = mockApiFetch.mock.calls[0];
    expect(url).toBe("/api/dictation/transcribe");
  });

  it("returns the text field from the response", async () => {
    mockApiFetch.mockResolvedValue({
      success: true,
      text: "corrected text",
      raw: "raw text",
    });

    const result = await transcribeWav(emptyWav());
    expect(result).toBe("corrected text");
  });

  it("returns empty string when text is absent", async () => {
    mockApiFetch.mockResolvedValue({ success: true });

    const result = await transcribeWav(emptyWav());
    expect(result).toBe("");
  });

  it("sends audio as the request body with octet-stream content type", async () => {
    const audio = emptyWav();
    await transcribeWav(audio);

    const [, init] = mockApiFetch.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(init.headers["Content-Type"]).toBe("application/octet-stream");
    expect(init.body).toBe(audio);
  });
});
