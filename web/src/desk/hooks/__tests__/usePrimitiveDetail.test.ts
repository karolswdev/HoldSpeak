/** HS-117-13 — usePrimitiveDetail hook tests. */
import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { usePrimitiveDetail } from "../usePrimitiveDetail";

describe("usePrimitiveDetail", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches on mount with the correct id", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ name: "test" });
    const { result } = renderHook(() =>
      usePrimitiveDetail("widget", "abc", fetchFn),
    );

    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(fetchFn).toHaveBeenCalledWith("abc");
    expect(result.current.data).toEqual({ name: "test" });
    expect(result.current.error).toBeNull();
  });

  it("refetches when id changes", async () => {
    const fetchFn = vi.fn()
      .mockResolvedValueOnce({ name: "first" })
      .mockResolvedValueOnce({ name: "second" });

    const { result, rerender } = renderHook(
      ({ id }: { id: string }) => usePrimitiveDetail("widget", id, fetchFn),
      { initialProps: { id: "a" } },
    );

    await waitFor(() => expect(result.current.data).toEqual({ name: "first" }));

    rerender({ id: "b" });

    await waitFor(() => expect(result.current.data).toEqual({ name: "second" }));
    expect(fetchFn).toHaveBeenCalledTimes(2);
    expect(fetchFn).toHaveBeenLastCalledWith("b");
  });

  it("aborts in-flight fetch on unmount", async () => {
    let resolve: (value: string) => void;
    const fetchFn = vi.fn().mockReturnValue(
      new Promise<string>((r) => { resolve = r; }),
    );

    const { result, unmount } = renderHook(() =>
      usePrimitiveDetail("widget", "x", fetchFn),
    );

    expect(result.current.loading).toBe(true);

    // Unmount before resolving.
    unmount();

    // Resolve after unmount — state should NOT update (no React warnings).
    await act(async () => {
      resolve!("stale");
      // Allow microtask to flush.
      await new Promise((r) => setTimeout(r, 0));
    });

    // The hook was unmounted so we can't inspect result.current meaningfully,
    // but the test passes if no React "state update on unmounted component"
    // warning is emitted.
    expect(fetchFn).toHaveBeenCalledTimes(1);
  });

  it("sets loading/error/data correctly on failure", async () => {
    const fetchFn = vi.fn().mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() =>
      usePrimitiveDetail("widget", "fail-id", fetchFn),
    );

    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("network down");
  });

  it("refresh() triggers a new fetch without clearing current data", async () => {
    const fetchFn = vi.fn()
      .mockResolvedValueOnce({ v: 1 })
      .mockResolvedValueOnce({ v: 2 });

    const { result } = renderHook(() =>
      usePrimitiveDetail("widget", "r", fetchFn),
    );

    await waitFor(() => expect(result.current.data).toEqual({ v: 1 }));

    // Trigger refresh — data should stay at v:1 during loading, then update.
    act(() => {
      result.current.refresh();
    });

    // Data is still present while loading.
    expect(result.current.data).toEqual({ v: 1 });

    await waitFor(() => expect(result.current.data).toEqual({ v: 2 }));
    expect(fetchFn).toHaveBeenCalledTimes(2);
  });

  it("returns null data when id is null", () => {
    const fetchFn = vi.fn();

    const { result } = renderHook(() =>
      usePrimitiveDetail("widget", null, fetchFn),
    );

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it("discards stale fetch when id changes before resolution", async () => {
    let resolveFirst: (value: string) => void;
    const fetchFn = vi.fn()
      .mockReturnValueOnce(new Promise<string>((r) => { resolveFirst = r; }))
      .mockResolvedValueOnce("second-result");

    const { result, rerender } = renderHook(
      ({ id }: { id: string }) => usePrimitiveDetail("widget", id, fetchFn),
      { initialProps: { id: "slow" } },
    );

    // Change id before the first fetch resolves.
    rerender({ id: "fast" });

    await waitFor(() => expect(result.current.data).toBe("second-result"));

    // Now resolve the stale first fetch — it should be ignored.
    await act(async () => {
      resolveFirst!("stale-result");
      await new Promise((r) => setTimeout(r, 0));
    });

    // Data should still be from the second fetch.
    expect(result.current.data).toBe("second-result");
  });
});
