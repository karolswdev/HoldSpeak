/** HS-95-03 — the shell's surface dispatcher (Constitution, Article I):
 * chrome and shelves never navigate to feature routes; they ask the OS to
 * open a surface. Stories HS-95-05..08 register their windows here; an
 * unregistered surface reports false so callers can fall back to the
 * legacy route until every surface lives in-world (HS-95-08 removes the
 * fallbacks and the guard keeps them out). */

export type SurfaceOpener = (scope?: string) => void;

const surfaces = new Map<string, SurfaceOpener>();

/** Register a window opener for a surface key. Returns the unregister. */
export function registerSurface(key: string, opener: SurfaceOpener) {
  surfaces.set(key, opener);
  return () => {
    if (surfaces.get(key) === opener) surfaces.delete(key);
  };
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
