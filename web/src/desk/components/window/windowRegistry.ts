// Window registry — module-level Maps + pub/sub for open windows.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useSyncExternalStore } from "react";
import { useDesk } from "../../store";
import { mruOrder } from "./windowGeometry";
import { shownNames } from "../../windowName";

/** Dock chip elements by window id — the minimize/restore motion's
 * target (HS-97-04). Populated by the Dock's ref callbacks. */
export const chipEls = new Map<string, HTMLElement>();

/** Window shell elements by id — the expose's fan targets (HS-97-06). */
export const shellEls = new Map<string, HTMLElement>();

/** Open windows announce themselves (title/icon/close) so the dock can
 * name and drive them without a parallel registry.
 * PHILO-13-11 (C1, slice two): `dock: false` marks a window that is part
 * of a screen, not a program (the Chair's four windows). It is a window
 * for the front, the screen title, Close and the cycle; it has no Dock chip
 * (the Chair screen holds its reopen Button). */
export const windowRegistry = new Map<
  string,
  { label: string; glyph: string; close: () => void; dock: boolean; kind?: string }
>();
export const registryListeners = new Set<() => void>();
export type RegisteredWindow = {
  id: string;
  /** The name every face shows. Two open windows with the same name have
   * their kind first (`Thought · <name>`); see windowName.ts. */
  label: string;
  /** The name of the thing in the window, with no kind word. */
  name: string;
  glyph: string;
  close: () => void;
  dock: boolean;
};
export let registrySnapshot: RegisteredWindow[] = [];
/** The open windows the Dock and Overview show (every window with a chip). */
export let dockSnapshot: RegisteredWindow[] = [];

export function publishRegistry() {
  const shown = shownNames(
    Array.from(windowRegistry.entries(), ([id, v]) => ({ id, name: v.label, kind: v.kind })),
  );
  registrySnapshot = Array.from(windowRegistry.entries()).map(
    ([id, v]) => ({ id, ...v, name: v.label, label: shown.get(id) ?? v.label }),
  );
  dockSnapshot = registrySnapshot.filter((w) => w.dock);
  for (const l of registryListeners) l();
}

/** PHILO-13-17 (C7; Astra r1 #751, condition 1) — each open window's
 * opening sequence. A window re-announces on a title change (retract, then
 * announce in the same commit), which moves it to the END of the Map; this
 * sequence survives that, so "the order the windows opened" stays true. A
 * window really closed (not re-announced by the next microtask) drops it, so
 * a reopened window is the newest. */
const openSeq = new Map<string, number>();
let nextSeq = 0;

/** The opening sequence of an open window (Infinity when not open). */
export function openedSeq(id: string): number {
  return openSeq.get(id) ?? Number.POSITIVE_INFINITY;
}

export function announceWindow(
  id: string,
  label: string,
  glyph: string,
  close: () => void,
  dock = true,
  /** The kind word that goes first when another open window has this name. */
  kind?: string,
) {
  if (!openSeq.has(id)) openSeq.set(id, ++nextSeq);
  windowRegistry.set(id, { label, glyph, close, dock, kind });
  publishRegistry();
}

export function retractWindow(id: string) {
  windowRegistry.delete(id);
  publishRegistry();
  queueMicrotask(() => {
    if (!windowRegistry.has(id)) openSeq.delete(id);
  });
}

function subscribeRegistry(cb: () => void) {
  registryListeners.add(cb);
  return () => {
    registryListeners.delete(cb);
  };
}

/** The open windows with a Dock chip (the Dock, Overview). The Chair's
 * windows are not here: they belong to the Chair screen. */
export function useOpenWindows() {
  return useSyncExternalStore(subscribeRegistry, () => dockSnapshot);
}

/** PHILO-13-11 (C1, slice two) — EVERY open window, the Chair's included:
 * the front window and the screen title read this. */
export function useAllOpenWindows() {
  return useSyncExternalStore(subscribeRegistry, () => registrySnapshot);
}

/** The name one open window shows now (its kind first when names collide). */
export function useShownName(id: string, fallback: string): string {
  return useAllOpenWindows().find((w) => w.id === id)?.label ?? fallback;
}

/** PHILO-13-11 (C1, R4) — ONE front window, from the ONE stacking order:
 * the last non-minimized id in `order` that is actually open. Pure, so the
 * frame, the screen title bar and the Cmd+W/Cmd+M target cannot disagree. */
export function frontOf(
  order: readonly string[],
  minimized: readonly string[],
  open: readonly { id: string }[],
): string | null {
  for (let i = order.length - 1; i >= 0; i--) {
    const id = order[i];
    if (minimized.includes(id)) continue;
    if (open.some((w) => w.id === id)) return id;
  }
  const shown = open.filter((w) => !minimized.includes(w.id));
  return shown.length ? shown[shown.length - 1].id : null;
}

/** HS-101 B8 — the front window: the last non-minimized id in the
 * stacking order that is actually open (the Cmd+W/Cmd+M target). */
export function frontWindowId(): string | null {
  const s = useDesk.getState();
  return frontOf(s.panelOrder, s.panelMin, registrySnapshot);
}

/** PHILO-13-11 (C1, R4) — the front window as a hook. It subscribes to the
 * stacking order AND to the window registry: the old per-frame selector read
 * the registry without subscribing to it, so a window that re-rendered after
 * it announced itself could compute "front" while the previous front window
 * kept a stale `is-front` (two blue title bars at once). */
export function useFrontWindowId(): string | null {
  const open = useAllOpenWindows();
  const order = useDesk((s) => s.panelOrder);
  const minimized = useDesk((s) => s.panelMin);
  return frontOf(order, minimized, open);
}

/** How many windows are open right now (ghost-reason source). */
export function openWindowCount(): number {
  return registrySnapshot.length;
}

/** How many windows with a Dock chip are open (Overview fans only these). */
export function dockWindowCount(): number {
  return dockSnapshot.length;
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

/** Ctrl+Shift+` — reverse the MRU cycle, landing on the window immediately
 * behind the frontmost one. */
export function cycleWindowsReverse(
  flashSwitcher: (target: string) => void,
): void {
  const ids = mruOrder(
    registrySnapshot.map((w) => w.id),
    useDesk.getState().panelOrder,
  );
  if (ids.length < 1) return;
  const next = ids[Math.max(0, ids.length - 2)];
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
