import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useUndoReceipt } from "../useUndoReceipt";

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("useUndoReceipt", () => {
  it("starts idle with no receipt", () => {
    const { result } = renderHook(() => useUndoReceipt());
    expect(result.current.phase).toBe("idle");
    expect(result.current.receipt).toBeNull();
  });

  it("fires the action after the window expires", () => {
    vi.useFakeTimers();
    const fire = vi.fn();
    const revert = vi.fn();
    const { result } = renderHook(() => useUndoReceipt(3));

    act(() => result.current.remove("item", fire, revert));
    expect(result.current.phase).toBe("pending");
    expect(result.current.receipt).not.toBeNull();
    expect(fire).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(3500));
    expect(fire).toHaveBeenCalledTimes(1);
    expect(result.current.phase).toBe("committed");
  });

  it("reverts on undo click before expiry", () => {
    vi.useFakeTimers();
    const fire = vi.fn();
    const revert = vi.fn();
    const { result } = renderHook(() => useUndoReceipt(8));

    act(() => result.current.remove("item", fire, revert));
    expect(result.current.phase).toBe("pending");

    act(() => result.current.undo());
    expect(revert).toHaveBeenCalledTimes(1);
    expect(fire).not.toHaveBeenCalled();
    expect(result.current.phase).toBe("restored");
  });

  it("clears receipt after restored delay", () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useUndoReceipt(8));

    act(() => result.current.remove("item", vi.fn(), vi.fn()));
    act(() => result.current.undo());
    expect(result.current.phase).toBe("restored");

    act(() => vi.advanceTimersByTime(1600));
    expect(result.current.receipt).toBeNull();
    expect(result.current.phase).toBe("idle");
  });

  it("countdown decrements remaining seconds", () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useUndoReceipt(4));

    act(() => result.current.remove("item", vi.fn(), vi.fn()));
    expect(result.current.phase).toBe("pending");

    act(() => vi.advanceTimersByTime(1250));
    expect(result.current.phase).toBe("pending");
  });

  it("undo is a no-op when not in pending phase", () => {
    const revert = vi.fn();
    const { result } = renderHook(() => useUndoReceipt());
    act(() => result.current.undo());
    expect(revert).not.toHaveBeenCalled();
  });
});
