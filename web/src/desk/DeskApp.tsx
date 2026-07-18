// The Desk route — the web app's front door (HS-73-02).
//
// React + Vite in the one Web tree. Full-bleed: the world owns the viewport;
// chrome is the floating
// minimal cluster (DeskChrome); a fresh desk shows the guiding empty state.
import { useEffect } from "react";
import { useDesk } from "./store";
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
import { AttentionDrawer } from "./components/AttentionDrawer";
import { DeskToolInspector } from "./components/DeskToolInspector";
import { Dock } from "./components/DeskWindow";
import { useProjections } from "./projections";
import "./desk.css";

export default function DeskApp() {
  const items = useDesk((s) => s.items);
  const updatedAt = useDesk((s) => s.updatedAt);
  const chatPersonaId = useDesk((s) => s.chatPersonaId);
  const setup = useDesk((s) => s.setup);
  const viewMode = useDesk((s) => s.viewMode);
  const { refresh } = useDesk.getState();

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
    <div className="desk-next">
      <Atmosphere />
      <DeskChrome showDailyStarts={!empty} />
      {empty ? (
        <EmptyDesk arrivalRequired={setup?.arrival_required === true} />
      ) : viewMode === "list" ? (
        <DeskListView />
      ) : (
        <WorldStage />
      )}
      {!empty ? <RecordOrb /> : null}
      {chatPersonaId && <PersonaChat personaId={chatPersonaId} />}
      <DeskToolInspector />
      <MissionControlConveyor />
      <DeliveryBoard />
      <DeliveryDossierWindow />
      <DeliveryTerminalWindow />
      <PanePicker />
      <SessionPullout />
      <AttentionDrawer />
      <Dock />
    </div>
  );
}
