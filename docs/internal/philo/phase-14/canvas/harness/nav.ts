/* Conductor canvas (copied from story-15) navigation, loaded in BOTH modes. It changes no behaviour:
 * each helper is what a Dock press, a palette pick or a menu row does, called
 * directly so the rig reaches a window at both widths. */
import { useDesk } from "@w/desk/store";
import { openIntelligence } from "@w/desk/intelligenceNavigation";
import { openProjectRoom } from "@w/desk/shell";
import { useChairState } from "@w/desk/chairState";
import { usePalette } from "@w/desk/chromeState";

declare global { interface Window { __cOpen?: Record<string, (...a: string[]) => unknown> } }

window.__cOpen = {
  surface: (key: string, scope?: string) => useDesk.getState().openSurfaceWindow(key, scope),
  brief: () => openIntelligence({ view: "brief" }),
  open: (ref: string) => useDesk.getState().openPullout(ref),
  room: (projectId: string) => openProjectRoom(projectId),
  focus: (id: string) => useDesk.getState().focusPanel(id),
  closeAll: () => { const s = useDesk.getState(); s.clearSurfaceWindows(); for (let i = 0; i < 12; i++) s.closePullout(); },
  floorList: () => { if (useChairState.getState().surface !== "floor") useChairState.getState().toggle(); useDesk.getState().setViewMode("list"); },
  select: (ref: string) => useDesk.getState().setSelected([ref]),
  palette: (open: string) => usePalette.getState().setOpen(open === "1"),
  chair: () => { if (useChairState.getState().surface !== "chair") useChairState.getState().toggle(); },
  state: () => { const s = useDesk.getState() as any; return { order: s.panelOrder, min: s.panelMin, sel: s.selectedIds }; },
};
