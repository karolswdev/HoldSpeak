// The Desk route — the web app's front door (HS-73-02).
//
// React + Vite in the one Web tree. Full-bleed: the world owns the viewport;
// chrome is the floating
// minimal cluster (DeskChrome); a fresh desk shows the guiding empty state.
// Arrival routing is owned by this route so a brand-new user reaches /welcome.
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useDesk } from "./store";
import { Stage } from "./components/Stage";
import { World } from "./components/World";
import { DeskChrome } from "./components/DeskChrome";
import { EmptyDesk } from "./components/EmptyDesk";
import { RecordOrb } from "./components/RecordOrb";
import { RecipeRail } from "./components/RecipeRail";
import { PersonaChat } from "./components/PersonaChat";
import { MissionControlConveyor } from "./components/MissionControlConveyor";
import { SessionPullout, PanePicker } from "./components/SessionPullout";
import "./desk.css";

export default function DeskApp() {
  const items = useDesk((s) => s.items);
  const updatedAt = useDesk((s) => s.updatedAt);
  const chatPersonaId = useDesk((s) => s.chatPersonaId);
  const setup = useDesk((s) => s.setup);
  const { refresh } = useDesk.getState();
  const navigate = useNavigate();

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (setup?.first_run) navigate("/welcome", { replace: true });
    else if (setup?.overall === "blocked")
      navigate("/setup", { replace: true });
  }, [navigate, setup]);

  const total = Object.values(items).reduce((n, l) => n + l.length, 0);

  return (
    <div className="desk-next">
      <Stage />
      <DeskChrome />
      {updatedAt !== null && total === 0 ? <EmptyDesk /> : <World />}
      <RecordOrb />
      <RecipeRail />
      {chatPersonaId && <PersonaChat personaId={chatPersonaId} />}
      <MissionControlConveyor />
      <PanePicker />
      <SessionPullout />
    </div>
  );
}
