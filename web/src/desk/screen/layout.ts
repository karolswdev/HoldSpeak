/** PHILO-14 A1 — the A-1 arrangement at 1440 (pure).
 *
 *  The drawers and Projects down the left (a second column when they do not
 *  fit), the loose objects flowing in the field beside them, and Archive at
 *  the bottom right. 393 uses no positions: one 4-column grid in DOM order
 *  (screen.css). */
import type { ScreenObject } from "./compose";

export interface Placed {
  x: number;
  y: number;
}

const COL = 120; // an icon is 112 px wide; 8 px between
const DRAWER_ROW = 96;
const FIELD_ROW = 100;
const EDGE = 20;
const TOP = 12;
const FIELD_GAP = 70; // A-1: the field starts 70 px right of the drawer column
const BOTTOM = 136; // Parked: its top this far above the screen's foot
const TALK_ZONE = 72; // the TALK control at the foot-left (Astra's P3 on #939)
const NOT_READ_LINE = 30; // a NOT READ drawer's Retry line
// PHILO-17 (phonepass): a caption (People's `1:1 15:00`) adds 24 px to the
// compact desktop icon; preserve that extra room above the next drawer's
// count notch rather than reducing the caption's readable size.
const CAPTION_LINE = 24;

export function layoutScreen(
  objects: readonly ScreenObject[],
  width: number,
  height: number,
  savedPositions: Readonly<Record<string, Placed>> = {},
): Record<string, Placed> {
  const savedOrder = new Map(Object.keys(savedPositions).map((key, index) => [key, index]));
  const ordered = objects
    .map((object, index) => ({ object, index }))
    .sort((left, right) => {
      const leftOrder = savedOrder.get(left.object.key);
      const rightOrder = savedOrder.get(right.object.key);
      if (leftOrder !== undefined && rightOrder !== undefined) return leftOrder - rightOrder;
      if (leftOrder !== undefined) return -1;
      if (rightOrder !== undefined) return 1;
      return left.index - right.index;
    })
    .map(({ object }) => object);
  const at: Record<string, Placed> = {};
  // The drawers fill the left column above the TALK control at the foot
  // (TALK_ZONE); a NOT READ drawer is taller (its Retry line).
  const drawers = ordered.filter((o) => o.role === "drawer");
  const columnFoot = Math.max(TOP + DRAWER_ROW, height - TALK_ZONE);
  let col = 0;
  let y = TOP;
  for (const o of drawers) {
    const tall = DRAWER_ROW + (o.notRead ? NOT_READ_LINE : 0) + (o.caption ? CAPTION_LINE : 0);
    if (y > TOP && y + tall > columnFoot) {
      col += 1;
      y = TOP;
    }
    at[o.key] = { x: EDGE + COL * col, y };
    y += tall;
  }
  const drawerCols = drawers.length ? col + 1 : 1;

  for (const o of ordered) {
    if (o.role === "parked") at[o.key] = { x: width - EDGE - COL, y: Math.max(TOP + DRAWER_ROW, height - BOTTOM) };
  }

  const fieldLeft = EDGE + COL * drawerCols + FIELD_GAP;
  const fieldRight = width - EDGE;
  const cols = Math.max(1, Math.floor((fieldRight - fieldLeft) / COL));
  ordered
    .filter((o) => o.role === "loose")
    .forEach((o, i) => {
      at[o.key] = { x: fieldLeft + COL * (i % cols), y: 24 + FIELD_ROW * Math.floor(i / cols) };
    });
  const placed: Record<string, Placed> = {};
  const occupied: Array<Placed & { height: number }> = [];
  const objectHeight = (object: ScreenObject) => DRAWER_ROW
    + (object.notRead ? NOT_READ_LINE : 0) + (object.caption ? CAPTION_LINE : 0);
  // Reserve saved rectangles even while their producer's reply is pending.
  // A project reply must not claim the place of a note that arrives later.
  for (const [key, saved] of Object.entries(savedPositions)) {
    const object = objects.find((candidate) => candidate.key === key);
    placed[key] = saved;
    occupied.push({ ...saved, height: object ? objectHeight(object) : DRAWER_ROW });
  }
  for (const object of ordered) {
    if (placed[object.key]) continue;
    const height = objectHeight(object);
    let position = at[object.key];
    if (!position) continue;
    while (occupied.some((other) => (
      position.x < other.x + 112 && position.x + 112 > other.x
      && position.y < other.y + other.height && position.y + height > other.y
    ))) {
      if (object.role === "drawer") {
        const nextY = position.y + height;
        position = nextY + height > columnFoot
          ? { x: position.x + COL, y: TOP }
          : { x: position.x, y: nextY };
      } else {
        const nextX = position.x + COL;
        position = nextX + 112 > fieldRight
          ? { x: fieldLeft, y: position.y + FIELD_ROW }
          : { x: nextX, y: position.y };
      }
    }
    placed[object.key] = position;
    occupied.push({ ...position, height });
  }
  return placed;
}
