// A window that reads its own data follows the bus: one quiet reload after a
// `desk_changed` burst, and nothing without a bus.
import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const bus = vi.hoisted(() => ({
  handlers: new Set<(frame: unknown) => void>(),
  present: true,
}));

vi.mock("../runtime/RuntimeBus", () => {
  const value = {
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      if (type !== "desk_changed") return () => undefined;
      bus.handlers.add(handler);
      return () => bus.handlers.delete(handler);
    },
  };
  return {
    useRuntimeBus: () => {
      if (!bus.present) throw new Error("useRuntimeBus must be used inside RuntimeBusProvider");
      return value;
    },
  };
});

import { DESK_CHANGED_DEBOUNCE_MS, useOnDeskChanged } from "./useDeskChangedRefresh";

function Window({ reload }: { reload: () => void }) {
  useOnDeskChanged(reload);
  return null;
}

const frame = () => bus.handlers.forEach((handler) => handler({ type: "desk_changed", data: {} }));

describe("useOnDeskChanged", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    bus.handlers.clear();
    bus.present = true;
  });
  afterEach(() => vi.useRealTimers());

  it("reloads once after a burst of frames", () => {
    const reload = vi.fn();
    render(<Window reload={reload} />);
    act(() => { frame(); frame(); frame(); });
    expect(reload).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS); });
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("reloads while frames keep coming (20 frames 250 ms apart)", () => {
    const reload = vi.fn();
    render(<Window reload={reload} />);
    act(() => {
      for (let i = 0; i < 20; i += 1) {
        frame();
        vi.advanceTimersByTime(250);
      }
    });
    expect(reload.mock.calls.length).toBeGreaterThanOrEqual(3);
  });

  it("calls the newest reload and keeps one subscription", () => {
    const first = vi.fn();
    const second = vi.fn();
    const { rerender } = render(<Window reload={first} />);
    rerender(<Window reload={second} />);
    expect(bus.handlers.size).toBe(1);
    act(() => { frame(); vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS); });
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledTimes(1);
  });

  it("stops at unmount and does nothing without a bus", () => {
    const reload = vi.fn();
    const { unmount } = render(<Window reload={reload} />);
    act(() => { frame(); });
    unmount();
    act(() => { vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS); });
    expect(reload).not.toHaveBeenCalled();
    expect(bus.handlers.size).toBe(0);

    bus.present = false;
    render(<Window reload={reload} />);
    expect(bus.handlers.size).toBe(0);
  });
});
