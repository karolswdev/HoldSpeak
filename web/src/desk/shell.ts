/** HS-95-03 — the shell's surface dispatcher (Constitution, Article I):
 * chrome and shelves never navigate to feature routes; they ask the OS to
 * open a surface. Stories HS-95-05..08 register their windows here; an
 * unregistered surface reports false so callers can fall back to the
 * legacy route until every surface lives in-world (HS-95-08 removes the
 * fallbacks and the guard keeps them out). */

export type SurfaceOpenOptions = { origin?: "dock" | "menu" | "route" };

export type SurfaceOpener = (scope?: string, options?: SurfaceOpenOptions) => void;

const surfaces = new Map<string, SurfaceOpener>();
const pendingOpens: Array<{ key: string; scope?: string; options?: SurfaceOpenOptions }> = [];
const STAGED_SURFACE_OPEN_KEY = "hs.desk.staged-surface-open";

type StagedSurfaceOpen = { key: string; scope?: string };

/** Register a window opener for a surface key. Returns the unregister.
 * Registration flushes any queued deep-link opens for the key (a demoted
 * route can ask before the desk has mounted its windows). */
export function registerSurface(key: string, opener: SurfaceOpener) {
  surfaces.set(key, opener);
  for (let i = pendingOpens.length - 1; i >= 0; i--) {
    if (pendingOpens[i].key === key) {
      const [queued] = pendingOpens.splice(i, 1);
      opener(queued.scope, queued.options);
    }
  }
  return () => {
    if (surfaces.get(key) === opener) surfaces.delete(key);
  };
}

/** Open now if registered, else queue until the surface registers (the
 * demoted-route arrival path). */
export function openSurfaceWhenReady(key: string, scope?: string, options?: SurfaceOpenOptions): void {
  if (!openSurface(key, scope, options)) pendingOpens.push({ key, scope, options });
}

/** Stage one demoted-route intent until normal SurfaceWindows has finished
 * registering. Session storage survives the route hand-off but is consumed
 * exactly once by the normal registry; first-value recovery deliberately
 * leaves it alone because it only registers Setup. */
export function stageSurfaceOpen(key: string, scope?: string): void {
  try {
    sessionStorage.setItem(STAGED_SURFACE_OPEN_KEY, JSON.stringify({ key, scope }));
  } catch {
    // Storage can be unavailable; the legacy in-memory dispatcher is still
    // preferable to abandoning a lawful deep link.
    openSurfaceWhenReady(key, scope);
  }
}

export function consumeStagedSurfaceOpen(): StagedSurfaceOpen | null {
  try {
    const raw = sessionStorage.getItem(STAGED_SURFACE_OPEN_KEY);
    sessionStorage.removeItem(STAGED_SURFACE_OPEN_KEY);
    if (!raw) return null;
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

/** Open a surface in-world. False = not yet registered (legacy fallback). */
export function openSurface(key: string, scope?: string, options?: SurfaceOpenOptions): boolean {
  if (firstAnswers.get(key)?.(scope, options)) return true;
  const opener = surfaces.get(key);
  if (!opener) return false;
  opener(scope, options);
  return true;
}

/** Test seam. */
export function __resetSurfaces(): void {
  surfaces.clear();
  firstAnswers.clear();
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
  openSurfaceOr(PROJECT_ROOM_KEY, "/project-memory", id ? `project:${id}` : undefined);
}

/** Open a desk primitive's pull-out. On the desk this opens in place; on
 * a flat route it walks home first (`/?open=<ref>` is the arrival path). */
export function openPrimitive(ref: string): void {
  if (window.location.pathname === "/") {
    // The arrival path's exact behavior: refresh first so a just-created
    // primitive is in the items before the pull-out resolves it.
    void import("./store").then((m) =>
      m.useDesk
        .getState()
        .refresh()
        .then(() => m.useDesk.getState().openPullout(ref)),
    );
    return;
  }
  shellNavigate?.(`/?open=${encodeURIComponent(ref)}`);
}

/** Open a thread bound to a recipe (HS-151-07: replaces the retired PersonaChat). */
export function openPersona(personaId: string): void {
  void import("./newThread").then((m) => m.openNewThread({ recipe_id: personaId }));
}

/** Open a Coder session's window. PHILO-14 C2: a session that belongs to a
 * launch opens the agent's lane window (its face); a plain session keeps
 * the session window. */
export function openCoderSession(key: string, opts?: { answer?: boolean }): void {
  // Conductor F2 (K5b): `answer` opens the answer well in the window's body,
  // the steer composer recording (in the lane: the ask well's mic).
  void Promise.all([import("./steering"), import("./lane/laneStore")]).then(([steering, lane]) => {
    const launchId = lane.launchForSession(key);
    if (launchId) {
      lane.useLane.getState().open(launchId, { sessionKey: key, answer: opts?.answer });
      return;
    }
    if (lane.useLane.getState().launchId) lane.useLane.getState().close();
    steering.useSteering.getState().openSession(key, opts);
  });
}

/** PHILO-14 C2: open a launched agent's lane window by its launch id. */
export function openAgentLane(launchId: string, opts?: { sessionKey?: string | null; answer?: boolean }): void {
  void import("./lane/laneStore").then((m) => m.useLane.getState().open(launchId, opts));
}
