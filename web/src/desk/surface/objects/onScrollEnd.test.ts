import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { onScrollEnd } from "./wholeRows";

describe("onScrollEnd: a scroll ends with or without the scrollend event", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("uses scrollend where the browser has it", () => {
    const well = document.createElement("div"), ended = vi.fn();
    const off = onScrollEnd(well, ended, true);
    well.dispatchEvent(new Event("scroll"));
    vi.advanceTimersByTime(500);
    expect(ended).not.toHaveBeenCalled();
    well.dispatchEvent(new Event("scrollend"));
    expect(ended).toHaveBeenCalledTimes(1);
    off();
    well.dispatchEvent(new Event("scrollend"));
    expect(ended).toHaveBeenCalledTimes(1);
  });

  it("without scrollend, a scroll ends after 120 ms with no scroll event", () => {
    const well = document.createElement("div"), ended = vi.fn();
    const off = onScrollEnd(well, ended, false);
    well.dispatchEvent(new Event("scroll"));
    vi.advanceTimersByTime(100);
    well.dispatchEvent(new Event("scroll"));     // still moving: the wait starts again
    vi.advanceTimersByTime(100);
    expect(ended).not.toHaveBeenCalled();
    vi.advanceTimersByTime(20);
    expect(ended).toHaveBeenCalledTimes(1);
    well.dispatchEvent(new Event("scrollend"));  // no native event is listened for
    expect(ended).toHaveBeenCalledTimes(1);
    well.dispatchEvent(new Event("scroll"));
    off();
    vi.advanceTimersByTime(500);
    expect(ended).toHaveBeenCalledTimes(1);
  });
});
