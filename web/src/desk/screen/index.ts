// PHILO-14 A1 — the screen: the Chair as the desk of objects.
export { Screen } from "./Screen";
export { composeScreen, screenIsBare, agentName, agentState, shortItemName, normalizeRef } from "./compose";
export type { ScreenObject, ScreenInputs, ScreenPerson, ScreenRole } from "./compose";
export { layoutScreen } from "./layout";
export { openDrawer, openTarget, type ScreenTarget } from "./open";
