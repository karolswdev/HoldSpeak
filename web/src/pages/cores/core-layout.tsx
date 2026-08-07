// HS-117-07 — shared layout helpers extracted from the 16 core page
// components. renderHeroSlot: the hero ternary (9+ cores).
// CoreResourceGuard: the SurfaceState loading/error/empty guard
// (12 cores).

import type { ReactNode } from "react";
import { SurfaceState, SurfaceVerbs } from "../../desk/surface/Surface";
import type { CoreProps } from "./core-types";

/* ── renderHeroSlot ────────────────────────────────────────── */

/** Replaces the identical `hero ? hero(verbs) : <SurfaceVerbs>...`
 *  ternary copied across 9+ cores. When verbs is null/undefined and
 *  no status is given, the fallback renders nothing (the
 *  hero-passes-null variant used by DictationCore, CompanionCore etc). */
export function renderHeroSlot(
  hero: CoreProps["hero"],
  verbs: ReactNode,
  status?: ReactNode,
): ReactNode {
  if (verbs == null && status == null) return hero ? hero(null) : null;
  return hero ? hero(verbs) : (
    <SurfaceVerbs status={status}>{verbs}</SurfaceVerbs>
  );
}

/* ── CoreResourceGuard ─────────────────────────────────────── */

/** Wraps the SurfaceState loading/error/empty guard that 12 cores
 *  repeat with identical props. Pass `empty` explicitly (most cores
 *  derive it from filtered rows, not raw resource data). */
export function CoreResourceGuard({
  resource,
  empty,
  emptyLabel,
  emptyGlyph,
  emptyImage,
  children,
}: {
  resource: { loading: boolean; error: string; reload(): unknown };
  empty?: boolean;
  emptyLabel?: string;
  emptyGlyph?: string;
  emptyImage?: string;
  children: ReactNode;
}) {
  return (
    <SurfaceState
      loading={resource.loading}
      error={resource.error}
      empty={empty}
      emptyLabel={emptyLabel}
      emptyGlyph={emptyGlyph}
      emptyImage={emptyImage}
      onRetry={() => void resource.reload()}
    >
      {children}
    </SurfaceState>
  );
}
