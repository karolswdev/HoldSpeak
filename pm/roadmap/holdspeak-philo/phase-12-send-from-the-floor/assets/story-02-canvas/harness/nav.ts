/* PHILO-12-02 canvas harness navigation, loaded in BOTH modes. It changes no
 * behaviour: each helper is what a Dock click or a palette pick does, called
 * directly so the rig reaches a window at 393 too. */
import { useDesk } from "@w/desk/store";
import { openIntelligence } from "@w/desk/intelligenceNavigation";
import { qualifiedRef } from "@w/desk/api";

declare global { interface Window { __p12Open?: Record<string, (...a: string[]) => void> } }

window.__p12Open = {
  settings: () => useDesk.getState().openSurfaceWindow("configure-settings", "integrations"),
  brief: () => openIntelligence({ view: "brief" }),
  open: (kind: string, id: string) => useDesk.getState().openPullout(qualifiedRef(kind, id)),
  select: (ref: string) => useDesk.getState().setSelected([ref]),
  clearSelection: () => useDesk.getState().setSelected([]),
  closeAll: () => { const s = useDesk.getState(); s.clearSurfaceWindows(); for (let i = 0; i < 12; i++) s.closePullout(); },
  view: (v: string) => { const s = useDesk.getState() as unknown as Record<string, (x: string) => void>; s.setViewMode?.(v); },
};
