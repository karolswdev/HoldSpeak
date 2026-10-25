// Window grammar 2026-10-24 — back slot: a core that has its own narrow
// list → detail step (Settings' rail → pane) hands the hosting window's
// compact title-bar Back to that step. Mirrors the title slot (title.tsx):
// the host provides a setter; cores call `useWindowBack`; unmount or a null
// back returns the frame's default (close the window).
import { createContext, useContext, useEffect } from "react";

export type WindowBack = {
  onBack: () => void;
  /** The test id the frame's Back carries while this step owns it. */
  testId?: string;
};

/** The host provides a setter; null means no host (pullouts, tests). */
export const BackSlotContext = createContext<((back: WindowBack | null) => void) | null>(null);

/** True when a hosting window will take the step (the core then draws no
 *  Back of its own at a compact viewport). */
export function useHasWindowBack(): boolean {
  return useContext(BackSlotContext) !== null;
}

/** Hand the frame's compact Back to `back`, or give it back with null.
 *  `deps` gates republishing. */
export function useWindowBack(back: WindowBack | null, deps: unknown[]) {
  const setBack = useContext(BackSlotContext);
  useEffect(() => {
    if (!setBack) return;
    setBack(back);
    return () => setBack(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setBack, ...deps]);
}
