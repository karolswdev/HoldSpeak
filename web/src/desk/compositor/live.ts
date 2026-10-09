/** PHILO-16 — the compositor's live state (store side, no DOM).
 *
 * ONE place derives every window's plane, rank and z: the mounted windows
 * (each frame registers here in a layout effect, so a new window is counted
 * before the first paint) and the store's `panelDepth` / `panelMin`. The
 * frame, the front-window readers (⌘W, the screen title) and the motion all
 * read this one derivation, so two fronts cannot happen by construction.
 *
 * It also holds the presentation: the arrangement mode (free, tile, stage,
 * exposé) and, for stage and exposé, the plates each window is drawn as.
 * A plate is presentation only: the store's rects (the user's arrangement)
 * are never written by stage or exposé, so Esc returns them exactly. */
import { useDesk } from "../store";
import { assignPlanes, rankOf, type Plane } from "./planes";
import { zFor, type Layer } from "./layers";
import { createDepartures, inheritedAtMount } from "./departure";
import type { Rect } from "./geometry";

// ---- mounted windows -------------------------------------------------------

export interface MountedWindow {
  /** The Room (project ref) the window belongs to, for Gather. */
  room?: string;
  layer: Layer;
}

const mounted = new Map<string, MountedWindow>();
const listeners = new Set<() => void>();
let version = 0;

function notify() {
  version += 1;
  for (const l of listeners) l();
}

export function subscribeLive(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function liveVersion(): number {
  return version;
}

/** A frame is open (its layout effect). Idempotent. */
export function mountWindow(id: string, info: MountedWindow): void {
  const prev = mounted.get(id);
  if (prev && prev.room === info.room && prev.layer === info.layer) return;
  mounted.set(id, info);
  notify();
}

/** A frame closed or unmounted. */
export function unmountWindow(id: string): void {
  if (!mounted.delete(id)) return;
  notify();
}

export function mountedWindows(): ReadonlyMap<string, MountedWindow> {
  return mounted;
}

export function roomOf(id: string): string | undefined {
  return mounted.get(id)?.room;
}

// ---- planes ----------------------------------------------------------------

export interface LivePlanes {
  planes: Map<string, Plane>;
  ranks: Map<string, number>;
  /** Shown windows, back to front. */
  shown: string[];
  front: string | null;
}

let cache: { v: number; depth: unknown; min: unknown; out: LivePlanes } | null = null;

/** The planes of the mounted windows from the store's depths. Memoized on
 * (mount version, depth object, minimized array). */
export function computePlanes(
  depth: Readonly<Record<string, number>> = useDesk.getState().panelDepth,
  min: readonly string[] = useDesk.getState().panelMin,
): LivePlanes {
  if (cache && cache.v === version && cache.depth === depth && cache.min === min) return cache.out;
  const windows = Array.from(mounted.keys()).map((id) => ({
    id,
    // A window not yet in the stacking sorts under every stacked one.
    depth: depth[id] ?? Number.MIN_SAFE_INTEGER,
    minimized: min.includes(id),
  }));
  const planes = assignPlanes(windows);
  const ranks = rankOf(windows);
  const shown = Array.from(ranks.entries())
    .sort((a, b) => a[1] - b[1])
    .map(([id]) => id);
  const out: LivePlanes = { planes, ranks, shown, front: shown.length ? shown[shown.length - 1] : null };
  cache = { v: version, depth, min, out };
  return out;
}

/** The ONE front window (null when none is shown). */
export function frontId(): string | null {
  return computePlanes().front;
}

/** The z of a window from its rank (the window layer). */
export function zOfWindow(id: string, planes: LivePlanes = computePlanes()): number {
  return zFor("window", planes.ranks.get(id) ?? 0);
}

// ---- presentation (arrangement mode + plates) ------------------------------

export type Mode = "free" | "tile" | "stage" | "expose";

export interface PlateState {
  rect: Rect;
  k?: number;
}

/** A window's free state, remembered when an arrangement begins. */
export interface SavedRect {
  rect: Rect | null;
  arranged: boolean;
  max: boolean;
}

interface Presentation {
  mode: Mode;
  /** Stage and exposé: the plate each window is drawn as. */
  plates: Readonly<Record<string, PlateState>>;
  /** The free rects remembered when an arrangement began (Esc returns). */
  saved: Readonly<Record<string, SavedRect>>;
  /** The window on stage (stage mode). */
  staged: string | null;
}

let presentation: Presentation = { mode: "free", plates: {}, saved: {}, staged: null };
const presentationListeners = new Set<() => void>();

export function getPresentation(): Presentation {
  return presentation;
}

export function setPresentation(next: Partial<Presentation>): void {
  presentation = { ...presentation, ...next };
  for (const l of presentationListeners) l();
}

export function subscribePresentation(listener: () => void): () => void {
  presentationListeners.add(listener);
  return () => presentationListeners.delete(listener);
}

export function modeNow(): Mode {
  return presentation.mode;
}

// ---- departures and inheritance -------------------------------------------

/** Snapshots of windows on their way out (seat, close). */
export const departures = createDepartures();

/** The windows present when the desk loaded: they never replay an entrance.
 * The stacking persisted with the workspace names exactly the windows that
 * were open (a closed window leaves the stacking). */
export const inheritance = inheritedAtMount(Object.keys(useDesk.getState().panelDepth));
