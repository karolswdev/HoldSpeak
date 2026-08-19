import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest } from "../../../lib/api";
import { currentWriteFailure, clearWriteFailure } from "../../hooks/useWriteReceipt";
import { createRecordingSlice } from "../recordingSlice";
import type { DeskState } from "../types";

vi.mock("../../../lib/api", () => ({ apiRequest: vi.fn() }));

const request = vi.mocked(apiRequest);

function makeSlice() {
  const state: Record<string, unknown> = {
    items: { meeting: [] },
    refresh: vi.fn().mockResolvedValue(undefined),
  };
  const set = (partial: Partial<DeskState> | ((s: DeskState) => Partial<DeskState>)) => {
    Object.assign(
      state,
      typeof partial === "function"
        ? partial(state as unknown as DeskState)
        : partial,
    );
  };
  const get = () => state as unknown as DeskState;
  Object.assign(
    state,
    createRecordingSlice(set, get, { setState: set, getState: get } as never),
  );
  return state as unknown as ReturnType<typeof createRecordingSlice> & {
    refresh: ReturnType<typeof vi.fn>;
  };
}

describe("recordingSlice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearWriteFailure();
  });

  it("leaves a refused stop retryable, then idles only after the retry lands", async () => {
    request.mockRejectedValueOnce(new TypeError("offline")).mockResolvedValueOnce({});
    const state = makeSlice();
    (state as unknown as { recording: string }).recording = "recording";

    await state.stopRecording();

    expect(state.recording).toBe("recording");
    expect(state.refresh).not.toHaveBeenCalled();
    const refusal = currentWriteFailure();
    expect(refusal?.verb).toBe("STOP RECORDING");
    expect(refusal?.retry).toEqual(expect.any(Function));

    refusal?.retry?.();
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    expect(request).toHaveBeenCalledTimes(2);
    expect(state.recording).toBe("idle");
    expect(state.refresh).toHaveBeenCalledOnce();
  });

  it("returns a refused start to idle and retries the same start into recording", async () => {
    request.mockRejectedValueOnce(new TypeError("offline")).mockResolvedValueOnce({});
    const state = makeSlice();

    await state.startRecording();

    expect(state.recording).toBe("idle");
    const refusal = currentWriteFailure();
    expect(refusal?.verb).toBe("START RECORDING");
    expect(refusal?.retry).toEqual(expect.any(Function));

    refusal?.retry?.();
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    expect(request).toHaveBeenCalledTimes(2);
    expect(state.recording).toBe("recording");
  });
});
