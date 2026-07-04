// The Desk island — the web app's front door (HS-73-02).
//
// React + Vite inside the existing Astro build (the owner's 2026-07-02 stack
// decision). Full-bleed: the world owns the viewport; chrome is the floating
// minimal cluster (DeskChrome); a fresh desk shows the guiding empty state.
// The first-run guard runs INLINE on index.astro before this island mounts,
// so a brand-new user never sees the desk before /welcome.
import { useEffect } from "react";
import { useDesk } from "./store";
import { Stage } from "./components/Stage";
import { World } from "./components/World";
import { DeskChrome } from "./components/DeskChrome";
import { EmptyDesk } from "./components/EmptyDesk";
import { RecordOrb } from "./components/RecordOrb";
import { AgentRail } from "./components/AgentRail";
import { MissionControlConveyor } from "./components/MissionControlConveyor";
import "./desk.css";

export default function DeskApp() {
  const items = useDesk((s) => s.items);
  const updatedAt = useDesk((s) => s.updatedAt);
  const { refresh } = useDesk.getState();

  useEffect(() => {
    void refresh();
  }, []);

  const total = Object.values(items).reduce((n, l) => n + l.length, 0);

  return (
    <div className="desk-next">
      <Stage />
      <DeskChrome />
      {updatedAt !== null && total === 0 ? <EmptyDesk /> : <World />}
      <RecordOrb />
      <AgentRail />
      <MissionControlConveyor />
    </div>
  );
}
