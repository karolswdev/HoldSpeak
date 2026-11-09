/** HS-95-03 — the shell's surface dispatcher (Constitution, Article I):
 * chrome and shelves never navigate to feature routes; they ask the OS to
 * open a surface. Stories HS-95-05..08 register their windows here; an
 * unregistered surface reports false so callers can fall back to the
 * legacy route until every surface lives in-world (HS-95-08 removes the
 * fallbacks and the guard keeps them out). */

import { meetingWindowRef, objectWindowStandIn } from "./objectWindows";
import type { DeskNavigation } from "./store/types";

export type SurfaceOpenOptions = { origin?: "dock" | "menu" | "route" };

export type SurfaceOpener = (scope?: string, options?: SurfaceOpenOptions) => void;

const surfaces = new Map<string, SurfaceOpener>();
const STAGED_SURFACE_OPEN_KEY = "hs.desk.staged-surface-open";

type StagedSurfaceOpen = { key: string; scope?: string };

/** HS-S12 (D12 / G-OPEN, ruled 2026-11-07: one explicit latest startup
 * intent). Before the normal Desk host is ready the desk keeps ONE intent:
 * the latest explicit open (a `openSurfaceWhenReady` request, a staged route
 * arrival, a press on a key that already opened). It is not a queue: a newer
 * request replaces an older one, so an older request never replays after a
 * newer one and takes the front. `staged` marks a route arrival: recovery
 * (first run) never consumes it. The intent is transient: not stored as a
 * window, not sent to the hub. */
type StartupIntent = { key: string; scope?: string; options?: SurfaceOpenOptions; staged: boolean };
let startupIntent: StartupIntent | null = null;
/** The stored arrival this runtime already consumed (a storage that cannot
 * remove it must not replay it on a host remount). */
let consumedStoredArrival: string | null = null;
/** The mode the surface host last flushed in: during first-run recovery a
 * pressed door does not spend the normal Desk's staged arrival. */
let hostMode: "none" | "recovery" | "normal" = "none";

/** Register a window opener for a surface key. Returns the unregister.
 * Registration replays nothing: the host's one `flushStartupIntent` decides
 * what opens first. */
export function registerSurface(key: string, opener: SurfaceOpener) {
  surfaces.set(key, opener);
  return () => {
    if (surfaces.get(key) === opener) surfaces.delete(key);
  };
}

/** Open now if the key is admitted; else keep it as THE startup intent
 * (it replaces an older one). Not a receipt that a window mounted. */
export function openSurfaceWhenReady(key: string, scope?: string, options?: SurfaceOpenOptions): void {
  if (!openSurface(key, scope, options)) startupIntent = { key, scope, options, staged: false };
}

/** Stage one demoted-route arrival. It is the latest startup intent at once
 * (in memory); session storage also keeps it across a reload before the
 * Desk is ready. A failed storage write changes reliability, not order. */
export function stageSurfaceOpen(key: string, scope?: string): void {
  startupIntent = { key, scope, staged: true };
  try {
    const raw = JSON.stringify({ key, scope });
    sessionStorage.setItem(STAGED_SURFACE_OPEN_KEY, raw);
    consumedStoredArrival = null;
  } catch {
    // Storage can be unavailable; the in-memory intent still lands.
  }
}

/** The stored arrival (a reload between the route and the Desk), removed. */
export function consumeStagedSurfaceOpen(): StagedSurfaceOpen | null {
  try {
    const raw = sessionStorage.getItem(STAGED_SURFACE_OPEN_KEY);
    try {
      sessionStorage.removeItem(STAGED_SURFACE_OPEN_KEY);
    } catch {
      // Not removable: the runtime remembers it was consumed (below).
    }
    if (!raw || raw === consumedStoredArrival) return null;
    consumedStoredArrival = raw;
    const parsed: unknown = JSON.parse(raw);
    if (
      typeof parsed === "object" &&
      parsed !== null &&
      typeof (parsed as StagedSurfaceOpen).key === "string"
    ) {
      const { key, scope } = parsed as StagedSurfaceOpen;
      return typeof scope === "string" ? { key, scope } : { key };
    }
  } catch {
    // An invalid/stale browser value must not block ordinary Desk startup.
  }
  return null;
}

/** HS-S12: the ONE place that decides what opens first. The surface host
 * calls it once its keys are registered. `normal`: the latest intent (in
 * memory, else the stored arrival) opens; a key no host admits stays the
 * intent. `recovery`: only a request (never a staged route arrival) whose
 * key a recovery door admits opens; everything else waits for the normal
 * Desk. Returns true when an intent opened. */
export function flushStartupIntent(mode: "normal" | "recovery"): boolean {
  hostMode = mode;
  if (mode === "recovery") {
    const intent = startupIntent;
    if (!intent || intent.staged || !surfaces.has(intent.key)) return false;
    startupIntent = null;
    return openSurface(intent.key, intent.scope, intent.options);
  }
  const stored = consumeStagedSurfaceOpen();
  // The in-memory intent is always this runtime's latest (a stage writes it
  // too); the stored one is used only after a reload.
  const intent = startupIntent ?? (stored ? { ...stored, staged: true } : null);
  startupIntent = null;
  if (!intent) return false;
  if (openSurface(intent.key, intent.scope, intent.options)) return true;
  startupIntent = intent;
  return false;
}

function supersedeRequest(): void {
  if (startupIntent && (!startupIntent.staged || hostMode !== "recovery")) startupIntent = null;
}

/** The startup intent still waiting (test and readiness seam). */
export function pendingStartupIntent(): Readonly<StartupIntent> | null {
  return startupIntent;
}

/** PHILO-13-11 (C1, slice two) — a mounted screen may answer a surface key
 * first (the Chair at 393: the Speak AppIcon opens its Capture window, the
 * owner's "Yes", 2026-10-02). The answer returns true when it took the open;
 * false passes the key on to its window. Returns the unregister. */
const firstAnswers = new Map<string, (scope?: string, options?: SurfaceOpenOptions) => boolean>();
export function answerSurfaceFirst(
  key: string,
  answer: (scope?: string, options?: SurfaceOpenOptions) => boolean,
): () => void {
  firstAnswers.set(key, answer);
  return () => {
    if (firstAnswers.get(key) === answer) firstAnswers.delete(key);
  };
}

/** Open a surface in-world. False = not yet registered (legacy fallback).
 * An open that lands is the latest explicit intent: an older waiting request
 * is dropped, so it never replays over this one (HS-S12). A staged route
 * arrival stays while first-run recovery holds the host: a recovery door
 * pressed there does not spend the normal Desk's arrival. */
export function openSurface(key: string, scope?: string, options?: SurfaceOpenOptions): boolean {
  if (firstAnswers.get(key)?.(scope, options)) {
    supersedeRequest();
    return true;
  }
  const opener = surfaces.get(key);
  if (!opener) return false;
  supersedeRequest();
  opener(scope, options);
  return true;
}

/** Test seam. */
export function __resetSurfaces(): void {
  surfaces.clear();
  firstAnswers.clear();
  startupIntent = null;
  consumedStoredArrival = null;
  hostMode = "none";
}

/** The router's navigate, delegated once by the app shell so cores and
 * chrome can fall back to a legacy route without importing the router. */
let shellNavigate: ((href: string) => void) | null = null;

export function setShellNavigator(nav: (href: string) => void): void {
  shellNavigate = nav;
}

/** Open a surface in-world, else navigate to its legacy route. */
export function openSurfaceOr(
  key: string, fallbackHref: string,
  scope?: string, options?: SurfaceOpenOptions,
): void {
  if (openSurface(key, scope, options)) return;
  shellNavigate?.(fallbackHref);
}

/** PHILO-9-03 (F1): the ONE key that opens a project's Room. The Room is the
 * Desk memory surface scoped `project:<id>` (applications.ts
 * `open-project-memory`); the old key `project-room` was registered nowhere
 * and its fallback `/projects` is no route, so eight callers opened nothing.
 * An empty id opens Desk memory unscoped, never a dead route. */
export const PROJECT_ROOM_KEY = "open-project-memory";
export function openProjectRoom(projectId: string | null | undefined): void {
  const id = (projectId ?? "").trim();
  const scope = id ? `project:${id}` : undefined;
  if (openSurface(PROJECT_ROOM_KEY, scope)) return;
  // HS-S12: before the Desk is ready the Room is the startup intent, scope
  // and all (a proposal target keeps its project); off the desk, walk home.
  // The old fallback `/project-memory` is no route: it landed on `/` and
  // lost the project.
  openSurfaceWhenReady(PROJECT_ROOM_KEY, scope);
  if (typeof window !== "undefined" && window.location.pathname !== "/") shellNavigate?.("/");
}

/** Open a desk primitive's pull-out. On the desk this opens in place; on
 * a flat route it walks home first (`/?open=<ref>` is the arrival path). */
export function openPrimitive(ref: string, navigation?: DeskNavigation): void {
  if (ref.startsWith("meeting:") && meetingWindowRef(ref)) {
    openSurfaceOr("review-meetings", "/history", ref);
    return;
  }
  if (window.location.pathname === "/") {
    // PHILO-17: a meeting or a person window reads its own object; it opens
    // at once, with no desk refresh first.
    if (!ref.startsWith("artifact:") && objectWindowStandIn(ref)) {
      void import("./store").then((m) => navigation === undefined
        ? m.useDesk.getState().openPullout(ref)
        : m.useDesk.getState().openPullout(ref, undefined, navigation));
      return;
    }
    // The arrival path's exact behavior: refresh first so a just-created
    // primitive is in the items before the pull-out resolves it.
    void import("./store").then(async (m) => {
      if (ref.startsWith("artifact:")) {
        const { holdObject } = await import("./api");
        holdObject(ref);
      }
      await m.useDesk.getState().refresh();
      if (navigation === undefined) m.useDesk.getState().openPullout(ref);
      else m.useDesk.getState().openPullout(ref, undefined, navigation);
    });
    return;
  }
  shellNavigate?.(`/?open=${encodeURIComponent(ref)}`);
}

/** Open a thread bound to a recipe (HS-151-07: replaces the retired PersonaChat). */
export function openPersona(personaId: string): void {
  void import("./newThread").then((m) => m.openNewThread({ recipe_id: personaId }));
}

/** Open a Coder session's window. A session that belongs to a launch
 * opens that agent in Agents (its one face, 2026-11-08); a plain session
 * keeps the session window. */
export function openCoderSession(key: string, opts?: { answer?: boolean; raw?: boolean }): void {
  // Conductor F2 (K5b): `answer` opens the answer well in the window's body,
  // the steer composer recording.
  void Promise.all([import("./steering"), import("./lane/laneStore")]).then(([steering, lane]) => {
    const launchId = lane.launchForSession(key);
    if (launchId) {
      openAgentLane(launchId, { sessionKey: key, answer: opts?.answer, raw: opts?.raw });
      return;
    }
    steering.useSteering.getState().openSession(key, opts);
  });
}

/** Open a launched agent by its launch id: Agents, on that agent (the lane
 * store binds to it; `raw` shows its terminal in the pane). */
export function openAgentLane(launchId: string, opts?: { sessionKey?: string | null; answer?: boolean; raw?: boolean }): void {
  void import("./lane/laneStore").then((m) => {
    m.useLane.getState().open(launchId, opts);
    presentLane(launchId);
  });
}

/** The agent in front: Agents opens (or comes forward) with the launch picked. */
function presentLane(launchId: string): void {
  void import("./conductor/store").then(({ useConductor }) => useConductor.getState().openWindow(null, `launch:${launchId}`));
}
