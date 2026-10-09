// PHILO-16 (C) — the Switchboard's geometry, pure: plug points and wire paths.
//
// A wire runs from a job's plug (the right edge of the job) to an engine's
// plug (the left edge of the engine) as one cubic curve whose two control
// points share the horizontal midpoint (canvas Board 2, `draw()`). Every
// number here is in the coordinate space of the wires layer.

export interface Point {
  x: number;
  y: number;
}

export interface Box {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

/** How far the wire stops short of the plug square's centre (half a plug). */
export const PLUG_INSET = 6;

/** The plug point on one side of a box, relative to an origin box. */
export function plugPoint(box: Box, side: "left" | "right", origin: Box): Point {
  const x = side === "right" ? box.right - origin.left : box.left - origin.left;
  const y = box.top - origin.top + (box.bottom - box.top) / 2;
  return { x, y };
}

/** One cubic wire from a job plug to an engine plug. */
export function wirePath(from: Point, to: Point, inset = PLUG_INSET): string {
  const x1 = round(from.x + inset);
  const x2 = round(to.x - inset);
  const y1 = round(from.y);
  const y2 = round(to.y);
  const mx = round((x1 + x2) / 2);
  return `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
}

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

/** A new chain after a drop: first moves the engine to the head; a fallback
 *  appends it after the others. Never a duplicate; never more than four. */
export function patchChain<T>(chain: readonly T[], item: T, asFallback: boolean): T[] {
  const rest = chain.filter((entry) => entry !== item);
  return (asFallback ? [...rest, item] : [item, ...rest]).slice(0, 4);
}
