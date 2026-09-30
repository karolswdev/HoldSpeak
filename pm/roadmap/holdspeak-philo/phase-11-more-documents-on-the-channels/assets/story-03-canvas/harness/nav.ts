/* PHILO-11-03 canvas harness navigation, loaded in BOTH modes (today and
 * proposal). It changes no behaviour: each helper is what a Dock click, a
 * WHY chip or a row click does, called directly so the rig reaches a window
 * at 393 too (where the Dock shows only icons). */
import { useDesk } from "@w/desk/store";
import { openIntelligence } from "@w/desk/intelligenceNavigation";
import { qualifiedRef } from "@w/desk/api";

declare global {
  interface Window { __p11Open?: Record<string, (...a: string[]) => void> }
}

/* ── harness navigation (what a Dock click or a row does, stated) ─────── */

window.__p11Open = {
  settings: () => useDesk.getState().openSurfaceWindow("configure-settings", "integrations"),
  brief: () => openIntelligence({ view: "brief" }),
  record: (id: string) => openIntelligence({ view: "receipts", receiptId: id }),
  decisions: () => openIntelligence({ view: "receipts" }),
  decision: (id: string) => useDesk.getState().openPullout(qualifiedRef("decision", id)),
  meeting: (id: string) => useDesk.getState().openPullout(qualifiedRef("meeting", id)),
  closeAll: () => { const s = useDesk.getState(); s.clearSurfaceWindows(); for (let i = 0; i < 12; i++) s.closePullout(); },
  meetings: (id: string) => useDesk.getState().openSurfaceWindow("review-meetings", `meeting:${id}`),
};
