/** HS-95-03 — the shell's surface dispatcher (Constitution, Article I):
 * chrome and shelves never navigate to feature routes; they ask the OS to
 * open a surface. Stories HS-95-05..08 register their windows here; an
 * unregistered surface reports false so callers can fall back to the
 * legacy route until every surface lives in-world (HS-95-08 removes the
 * fallbacks and the guard keeps them out). */

export type SurfaceOpener = (scope?: string) => void;

const surfaces = new Map<string, SurfaceOpener>();
const pendingOpens: Array<{ key: string; scope?: string }> = [];

/** Register a window opener for a surface key. Returns the unregister.
 * Registration flushes any queued deep-link opens for the key (a demoted
 * route can ask before the desk has mounted its windows). */
export function registerSurface(key: string, opener: SurfaceOpener) {
  surfaces.set(key, opener);
  for (let i = pendingOpens.length - 1; i >= 0; i--) {
    if (pendingOpens[i].key === key) {
      const [queued] = pendingOpens.splice(i, 1);
      opener(queued.scope);
    }
  }
  return () => {
    if (surfaces.get(key) === opener) surfaces.delete(key);
  };
}

/** Open now if registered, else queue until the surface registers (the
 * demoted-route arrival path). */
export function openSurfaceWhenReady(key: string, scope?: string): void {
  if (!openSurface(key, scope)) pendingOpens.push({ key, scope });
}

/** Open a surface in-world. False = not yet registered (legacy fallback). */
export function openSurface(key: string, scope?: string): boolean {
  const opener = surfaces.get(key);
  if (!opener) return false;
  opener(scope);
  return true;
}

/** Test seam. */
export function __resetSurfaces(): void {
  surfaces.clear();
}

/** The router's navigate, delegated once by the app shell so cores and
 * chrome can fall back to a legacy route without importing the router. */
let shellNavigate: ((href: string) => void) | null = null;

export function setShellNavigator(nav: (href: string) => void): void {
  shellNavigate = nav;
}

/** Open a surface in-world, else navigate to its legacy route. */
export function openSurfaceOr(
  key: string,
  fallbackHref: string,
  scope?: string,
): void {
  if (openSurface(key, scope)) return;
  shellNavigate?.(fallbackHref);
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

/** Open a Persona's chat window (the one chat surface). */
export function openPersona(personaId: string): void {
  void import("./store").then((m) => m.useDesk.getState().openChat(personaId));
}

/** Open a Coder session's window (the one session surface). */
export function openCoderSession(key: string): void {
  void import("./steering").then((m) =>
    m.useSteering.getState().openSession(key),
  );
}
