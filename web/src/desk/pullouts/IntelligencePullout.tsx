import { useEffect, useRef, useState } from "react";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { INTELLIGENCE_NAVIGATE, type IntelligenceNavigation, type IntelligenceView } from "../intelligenceNavigation";
import { BriefView } from "./views/BriefView";
import { FollowThroughView } from "./views/FollowThroughView";
import { ReceiptsView } from "./views/ReceiptsView";
import type { PulloutContentProps } from "./types";
import "./intelligence.css";

const VIEW_STORAGE_KEY = "hs.desk.intelligence-view";

const VIEWS: ReadonlyArray<{ id: IntelligenceView; label: string }> = [
  { id: "brief", label: "Brief" },
  { id: "follow-through", label: "Follow-through" },
  { id: "receipts", label: "Receipts" },
];

function initialView(): IntelligenceView {
  if (typeof window === "undefined") return "brief";
  const saved = window.localStorage.getItem(VIEW_STORAGE_KEY);
  return VIEWS.some((view) => view.id === saved)
    ? (saved as IntelligenceView)
    : "brief";
}

function IntelligenceHeader({
  activeView,
  setActiveView,
}: {
  activeView: IntelligenceView;
  setActiveView: (view: IntelligenceView) => void;
}) {
  return (
    <div className="intelligence-segments" role="group" aria-label="Intelligence view">
      {VIEWS.map((view) => (
        <button
          key={view.id}
          type="button"
          className={`intelligence-segment${activeView === view.id ? " is-active" : ""}`}
          aria-pressed={activeView === view.id}
          onClick={() => setActiveView(view.id)}
        >
          {view.label}
        </button>
      ))}
    </div>
  );
}

/** Desk-wide intelligence shell. Its three views gain their material in HS-128-02–04. */
export function IntelligencePullout({ object }: PulloutContentProps) {
  const [activeView, setActiveView] = useState<IntelligenceView>(initialView);
  const [navigation, setNavigation] = useState<IntelligenceNavigation>({ view: initialView() });
  const [history, setHistory] = useState<IntelligenceNavigation[]>([]);
  const navigationRef = useRef(navigation);
  navigationRef.current = navigation;

  useEffect(() => {
    window.localStorage.setItem(VIEW_STORAGE_KEY, activeView);
  }, [activeView]);

  useEffect(() => {
    const navigate = (event: Event) => {
      const request = (event as CustomEvent<IntelligenceNavigation>).detail;
      const current = navigationRef.current;
      // HS-129-03 — the dock opens Brief by dispatching its current destination;
      // that is not a drill and must not mint a phantom BACK step.
      const sameDestination = request.view === current.view
        && request.followThroughId === current.followThroughId
        && request.overdueOnly === current.overdueOnly
        && request.receiptId === current.receiptId
        && request.receiptQuery === current.receiptQuery
        && request.whyOnly === current.whyOnly
        && request.receiptWorkRef === current.receiptWorkRef;
      if (!sameDestination)
        setHistory((history) => [...history, current]);
      setNavigation(request);
      setActiveView(request.view);
    };
    window.addEventListener(INTELLIGENCE_NAVIGATE, navigate);
    return () => window.removeEventListener(INTELLIGENCE_NAVIGATE, navigate);
  }, []);

  if (object.kind !== "intelligence") return null;

  const goBack = () => {
    const previous = history.at(-1);
    if (!previous) return;
    setHistory((current) => current.slice(0, -1));
    setNavigation(previous);
    setActiveView(previous.view);
  };
  const header = (
    <div className="intelligence-header">
      {history.length ? <button type="button" className="receipt-back" onClick={goBack}>← BACK</button> : null}
      <IntelligenceHeader activeView={activeView} setActiveView={setActiveView} />
    </div>
  );

  if (activeView === "brief") return <BriefView header={header} onOpenFollowThrough={(followThroughId) => {
    setHistory((current) => [...current, navigation]);
    setNavigation({ view: "follow-through", followThroughId });
    setActiveView("follow-through");
  }} />;

  if (activeView === "follow-through") {
    return (
      <>
        <div className="desk-pullout-body desk-surface-body intelligence-pullout">
          {header}
          <section className="intelligence-view" aria-live="polite">
            <FollowThroughView overdueOnly={navigation.overdueOnly} focusCardId={navigation.followThroughId} onOpenReceipts={(receiptId) => {
              setHistory((current) => [...current, navigation]);
              setNavigation({ view: "receipts", receiptId });
              setActiveView("receipts");
            }} />
          </section>
        </div>
        <SurfaceFooter />
      </>
    );
  }

  return (
    <>
      <div className="desk-pullout-body desk-surface-body intelligence-pullout">
        {header}
        <section className="intelligence-view" aria-live="polite">
          <ReceiptsView initialQuery={navigation.receiptQuery} initialWhyOnly={navigation.whyOnly} workRef={navigation.receiptWorkRef} receiptId={navigation.receiptId} />
        </section>
      </div>
      <SurfaceFooter />
    </>
  );
}
