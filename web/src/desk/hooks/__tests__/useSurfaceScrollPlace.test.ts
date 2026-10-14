import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  surfaceScrollPlaceKey,
  useSurfaceScrollPlace,
} from "../useSurfaceScrollPlace";
import { keepPlace, keptPlace } from "../../deskMemory";

function sizedBody(scrollHeight: number, clientHeight: number): HTMLDivElement {
  const body = document.createElement("div");
  Object.defineProperty(body, "scrollHeight", {
    configurable: true,
    value: scrollHeight,
  });
  Object.defineProperty(body, "clientHeight", {
    configurable: true,
    value: clientHeight,
  });
  return body;
}

describe("useSurfaceScrollPlace", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("restores the saved position for the exact window and scope", () => {
    const key = surfaceScrollPlaceKey("surface-meetings", "meeting:m1");
    keepPlace(key, "120");
    const { result, unmount } = renderHook(() =>
      useSurfaceScrollPlace("surface-meetings", "meeting:m1"),
    );
    const body = sizedBody(600, 200);

    act(() => result.current(body));
    act(() => vi.runOnlyPendingTimers());

    expect(body.scrollTop).toBe(120);
    expect(keptPlace(key)).toBe("120");
    act(() => result.current(null));
    unmount();
  });

  it("cancels a pending jump, then keeps the owner's next scroll", () => {
    const key = surfaceScrollPlaceKey("surface-meetings", "meeting:m1");
    keepPlace(key, "120");
    const { result, unmount } = renderHook(() =>
      useSurfaceScrollPlace("surface-meetings", "meeting:m1"),
    );
    const body = sizedBody(100, 200);

    act(() => result.current(body));
    act(() => body.dispatchEvent(new Event("scroll")));
    expect(keptPlace(key)).toBe("120");

    act(() => body.dispatchEvent(new Event("wheel", { bubbles: true })));
    body.scrollTop = 260;
    act(() => body.dispatchEvent(new Event("scroll")));

    expect(keptPlace(key)).toBe("260");
    act(() => result.current(null));
    unmount();
  });

  it("keeps zero after a no-place body reaches a place and returns to top", () => {
    const key = surfaceScrollPlaceKey("surface-meetings");
    const { result, unmount } = renderHook(() =>
      useSurfaceScrollPlace("surface-meetings"),
    );
    const body = sizedBody(600, 200);

    act(() => result.current(body));
    body.scrollTop = 120;
    act(() => body.dispatchEvent(new Event("scroll")));
    body.scrollTop = 0;
    act(() => body.dispatchEvent(new Event("scroll")));

    expect(keptPlace(key)).toBe("0");
    act(() => result.current(null));
    unmount();
  });

  it("restores the original target when content arrives before the deadline", async () => {
    vi.useRealTimers();
    const key = surfaceScrollPlaceKey("surface-meetings", "meeting:m1");
    keepPlace(key, "120");
    const { result, unmount } = renderHook(() =>
      useSurfaceScrollPlace("surface-meetings", "meeting:m1"),
    );
    const body = sizedBody(100, 200);

    act(() => result.current(body));
    await new Promise((resolve) => setTimeout(resolve, 40));
    Object.defineProperty(body, "scrollHeight", { configurable: true, value: 600 });
    body.appendChild(document.createElement("span"));

    await waitFor(() => expect(body.scrollTop).toBe(120), { timeout: 1_000 });
    act(() => result.current(null));
    unmount();
  });

  it("does not replay a place when the hosted core refreshes in the same scope", () => {
    const key = surfaceScrollPlaceKey("surface-meetings", "meeting:m1");
    keepPlace(key, "120");
    const { result, rerender, unmount } = renderHook(() =>
      useSurfaceScrollPlace("surface-meetings", "meeting:m1"),
    );
    const body = sizedBody(600, 200);

    act(() => result.current(body));
    act(() => vi.runOnlyPendingTimers());
    expect(body.scrollTop).toBe(120);

    body.scrollTop = 260;
    act(() => body.dispatchEvent(new Event("scroll")));
    rerender();
    expect(body.scrollTop).toBe(260);
    expect(keptPlace(key)).toBe("260");
    act(() => result.current(null));
    unmount();
  });

  it("restores separate list and detail places when backing to the list", () => {
    const listKey = surfaceScrollPlaceKey("surface-meetings");
    const detailKey = surfaceScrollPlaceKey("surface-meetings", "meeting:m1");
    keepPlace(listKey, "40");
    keepPlace(detailKey, "90");
    const { result, rerender, unmount } = renderHook(
      ({ scope }: { scope?: string }) =>
        useSurfaceScrollPlace("surface-meetings", scope),
      { initialProps: { scope: undefined } as { scope: string | undefined } },
    );
    const body = sizedBody(600, 200);

    act(() => result.current(body));
    act(() => vi.runOnlyPendingTimers());
    expect(body.scrollTop).toBe(40);
    act(() => result.current(null));

    rerender({ scope: "meeting:m1" });
    act(() => result.current(body));
    act(() => vi.runOnlyPendingTimers());
    expect(body.scrollTop).toBe(90);
    act(() => result.current(null));

    rerender({ scope: undefined });
    act(() => result.current(body));
    act(() => vi.runOnlyPendingTimers());
    expect(body.scrollTop).toBe(40);
    act(() => result.current(null));
    unmount();
  });
});
