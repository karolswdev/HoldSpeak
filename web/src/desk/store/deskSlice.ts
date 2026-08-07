/** Desk interaction slice (HS-117-02): UI state for the desk surface --
 * dive, drag, new-beat, editor, hover, rename, selection, ask, chat,
 * tool inspector, view mode. */
import type { DeskState, DeskView, SliceCreator } from "./types";

// ---- localStorage helpers -----------------------------------------------

const VIEW_KEY = "hs.desk.view";

function loadViewMode(): DeskView | "unset" {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get("view");
    if (fromUrl === "list") return "list";
    if (fromUrl === "spatial") return "spatial";
    const saved = localStorage.getItem(VIEW_KEY);
    if (saved === "list") return "list";
    if (saved === "spatial") return "spatial";
    return "unset";
  } catch {
    return "spatial";
  }
}

function persistViewMode(mode: DeskView) {
  try {
    localStorage.setItem(VIEW_KEY, mode);
  } catch {
    /* storage may be unavailable; the choice just won't persist */
  }
  try {
    const url = new URL(window.location.href);
    if (mode === "list") url.searchParams.set("view", "list");
    else url.searchParams.delete("view");
    window.history.replaceState(null, "", url);
  } catch {
    /* environments without history keep the in-memory choice */
  }
}

// ---- the slice ----------------------------------------------------------

export type DeskSlice = Pick<
  DeskState,
  | "divedZone"
  | "draggingId"
  | "newIds"
  | "editingId"
  | "hoverZoneId"
  | "renamingZoneId"
  | "selectedIds"
  | "askOpen"
  | "chatPersonaId"
  | "toolInspector"
  | "viewMode"
  | "setViewMode"
  | "markNew"
  | "openEditor"
  | "closeEditor"
  | "setHoverZone"
  | "setRenamingZone"
  | "diveInto"
  | "surface"
  | "toggleSelected"
  | "setSelected"
  | "clearSelection"
  | "openAsk"
  | "closeAsk"
  | "openChat"
  | "closeChat"
  | "openToolInspector"
  | "closeToolInspector"
  | "setDragging"
>;

export const createDeskSlice: SliceCreator<DeskSlice> = (set, get) => ({
  divedZone: null,
  draggingId: null,
  newIds: [],
  editingId: null,
  hoverZoneId: null,
  renamingZoneId: null,
  selectedIds: [],
  askOpen: false,
  chatPersonaId: null,
  toolInspector: null,
  viewMode: loadViewMode(),

  setViewMode(mode) {
    set({ viewMode: mode });
    persistViewMode(mode);
  },

  markNew(id) {
    set({ newIds: [...get().newIds, id] });
    setTimeout(() => {
      set({ newIds: get().newIds.filter((x) => x !== id) });
    }, 4500);
  },

  openEditor(id) {
    set({
      editingId: id,
      pullouts: get().pullouts.filter((p) => p.id !== id),
      toolInspector: null,
    });
  },
  closeEditor() {
    set({ editingId: null });
    void get().refresh();
  },

  setHoverZone(id) {
    if (get().hoverZoneId !== id) set({ hoverZoneId: id });
  },
  setRenamingZone(id) {
    set({ renamingZoneId: id });
  },
  diveInto(zoneId) {
    set({
      divedZone: zoneId,
      pullouts: [],
      editingId: null,
      toolInspector: null,
    });
  },
  surface() {
    set({ divedZone: null });
  },

  toggleSelected(id) {
    const cur = get().selectedIds;
    set({
      selectedIds: cur.includes(id)
        ? cur.filter((x) => x !== id)
        : [...cur, id],
    });
  },
  setSelected(ids) {
    set({ selectedIds: ids });
  },
  clearSelection() {
    set({ selectedIds: [], askOpen: false });
  },
  openAsk() {
    set({ askOpen: true, editingId: null });
    get().focusPanel("ask");
  },
  closeAsk() {
    set({ askOpen: false });
  },
  openChat(personaId) {
    set({ chatPersonaId: personaId, editingId: null });
    get().focusPanel("chat");
  },
  closeChat() {
    set({ chatPersonaId: null });
  },
  openToolInspector(kind, id) {
    set({ toolInspector: { kind, id }, editingId: null });
    get().focusPanel("inspector");
  },
  closeToolInspector() {
    set({ toolInspector: null });
  },
  setDragging(id) {
    set({ draggingId: id });
  },
});
