/** PHILO-14 C4 — the Conductor drawer: where agents live. `openConductor()`
 *  is the one opener (the screen, the Dock, Go, ⌘3, `/conductor`). */
export { openConductor, useConductor, CONDUCTOR_KEY, CONDUCTOR_WINDOW_ID } from "./store";
export { ConductorWindows } from "./ConductorWindows";
export { ConductorWindow } from "./ConductorWindow";
export { conductorMembers, conductorHead, headWords, type ConductorMember } from "./members";
