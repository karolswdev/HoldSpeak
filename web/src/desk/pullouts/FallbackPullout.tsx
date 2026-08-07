/** Fallback pullout for kinds with no custom content (HS-117-15). */
import { SurfaceState } from "../surface/Surface";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import type { PulloutContentProps } from "./types";

export function FallbackPullout({ object }: PulloutContentProps) {
  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <SurfaceState
          empty
          emptyLabel={`No detail view for ${object.kind}`}
          emptyGlyph="◇"
        />
      </div>
      <SurfaceFooter />
    </>
  );
}
