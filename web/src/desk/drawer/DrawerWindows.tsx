/** PHILO-14 A2 — every open drawer and every drawer Get Info window. */
import { useEffect } from "react";
import { ApplicationBoundary } from "../components/ApplicationBoundary";
import { registerSurface } from "../shell";
import { DrawerInfoWindow } from "./InfoWindow";
import { DrawerWindow } from "./DrawerWindow";
import { openDrawer, useDrawers } from "./store";

/** The surface key a Project primitive opens through (`lib/primitives.ts`):
 *  every generic open of a Project lands here, in its drawer. */
export const PROJECT_DRAWER_KEY = "open-project-drawer";

export function DrawerWindows() {
  const drawers = useDrawers((s) => s.drawers);
  const infos = useDrawers((s) => s.infos);
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
      {infos.map((info) => (
        <ApplicationBoundary key={info.ref} label="Info">
          <DrawerInfoWindow info={info} />
        </ApplicationBoundary>
      ))}
    </>
  );
}
