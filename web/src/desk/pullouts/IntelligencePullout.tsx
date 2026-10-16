import { Activity, useContext, useEffect, useLayoutEffect, useRef, useState, type ReactNode, type UIEventHandler } from "react";
import { createPortal } from "react-dom";
import { Button } from "../../components/signal/Signal";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { FootSlotContext } from "../surface/foot";
import { INTELLIGENCE_NAVIGATE, type IntelligenceNavigation, type IntelligenceView } from "../intelligenceNavigation";
import { BriefView } from "./views/BriefView";
import { FollowThroughView } from "./views/FollowThroughView";
import { DecisionsView } from "./views/DecisionsView";
import { TodayView } from "./views/TodayView";
import type { PulloutContentProps } from "./types";
import "./intelligence.css";

const VIEW_STORAGE_KEY = "hs.desk.intelligence-view";

const VIEWS: ReadonlyArray<{ id: IntelligenceView; label: string }> = [
  // PHILO-17 (owner pick, concept C): the day as a timeline leads.
  { id: "today", label: "Day" },
  { id: "brief", label: "Brief" },
  { id: "follow-through", label: "Follow-through" },
  { id: "receipts", label: "Decisions" },
];

function initialView(): IntelligenceView {
  if (typeof window === "undefined") return "today";
  const saved = window.localStorage.getItem(VIEW_STORAGE_KEY);
  return VIEWS.some((view) => view.id === saved)
    ? (saved as IntelligenceView)
    : "today";
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
        <Button
          variant="chrome"
          key={view.id}
          className={`intelligence-segment${activeView === view.id ? " is-active" : ""}`}
          aria-pressed={activeView === view.id}
          onClick={() => selectView(view.id)}
        >
          {view.label}
        </Button>
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

// Activity hides its own DOM, but React leaves portals in their target.
// Keep each retained view's foot in a target whose visibility changes at
// the shell boundary, so inactive actions cannot escape into the frame.
function RetainedView({ active, children, onScroll }: { active: boolean; children: ReactNode; onScroll: UIEventHandler<HTMLDivElement> }) {
  const frameFoot = useContext(FootSlotContext);
  const [viewFoot, setViewFoot] = useState<HTMLDivElement | null>(null);
  return <>
    {frameFoot ? createPortal(<div ref={setViewFoot} style={{ display: active ? "contents" : "none" }} />, frameFoot) : null}
    <Activity mode={active ? "visible" : "hidden"}>
      <FootSlotContext.Provider value={frameFoot ? viewFoot : null}>
        <div style={{ display: "contents" }} onScrollCapture={onScroll}>{children}</div>
      </FootSlotContext.Provider>
    </Activity>
  </>;
}

/** Desk-wide intelligence shell. Its three views gain their material in HS-128-02–04. */
export function IntelligencePullout({ object }: PulloutContentProps) {
  // HS-132-08 — one navigation state. `activeView` used to live beside it, so
  // a segment click moved the view while a dispatched drill filter stayed on,
  // hiding lanes nothing named.
  const [navigation, setNavigation] = useState<IntelligenceNavigation>(() => ({ view: initialView() }));
  const activeView = navigation.view;
  const [visited, setVisited] = useState<Set<IntelligenceView>>(() => new Set([activeView]));
  const scrollPositions = useRef(new Map<IntelligenceView, Map<HTMLElement, { top: number; left: number }>>());

  useEffect(() => {
    setVisited((current) => current.has(activeView) ? current : new Set([...current, activeView]));
  }, [activeView]);
  useLayoutEffect(() => {
    for (const [node, position] of scrollPositions.current.get(activeView) ?? []) {
      node.scrollTop = position.top;
      node.scrollLeft = position.left;
    }
  }, [activeView]);

  useEffect(() => {
    window.localStorage.setItem(VIEW_STORAGE_KEY, activeView);
  }, [activeView]);

  useEffect(() => {
    const navigate = (event: Event) => {
      const request = (event as CustomEvent<IntelligenceNavigation>).detail;
      // PHILO-17 (owner): the tabs are the navigation, so a drill keeps no
      // BACK step; the request is the view.
      setNavigation(request);
    };
    window.addEventListener(INTELLIGENCE_NAVIGATE, navigate);
    return () => window.removeEventListener(INTELLIGENCE_NAVIGATE, navigate);
  }, []);

  if (object.kind !== "intelligence") return null;

  // A segment click is navigation, not a modifier: it lands on the bare view
  // and takes every drill filter with it.
  const selectView = (view: IntelligenceView) => setNavigation({ view });
  const clearOverdueOnly = () =>
    setNavigation((current) => ({ ...current, overdueOnly: undefined }));
  const header = (
    <div className="intelligence-header">
      {/* PHILO-17 (owner): the tabs are the navigation; no BACK above them. */}
      <IntelligenceHeader activeView={activeView} selectView={selectView} />
      <FilterTokens navigation={navigation} clearOverdueOnly={clearOverdueOnly} />
    </div>
  );

  const brief = <BriefView header={header} onOpenFollowThrough={(followThroughId) => {
    setNavigation({ view: "follow-through", followThroughId });
  }} />;
  const followThrough = (
      <>
        <div className="desk-pullout-body desk-surface-body intelligence-pullout">
          {header}
          <section className="intelligence-view" aria-live="polite">
            <FollowThroughView overdueOnly={navigation.overdueOnly} focusCardId={navigation.followThroughId} onClearFilter={clearOverdueOnly} onOpenReceipts={(receiptId) => {
              setNavigation({ view: "receipts", receiptId });
            }} />
          </section>
        </div>
        <SurfaceFooter />
      </>
    );

  const decisions = (
    <>
      <div className="desk-pullout-body desk-surface-body intelligence-pullout">
        {header}
        <section className="intelligence-view" aria-live="polite">
          <DecisionsView initialQuery={navigation.receiptQuery} initialWhyOnly={navigation.whyOnly} workRef={navigation.receiptWorkRef} receiptId={navigation.receiptId} decisionId={navigation.decisionId} decisionNonce={navigation.nonce} />
        </section>
      </div>
      <SurfaceFooter />
    </>
  );
  const views = { today: <TodayView header={header} />, brief, "follow-through": followThrough, receipts: decisions };
  // A source round trip keeps the actual view's state and scrolling DOM.
  // Hidden views suspend effects; their frame feet are hidden separately.
  return VIEWS.filter((view) => visited.has(view.id) || view.id === activeView).map((view) => (
    <RetainedView key={view.id} active={view.id === activeView} onScroll={(event) => {
        const node = event.target as HTMLElement;
        const positions = scrollPositions.current.get(view.id) ?? new Map();
        positions.set(node, { top: node.scrollTop, left: node.scrollLeft });
        scrollPositions.current.set(view.id, positions);
      }}>{views[view.id]}</RetainedView>
  ));
}
