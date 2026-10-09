/** PHILO-16 (L4) — layers are a type with rules, not z-index numbers.
 *
 * Every surface on the desk declares one layer; its z is derived here from
 * the `--desk-z-*` ladder (tokens.css, section 3) and never written by hand.
 * Pure: no DOM, no React. */
import { DESK_Z } from "../../lib/tokens.gen";

export type Layer = "floor" | "world" | "window" | "chrome" | "transient";

export const LAYERS: readonly Layer[] = ["floor", "world", "window", "chrome", "transient"];

/** The z ladder by name. `tokens.gen` carries six stops; the waveform (78)
 * and the popover (82) are in tokens.css only (`--desk-z-waveform`,
 * `--desk-z-popover`), so they are named here with the same numbers. */
export const Z = {
  canvas: DESK_Z.canvas,
  worldOverlay: DESK_Z.worldOverlay,
  chrome: DESK_Z.chrome,
  windowBase: DESK_Z.windowBase,
  /** The highest window: one under the waveform, so no window ever rises
   * over the dock or a transient, however many windows are open. */
  windowTop: 77,
  waveform: 78,
  dock: DESK_Z.dock,
  transient: DESK_Z.transient,
  popover: 82,
} as const;

/** The chrome layer's stops, bottom to top: the menu-bar band (under the
 * windows by design), the input waveform, the dock. */
export const CHROME_STOPS = [Z.chrome, Z.waveform, Z.dock] as const;
/** The transient layer's stops: an open chrome transient, a popover. */
export const TRANSIENT_STOPS = [Z.transient, Z.popover] as const;

const stop = (stops: readonly number[], depth: number) =>
  stops[Math.max(0, Math.min(stops.length - 1, Math.floor(depth)))];

/** The z of a surface on `layer` at `depth`. For `window`, depth is the
 * window's rank among shown windows (0 = the back); the band is
 * `windowBase`..`windowTop`. For `chrome` and `transient`, depth picks the
 * stop (see CHROME_STOPS / TRANSIENT_STOPS). */
export function zFor(layer: Layer, depth = 0): number {
  switch (layer) {
    case "floor":
      return Z.canvas;
    case "world":
      return Z.worldOverlay;
    case "window":
      return Math.min(Z.windowTop, Z.windowBase + Math.max(0, Math.floor(depth)));
    case "chrome":
      return stop(CHROME_STOPS, depth);
    case "transient":
      return stop(TRANSIENT_STOPS, depth);
  }
}

/** Only a window moves (drag, arrange). The floor, the world overlays, the
 * chrome and the transients are anchored to the view. */
export function canMove(layer: Layer): boolean {
  return layer === "window";
}

/** Only a window raises: a press brings it to the Front plane. Every other
 * layer has a fixed place in the ladder. */
export function canRaise(layer: Layer): boolean {
  return layer === "window";
}

/** The compositor draws the frame (planes, light, veil) of a window only;
 * the other layers draw themselves. */
export function compositorDraws(layer: Layer): boolean {
  return layer === "window";
}
