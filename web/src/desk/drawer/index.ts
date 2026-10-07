/** PHILO-14 A2 — a Project opens as a drawer. `openDrawer(projectId)` is the
 *  one opener (the screen, the Dock, a `project:` ref). */
export { openDrawer, useDrawers, drawerWindowId, infoWindowId } from "./store";
export { DrawerWindows } from "./DrawerWindows";
export { DrawerWindow, drawerReceipt, type DrawerView } from "./DrawerWindow";
export { DrawerInfoWindow } from "./InfoWindow";
export { drawerMembers, drawerHead, type DrawerMember, type DrawerHead } from "./members";
