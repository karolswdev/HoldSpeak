import { useDesk } from "../../store";
import { flashSwitcher } from "./Switcher";
import { back, tileFront, userArranged } from "../../compositor/useCompositor";
import { getPresentation, modeNow } from "../../compositor/live";
import { chairPhoneToBack, chairWindowSpec } from "../../chair/chairWindows";
import {
  cycleWindows as cycleWindowsRaw,
  cycleWindowsReverse as cycleWindowsReverseRaw,
  frontWindowId,
  shellEls,
} from "./windowRegistry";

/** Window command handlers live below the React frame/barrel so the command
 * registry and keymap do not form a component import cycle. */
export function cycleWindows(): void {
  cycleWindowsRaw(flashSwitcher);
}

export function cycleWindowsReverse(): void {
  cycleWindowsReverseRaw(flashSwitcher);
}

/** PHILO-16 — Tile left / right (⌘⌥← / ⌘⌥→): the front window takes the
 * half, the near window the other half; they touch, so one steel divider
 * sits between them (the compositor, `tileFront`). One window open: it takes
 * the half alone (the old Snap). */
export function snapFrontWindow(side: "left" | "right"): void {
  tileFront(side);
}

export {
  tileFront,
  toggleStage,
  toggleExposeMode,
  gatherFront,
  gatherRoom,
  cascadeAll,
  back as arrangeBack,
} from "../../compositor/useCompositor";

/** PHILO-13-12 (C2) — zoom one window between its two remembered rects.
 * The FIRST zoom keeps the normal rect even when the owner never arranged
 * the window: only arranged rects are saved, so without this a reload
 * measured the zoomed size as the normal one (Astra, PR #731). The rect is
 * read from the glass, so a content-sized window comes back exactly. */
export function zoomWindow(id: string): void {
  // Astra M1: Zoom pressed during Stage or Exposé leaves it first (every
  // window back to its remembered rects), then zooms. In a tiled
  // arrangement, zoom is his own arrangement: Esc no longer undoes it.
  const mode = modeNow();
  // Astra round 2: leaving Stage or Exposé animates, so the glass shows a
  // box in flight; the record is the destination (§13 L6). The normal rect
  // is the remembered free rect (what Esc restores), never a measurement.
  const remembered =
    mode === "stage" || mode === "expose" ? getPresentation().saved[id] : undefined;
  if (mode === "stage" || mode === "expose") back();
  else if (mode === "tile") userArranged();
  const state = useDesk.getState();
  if (remembered !== undefined) {
    if (!state.panelMax.includes(id) && remembered.rect) state.setPanelRect(id, remembered.rect, true);
    useDesk.getState().toggleMaximizePanel(id);
    return;
  }
  // A Chair window the owner never moved has no rect: its CSS tile place is
  // its normal rect (C1-4e). Writing the measured tile here made it an
  // arranged rect, and the next open clamped it into the shell band (54 px),
  // 12 px under its tile place (42 px). Unzoomed, it goes back to its tile.
  const tileAtHome = Boolean(chairWindowSpec(id)) && !state.panelRects[id];
  if (!tileAtHome && !state.panelMax.includes(id) && !state.panelSaved.includes(id)) {
    const r = shellEls.get(id)?.getBoundingClientRect();
    const rect =
      r && r.width && r.height
        ? { x: r.left, y: r.top, w: r.width, h: r.height }
        : state.panelRects[id];
    if (rect) state.setPanelRect(id, rect, true);
  }
  useDesk.getState().toggleMaximizePanel(id);
}

/** PHILO-13-12 (C2) — ⌃M: zoom the front window between its two
 * remembered rects (Intuition's zoom). The same toggle as the gadget. */
export function zoomFrontWindow(): void {
  const id = frontWindowId();
  if (!id) return;
  const state = useDesk.getState();
  if (state.panelMin.includes(id)) state.restorePanel(id);
  zoomWindow(id);
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
