import { useSyncExternalStore } from "react";

/** The one phone-width breakpoint. Mirrors the `@media (max-width: 720px)`
 *  blocks in the shell furniture stylesheets (dock.css, chrome-menus.css). */
export const COMPACT_VIEWPORT_QUERY = "(max-width: 720px)";

/** True while the viewport is at phone width.
 *
 * HS-202-02 — extracted from `DeskWindow.tsx` so the menu bar reads the
 * same fact the window sheets do: one breakpoint, one subscriber, no
 * second copy to drift.
 */
export function useCompactViewport(): boolean {
  return useSyncExternalStore(
    (cb) => {
      if (typeof window.matchMedia !== "function") return () => {};
      const mq = window.matchMedia(COMPACT_VIEWPORT_QUERY);
      mq.addEventListener?.("change", cb);
      return () => mq.removeEventListener?.("change", cb);
    },
    () =>
      typeof window.matchMedia === "function"
        ? window.matchMedia(COMPACT_VIEWPORT_QUERY).matches
        : false,
  );
}
