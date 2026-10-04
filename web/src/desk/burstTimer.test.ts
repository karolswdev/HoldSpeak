// Astra, #785 finding 3: a trailing debounce with no cap never ran while
// frames kept coming (20 frames 250 ms apart: zero refreshes in 5 s).
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BURST_MAX_WAIT_MS, burstTimer } from "./burstTimer";

describe("burstTimer", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("runs once, after the burst, for a short burst", () => {
    const run = vi.fn();
    const burst = burstTimer(run, 300);
    burst.bump(); vi.advanceTimersByTime(100);
    burst.bump(); vi.advanceTimersByTime(100);
    burst.bump();
    vi.advanceTimersByTime(299);
    expect(run).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(run).toHaveBeenCalledTimes(1);
  });

  it("still runs while calls keep coming: 20 calls 250 ms apart", () => {
    const run = vi.fn();
    const burst = burstTimer(run, 300);
    const firstRunAt: number[] = [];
    run.mockImplementation(() => firstRunAt.push(Date.now()));
    const began = Date.now();
    for (let i = 0; i < 20; i += 1) {
      burst.bump();
      vi.advanceTimersByTime(250);
    }
    // 5 s of calls that never leave a 300 ms gap.
    expect(run.mock.calls.length).toBeGreaterThanOrEqual(3);
    expect(firstRunAt[0] - began).toBeLessThanOrEqual(BURST_MAX_WAIT_MS);
    vi.advanceTimersByTime(300);
    const settled = run.mock.calls.length;
    vi.advanceTimersByTime(5000);
    expect(run).toHaveBeenCalledTimes(settled); // nothing runs with no new call
  });

  it("cancel drops the waiting run", () => {
    const run = vi.fn();
    const burst = burstTimer(run, 300);
    burst.bump();
    burst.cancel();
    vi.advanceTimersByTime(5000);
    expect(run).not.toHaveBeenCalled();
  });
});
