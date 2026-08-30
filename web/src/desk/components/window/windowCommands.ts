import { useDesk } from "../../store";
import { flashSwitcher } from "./Switcher";
import { snapForPointer } from "./windowGeometry";
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

export function maximizeFrontWindow(): void {
  const id = frontWindowId();
  if (!id) return;
  const state = useDesk.getState();
  if (state.panelMin.includes(id)) state.restorePanel(id);
  if (!state.panelMax.includes(id)) state.toggleMaximizePanel(id);
  else state.focusPanel(id);
}
