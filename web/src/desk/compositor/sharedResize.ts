/** PHILO-16 (L8) — touching edges are one boundary.
 *
 * Any two shown windows whose opposite edges touch (within 1 px) and whose
 * spans overlap share a boundary. Boundaries on one line that share windows
 * are grouped by connectivity and drag as one: every near edge moves, every
 * far edge stays, and no window goes under its minimum size. Tile and Gather
 * do not make a "divider mode"; they make touching windows, and the divider
 * is derived from them. Pure: no DOM. */
import type { Rect } from "./geometry";

export const MIN_W = 320;
export const MIN_H = 220;
const TOLERANCE = 1;

export interface ResizeWindow {
  id: string;
  rect: Rect;
  depth: number;
}

export interface Boundary {
  /** "v": a vertical line (windows left and right of it); "h": horizontal. */
  axis: "v" | "h";
  /** The line's coordinate (x for "v", y for "h"). */
  at: number;
  /** Windows on the left (v) or above (h): their right/bottom edge moves. */
  before: string[];
  /** Windows on the right (v) or below (h): their left/top edge moves. */
  after: string[];
  /** The extent along the line where windows touch (y for "v", x for "h"). */
  start: number;
  end: number;
}

interface Contact {
  a: string;
  b: string;
  at: number;
  start: number;
  end: number;
}

function contacts(windows: readonly ResizeWindow[], axis: "v" | "h"): Contact[] {
  const out: Contact[] = [];
  for (const a of windows) {
    for (const b of windows) {
      if (a.id === b.id) continue;
      const ra = a.rect;
      const rb = b.rect;
      const edgeA = axis === "v" ? ra.x + ra.w : ra.y + ra.h;
      const edgeB = axis === "v" ? rb.x : rb.y;
      if (Math.abs(edgeA - edgeB) > TOLERANCE) continue;
      const start = axis === "v" ? Math.max(ra.y, rb.y) : Math.max(ra.x, rb.x);
      const end = axis === "v" ? Math.min(ra.y + ra.h, rb.y + rb.h) : Math.min(ra.x + ra.w, rb.x + rb.w);
      if (end - start <= TOLERANCE) continue;
      out.push({ a: a.id, b: b.id, at: (edgeA + edgeB) / 2, start, end });
    }
  }
  return out;
}

function group(list: Contact[], axis: "v" | "h"): Boundary[] {
  // Union-find over contacts: two contacts join when they lie on the same
  // line and share a window.
  const parent = list.map((_, i) => i);
  const find = (i: number): number => (parent[i] === i ? i : (parent[i] = find(parent[i])));
  for (let i = 0; i < list.length; i++) {
    for (let j = i + 1; j < list.length; j++) {
      const p = list[i];
      const q = list[j];
      if (Math.abs(p.at - q.at) > TOLERANCE) continue;
      if (p.a === q.a || p.b === q.b || p.a === q.b || p.b === q.a) parent[find(i)] = find(j);
    }
  }
  const groups = new Map<number, Contact[]>();
  list.forEach((c, i) => {
    const root = find(i);
    groups.set(root, [...(groups.get(root) ?? []), c]);
  });
  return Array.from(groups.values()).map((cs) => ({
    axis,
    at: Math.round(cs.reduce((s, c) => s + c.at, 0) / cs.length),
    before: Array.from(new Set(cs.map((c) => c.a))),
    after: Array.from(new Set(cs.map((c) => c.b))),
    start: Math.min(...cs.map((c) => c.start)),
    end: Math.max(...cs.map((c) => c.end)),
  }));
}

/** Every shared boundary between the windows, vertical ones first. */
export function boundaries(windows: readonly ResizeWindow[]): Boundary[] {
  return [...group(contacts(windows, "v"), "v"), ...group(contacts(windows, "h"), "h")];
}

/** Move a boundary by `delta` px. Every `before` window's far (left/top) edge
 * stays and its near edge moves; every `after` window's far (right/bottom)
 * edge stays and its near edge moves. The delta is clamped so no window
 * goes under MIN_W x MIN_H. Returns the new rects of the moved windows. */
export function resizeBoundary(
  boundary: Boundary,
  windows: readonly ResizeWindow[],
  delta: number,
  min = { w: MIN_W, h: MIN_H },
): Map<string, Rect> {
  const byId = new Map(windows.map((w) => [w.id, w.rect]));
  const v = boundary.axis === "v";
  const size = (r: Rect) => (v ? r.w : r.h);
  const floor = v ? min.w : min.h;
  let lo = -Infinity;
  let hi = Infinity;
  for (const id of boundary.before) {
    const r = byId.get(id);
    if (r) lo = Math.max(lo, floor - size(r));
  }
  for (const id of boundary.after) {
    const r = byId.get(id);
    if (r) hi = Math.min(hi, size(r) - floor);
  }
  const d = Math.max(Math.min(lo, 0), Math.min(Math.max(hi, 0), delta));
  const out = new Map<string, Rect>();
  for (const id of boundary.before) {
    const r = byId.get(id);
    if (r) out.set(id, v ? { ...r, w: r.w + d } : { ...r, h: r.h + d });
  }
  for (const id of boundary.after) {
    const r = byId.get(id);
    if (r) out.set(id, v ? { ...r, x: r.x + d, w: r.w - d } : { ...r, y: r.y + d, h: r.h - d });
  }
  return out;
}
