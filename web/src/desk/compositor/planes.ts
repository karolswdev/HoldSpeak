/** PHILO-16 (L3) — depth is a counter; the plane is derived.
 *
 * Every window carries `depth`, a number the authority increments on a raise
 * (`depth = ++highest`). Nothing reorders an array. The planes of §3 (FRONT ·
 * NEAR · FAR · SEATED) come from the rank by depth among the shown windows,
 * so a reload that keeps the numbers keeps the planes. Pure: no DOM. */

export type Plane = "front" | "near" | "far" | "seated";

export interface PlaneWindow {
  id: string;
  depth: number;
  minimized: boolean;
}

/** The planes of a set of windows. The shown window with the greatest depth
 * is FRONT, the next is NEAR, every other shown window is FAR, a minimized
 * window is SEATED (it keeps its depth). Equal depths keep the input order:
 * the later one is nearer. Exactly one window is FRONT when any is shown. */
export function assignPlanes(windows: readonly PlaneWindow[]): Map<string, Plane> {
  const planes = new Map<string, Plane>();
  const shown = windows
    .map((w, i) => ({ w, i }))
    .filter(({ w }) => !w.minimized)
    .sort((a, b) => a.w.depth - b.w.depth || a.i - b.i);
  for (const w of windows) if (w.minimized) planes.set(w.id, "seated");
  shown.forEach(({ w }, rank) => {
    const fromTop = shown.length - 1 - rank;
    planes.set(w.id, fromTop === 0 ? "front" : fromTop === 1 ? "near" : "far");
  });
  return planes;
}

/** The rank of every shown window, 0 = the back (the z offset in the window
 * layer). Minimized windows have no rank. */
export function rankOf(windows: readonly PlaneWindow[]): Map<string, number> {
  const ranks = new Map<string, number>();
  windows
    .map((w, i) => ({ w, i }))
    .filter(({ w }) => !w.minimized)
    .sort((a, b) => a.w.depth - b.w.depth || a.i - b.i)
    .forEach(({ w }, rank) => ranks.set(w.id, rank));
  return ranks;
}

/** The stacking state: depth per window, and the seated (minimized) ids. */
export interface StackState {
  depth: Readonly<Record<string, number>>;
  seated: readonly string[];
}

export function highest(depth: Readonly<Record<string, number>>): number {
  let top = 0;
  for (const d of Object.values(depth)) if (d > top) top = d;
  return top;
}

/** Ids from back to front (the old `panelOrder` shape, derived). */
export function orderFromDepth(depth: Readonly<Record<string, number>>): string[] {
  return Object.entries(depth)
    .sort((a, b) => a[1] - b[1])
    .map(([id]) => id);
}

/** A depth map from a back-to-front order (the one-time migration of the
 * old `panelOrder`, and the bridge for a legacy order write). */
export function depthFromOrder(order: readonly string[]): Record<string, number> {
  const depth: Record<string, number> = {};
  order.forEach((id, i) => {
    depth[id] = i + 1;
  });
  return depth;
}

/** Raise: the window takes `++highest`. A window that already holds the
 * highest depth alone is not touched (the state object is returned as is). */
export function raise(state: StackState, id: string): StackState {
  const top = highest(state.depth);
  const mine = state.depth[id];
  const alone =
    mine !== undefined &&
    mine === top &&
    Object.entries(state.depth).every(([other, d]) => other === id || d < top);
  if (alone) return state;
  return { ...state, depth: { ...state.depth, [id]: top + 1 } };
}

/** Send back: the window goes under the lowest shown window. */
export function sendBack(state: StackState, id: string): StackState {
  const shown = Object.entries(state.depth).filter(
    ([other]) => other !== id && !state.seated.includes(other),
  );
  if (shown.length === 0) return state.depth[id] === undefined
    ? { ...state, depth: { ...state.depth, [id]: 1 } }
    : state;
  const lowest = Math.min(...shown.map(([, d]) => d));
  if ((state.depth[id] ?? Infinity) < lowest) return state;
  return { ...state, depth: { ...state.depth, [id]: lowest - 1 } };
}

/** Seat (minimize): the window keeps its depth; it is simply not shown. */
export function seat(state: StackState, id: string): StackState {
  if (state.seated.includes(id)) return state;
  return { ...state, seated: [...state.seated, id] };
}

/** Unseat (restore): the window comes back and is raised to the Front. */
export function unseat(state: StackState, id: string): StackState {
  const seated = state.seated.filter((x) => x !== id);
  return raise({ ...state, seated }, id);
}
