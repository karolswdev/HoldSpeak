import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useUndoReceipt } from "../useUndoReceipt";
import { OUTCOME_LINGER_MS } from "../../linger";

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

  it("keeps the committed receipt for the desk's outcome linger", () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useUndoReceipt(1));
    act(() => result.current.remove("item", vi.fn(), vi.fn()));
    act(() => vi.advanceTimersByTime(1000));
    expect(result.current.phase).toBe("committed");
    act(() => vi.advanceTimersByTime(OUTCOME_LINGER_MS - 1));
    expect(result.current.phase).toBe("committed");
    act(() => vi.advanceTimersByTime(1));
    expect(result.current.receipt).toBeNull();
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

    act(() => vi.advanceTimersByTime(OUTCOME_LINGER_MS - 1));
    expect(result.current.phase).toBe("restored");
    act(() => vi.advanceTimersByTime(1));
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

  // PHILO-8-02 — a removal is never dropped (cause 2 and cause 3).
  it("a second remove commits the first at once and keeps one slot", () => {
    vi.useFakeTimers();
    const fireA = vi.fn();
    const fireB = vi.fn();
    const { result } = renderHook(() => useUndoReceipt(8));

    act(() => result.current.remove("A", fireA, vi.fn()));
    act(() => vi.advanceTimersByTime(1500));
    act(() => result.current.remove("B", fireB, vi.fn()));
    expect(fireA).toHaveBeenCalledTimes(1);
    expect(fireB).not.toHaveBeenCalled();
    expect(result.current.phase).toBe("pending");

    act(() => vi.advanceTimersByTime(8500));
    expect(fireA).toHaveBeenCalledTimes(1);
    expect(fireB).toHaveBeenCalledTimes(1);
  });

  it("undo after a second remove keeps only the pending one", () => {
    vi.useFakeTimers();
    const fireA = vi.fn();
    const fireB = vi.fn();
    const revertB = vi.fn();
    const { result } = renderHook(() => useUndoReceipt(8));

    act(() => result.current.remove("A", fireA, vi.fn()));
    act(() => result.current.remove("B", fireB, revertB));
    act(() => result.current.undo());
    act(() => vi.advanceTimersByTime(20_000));
    expect(fireA).toHaveBeenCalledTimes(1);
    expect(fireB).not.toHaveBeenCalled();
    expect(revertB).toHaveBeenCalledTimes(1);
  });

  it("unmount commits a pending removal", () => {
    vi.useFakeTimers();
    const fire = vi.fn();
    const { result, unmount } = renderHook(() => useUndoReceipt(8));
    act(() => result.current.remove("item", fire, vi.fn()));
    unmount();
    expect(fire).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(20_000);
    expect(fire).toHaveBeenCalledTimes(1);
  });

  it("unmount after undo or commit fires nothing more", () => {
    vi.useFakeTimers();
    const undone = vi.fn();
    const committed = vi.fn();
    const first = renderHook(() => useUndoReceipt(8));
    act(() => first.result.current.remove("item", undone, vi.fn()));
    act(() => first.result.current.undo());
    first.unmount();
    expect(undone).not.toHaveBeenCalled();

    const second = renderHook(() => useUndoReceipt(1));
    act(() => second.result.current.remove("item", committed, vi.fn()));
    act(() => vi.advanceTimersByTime(1500));
    second.unmount();
    expect(committed).toHaveBeenCalledTimes(1);
  });

  it("flush commits the pending removal now", () => {
    vi.useFakeTimers();
    const fire = vi.fn();
    const { result } = renderHook(() => useUndoReceipt(8));
    act(() => result.current.remove("item", fire, vi.fn()));
    act(() => result.current.flush());
    expect(fire).toHaveBeenCalledTimes(1);
    expect(result.current.phase).toBe("committed");
  });
});
