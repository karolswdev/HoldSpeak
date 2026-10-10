/** PHILO-14 A2 — every open drawer and every drawer Get Info window. */
import { useEffect } from "react";
import { ApplicationBoundary } from "../components/ApplicationBoundary";
import { registerSurface } from "../shell";
import { DrawerInfoWindow } from "./InfoWindow";
import { DrawerWindow } from "./DrawerWindow";
import { ParkedDrawer } from "./ParkedDrawer";
import { openDrawer, useDrawers } from "./store";

/** PARKED (PHILO-17 U30): the drawer's surface key. A Project opens its
 *  Room now (`lib/primitives.ts`); no product opener names this key. It
 *  stays registered so a parked drawer still opens by its key. */
export const PROJECT_DRAWER_KEY = "open-project-drawer";

export function DrawerWindows() {
  const drawers = useDrawers((s) => s.drawers);
  const infos = useDrawers((s) => s.infos);
  const parked = useDrawers((s) => s.parked);
  useEffect(
    () =>
      registerSurface(PROJECT_DRAWER_KEY, (scope) => {
        if (scope?.startsWith("project:")) openDrawer(scope.slice("project:".length));
      }),
    [],
  );
  return (
    <>
      {drawers.map((drawer) => (
        <ApplicationBoundary key={drawer.projectId} label="Drawer">
          <DrawerWindow drawer={drawer} />
        </ApplicationBoundary>
      ))}
      {parked ? (
        <ApplicationBoundary label="Parked">
          <ParkedDrawer origin={parked.origin} />
        </ApplicationBoundary>
      ) : null}
      {infos.map((info) => (
        <ApplicationBoundary key={info.ref} label="Info">
          <DrawerInfoWindow info={info} />
        </ApplicationBoundary>
      ))}
    </>
  );
}
