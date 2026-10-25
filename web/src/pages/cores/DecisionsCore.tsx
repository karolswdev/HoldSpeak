/* Betterment P4 (projects): Decisions as its own window. The one home of
 * the desk's decisions (DESIGN.md "Decisions: one home"): the same view
 * Today ▸ Decisions shows (search, the current filter, the record, its
 * Supersede), in a window that Go and the phone Go open in one press.
 *
 * Window grammar (2026-10-24): Toolbar [New decision] + Current only +
 * search → the dense list view (Decision · When · Where · State) → the
 * status bar (`5 decisions · 1 open`). A press selects a row; Enter or a
 * double press opens the decision in place. */
import { DecisionsView } from "../../desk/pullouts/views/DecisionsView";
import type { CoreProps } from "./core-types";
import "../../desk/pullouts/intelligence.css";
import "./decisions.css";

export function DecisionsCore(_props: CoreProps) {
  return (
    <div className="decisions-window" data-testid="decisions-window">
      <section className="decisions-window-section" aria-live="polite">
        <DecisionsView windowed />
      </section>
    </div>
  );
}
