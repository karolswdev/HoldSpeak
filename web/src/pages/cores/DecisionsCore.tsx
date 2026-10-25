/* Betterment P4 (projects): Decisions as its own window. The one home of
 * the desk's decisions (DESIGN.md "Decisions: one home"): the same view
 * Today ▸ Decisions shows (search, the current filter, the record, its
 * Supersede), in a window that Go and the phone Go open in one press.
 *
 * Window grammar (2026-10-24): Toolbar [New decision] + Current only +
 * search → the dense list view (Decision · When · Where · State) → the
 * status bar (`5 decisions · 1 open`). A press selects a row; Enter or a
 * double press opens the decision in place: the reader (toolbar ‹ Decisions
 * and Send…, the decision as its heading, the Why as its body, the status
 * bar `● Decided just now`). */
import { DecisionsView } from "../../desk/pullouts/views/DecisionsView";
import { useDesk } from "../../desk/store";
import type { CoreProps } from "./core-types";
import "../../desk/pullouts/intelligence.css";
import "./decisions.css";

export function DecisionsCore({ scope }: CoreProps) {
  // The owner, 2026-10-25: a decision just made opens here, selected, in the
  // reader (`record:<id>`), never in Today's window.
  const recordId = scope?.startsWith("record:") ? scope.slice("record:".length) : undefined;
  return (
    <div className="decisions-window" data-testid="decisions-window">
      <section className="decisions-window-section" aria-live="polite">
        <DecisionsView
          windowed
          receiptId={recordId}
          onBackToList={() => useDesk.getState().openSurfaceWindow("open-decisions", undefined)}
        />
      </section>
    </div>
  );
}
