/** PHILO-16 (L7) — departure is representation.
 *
 * A closing or seating window keeps one immutable visual snapshot until its
 * exit animation reports done, while the window itself leaves the collection
 * at once (the live component unmounts in the same event, so no render shows
 * a window in neither list). Windows present when the desk mounts are
 * "inherited": they never replay an entrance. Pure: no DOM, no React. */
import type { Rect } from "./geometry";
import type { Plane } from "./planes";

export interface Snapshot {
  id: string;
  rect: Rect;
  plane: Plane;
  /** Per-departure key: the same window may leave twice in a row. */
  key: number;
}

export interface Departures {
  /** Retain a snapshot of `id` as it was when it left. */
  retainSnapshot(id: string, rect: Rect, plane: Plane): Snapshot;
  /** The exit animation of `id` (or of one snapshot by key) is done. */
  release(id: string, key?: number): void;
  /** The snapshots still on screen, oldest first. */
  list(): readonly Snapshot[];
  subscribe(listener: () => void): () => void;
}

export function createDepartures(): Departures {
  let snapshots: readonly Snapshot[] = [];
  let seq = 0;
  const listeners = new Set<() => void>();
  const notify = () => {
    for (const l of listeners) l();
  };
  return {
    retainSnapshot(id, rect, plane) {
      const snap: Snapshot = Object.freeze({ id, rect: Object.freeze({ ...rect }), plane, key: ++seq });
      snapshots = Object.freeze([...snapshots, snap]);
      notify();
      return snap;
    },
    release(id, key) {
      const next = snapshots.filter((s) => !(s.id === id && (key === undefined || s.key === key)));
      if (next.length === snapshots.length) return;
      snapshots = Object.freeze(next);
      notify();
    },
    list: () => snapshots,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

export interface Inheritance {
  /** True for a window that was present when the desk mounted, until it is
   * closed: its mount is a return, not an arrival (no entrance). A mount
   * after `forget` (closed, then opened again) is an arrival. Idempotent,
   * so a double-run mount (React strict mode) agrees with itself. */
  isInherited(id: string): boolean;
  /** The window closed: its next mount is an arrival. */
  forget(id: string): void;
}

/** The windows present at mount (`ids`: the restored workspace's windows). */
export function inheritedAtMount(ids: Iterable<string>): Inheritance {
  const waiting = new Set(ids);
  return {
    isInherited: (id) => waiting.has(id),
    forget(id) {
      waiting.delete(id);
    },
  };
}
