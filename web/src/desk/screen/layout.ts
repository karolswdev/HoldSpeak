/** PHILO-14 A1 — the A-1 arrangement at 1440 (pure).
 *
 *  Board A-1: the drawers down the left (a second column when they do not
 *  fit), the loose objects flowing in the field beside them, the live agents
 *  and Needs you at the top right, Parked at the bottom right. 393 uses no
 *  positions: one 4-column grid in DOM order (screen.css). */
import type { ScreenObject } from "./compose";

export interface Placed {
  x: number;
  y: number;
}

const COL = 120; // an icon is 112 px wide; 8 px between
const DRAWER_ROW = 112;
const FIELD_ROW = 116;
const EDGE = 20;
const TOP = 12;
const FIELD_GAP = 70; // A-1: the field starts 70 px right of the drawer column
const RIGHT_COL = 140; // Needs you and Parked: 140 px in from the right edge
const AGENT_COL = 130; // the agents: one column left of Needs you
const BOTTOM = 136; // Parked: its top this far above the screen's foot

export function layoutScreen(objects: readonly ScreenObject[], width: number, height: number): Record<string, Placed> {
  const at: Record<string, Placed> = {};
  const perCol = Math.max(1, Math.floor((height - TOP) / DRAWER_ROW));

  const drawers = objects.filter((o) => o.role === "drawer");
  drawers.forEach((o, i) => {
    at[o.key] = { x: EDGE + COL * Math.floor(i / perCol), y: TOP + DRAWER_ROW * (i % perCol) };
  });
  const drawerCols = Math.max(1, Math.ceil(drawers.length / perCol));

  const right = width - RIGHT_COL;
  for (const o of objects) {
    if (o.role === "needs") at[o.key] = { x: right, y: TOP };
    if (o.role === "parked") at[o.key] = { x: right, y: Math.max(TOP + DRAWER_ROW, height - BOTTOM) };
  }

  const agents = objects.filter((o) => o.role === "agent");
  let agentLeft = right;
  agents.forEach((o, i) => {
    const x = right - AGENT_COL * (1 + Math.floor(i / perCol));
    agentLeft = Math.min(agentLeft, x);
    at[o.key] = { x, y: TOP + DRAWER_ROW * (i % perCol) };
  });

  const fieldLeft = EDGE + COL * drawerCols + FIELD_GAP;
  const fieldRight = agentLeft - EDGE;
  const cols = Math.max(1, Math.floor((fieldRight - fieldLeft) / COL));
  objects
    .filter((o) => o.role === "loose")
    .forEach((o, i) => {
      at[o.key] = { x: fieldLeft + COL * (i % cols), y: 24 + FIELD_ROW * Math.floor(i / cols) };
    });
  return at;
}
