/* Betterment P4 (projects): Decisions as its own window. The one home of
 * the desk's decisions (DESIGN.md "Decisions: one home"): the same view
 * Today ▸ Decisions shows (search, the current filter, the record, its
 * Supersede), in a window that Go and the phone Go open in one press. */
import { DecisionsView } from "../../desk/pullouts/views/DecisionsView";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import type { CoreProps } from "./core-types";
import "../../desk/pullouts/intelligence.css";

export function DecisionsCore(_props: CoreProps) {
  return (
    <>
      <div className="desk-surface-body intelligence-pullout" data-testid="decisions-window">
        <section className="intelligence-view" aria-live="polite">
          <DecisionsView />
        </section>
      </div>
      <SurfaceFooter />
    </>
  );
}
