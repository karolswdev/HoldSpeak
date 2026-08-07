import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useCopyReceipt } from "../useCopyReceipt";

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("useCopyReceipt", () => {
  it("copies text to clipboard and returns a receipt", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    const { result } = renderHook(() => useCopyReceipt());
    expect(result.current.state).toBe("idle");
    expect(result.current.receipt).toBeNull();

    await act(() => result.current.copy("hello"));

    expect(writeText).toHaveBeenCalledWith("hello");
    expect(result.current.state).toBe("copied");
    expect(result.current.receipt).not.toBeNull();
  });

  it("auto-clears receipt after 2 seconds", async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    const { result } = renderHook(() => useCopyReceipt());
    await act(() => result.current.copy("test"));
    expect(result.current.state).toBe("copied");

    act(() => vi.advanceTimersByTime(2000));
    expect(result.current.state).toBe("idle");
    expect(result.current.receipt).toBeNull();
  });

  it("handles clipboard failure", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("denied"));
    Object.assign(navigator, { clipboard: { writeText } });

    const { result } = renderHook(() => useCopyReceipt());
    await act(() => result.current.copy("fail"));

    expect(result.current.state).toBe("failed");
    expect(result.current.receipt).not.toBeNull();
  });
});
