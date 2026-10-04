/** One run after a burst of calls: a trailing debounce with a hard cap.
 *
 * `bump()` asks for a run `waitMs` after the last bump. A burst that never
 * stops (an agent writing, a steward run) would hold that off forever, so the
 * run also happens no later than `maxWaitMs` after the FIRST bump that is
 * still waiting. `cancel()` drops a waiting run. */
export const BURST_MAX_WAIT_MS = 1500;

export interface BurstTimer {
  bump(): void;
  cancel(): void;
}

export function burstTimer(
  run: () => void,
  waitMs: number,
  maxWaitMs: number = BURST_MAX_WAIT_MS,
): BurstTimer {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let firstAt: number | null = null;

  const fire = () => {
    timer = null;
    firstAt = null;
    run();
  };

  return {
    bump() {
      const now = Date.now();
      if (firstAt === null) firstAt = now;
      if (timer !== null) clearTimeout(timer);
      const left = Math.max(0, firstAt + Math.max(maxWaitMs, waitMs) - now);
      timer = setTimeout(fire, Math.min(waitMs, left));
    },
    cancel() {
      if (timer !== null) clearTimeout(timer);
      timer = null;
      firstAt = null;
    },
  };
}
