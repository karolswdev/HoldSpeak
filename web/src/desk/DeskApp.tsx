// The Desk route — the web app's front door (HS-73-02).
//
// React + Vite in the one Web tree. Full-bleed: the world owns the viewport;
// chrome is the floating
// minimal cluster (DeskChrome); a fresh desk shows the guiding empty state.
// HS-135-06: the Chair is HOME at `/`. The spatial floor stays intact
// behind a dock button (counsel ruling B.Q1).
import { useEffect } from "react";
import { defaultViewFor, useDesk } from "./store";
import { useChairState } from "./chairState";
import { ChairHome } from "./chair";
import { Atmosphere } from "./gl/Atmosphere";
import { WorldStage } from "./gl/WorldStage";
import { DeskListView } from "./components/DeskListView";
import { DeskChrome } from "./components/DeskChrome";
import { EmptyDesk } from "./components/EmptyDesk";
import { RecordOrb } from "./components/RecordOrb";
import { PersonaChat } from "./components/PersonaChat";
import { MissionControlConveyor } from "./components/MissionControlConveyor";
import { SessionPullout, PanePicker } from "./components/SessionPullout";
import { DeliveryBoard } from "./components/DeliveryBoard";
import { DeliveryDossierWindow } from "./components/DeliveryDossierWindow";
import { DeliveryTerminalWindow } from "./components/DeliveryTerminalWindow";
import { RoadmapWindow } from "./components/RoadmapWindow";
import { RepoWindow } from "./components/RepoWindow";
import { WorkbenchWindow } from "./components/WorkbenchWindow";
import { NewWorkbenchChooser } from "./components/NewWorkbenchChooser";
import { AttentionDrawer } from "./components/AttentionDrawer";
import { GlassDropLayer } from "./components/GlassDropLayer";
import { DeskToolInspector } from "./components/DeskToolInspector";
import { Dock, Expose, SnapGhost, Switcher } from "./components/DeskWindow";
import { SurfaceWindows } from "./components/SurfaceWindows";
import { TrustWindow } from "./components/TrustWindow";
import { useProjections } from "./projections";
import "./desk.css";

export default function DeskApp() {
  const items = useDesk((s) => s.items);
  const updatedAt = useDesk((s) => s.updatedAt);
  const chatPersonaId = useDesk((s) => s.chatPersonaId);
  const roadmapWindows = useDesk((s) => s.roadmapWindows);
  const repositoryWindows = useDesk((s) => s.repositoryWindows);
  const workbenchWindows = useDesk((s) => s.workbenchWindows);
  const setup = useDesk((s) => s.setup);
  const viewMode = useDesk((s) => s.viewMode);
  const { refresh } = useDesk.getState();

  // HS-135-06: Chair is HOME; the floor stays one dock-button away.
  const surface = useChairState((s) => s.surface);
  const showFloor = surface === "floor";

  useEffect(() => {
    void refresh().then(() => {
      const open = new URLSearchParams(window.location.search).get("open");
      if (open) useDesk.getState().openPullout(open);
    });
    void useProjections.getState().refresh(true);
  }, []);

  const total = Object.values(items).reduce((n, l) => n + l.length, 0);
  const empty = updatedAt !== null && total === 0;

  return (
    <div className="desk-next" id="desk-next">
      {/* GL layers render only when the spatial floor is active. */}
      {showFloor && <Atmosphere />}
      {showFloor && <GlassDropLayer />}
      <DeskChrome showDailyStarts={!empty} />
      {showFloor ? (
        empty ? (
          <EmptyDesk arrivalRequired={setup?.arrival_required === true} />
        ) : defaultViewFor(viewMode, total, window.innerWidth <= 720) ===
          "list" ? (
          <DeskListView />
        ) : (
          <WorldStage />
        )
      ) : (
        <ChairHome />
      )}
      {chatPersonaId && <PersonaChat personaId={chatPersonaId} />}
      <DeskToolInspector />
      <MissionControlConveyor />
      <DeliveryBoard />
      <DeliveryDossierWindow />
      <DeliveryTerminalWindow />
      {roadmapWindows.map((roadmap) => (
        <RoadmapWindow key={roadmap.slug} slug={roadmap.slug} origin={roadmap.origin} />
      ))}
      {repositoryWindows.map((repository) => (
        <RepoWindow key={repository.id} repositoryId={repository.id} origin={repository.origin} />
      ))}
      {workbenchWindows.map((wb) => (
        <WorkbenchWindow key={wb.id} workbenchId={wb.id} origin={wb.origin} />
      ))}
      <NewWorkbenchChooser />
      <PanePicker />
      <SessionPullout />
      <AttentionDrawer />
      <SurfaceWindows />
      <TrustWindow />
      <Dock center={!empty ? <RecordOrb /> : null} />
      <SnapGhost />
      <Expose />
      <Switcher />
    </div>
  );
}
