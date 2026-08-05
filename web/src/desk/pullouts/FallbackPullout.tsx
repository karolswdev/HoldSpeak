/** Fallback pullout for kinds with no custom content (HS-117-15). */
import type { PrimitiveKind } from "../../lib/primitives";

export function FallbackPullout({ kind }: { kind: PrimitiveKind }) {
  return (
    <>
      <div className="desk-pullout-body desk-surface-body" />
      <footer className="desk-pullout-foot" />
    </>
  );
}
