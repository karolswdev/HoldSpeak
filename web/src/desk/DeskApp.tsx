// The Desk route — the web app's front door (HS-73-02).
//
// React + Vite in the one Web tree. Full-bleed: the world owns the viewport;
// chrome is the floating
// minimal cluster (DeskChrome); a fresh desk shows the guiding empty state.
// HS-135-06: the Chair is HOME at `/`. The spatial floor stays intact
// behind a dock button (counsel ruling B.Q1).
import { useCallback, useEffect, useState } from "react";
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
import { ScheduleCreateWindow } from "./components/ScheduleCreateWindow";
import { AttentionDrawer } from "./components/AttentionDrawer";
import { GlassDropLayer } from "./components/GlassDropLayer";
import { DeskToolInspector } from "./components/DeskToolInspector";
import { Dock, Expose, SnapGhost, Switcher } from "./components/DeskWindow";
import { SurfaceWindows } from "./components/SurfaceWindows";
import { TrustWindow } from "./components/TrustWindow";
import { InlineEditor } from "./components/InlineEditor";
import { objectByRef } from "./world";
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
  const loading = useDesk((s) => s.loading);
  const viewMode = useDesk((s) => s.viewMode);
  const editingId = useDesk((s) => s.editingId);
  const error = useDesk((s) => s.error);
  const { refresh } = useDesk.getState();
  const [refreshFailure, setRefreshFailure] = useState<string | null>(null);

  const refreshDesk = useCallback(async () => {
    setRefreshFailure(null);
    try {
      await refresh();
      const open = new URLSearchParams(window.location.search).get("open");
      if (open) useDesk.getState().openPullout(open);
    } catch (caught) {
      setRefreshFailure(
        caught instanceof Error && caught.message
          ? caught.message
          : "HoldSpeak could not load your Desk.",
      );
    }
  }, [refresh]);

  // HS-135-06: Chair is HOME; the floor stays one dock-button away.
  const surface = useChairState((s) => s.surface);
  // `updatedAt` changes only after the first combined desk/setup refresh has
  // settled. Keep the room quiet while that server-owned arrival choice is
  // unknown; later background refreshes preserve the normal Chair.
  const setupFailure =
    refreshFailure ??
    (updatedAt !== null && setup === null
      ? error || "HoldSpeak could not read setup status."
      : null);
  const setupPending = !setupFailure && updatedAt === null && (loading || setup === null);
  const arrivalRequired = setup?.arrival_required === true;
  // HS-140-01: first value owns HOME. A stale Floor preference must not
  // detour a fresh owner away from the one capture path.
  const showFloor = surface === "floor" && !arrivalRequired;

  useEffect(() => {
    void refreshDesk();
    void useProjections.getState().refresh(true);
  }, [refreshDesk]);

  const total = Object.values(items).reduce((n, l) => n + l.length, 0);
  const empty = updatedAt !== null && total === 0;

  if (setupPending || setupFailure) {
    return (
      <div
        className="desk-next desk-arrival-pending"
        id="desk-next"
        aria-busy="true"
        aria-label="Preparing HoldSpeak"
      >
        {setupFailure ? (
          <div role="alert">
            <p>HoldSpeak could not prepare your Desk: {setupFailure}</p>
            <button type="button" onClick={() => void refreshDesk()}>
              Retry
            </button>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="desk-next" id="desk-next">
      {/* GL layers render only when the spatial floor is active. */}
      {showFloor && <Atmosphere />}
      {showFloor && <GlassDropLayer />}
      {!arrivalRequired && <DeskChrome showDailyStarts={!empty} />}
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
        <ChairHome arrivalRequired={arrivalRequired} />
      )}
      {/* HS-135-13 fix: the InlineEditor must render on the Chair too,
          not only the Floor (DeskListView/WorldStage own their own copy).
          Without this, "New Agent" from a Workbench on the Chair sets
          editingId but nothing renders the editor. */}
      {!arrivalRequired && !showFloor && editingId && (() => {
        const o = objectByRef(items, editingId);
        return o ? <InlineEditor key={o.id} o={o} u={{ x: 0.5, y: 0.4 }} /> : null;
      })()}
      {!arrivalRequired && chatPersonaId && <PersonaChat personaId={chatPersonaId} />}
      {!arrivalRequired && <DeskToolInspector />}
      {!arrivalRequired && <MissionControlConveyor />}
      {!arrivalRequired && <DeliveryBoard />}
      {!arrivalRequired && <DeliveryDossierWindow />}
      {!arrivalRequired && <DeliveryTerminalWindow />}
      {!arrivalRequired && roadmapWindows.map((roadmap) => (
        <RoadmapWindow key={roadmap.slug} slug={roadmap.slug} origin={roadmap.origin} />
      ))}
      {!arrivalRequired && repositoryWindows.map((repository) => (
        <RepoWindow key={repository.id} repositoryId={repository.id} origin={repository.origin} />
      ))}
      {!arrivalRequired && workbenchWindows.map((wb) => (
        <WorkbenchWindow key={wb.id} workbenchId={wb.id} origin={wb.origin} />
      ))}
      {!arrivalRequired && <NewWorkbenchChooser />}
      {!arrivalRequired && <ScheduleCreateWindow />}
      {!arrivalRequired && <PanePicker />}
      {!arrivalRequired && <SessionPullout />}
      {!arrivalRequired && <AttentionDrawer />}
      {/* Recovery remains direct and in-place: FirstWords opens Setup through
          this existing surface registry without restoring the whole Desk. */}
      <SurfaceWindows
        key={arrivalRequired ? "first-value-recovery" : "desk"}
        firstValueRecoveryOnly={arrivalRequired}
      />
      {!arrivalRequired && <TrustWindow />}
      {!arrivalRequired && <Dock center={!empty ? <RecordOrb /> : null} />}
      {!arrivalRequired && <SnapGhost />}
      {!arrivalRequired && <Expose />}
      {!arrivalRequired && <Switcher />}
    </div>
  );
}
