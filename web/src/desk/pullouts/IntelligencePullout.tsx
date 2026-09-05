import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { INTELLIGENCE_NAVIGATE, type IntelligenceNavigation, type IntelligenceView } from "../intelligenceNavigation";
import { BriefView } from "./views/BriefView";
import { FollowThroughView } from "./views/FollowThroughView";
import { DecisionsView } from "./views/DecisionsView";
import type { PulloutContentProps } from "./types";
import "./intelligence.css";

const VIEW_STORAGE_KEY = "hs.desk.intelligence-view";

const VIEWS: ReadonlyArray<{ id: IntelligenceView; label: string }> = [
  { id: "brief", label: "Brief" },
  { id: "follow-through", label: "Follow-through" },
  { id: "receipts", label: "Decisions" },
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
  selectView,
}: {
  activeView: IntelligenceView;
  selectView: (view: IntelligenceView) => void;
}) {
  return (
    <div className="intelligence-segments" role="group" aria-label="Intelligence view">
      {VIEWS.map((view) => (
        <button
          key={view.id}
          type="button"
          className={`intelligence-segment${activeView === view.id ? " is-active" : ""}`}
          aria-pressed={activeView === view.id}
          onClick={() => selectView(view.id)}
        >
          {view.label}
        </button>
      ))}
    </div>
  );
}

/**
 * HS-132-08 — a drill filter is never invisible.
 *
 * Following the dock's "N overdue" chip narrows the board; the token names
 * that narrowing and dismisses it. Nothing else may hide lanes silently.
 */
function FilterTokens({
  navigation,
  clearOverdueOnly,
}: {
  navigation: IntelligenceNavigation;
  clearOverdueOnly: () => void;
}) {
  if (!navigation.overdueOnly) return null;
  return (
    <div className="intelligence-filters" aria-label="Active filters">
      <Button
        dense
        aria-label="Clear filter OVERDUE ONLY"
        onClick={clearOverdueOnly}
      >
        FILTER · OVERDUE ONLY <span aria-hidden="true">✕</span>
      </Button>
    </div>
  );
}

/** Desk-wide intelligence shell. Its three views gain their material in HS-128-02–04. */
export function IntelligencePullout({ object }: PulloutContentProps) {
  // HS-132-08 — one navigation state. `activeView` used to live beside it, so
  // a segment click moved the view while a dispatched drill filter stayed on,
  // hiding lanes nothing named.
  const [navigation, setNavigation] = useState<IntelligenceNavigation>(() => ({ view: initialView() }));
  const [history, setHistory] = useState<IntelligenceNavigation[]>([]);
  const activeView = navigation.view;
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
  };
  // A segment click is navigation, not a modifier: it lands on the bare view
  // and takes every drill filter with it.
  const selectView = (view: IntelligenceView) => setNavigation({ view });
  const clearOverdueOnly = () =>
    setNavigation((current) => ({ ...current, overdueOnly: undefined }));
  const header = (
    <div className="intelligence-header">
      {history.length ? <Button dense variant="ghost" className="receipt-back" onClick={goBack}>BACK</Button> : null}
      <IntelligenceHeader activeView={activeView} selectView={selectView} />
      <FilterTokens navigation={navigation} clearOverdueOnly={clearOverdueOnly} />
    </div>
  );

  if (activeView === "brief") return <BriefView header={header} onOpenFollowThrough={(followThroughId) => {
    setHistory((current) => [...current, navigation]);
    setNavigation({ view: "follow-through", followThroughId });
  }} />;

  if (activeView === "follow-through") {
    return (
      <>
        <div className="desk-pullout-body desk-surface-body intelligence-pullout">
          {header}
          <section className="intelligence-view" aria-live="polite">
            <FollowThroughView overdueOnly={navigation.overdueOnly} focusCardId={navigation.followThroughId} onClearFilter={clearOverdueOnly} onOpenReceipts={(receiptId) => {
              setHistory((current) => [...current, navigation]);
              setNavigation({ view: "receipts", receiptId });
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
          <DecisionsView initialQuery={navigation.receiptQuery} initialWhyOnly={navigation.whyOnly} workRef={navigation.receiptWorkRef} receiptId={navigation.receiptId} />
        </section>
      </div>
      <SurfaceFooter />
    </>
  );
}
