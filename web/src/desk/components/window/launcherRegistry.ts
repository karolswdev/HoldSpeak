// Launcher registry — module-level pub/sub for dock launchers.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useSyncExternalStore } from "react";

/** HS-97-07 — dock launchers: fixed shelf verbs (Desk memory, Delivery,
 * Panes) announce themselves so ONE dock carries launch and running
 * state; the floating pills are gone. */
export interface DockLauncher {
  id: string;
  label: string;
  glyph: string;
  open: boolean;
  badge?: number;
  activate: () => void;
}

const LAUNCHER_SEAT: Record<string, number> = {
  attention: 0,
  "delivery-board": 1,
  panes: 2,
};

const launcherRegistry = new Map<string, DockLauncher>();
let launcherSnapshot: DockLauncher[] = [];
const launcherListeners = new Set<() => void>();

function publishLaunchers() {
  launcherSnapshot = Array.from(launcherRegistry.values()).sort(
    (a, b) => (LAUNCHER_SEAT[a.id] ?? 9) - (LAUNCHER_SEAT[b.id] ?? 9),
  );
  for (const l of launcherListeners) l();
}

export function announceLauncher(l: DockLauncher) {
  launcherRegistry.set(l.id, l);
  publishLaunchers();
}

export function retractLauncher(id: string) {
  launcherRegistry.delete(id);
  publishLaunchers();
}

/** HS-111-01 — programs may hand over to a docked program (the Prefs
 * Delivery module opens the Delivery board). False = not announced. */
export function activateLauncher(id: string): boolean {
  const launcher = launcherRegistry.get(id);
  if (!launcher) return false;
  launcher.activate();
  return true;
}

export function useLaunchers() {
  return useSyncExternalStore(
    (cb) => {
      launcherListeners.add(cb);
      return () => launcherListeners.delete(cb);
    },
    () => launcherSnapshot,
  );
}
