import { useDesk } from "../../store";
import { flashSwitcher } from "./Switcher";
import { snapForPointer } from "./windowGeometry";
import { chairPhoneToBack } from "../../chair/chairWindows";
import {
  cycleWindows as cycleWindowsRaw,
  cycleWindowsReverse as cycleWindowsReverseRaw,
  frontWindowId,
} from "./windowRegistry";

/** Window command handlers live below the React frame/barrel so the command
 * registry and keymap do not form a component import cycle. */
export function cycleWindows(): void {
  cycleWindowsRaw(flashSwitcher);
}

export function cycleWindowsReverse(): void {
  cycleWindowsReverseRaw(flashSwitcher);
}

export function snapFrontWindow(side: "left" | "right"): void {
  const id = frontWindowId();
  if (!id || typeof window === "undefined") return;
  const state = useDesk.getState();
  const vw = window.innerWidth || 1280;
  const vh = window.innerHeight || 800;
  const rect = snapForPointer(side === "left" ? 0 : vw, vh / 2, vw, vh);
  if (!rect) return;
  if (state.panelMax.includes(id)) state.toggleMaximizePanel(id);
  if (state.panelMin.includes(id)) state.restorePanel(id);
  state.setPanelRect(id, rect, true);
  state.focusPanel(id);
}

/** PHILO-13-12 (C2) — ⌃M: zoom the front window between its two
 * remembered rects (Intuition's zoom). The same toggle as the gadget. */
export function zoomFrontWindow(): void {
  const id = frontWindowId();
  if (!id) return;
  const state = useDesk.getState();
  if (state.panelMin.includes(id)) state.restorePanel(id);
  state.toggleMaximizePanel(id);
}

/** Kept for its importers: zoom the front window (was: maximize only). */
export const maximizeFrontWindow = zoomFrontWindow;

/** PHILO-13-12 (C2) — depth: send this window behind every other window.
 * The next window in the order becomes the front window (one blue window;
 * the screen title follows it). On the phone the Chair shows one window at
 * a time, so a Chair window sent back gives the work area to the next one. */
export function sendWindowToBack(id: string): void {
  useDesk.getState().sendPanelToBack(id);
  chairPhoneToBack(id);
}

/** ⌃B — depth on the front window. */
export function sendFrontWindowToBack(): void {
  const id = frontWindowId();
  if (id) sendWindowToBack(id);
}
