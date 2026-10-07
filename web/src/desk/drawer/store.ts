/** PHILO-14 A2 — the open drawers and their Get Info windows.
 *
 *  A Project opens as a drawer: its own window, one per Project (a second
 *  open brings the same window forward). Get Info opens a window of its own
 *  for one member. The view (Icons | List) is remembered per drawer in the
 *  desk store (`zoneViewPrefs["project:<id>"]`), not here.
 */
import { create } from "zustand";
import type { ParkOutcome } from "../surface";
import type { DrawerMember } from "./members";

export interface OpenDrawer {
  projectId: string;
  origin: { x: number; y: number } | null;
}

export interface OpenInfo {
  /** The member's ref: one Info window per object. */
  ref: string;
  member: DrawerMember;
  projectId: string;
}

interface DrawerState {
  drawers: OpenDrawer[];
  infos: OpenInfo[];
  /** Bumped after a write from an Info window (Rename, Park): drawers re-read. */
  revision: number;
  /** PHILO-13-02 on the surviving face: a drawer shows the park receipt
   *  (`PARKED · <name>`, Restore) of the object parked from its Info window. */
  receipts: Record<string, ParkOutcome>;
  setReceipt(projectId: string, outcome: ParkOutcome | null): void;
  openDrawer(projectId: string, origin?: { x: number; y: number } | null): void;
  closeDrawer(projectId: string): void;
  openInfo(member: DrawerMember, projectId: string): void;
  closeInfo(ref: string): void;
  changed(): void;
}

export const drawerWindowId = (projectId: string) => `drawer:project:${projectId}`;
// The workspace keeps a window's place under an id of [A-Za-z0-9:_-] only.
export const infoWindowId = (ref: string) => `drawer-info:${ref.replace(/[^A-Za-z0-9:_-]/g, "_")}`;

export const useDrawers = create<DrawerState>((set, get) => ({
  drawers: [],
  infos: [],
  revision: 0,
  receipts: {},
  setReceipt(projectId, outcome) {
    const next = { ...get().receipts };
    if (outcome) next[projectId] = outcome;
    else delete next[projectId];
    set({ receipts: next });
  },
  openDrawer(projectId, origin = null) {
    const id = projectId.trim();
    if (!id) return;
    if (get().drawers.some((d) => d.projectId === id)) {
      // Already open: the frame brings it forward on its own registry.
      void import("../store").then((m) => {
        const desk = m.useDesk.getState();
        if (desk.panelMin.includes(drawerWindowId(id))) desk.restorePanel(drawerWindowId(id));
        desk.focusPanel(drawerWindowId(id));
      });
      return;
    }
    set({ drawers: [...get().drawers, { projectId: id, origin }] });
  },
  closeDrawer(projectId) {
    set({
      drawers: get().drawers.filter((d) => d.projectId !== projectId),
      infos: get().infos.filter((i) => i.projectId !== projectId),
    });
  },
  openInfo(member, projectId) {
    const rest = get().infos.filter((i) => i.ref !== member.ref);
    set({ infos: [...rest, { ref: member.ref, member, projectId }] });
  },
  closeInfo(ref) {
    set({ infos: get().infos.filter((i) => i.ref !== ref) });
  },
  changed() {
    set({ revision: get().revision + 1 });
  },
}));

/** Open a Project as its drawer (the screen, the Dock, a `project:` ref). */
export function openDrawer(projectId: string | null | undefined, origin?: { x: number; y: number } | null): void {
  useDrawers.getState().openDrawer(String(projectId ?? ""), origin ?? null);
}
