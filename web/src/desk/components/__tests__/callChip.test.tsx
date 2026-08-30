// HS-154-03 -- CallChip renders all four states; click stops.
//
// The chip is the ONE visible call-mode indicator. This test proves:
// 1. All four visual states render (off / listening / thinking / speaking).
// 2. Click in any non-OFF state -> OFF, tts.stop spy, loop stop spy.
// 3. Click when OFF -> starts (patchThread call_mode=1).
// 4. Hydration: callMode=1 with no streaming/tts -> LISTENING.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, act } from "@testing-library/react";

// ---- mocks (must come before component import) ----

const mockPatchThread = vi.fn().mockResolvedValue({});
vi.mock("../../threads", () => ({
  patchThread: (...args: unknown[]) => mockPatchThread(...args),
}));

// TTS mock
let ttsStateCallback: ((s: string) => void) | null = null;
const mockTtsStop = vi.fn();
vi.mock("../../../lib/tts", () => ({
  onStateChange: (cb: (s: string) => void) => {
    ttsStateCallback = cb;
    return () => { ttsStateCallback = null; };
  },
  stop: (...args: unknown[]) => mockTtsStop(...args),
}));

// Call loop wiring mock
const mockLoopStart = vi.fn().mockResolvedValue(undefined);
const mockLoopStop = vi.fn();
vi.mock("../../callLoopWiring", () => ({
  wireCallLoop: () => ({
    start: () => mockLoopStart(),
    stop: () => mockLoopStop(),
    state: () => "idle",
  }),
}));

import { CallChip } from "../CallChip";

// ---- test suite ----

describe("CallChip", () => {
  const THREAD_ID = "th_chip_test";
  const onReload = vi.fn();

  beforeEach(() => {
    mockPatchThread.mockClear();
    mockTtsStop.mockClear();
    mockLoopStart.mockClear();
    mockLoopStop.mockClear();
    onReload.mockClear();
    ttsStateCallback = null;
  });

  afterEach(() => {
    cleanup();
  });

  it("renders OFF when callMode=0", () => {
    render(<CallChip threadId={THREAD_ID} callMode={0} isStreaming={false} />);
    const chip = screen.getByTestId("call-chip");
    expect(chip.getAttribute("data-call-state")).toBe("off");
    expect(chip.textContent).toBe("CALL");
  });

  it("renders LISTENING when callMode=1, no streaming, tts idle", () => {
    render(<CallChip threadId={THREAD_ID} callMode={1} isStreaming={false} />);
    const chip = screen.getByTestId("call-chip");
    expect(chip.getAttribute("data-call-state")).toBe("listening");
    expect(chip.textContent).toBe("LISTENING");
  });

  it("renders THINKING when callMode=1 and isStreaming=true", () => {
    render(<CallChip threadId={THREAD_ID} callMode={1} isStreaming={true} />);
    const chip = screen.getByTestId("call-chip");
    expect(chip.getAttribute("data-call-state")).toBe("thinking");
    expect(chip.textContent).toBe("THINKING");
  });

  it("renders SPEAKING when callMode=1 and tts is speaking", () => {
    render(<CallChip threadId={THREAD_ID} callMode={1} isStreaming={false} />);
    // Simulate TTS speaking
    act(() => {
      ttsStateCallback?.("speaking");
    });
    const chip = screen.getByTestId("call-chip");
    expect(chip.getAttribute("data-call-state")).toBe("speaking");
    expect(chip.textContent).toBe("SPEAKING");
  });

  it("click in LISTENING stops everything and patches call_mode=0", () => {
    render(
      <CallChip threadId={THREAD_ID} callMode={1} isStreaming={false} onReload={onReload} />,
    );
    const chip = screen.getByTestId("call-chip");
    fireEvent.click(chip);

    expect(mockTtsStop).toHaveBeenCalled();
    expect(mockLoopStop).toHaveBeenCalled();
    expect(mockPatchThread).toHaveBeenCalledWith(THREAD_ID, { call_mode: 0 });
  });

  it("click in THINKING stops everything", () => {
    render(
      <CallChip threadId={THREAD_ID} callMode={1} isStreaming={true} onReload={onReload} />,
    );
    const chip = screen.getByTestId("call-chip");
    fireEvent.click(chip);

    expect(mockTtsStop).toHaveBeenCalled();
    expect(mockLoopStop).toHaveBeenCalled();
    expect(mockPatchThread).toHaveBeenCalledWith(THREAD_ID, { call_mode: 0 });
  });

  it("click in SPEAKING stops everything", () => {
    render(
      <CallChip threadId={THREAD_ID} callMode={1} isStreaming={false} onReload={onReload} />,
    );
    // Simulate TTS speaking
    act(() => {
      ttsStateCallback?.("speaking");
    });
    const chip = screen.getByTestId("call-chip");
    fireEvent.click(chip);

    expect(mockTtsStop).toHaveBeenCalled();
    expect(mockLoopStop).toHaveBeenCalled();
    expect(mockPatchThread).toHaveBeenCalledWith(THREAD_ID, { call_mode: 0 });
  });

  it("click in OFF patches call_mode=1 (start)", () => {
    render(
      <CallChip threadId={THREAD_ID} callMode={0} isStreaming={false} onReload={onReload} />,
    );
    const chip = screen.getByTestId("call-chip");
    fireEvent.click(chip);

    expect(mockPatchThread).toHaveBeenCalledWith(THREAD_ID, { call_mode: 1 });
    // tts.stop and loop.stop should NOT have been called (we're starting, not stopping)
    expect(mockTtsStop).not.toHaveBeenCalled();
  });

  it("is keyboard reachable (Enter toggles)", () => {
    render(
      <CallChip threadId={THREAD_ID} callMode={1} isStreaming={false} onReload={onReload} />,
    );
    const chip = screen.getByTestId("call-chip");
    expect(chip.getAttribute("tabindex")).toBe("0");
    fireEvent.keyDown(chip, { key: "Enter" });
    expect(mockPatchThread).toHaveBeenCalledWith(THREAD_ID, { call_mode: 0 });
  });

  it("is keyboard reachable (Space toggles)", () => {
    render(
      <CallChip threadId={THREAD_ID} callMode={0} isStreaming={false} onReload={onReload} />,
    );
    const chip = screen.getByTestId("call-chip");
    fireEvent.keyDown(chip, { key: " " });
    expect(mockPatchThread).toHaveBeenCalledWith(THREAD_ID, { call_mode: 1 });
  });

  it("hydration: callMode=1 on mount starts the loop", async () => {
    render(
      <CallChip threadId={THREAD_ID} callMode={1} isStreaming={false} />,
    );
    // The useEffect should have started the loop
    // Wait for the async effect
    await vi.waitFor(() => {
      expect(mockLoopStart).toHaveBeenCalled();
    });
  });
});
