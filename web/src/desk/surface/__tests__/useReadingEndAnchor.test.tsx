import { renderHook, waitFor, act } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useReadingEndAnchor } from "../useReadingEndAnchor";

function sizedReading(scrollHeight: number, clientHeight: number): { element: HTMLDivElement; setHeight: (next: number) => void } {
  let height = scrollHeight;
  const element = document.createElement("div");
  Object.defineProperty(element, "scrollHeight", { configurable: true, get: () => height });
  Object.defineProperty(element, "clientHeight", { configurable: true, value: clientHeight });
  return { element, setHeight: (next) => { height = next; } };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useReadingEndAnchor", () => {
  it("keeps the bottom edge after a viewport/content resize", async () => {
    const { element, setHeight } = sizedReading(600, 200);
    const ref = { current: element };
    const { unmount } = renderHook(() => useReadingEndAnchor(ref, true));

    expect(element.scrollTop).toBe(400);
    act(() => element.dispatchEvent(new Event("scroll")));
    setHeight(900);
    act(() => window.dispatchEvent(new Event("resize")));
    await waitFor(() => expect(element.scrollTop).toBe(700));

    unmount();
  });

  it("preserves a reader's position above the end", async () => {
    const { element, setHeight } = sizedReading(600, 200);
    const ref = { current: element };
    const { unmount } = renderHook(() => useReadingEndAnchor(ref, true));

    element.scrollTop = 120;
    act(() => {
      element.dispatchEvent(new Event("wheel", { bubbles: true }));
      element.dispatchEvent(new Event("scroll"));
    });
    setHeight(900);
    act(() => window.dispatchEvent(new Event("resize")));
    await new Promise((resolve) => window.setTimeout(resolve, 10));
    expect(element.scrollTop).toBe(120);

    unmount();
  });

  it("does not require ResizeObserver", async () => {
    vi.stubGlobal("ResizeObserver", undefined);
    const { element, setHeight } = sizedReading(600, 200);
    const ref = { current: element };
    const { unmount } = renderHook(() => useReadingEndAnchor(ref, true));

    setHeight(900);
    act(() => window.dispatchEvent(new Event("resize")));
    await waitFor(() => expect(element.scrollTop).toBe(700));

    unmount();
  });

  it("reattaches when the active reading node changes", () => {
    const first = sizedReading(400, 200).element;
    const second = sizedReading(800, 200).element;
    const ref = { current: first };
    const { rerender, unmount } = renderHook(
      ({ active }: { active: boolean }) => useReadingEndAnchor(ref, active),
      { initialProps: { active: false } },
    );

    ref.current = second;
    rerender({ active: true });
    expect(second.scrollTop).toBe(600);
    unmount();
  });
});

