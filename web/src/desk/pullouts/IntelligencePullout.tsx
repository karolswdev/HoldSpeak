import { useEffect, useState } from "react";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { BriefView } from "./views/BriefView";
import { FollowThroughView } from "./views/FollowThroughView";
import { ReceiptsView } from "./views/ReceiptsView";
import type { PulloutContentProps } from "./types";
import "./intelligence.css";

type IntelligenceView = "brief" | "follow-through" | "receipts";

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

  useEffect(() => {
    window.localStorage.setItem(VIEW_STORAGE_KEY, activeView);
  }, [activeView]);

  if (object.kind !== "intelligence") return null;

  const header = (
    <IntelligenceHeader activeView={activeView} setActiveView={setActiveView} />
  );

  if (activeView === "brief") return <BriefView header={header} />;

  if (activeView === "follow-through") {
    return (
      <>
        <div className="desk-pullout-body desk-surface-body intelligence-pullout">
          {header}
          <section className="intelligence-view" aria-live="polite">
            <FollowThroughView />
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
          <ReceiptsView />
        </section>
      </div>
      <SurfaceFooter />
    </>
  );
}
