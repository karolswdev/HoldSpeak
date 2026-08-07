/**
 * HS-118-07 — Sprite state store.
 *
 * A Zustand store that derives sprite states for workbenches, meetings,
 * and artifacts from runtime bus events and store data. Subscribes to
 * `runtime_activity` frames from the WebSocket bus to detect
 * `workbench.run_start` / `workbench.run_complete`, and derives state
 * from `pendingCount` changes.
 *
 * The fresh->idle timer: after `workbench.run_complete`, a 5-minute
 * setTimeout fires. On expiry the workbench's state re-derives. A new
 * `run_start` clears the timer.
 */
import { create } from "zustand";
import {
  deriveWorkbenchSpriteState,
  deriveArtifactSpriteState,
  deriveMeetingSpriteState,
} from "./spriteVariants";

/** Five minutes in ms (the fresh->idle window). */
const FRESH_TIMEOUT_MS = 5 * 60 * 1000;

interface SpriteStateStore {
  /** Per-id sprite state: keyed by primitive id. */
  states: Record<string, string>;
  /** Set a specific primitive's sprite state. */
  setState(id: string, state: string): void;
  /** Remove a primitive's sprite state. */
  clearState(id: string): void;
  /** Derive and set a workbench's sprite state from current snapshot. */
  deriveWorkbench(id: string, pendingCount: number, runtimeState?: string | null): void;
  /** Derive and set an artifact's sprite state from its status. */
  deriveArtifact(id: string, status: string | null | undefined): void;
  /** Derive and set a meeting's sprite state from recording state. */
  deriveMeeting(id: string, recordingState?: string | null): void;
}

/** Active fresh->idle timers, keyed by workbench id. */
const freshTimers = new Map<string, ReturnType<typeof setTimeout>>();

export const useSpriteStates = create<SpriteStateStore>((set, get) => ({
  states: {},

  setState(id, state) {
    set({ states: { ...get().states, [id]: state } });
  },

  clearState(id) {
    const { [id]: _, ...rest } = get().states;
    set({ states: rest });
  },

  deriveWorkbench(id, pendingCount, runtimeState) {
    const state = deriveWorkbenchSpriteState(pendingCount, runtimeState);
    set({ states: { ...get().states, [id]: state } });
  },

  deriveArtifact(id, status) {
    const state = deriveArtifactSpriteState(status);
    set({ states: { ...get().states, [id]: state } });
  },

  deriveMeeting(id, recordingState) {
    const state = deriveMeetingSpriteState(recordingState);
    set({ states: { ...get().states, [id]: state } });
  },
}));

/**
 * Handle a workbench run_start event: set state to "running" and
 * clear any pending fresh->idle timer.
 */
export function handleWorkbenchRunStart(workbenchId: string): void {
  const timer = freshTimers.get(workbenchId);
  if (timer) {
    clearTimeout(timer);
    freshTimers.delete(workbenchId);
  }
  useSpriteStates.getState().setState(workbenchId, "running");
}

/**
 * Handle a workbench run_complete event: set state to "fresh" and
 * start a 5-minute timer that re-derives to "idle".
 */
export function handleWorkbenchRunComplete(
  workbenchId: string,
  _pendingCount = 0,
): void {
  // Clear any existing timer.
  const existing = freshTimers.get(workbenchId);
  if (existing) clearTimeout(existing);

  // Set to "fresh".
  useSpriteStates.getState().setState(workbenchId, "fresh");

  // After 5 minutes, re-derive from CURRENT store state (not the
  // stale pendingCount captured at run_complete time).
  const timer = setTimeout(() => {
    freshTimers.delete(workbenchId);
    // Read current pending count from the desk store at expiry time.
    // The caller (SpriteStateWatcher) can provide a getPendingCount
    // callback, but we default to 0 (idle) — the next loadAll() or
    // workbench detail fetch will correct it if items are pending.
    const currentPending = pendingCountReaders.get(workbenchId)?.() ?? 0;
    useSpriteStates.getState().deriveWorkbench(workbenchId, currentPending);
  }, FRESH_TIMEOUT_MS);

  freshTimers.set(workbenchId, timer);
}

const pendingCountReaders = new Map<string, () => number>();

export function registerPendingCountReader(
  workbenchId: string,
  reader: () => number,
): void {
  pendingCountReaders.set(workbenchId, reader);
}

/**
 * Cleanup all fresh timers (for hot module reload or unmount).
 */
export function clearAllFreshTimers(): void {
  for (const timer of freshTimers.values()) clearTimeout(timer);
  freshTimers.clear();
}
