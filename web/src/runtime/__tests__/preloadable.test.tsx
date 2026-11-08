// perf lane 2026-11-08: a lazy read before its render does not suspend, so
// React's 300 ms reveal throttle never holds the desk.
import { act, render, screen } from "@testing-library/react";
import { Suspense } from "react";
import { describe, expect, it } from "vitest";
import { preloadable } from "../preloadable";

const Face = () => <p>the desk</p>;

describe("preloadable", () => {
  it("draws a preloaded lazy in the first commit, with no fallback", async () => {
    let reads = 0;
    const surface = preloadable(async () => { reads += 1; return { default: Face }; });
    await surface.preload();
    expect(surface.loaded()).toBe(true);
    render(<Suspense fallback={<p>loading</p>}><surface.component /></Suspense>);
    expect(screen.getByText("the desk")).toBeTruthy();
    expect(screen.queryByText("loading")).toBeNull();
    await surface.preload();
    expect(reads).toBe(1);
  });

  it("still suspends, then draws, when it was not read first", async () => {
    const surface = preloadable(async () => ({ default: Face }));
    render(<Suspense fallback={<p>loading</p>}><surface.component /></Suspense>);
    expect(screen.getByText("loading")).toBeTruthy();
    await act(async () => { await surface.preload(); });
    expect(await screen.findByText("the desk")).toBeTruthy();
  });
});
