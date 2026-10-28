/** Lane HUB TIMEOUTS (2026-10-27): the owner's desk, away from his LAN,
 *  showed two windows "◌ Loading" for good while the hub was held by an
 *  engine probe. A first read with no answer after 8 s leaves the Loading
 *  species: `● Not answering` and one verb, Try again. */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Loading, NOT_ANSWERED_MS } from "../kit";
import { SurfaceState } from "../Surface";

describe("the not-answered face", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("SurfaceState loading is ◌ until 8 s, then Not answering · Try again", () => {
    const onRetry = vi.fn();
    const { container, rerender } = render(<SurfaceState loading onRetry={onRetry} />);
    expect(container.querySelector('[data-kind="loading"][aria-busy="true"]')).not.toBeNull();
    act(() => { vi.advanceTimersByTime(NOT_ANSWERED_MS - 1); });
    expect(screen.queryByText("Not answering")).toBeNull();
    act(() => { vi.advanceTimersByTime(1); });
    const line = screen.getByTestId("not-answering");
    expect(line.getAttribute("data-kind")).toBe("not-answering");
    expect(line.getAttribute("aria-busy")).toBeNull();
    expect(line.querySelector(".kit-dot")?.getAttribute("data-tone")).toBe("fail");
    expect(line.textContent).toBe("Not answering" + "Try again");
    const verbs = line.querySelectorAll("button");
    expect(verbs).toHaveLength(1);
    fireEvent.click(verbs[0]);
    expect(onRetry).toHaveBeenCalledTimes(1);
    // The read that was on its way lands: the window draws its content.
    rerender(<SurfaceState loading={false} onRetry={onRetry}><p>Standup</p></SurfaceState>);
    expect(screen.queryByTestId("not-answering")).toBeNull();
    expect(screen.getByText("Standup")).toBeTruthy();
  });

  it("kit Loading keeps its ghost rows until 8 s, then the same line", () => {
    const onRetry = vi.fn();
    const { container } = render(<Loading onRetry={onRetry} />);
    expect(container.querySelectorAll(".kit-loading-row")).toHaveLength(3);
    act(() => { vi.advanceTimersByTime(NOT_ANSWERED_MS); });
    expect(container.querySelector(".kit-loading")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("timeout 0 never leaves Loading", () => {
    const { container } = render(<Loading timeout={0} />);
    act(() => { vi.advanceTimersByTime(NOT_ANSWERED_MS * 4); });
    expect(container.querySelector(".kit-loading")).not.toBeNull();
  });
});
