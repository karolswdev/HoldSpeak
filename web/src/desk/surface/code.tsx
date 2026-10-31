// SurfaceCode on its own (PG-DIRECTION DIR2, 2026-10-31): the briefing page
// composes it without the desk's auth client; ./Surface.tsx re-exports it.
// Its material (surface.css) comes from ./Surface.tsx on the desk and from
// web/src/briefing/briefing.css on the page (see ./fold.tsx).
import type { ReactNode } from "react";

/** A raw trace (JSON, hook output) on the surface material. */
export function SurfaceCode({ children }: { children: ReactNode }) {
  return <pre className="surface-code">{children}</pre>;
}
