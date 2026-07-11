import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearPendingVoice,
  loadPendingVoice,
  savePendingVoice,
} from "./pendingVoice";

describe("pending voice recovery", () => {
  beforeEach(async () => {
    vi.stubGlobal("indexedDB", undefined);
    await clearPendingVoice("first-words");
  });

  afterEach(() => vi.unstubAllGlobals());

  it("retains a bounded capture until transcription confirms it", async () => {
    const audio = new Uint8Array([82, 73, 70, 70, 1, 2, 3, 4]).buffer;

    await savePendingVoice("first-words", audio);

    expect(
      Array.from(new Uint8Array((await loadPendingVoice("first-words"))!)),
    ).toEqual([82, 73, 70, 70, 1, 2, 3, 4]);
    await clearPendingVoice("first-words");
    expect(await loadPendingVoice("first-words")).toBeNull();
  });

  it("refuses an over-cap capture instead of growing local storage without bound", async () => {
    await savePendingVoice("first-words", new ArrayBuffer(16_000_001));
    expect(await loadPendingVoice("first-words")).toBeNull();
  });
});
