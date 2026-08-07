// Snap ghost — the translucent landing tile shown during edge-snap drags.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useSyncExternalStore } from "react";
import type { PanelRect } from "../../store";

/** HS-97-05 — the snap ghost: while a head drag hovers a snap region,
 * the landing tile renders as a translucent preview. Module-level
 * publisher so the one ghost lives outside any window. */
let ghostRect: PanelRect | null = null;
const ghostListeners = new Set<() => void>();

export function publishGhost(r: PanelRect | null) {
  const same =
    (r === null && ghostRect === null) ||
    (r !== null &&
      ghostRect !== null &&
      r.x === ghostRect.x &&
      r.y === ghostRect.y &&
      r.w === ghostRect.w &&
      r.h === ghostRect.h);
  if (same) return;
  ghostRect = r;
  for (const l of ghostListeners) l();
}

export function SnapGhost() {
  const rect = useSyncExternalStore(
    (cb) => {
      ghostListeners.add(cb);
      return () => ghostListeners.delete(cb);
    },
    () => ghostRect,
  );
  if (!rect) return null;
  return (
    <div
      className="desk-snap-ghost"
      style={{ top: rect.y, left: rect.x, width: rect.w, height: rect.h }}
      aria-hidden="true"
    />
  );
}
