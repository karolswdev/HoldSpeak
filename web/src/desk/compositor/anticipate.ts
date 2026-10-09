/** PHILO-16 (L2) — anticipate, then follow.
 *
 * A person's action shows at once; it holds while its request is in flight
 * (a pending count per window: several changes on one window hold together
 * until the last one settles); then the record replaces it, accepted or not.
 * An anticipated front ranks above every depth the record has assigned, so a
 * press never shows two fronts or a stale one. Pure: no DOM, no React.
 *
 * 16a keeps the record in the browser store; 16b moves it to the hub and the
 * requests become the hub's `desk_window_*` calls. */
import type { Rect } from "./geometry";

/** Anticipated fronts rank above every recorded depth. */
export const ANTICIPATED_FRONT = 1e9;

export interface WindowRecord {
  depth: number;
  minimized: boolean;
  rect?: Rect;
}

export interface Change {
  front?: boolean;
  minimized?: boolean;
  rect?: Rect;
}

interface Held {
  change: { depth?: number; minimized?: boolean; rect?: Rect };
  pending: number;
}

export interface Presentations {
  /** The window as it shows now: the record with any held change on top. */
  view(id: string): WindowRecord | undefined;
  /** How many requests on this window are still in flight. */
  pending(id: string): number;
  subscribe(listener: () => void): () => void;
  /** @internal */ readonly held: Map<string, Held>;
  /** @internal */ readonly read: (id: string) => WindowRecord | undefined;
  /** @internal */ notify(): void;
  /** @internal */ nextFront(): number;
}

/** A presentation layer over a record reader (`read(id)` returns the
 * authoritative window record, or undefined when there is none). */
export function createPresentations(read: (id: string) => WindowRecord | undefined): Presentations {
  const held = new Map<string, Held>();
  const listeners = new Set<() => void>();
  let fronts = 0;
  return {
    held,
    read,
    view(id) {
      const base = read(id);
      const h = held.get(id);
      if (!h) return base;
      return {
        depth: h.change.depth ?? base?.depth ?? 0,
        minimized: h.change.minimized ?? base?.minimized ?? false,
        rect: h.change.rect ?? base?.rect,
      };
    },
    pending(id) {
      return held.get(id)?.pending ?? 0;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    notify() {
      for (const l of listeners) l();
    },
    nextFront() {
      fronts += 1;
      return ANTICIPATED_FRONT + fronts;
    },
  };
}

/** Show `change` on window `id` at once and hold it until `request`
 * settles (resolved or rejected); then the record is read again and
 * replaces the anticipation. Resolves when the hold is released, never
 * rejects (a refused request simply shows the record's truth). */
export function anticipate(
  store: Presentations,
  id: string,
  change: Change,
  request: Promise<unknown>,
): Promise<void> {
  const prior = store.held.get(id);
  const next: Held = {
    change: {
      ...(prior?.change ?? {}),
      ...(change.front ? { depth: store.nextFront(), minimized: false } : {}),
      ...(change.minimized !== undefined ? { minimized: change.minimized } : {}),
      ...(change.rect ? { rect: change.rect } : {}),
    },
    pending: (prior?.pending ?? 0) + 1,
  };
  store.held.set(id, next);
  store.notify();
  const settle = () => {
    const h = store.held.get(id);
    if (!h) return;
    h.pending -= 1;
    if (h.pending <= 0) store.held.delete(id);
    store.notify();
  };
  return request.then(settle, settle);
}
