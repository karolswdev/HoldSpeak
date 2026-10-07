/** PHILO-14 C4 — the Conductor drawer and its Get Info windows, and the
 *  surface key that opens it (the screen's icon, the Dock, Go, ⌘3, the
 *  `/conductor` address). */
import { useEffect } from "react";
import { ApplicationBoundary } from "../components/ApplicationBoundary";
import { registerSurface } from "../shell";
import { ConductorInfoWindow } from "./ConductorInfoWindow";
import { ConductorWindow } from "./ConductorWindow";
import { CONDUCTOR_KEY, openConductor, useConductor } from "./store";

export function ConductorWindows() {
  const open = useConductor((s) => s.open);
  const infos = useConductor((s) => s.infos);
  useEffect(() => registerSurface(CONDUCTOR_KEY, () => openConductor()), []);
  return (
    <>
      {open ? (
        <ApplicationBoundary label="Conductor">
          <ConductorWindow />
        </ApplicationBoundary>
      ) : null}
      {infos.map((member) => (
        <ApplicationBoundary key={member.ref} label="Info">
          <ConductorInfoWindow member={member} />
        </ApplicationBoundary>
      ))}
    </>
  );
}
