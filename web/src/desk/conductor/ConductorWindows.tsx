/** PHILO-14 C4 — the Agents window and the surface key that opens it (the
 *  screen's icon, the Dock, Go, ⌘3, the `/conductor` address). The agent's
 *  facts are its pane's Details (the Get Info windows are parked). */
import { useEffect } from "react";
import { ApplicationBoundary } from "../components/ApplicationBoundary";
import { registerSurface } from "../shell";
import { ConductorWindow } from "./ConductorWindow";
import { CONDUCTOR_KEY, openConductor, useConductor } from "./store";

export function ConductorWindows() {
  const open = useConductor((s) => s.open);
  useEffect(() => registerSurface(CONDUCTOR_KEY, () => openConductor()), []);
  return (
    <>
      {open ? (
        <ApplicationBoundary label="Agents">
          <ConductorWindow />
        </ApplicationBoundary>
      ) : null}
    </>
  );
}
