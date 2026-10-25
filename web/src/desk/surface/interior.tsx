// Window grammar (2026-10-24) — the body inset. A window whose content is a
// list view or an editor runs edge to edge (its Toolbar, list and StatusBar
// touch the frame); forms and readers keep the 12-16 px inset. The host
// owns the body, so the core tells the host which interior it draws and the
// host sets `data-interior` on the body. Mirrors the title slot (title.tsx).
import { createContext, useContext, useLayoutEffect } from "react";

export type WindowInterior = "list" | "editor";

/** The host provides a setter; null means no host (pullouts, tests). */
export const InteriorSlotContext = createContext<
  ((interior: WindowInterior | null) => void) | null
>(null);

/** Tell the hosting window which interior this face draws (`list`,
 *  `editor`), or null for the default inset (forms, readers). */
export function useWindowInterior(interior: WindowInterior | null) {
  const setInterior = useContext(InteriorSlotContext);
  useLayoutEffect(() => {
    if (!setInterior) return;
    setInterior(interior);
    return () => setInterior(null);
  }, [setInterior, interior]);
}
