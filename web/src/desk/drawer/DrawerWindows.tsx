/** PHILO-14 A2 — every open drawer and every drawer Get Info window. */
import { ApplicationBoundary } from "../components/ApplicationBoundary";
import { DrawerInfoWindow } from "./InfoWindow";
import { DrawerWindow } from "./DrawerWindow";
import { useDrawers } from "./store";

export function DrawerWindows() {
  const drawers = useDrawers((s) => s.drawers);
  const infos = useDrawers((s) => s.infos);
  return (
    <>
      {drawers.map((drawer) => (
        <ApplicationBoundary key={drawer.projectId} label="Drawer">
          <DrawerWindow drawer={drawer} />
        </ApplicationBoundary>
      ))}
      {infos.map((info) => (
        <ApplicationBoundary key={info.ref} label="Info">
          <DrawerInfoWindow info={info} />
        </ApplicationBoundary>
      ))}
    </>
  );
}
