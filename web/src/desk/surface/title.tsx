// HS-158-05 — title slot: cores push a runtime window title into the
// head, overriding the manifest label. Mirrors the wing-slot pattern
// (wings.tsx): the host provides a setter; cores call `useWindowTitle`
// to publish; unmount/deps-change clears the override so the manifest
// label returns.
import { createContext, useContext, useEffect } from "react";

/** The host provides a setter; null means no host (pullouts, tests). */
export const TitleSlotContext = createContext<
  ((title: string | null) => void) | null
>(null);

/** Push a runtime title into the hosting window's head. Pass null to
 * clear. `deps` gates republishing (typically [projectName]). */
export function useWindowTitle(title: string | null, deps: unknown[]) {
  const setTitle = useContext(TitleSlotContext);
  useEffect(() => {
    if (!setTitle) return;
    setTitle(title);
    return () => setTitle(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setTitle, ...deps]);
}
