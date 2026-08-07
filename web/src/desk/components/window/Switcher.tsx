// Switcher — the transient MRU strip shown during Ctrl+` cycling.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useSyncExternalStore } from "react";
import { registrySnapshot } from "./windowRegistry";

/** HS-97-06 — the transient switcher strip's state. */
let switcherState: {
  items: { id: string; label: string; glyph: string }[];
  target: string;
} | null = null;
let switcherTimer: ReturnType<typeof setTimeout> | undefined;
const switcherListeners = new Set<() => void>();

export function flashSwitcher(target: string) {
  switcherState = {
    items: registrySnapshot.map((w) => ({
      id: w.id,
      label: w.label,
      glyph: w.glyph,
    })),
    target,
  };
  for (const l of switcherListeners) l();
  clearTimeout(switcherTimer);
  switcherTimer = setTimeout(() => {
    switcherState = null;
    for (const l of switcherListeners) l();
  }, 900);
}

/** The visible MRU switcher (HS-97-06): while Ctrl+` cycles, a strip
 * names every open window with the landing target highlighted, fading
 * once the cycle settles. */
export function Switcher() {
  const st = useSyncExternalStore(
    (cb) => {
      switcherListeners.add(cb);
      return () => switcherListeners.delete(cb);
    },
    () => switcherState,
  );
  if (!st) return null;
  return (
    <div className="desk-switcher" role="status">
      {st.items.map((w) => (
        <span
          key={w.id}
          className={
            "desk-switcher-chip" + (w.id === st.target ? " is-target" : "")
          }
        >
          <span aria-hidden="true">{w.glyph}</span> {w.label}
        </span>
      ))}
    </div>
  );
}
