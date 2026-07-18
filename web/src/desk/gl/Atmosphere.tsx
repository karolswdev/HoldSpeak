/** HS-95-01 — the diorama room's atmosphere (HS-71-01 values), CSS-only.
 * The base gradient paints once; the spotlight pulse animates transform and
 * opacity only (compositor work, never layout/paint). The dust motes that
 * used to live here on a 2D canvas render in the world's GL scene now;
 * `Stage.tsx` is retired. */
export function Atmosphere() {
  return (
    <div className="desk-stage" aria-hidden="true">
      <div className="desk-stage-glow" />
    </div>
  );
}
