import type {
  DeskState,
  PanelRect,
  WindowInstance,
  ZoneViewPref,
} from "./types";

/** A hard-cut workspace contract. Older Desk window keys are intentionally
 * ignored: this is the sole persisted document for window lifecycle state. */
export const DESK_WORKSPACE_STORAGE_KEY = "hs.desk.workspace.v1";
export const DESK_WORKSPACE_VERSION = 1 as const;

const PANEL_ORDER_LIMIT = 100;

export interface DeskWorkspaceDocumentV1 {
  version: typeof DESK_WORKSPACE_VERSION;
  windowsById: Record<string, WindowInstance>;
  panel: {
    rects: Record<string, PanelRect>;
    order: string[];
    max: string[];
  };
  zoneWindows: string[];
  zoneViewPrefs: Record<string, ZoneViewPref>;
}

const emptyWorkspace = (): DeskWorkspaceDocumentV1 => ({
  version: DESK_WORKSPACE_VERSION,
  windowsById: {},
  panel: { rects: {}, order: [], max: [] },
  zoneWindows: [],
  zoneViewPrefs: {},
});

const isPanelId = (value: unknown): value is string =>
  typeof value === "string" && /^[A-Za-z0-9:_-]+$/.test(value);

const isPanelRect = (value: unknown): value is PanelRect => {
  if (!value || typeof value !== "object") return false;
  const rect = value as PanelRect;
  return [rect.x, rect.y, rect.w, rect.h].every(Number.isFinite) &&
    rect.w > 0 && rect.h > 0;
};

const compactIds = (values: unknown, limit = PANEL_ORDER_LIMIT): string[] => {
  if (!Array.isArray(values)) return [];
  const unique = Array.from(new Set(values.filter(isPanelId)));
  return unique.length > limit ? unique.slice(-limit) : unique;
};

const isZoneViewPref = (value: unknown): value is ZoneViewPref => {
  if (!value || typeof value !== "object") return false;
  const pref = value as ZoneViewPref;
  return (
    (pref.view === "icons" || pref.view === "list") &&
    (pref.sort === "name" || pref.sort === "kind" || pref.sort === "modified") &&
    (pref.dir === "asc" || pref.dir === "desc")
  );
};

function parseWindows(value: unknown): Record<string, WindowInstance> {
  if (!value || typeof value !== "object") return {};
  const windows: Record<string, WindowInstance> = {};
  for (const [id, raw] of Object.entries(value)) {
    if (!isPanelId(id) || !raw || typeof raw !== "object") continue;
    const candidate = raw as Partial<WindowInstance>;
    if (
      candidate.id !== id ||
      candidate.kind !== "surface" ||
      typeof candidate.applicationKey !== "string" ||
      (candidate.scope !== null && typeof candidate.scope !== "string") ||
      candidate.persistence !== "workspace"
    ) continue;
    windows[id] = candidate as WindowInstance;
  }
  return windows;
}

export function loadDeskWorkspace(): DeskWorkspaceDocumentV1 {
  try {
    const raw: unknown = JSON.parse(
      localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "null",
    );
    if (!raw || typeof raw !== "object") return emptyWorkspace();
    const candidate = raw as Partial<DeskWorkspaceDocumentV1>;
    if (candidate.version !== DESK_WORKSPACE_VERSION)
      return emptyWorkspace();

    const panel = candidate.panel && typeof candidate.panel === "object"
      ? candidate.panel
      : { rects: {}, order: [], max: [] };
    const rects = Object.fromEntries(
      Object.entries(panel.rects && typeof panel.rects === "object" ? panel.rects : {})
        .filter(([id, rect]) => isPanelId(id) && isPanelRect(rect)),
    ) as Record<string, PanelRect>;
    const zoneViewPrefs = Object.fromEntries(
      Object.entries(
        candidate.zoneViewPrefs && typeof candidate.zoneViewPrefs === "object"
          ? candidate.zoneViewPrefs
          : {},
      ).filter(([id, pref]) => isPanelId(id) && isZoneViewPref(pref)),
    ) as Record<string, ZoneViewPref>;

    return {
      version: DESK_WORKSPACE_VERSION,
      windowsById: parseWindows(candidate.windowsById),
      panel: {
        rects,
        order: compactIds(panel.order),
        max: compactIds(panel.max),
      },
      zoneWindows: compactIds(candidate.zoneWindows),
      zoneViewPrefs,
    };
  } catch {
    return emptyWorkspace();
  }
}

type WorkspaceState = Pick<
  DeskState,
  | "windowsById"
  | "panelRects"
  | "panelSaved"
  | "panelOrder"
  | "panelMax"
  | "zoneWindows"
  | "zoneViewPrefs"
>;

export function saveDeskWorkspace(state: WorkspaceState): void {
  const rects: Record<string, PanelRect> = {};
  for (const id of state.panelSaved) {
    const rect = state.panelRects[id];
    if (rect && isPanelId(id) && isPanelRect(rect)) rects[id] = rect;
  }
  const document: DeskWorkspaceDocumentV1 = {
    version: DESK_WORKSPACE_VERSION,
    windowsById: state.windowsById,
    panel: {
      rects,
      order: compactIds(state.panelOrder),
      max: compactIds(state.panelMax),
    },
    zoneWindows: state.zoneWindows.map((window) => window.id),
    zoneViewPrefs: state.zoneViewPrefs,
  };
  try {
    localStorage.setItem(DESK_WORKSPACE_STORAGE_KEY, JSON.stringify(document));
  } catch {
    /* storage may be unavailable; the live compositor remains authoritative */
  }
}
