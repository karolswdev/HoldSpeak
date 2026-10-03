// PHILO-13-17 (C7, Q1/Q2; the owner's "Ratify, build it", 2026-10-03) —
// the phone's ring of open windows. At 393 one window fills the work area;
// a horizontal touch swipe on it moves to the next open window (finger to
// the left) or back (to the right), and the screen title's switcher lists
// the same ring. The ring: the open Chair windows in the Chair's order
// (Needs you, Brief, The week, then Capture once it opened at 393), then
// the open desk windows in the order they opened. It wraps.
// A Chair window takes the work area the way Go ▸ Chair does
// (openChairWindow: the desk window in front iconifies, never closes).
import { useEffect } from "react";
import { useDesk } from "../../store";
import { useChairState } from "../../chairState";
import { COMPACT_VIEWPORT_QUERY } from "../../useCompactViewport";
import {
  CHAIR_WINDOWS,
  openChairWindow,
  useChairWindows,
} from "../../chair/chairWindows";
import { frontWindowId, openedSeq, registrySnapshot } from "./windowRegistry";

export type RingWindow = { id: string; label: string; chair: boolean };

function compactNow(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia(COMPACT_VIEWPORT_QUERY).matches
  );
}

/** The open windows in ring order (Chair windows only on the Chair). */
export function phoneRing(): RingWindow[] {
  const cw = useChairWindows.getState();
  const onChair = useChairState.getState().surface === "chair";
  const chair = onChair
    ? CHAIR_WINDOWS.filter(
        (w) =>
          !cw.closed[w.id] &&
          (w.phone || (w.id === "chair:capture" && (cw.captureInRing || cw.phone === w.id))),
      ).map((w) => ({ id: w.id, label: w.title, chair: true }))
    : [];
  // The order the windows opened: their opening sequence, never the
  // registry Map's order (a title change re-announces a window at its end).
  const desk = registrySnapshot
    .filter((w) => w.dock && !w.id.startsWith("chair:"))
    .sort((a, b) => openedSeq(a.id) - openedSeq(b.id))
    .map((w) => ({ id: w.id, label: w.label, chair: false }));
  return [...chair, ...desk];
}

/** The window that fills the work area now: the front desk window, else
 * (on the Chair) the phone's Chair window. */
export function phoneCurrent(): string | null {
  const s = useDesk.getState();
  const f = frontWindowId();
  if (f && !f.startsWith("chair:") && !s.panelMin.includes(f)) return f;
  if (useChairState.getState().surface !== "chair") return null;
  return useChairWindows.getState().phone || null;
}

/** Bring one ring window to the work area. */
export function showRingWindow(id: string): void {
  if (id.startsWith("chair:")) {
    openChairWindow(id);
    return;
  }
  const s = useDesk.getState();
  if (s.panelMin.includes(id)) s.restorePanel(id);
  else s.focusPanel(id);
}

/** One step around the ring; the id it landed on, or null (nothing to move to). */
export function stepRing(dir: 1 | -1): string | null {
  const r = phoneRing();
  const at = r.findIndex((w) => w.id === phoneCurrent());
  if (r.length < 2 && at >= 0) return null;
  if (!r.length) return null;
  const from = at >= 0 ? at : dir === 1 ? -1 : 0;
  const next = r[(from + dir + r.length) % r.length];
  showRingWindow(next.id);
  return next.id;
}

/** A swipe: horizontal, more than 64 px, at least twice as wide as tall. */
export const SWIPE_MIN_PX = 64;

export function swipeDirection(dx: number, dy: number): 1 | -1 | 0 {
  if (Math.abs(dx) < SWIPE_MIN_PX || Math.abs(dx) < 2 * Math.abs(dy)) return 0;
  return dx < 0 ? 1 : -1;
}

/** A swipe that starts on a field, a menu or the Dock is theirs (the caret
 * and the shelf keep their own drag); only a window's body swipes. */
const NOT_A_SWIPE = "input, textarea, select, [contenteditable='true'], [role=menu], .desk-dock, .cm-editor";

/** Install the 393 swipe once (the screen title's switcher mounts it). */
export function usePhoneSwipe(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    let t0: { x: number; y: number } | null = null;
    const start = (e: TouchEvent) => {
      t0 = null;
      if (!compactNow() || e.touches.length !== 1) return;
      const target = e.target as Element | null;
      if (!target?.closest?.(".desk-window-shell")) return;
      if (target.closest(NOT_A_SWIPE)) return;
      t0 = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    };
    const end = (e: TouchEvent) => {
      const from = t0;
      t0 = null;
      if (!from) return;
      const t = e.changedTouches[0];
      if (!t) return;
      const dir = swipeDirection(t.clientX - from.x, t.clientY - from.y);
      if (dir) stepRing(dir);
    };
    const cancel = () => {
      t0 = null;
    };
    document.addEventListener("touchstart", start, { capture: true, passive: true });
    document.addEventListener("touchend", end, { capture: true, passive: true });
    document.addEventListener("touchcancel", cancel, { capture: true, passive: true });
    return () => {
      document.removeEventListener("touchstart", start, true);
      document.removeEventListener("touchend", end, true);
      document.removeEventListener("touchcancel", cancel, true);
    };
  }, [enabled]);
}
