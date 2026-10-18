/** Betterment daily D4: the Today window is one page (no wings). A drill
 *  to a decision (`receipts`) shows the Decisions page in the same window,
 *  with `Today` to come back; Today keeps its state and scroll meanwhile.
 *  The Follow-through wing is parked (`views/_parked`); its rows and verbs
 *  are the Needs-you rows. */
import { Activity, useContext, useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Button } from "../../components/signal/Signal";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { FootSlotContext } from "../surface/foot";
import { INTELLIGENCE_NAVIGATE, type IntelligenceNavigation } from "../intelligenceNavigation";
import { DecisionsView } from "./views/DecisionsView";
import { TodayView } from "./views/TodayView";
import type { PulloutContentProps } from "./types";
import "./intelligence.css";

// Activity hides its own DOM, but React leaves portals in their target.
// Keep each retained view's foot in a target whose visibility changes at
// the shell boundary, so inactive actions cannot escape into the frame.
function RetainedView({ active, children }: { active: boolean; children: ReactNode }) {
  const frameFoot = useContext(FootSlotContext);
  const [viewFoot, setViewFoot] = useState<HTMLDivElement | null>(null);
  return <>
    {frameFoot ? createPortal(<div ref={setViewFoot} style={{ display: active ? "contents" : "none" }} />, frameFoot) : null}
    <Activity mode={active ? "visible" : "hidden"}>
      <FootSlotContext.Provider value={frameFoot ? viewFoot : null}>
        <div style={{ display: "contents" }}>{children}</div>
      </FootSlotContext.Provider>
    </Activity>
  </>;
}

export function IntelligencePullout({ object }: PulloutContentProps) {
  const [navigation, setNavigation] = useState<IntelligenceNavigation>({ view: "today" });
  // The last Decisions request: kept while Today is in front, so the page
  // comes back as it was.
  const [receipts, setReceipts] = useState<IntelligenceNavigation | null>(null);
  useEffect(() => {
    const navigate = (event: Event) => {
      const request = (event as CustomEvent<IntelligenceNavigation>).detail;
      if (request.view === "follow-through") return; // the Needs-you window's (parked wing)
      if (request.view === "receipts") setReceipts(request);
      setNavigation(request);
    };
    window.addEventListener(INTELLIGENCE_NAVIGATE, navigate);
    return () => window.removeEventListener(INTELLIGENCE_NAVIGATE, navigate);
  }, []);

  if (object.kind !== "intelligence") return null;
  const decisions = navigation.view === "receipts";
  const sinceRequest = navigation.view === "brief" ? navigation.nonce ?? 1 : 0;
  return <>
    <RetainedView active={!decisions}>
      <TodayView sinceRequest={sinceRequest} />
    </RetainedView>
    {receipts ? (
      <RetainedView active={decisions}>
        <div className="desk-pullout-body desk-surface-body intelligence-pullout">
          <div className="intelligence-header">
            <Button dense variant="ghost" data-testid="intelligence-today" onClick={() => setNavigation({ view: "today" })}>Today</Button>
          </div>
          <section className="intelligence-view" aria-live="polite">
            <DecisionsView initialQuery={receipts.receiptQuery} initialWhyOnly={receipts.whyOnly} workRef={receipts.receiptWorkRef} receiptId={receipts.receiptId} decisionId={receipts.decisionId} decisionNonce={receipts.nonce} />
          </section>
        </div>
        <SurfaceFooter />
      </RetainedView>
    ) : null}
  </>;
}
