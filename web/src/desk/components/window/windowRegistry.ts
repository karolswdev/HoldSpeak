// Window registry — module-level Maps + pub/sub for open windows.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useSyncExternalStore } from "react";
import { useDesk } from "../../store";
import { mruOrder } from "./windowGeometry";

/** Dock chip elements by window id — the minimize/restore motion's
 * target (HS-97-04). Populated by the Dock's ref callbacks. */
export const chipEls = new Map<string, HTMLElement>();

/** Window shell elements by id — the expose's fan targets (HS-97-06). */
export const shellEls = new Map<string, HTMLElement>();

/** Open windows announce themselves (title/icon/close) so the dock can
 * name and drive them without a parallel registry. */
export const windowRegistry = new Map<
  string,
  { label: string; glyph: string; close: () => void }
>();
export const registryListeners = new Set<() => void>();
export let registrySnapshot: {
  id: string;
  label: string;
  glyph: string;
  close: () => void;
}[] = [];

export function publishRegistry() {
  registrySnapshot = Array.from(windowRegistry.entries()).map(
    ([id, v]) => ({ id, ...v }),
  );
  for (const l of registryListeners) l();
}

export function announceWindow(
  id: string,
  label: string,
  glyph: string,
  close: () => void,
) {
  windowRegistry.set(id, { label, glyph, close });
  publishRegistry();
}

export function retractWindow(id: string) {
  windowRegistry.delete(id);
  publishRegistry();
}

export function useOpenWindows() {
  return useSyncExternalStore(
    (cb) => {
      registryListeners.add(cb);
      return () => registryListeners.delete(cb);
    },
    () => registrySnapshot,
  );
}

/** HS-101 B8 — the front window: the last non-minimized id in the
 * stacking order that is actually open (the Cmd+W/Cmd+M target). */
export function frontWindowId(): string | null {
  const s = useDesk.getState();
  for (let i = s.panelOrder.length - 1; i >= 0; i--) {
    const id = s.panelOrder[i];
    if (s.panelMin.includes(id)) continue;
    if (registrySnapshot.some((w) => w.id === id)) return id;
  }
  const open = registrySnapshot.filter((w) => !s.panelMin.includes(w.id));
  return open.length ? open[open.length - 1].id : null;
}

/** How many windows are open right now (ghost-reason source). */
export function openWindowCount(): number {
  return registrySnapshot.length;
}

/* -- HS-111-07: the window verbs the registry runs (one truth; the
   keymap and every menu face reach them through verbRegistry). -- */

/** Cmd+W — close the front window. */
export function closeFrontWindow(): void {
  const id = frontWindowId();
  if (id) registrySnapshot.find((w) => w.id === id)?.close();
}

/** Cmd+M — minimize the front window. */
export function minimizeFrontWindow(): void {
  const id = frontWindowId();
  if (id) useDesk.getState().minimizePanel(id);
}

/** Ctrl+` — MRU cycle: the least-recent open window comes forward, and
 * the switcher strip names the landing (HS-97-06). */
export function cycleWindows(flashSwitcher: (target: string) => void): void {
  const ids = mruOrder(
    registrySnapshot.map((w) => w.id),
    useDesk.getState().panelOrder,
  );
  if (ids.length < 1) return;
  const next = ids[0];
  const s = useDesk.getState();
  if (s.panelMin.includes(next)) s.restorePanel(next);
  else s.focusPanel(next);
  flashSwitcher(next);
}

/** Cmd+1-Cmd+4 — an application whose window is already open focuses (or
 * restores) instead of re-opening. False = not open; launch instead. */
export function focusOrRestoreApp(windowId: string): boolean {
  if (!registrySnapshot.some((w) => w.id === windowId)) return false;
  const s = useDesk.getState();
  if (s.panelMin.includes(windowId)) s.restorePanel(windowId);
  s.focusPanel(windowId);
  return true;
}
