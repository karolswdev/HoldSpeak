/* PHILO-13-11 canvas harness navigation, loaded in BOTH modes. It changes no
 * behaviour: each helper is what a Dock click, a palette pick or a menu row
 * does, called directly so the rig reaches a window at 393 too. */
import { useDesk } from "@w/desk/store";
import { openIntelligence } from "@w/desk/intelligenceNavigation";
import { openProjectRoom } from "@w/desk/shell";
import { useChairState } from "@w/desk/chairState";

declare global { interface Window { __p13Open?: Record<string, (...a: string[]) => void> } }

window.__p13Open = {
  surface: (key: string, scope?: string) => useDesk.getState().openSurfaceWindow(key, scope),
  brief: () => openIntelligence({ view: "brief" }),
  open: (ref: string) => useDesk.getState().openPullout(ref),
  room: (projectId: string) => openProjectRoom(projectId),
  focus: (id: string) => useDesk.getState().focusPanel(id),
  closeAll: () => { const s = useDesk.getState(); s.clearSurfaceWindows(); for (let i = 0; i < 12; i++) s.closePullout(); },
  floor: () => { if (useChairState.getState().surface === "chair") useChairState.getState().toggle(); },
  chair: () => { if (useChairState.getState().surface !== "chair") useChairState.getState().toggle(); },
};
