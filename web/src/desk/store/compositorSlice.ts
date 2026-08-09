/** Compositor slice (HS-117-02): panel geometry, stacking order,
 * minimize/maximize, and all six window arrays. */
import { assertNever } from "../assertNever";
import type { DeskState, PanelRect, SliceCreator, ZoneViewPref } from "./types";
import {
  ZONE_WINDOW_CONFIG,
  INFO_WINDOW_CONFIG,
  ROADMAP_WINDOW_CONFIG,
  REPOSITORY_WINDOW_CONFIG,
  WORKBENCH_WINDOW_CONFIG,
  makeOpenWindow,
  makeCloseWindow,
  windowInitialState,
} from "./windowFactory";

// ---- localStorage persistence -------------------------------------------

const PANEL_KEY = "hs.desk.panels";
const PANEL_ORDER_LIMIT = 100;
const ZONE_VIEWS_KEY = "hs.desk.zone-views";

const isPanelId = (value: unknown): value is string =>
  typeof value === "string" && /^[A-Za-z0-9:_-]+$/.test(value);

const isPanelRect = (value: unknown): value is PanelRect => {
  if (!value || typeof value !== "object") return false;
  const rect = value as PanelRect;
  return [rect.x, rect.y, rect.w, rect.h].every(Number.isFinite) &&
    rect.w > 0 && rect.h > 0;
};

function compactPanelOrder(order: string[]): string[] {
  const unique = Array.from(new Set(order));
  return unique.length > PANEL_ORDER_LIMIT
    ? unique.slice(-PANEL_ORDER_LIMIT)
    : unique;
}

interface PanelLayout {
  rects: Record<string, PanelRect>;
  order: string[];
  max: string[];
}

export function loadPanelLayout(): PanelLayout {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(PANEL_KEY) || "{}") || {};
    const layout = raw as { rects?: unknown; order?: unknown; max?: unknown };
    const source = raw && typeof raw === "object" && layout.rects ? layout.rects : raw;
    const rects = Object.fromEntries(
      Object.entries(source && typeof source === "object" ? source : {}).filter(
        ([id, rect]) => isPanelId(id) && isPanelRect(rect),
      ),
    ) as Record<string, PanelRect>;
    const order = compactPanelOrder(
      (Array.isArray(layout.order) ? layout.order : []).filter(
        (value): value is string => isPanelId(value),
      ),
    );
    const max = Array.from(
      new Set(
        (Array.isArray(layout.max) ? layout.max : []).filter(
          (value): value is string => isPanelId(value),
        ),
      ),
    );
    return { rects, order, max };
  } catch {
    return { rects: {}, order: [], max: [] };
  }
}

function savePanelLayout(
  rects: Record<string, PanelRect>,
  keep: string[],
  order: string[],
  max: string[],
) {
  try {
    const out: Record<string, PanelRect> = {};
    for (const id of keep) if (rects[id]) out[id] = rects[id];
    localStorage.setItem(PANEL_KEY, JSON.stringify({ rects: out, order, max }));
  } catch {
    /* storage may be unavailable; arranging just won't persist */
  }
}

function loadZoneViewPrefs(): Record<string, ZoneViewPref> {
  try {
    const raw = localStorage.getItem(ZONE_VIEWS_KEY);
    return raw ? (JSON.parse(raw) as Record<string, ZoneViewPref>) : {};
  } catch {
    return {};
  }
}

// ---- pre-computed initial values ----------------------------------------

const initialPanelLayout = loadPanelLayout();
const initialPanelRects = initialPanelLayout.rects;

// ---- factory-generated open/close functions -----------------------------

const openZone = makeOpenWindow(ZONE_WINDOW_CONFIG);
const closeZone = makeCloseWindow(ZONE_WINDOW_CONFIG);
const openInfo = makeOpenWindow(INFO_WINDOW_CONFIG);
const closeInfo = makeCloseWindow(INFO_WINDOW_CONFIG);
const openRoadmap = makeOpenWindow(ROADMAP_WINDOW_CONFIG);
const closeRoadmap = makeCloseWindow(ROADMAP_WINDOW_CONFIG);
const openRepository = makeOpenWindow(REPOSITORY_WINDOW_CONFIG);
const closeRepository = makeCloseWindow(REPOSITORY_WINDOW_CONFIG);
const openWorkbench = makeOpenWindow(WORKBENCH_WINDOW_CONFIG);
const closeWorkbench = makeCloseWindow(WORKBENCH_WINDOW_CONFIG);

// ---- the slice ----------------------------------------------------------

export type CompositorSlice = Pick<
  DeskState,
  | "panelRects"
  | "panelSaved"
  | "panelOrder"
  | "panelMin"
  | "panelMax"
  | "pullouts"
  | "zoneWindows"
  | "zoneViewPrefs"
  | "infoWindows"
  | "roadmapWindows"
  | "repositoryWindows"
  | "workbenchWindows"
  | "newWorkbenchChooser"
  | "openPullout"
  | "closePullout"
  | "openZoneWindow"
  | "closeZoneWindow"
  | "setZoneViewPref"
  | "openInfoWindow"
  | "closeInfoWindow"
  | "openRoadmapWindow"
  | "closeRoadmapWindow"
  | "openRepositoryWindow"
  | "closeRepositoryWindow"
  | "openWorkbenchWindow"
  | "closeWorkbenchWindow"
  | "openNewWorkbenchChooser"
  | "closeNewWorkbenchChooser"
  | "setPanelRect"
  | "resetPanelRect"
  | "focusPanel"
  | "presentPanel"
  | "retirePanel"
  | "minimizePanel"
  | "restorePanel"
  | "toggleMaximizePanel"
  | "resetLayout"
>;

export const createCompositorSlice: SliceCreator<CompositorSlice> = (set, get) => ({
  panelRects: initialPanelRects,
  panelSaved: Object.keys(initialPanelRects),
  panelOrder: initialPanelLayout.order,
  panelMin: [],
  panelMax: initialPanelLayout.max,
  pullouts: [],
  zoneWindows: windowInitialState(ZONE_WINDOW_CONFIG),
  zoneViewPrefs: loadZoneViewPrefs(),
  infoWindows: [],
  roadmapWindows: [],
  repositoryWindows: [],
  workbenchWindows: [],
  newWorkbenchChooser: null,

  // ---- pullouts (hand-written: custom close with optional id) -----------

  openPullout(id, origin) {
    const resolved = resolveKindFromId(id, get);
    if (!resolved) {
      console.warn(`openPullout: unknown id "${id}"`);
      return;
    }
    const desc = PRIMITIVES[resolved.kind];
    switch (desc.surface.type) {
      case "pullout": {
        const open = get().pullouts;
        if (!open.some((p) => p.id === id))
          set({ pullouts: [...open, { id, origin: origin ?? null }] });
        set({ editingId: null });
        get().focusPanel(`pullout:${id}`);
        break;
      }
      case "window": {
        const method = `open${desc.surface.windowKey}` as const;
        (get() as unknown as Record<string, Function>)[method](resolved.resolvedId, origin);
        break;
      }
      case "surface": {
        const surfaceKey = desc.surface.surfaceKey;
        void import("../shell").then(({ openSurfaceWhenReady }) =>
          openSurfaceWhenReady(
            surfaceKey,
            resolved.kind === "project"
              ? `project:${resolved.resolvedId}`
              : undefined,
          ),
        );
        set({ editingId: null });
        break;
      }
      case "none":
        break;
      default:
        assertNever(desc.surface);
    }
  },
  closePullout(id) {
    const open = get().pullouts;
    if (open.length === 0) return;
    const victim =
      id ??
      [...open]
        .sort(
          (a, b) =>
            get().panelOrder.indexOf(`pullout:${a.id}`) -
            get().panelOrder.indexOf(`pullout:${b.id}`),
        )
        .pop()?.id;
    set({ pullouts: open.filter((p) => p.id !== victim) });
  },

  // ---- factory-generated window pairs -----------------------------------

  openZoneWindow(id, origin) {
    openZone(id, origin, set, get);
  },
  closeZoneWindow(id) {
    closeZone(id, set, get);
  },
  openInfoWindow(ref, origin) {
    openInfo(ref, origin, set, get);
  },
  closeInfoWindow(ref) {
    closeInfo(ref, set, get);
  },
  openRoadmapWindow(slug, origin) {
    openRoadmap(slug, origin, set, get);
  },
  closeRoadmapWindow(slug) {
    closeRoadmap(slug, set, get);
  },
  openRepositoryWindow(id, origin) {
    openRepository(id, origin, set, get);
  },
  closeRepositoryWindow(id) {
    closeRepository(id, set, get);
  },
  openWorkbenchWindow(id, origin) {
    openWorkbench(id, origin, set, get);
  },
  closeWorkbenchWindow(id) {
    closeWorkbench(id, set, get);
  },
  openNewWorkbenchChooser(origin) {
    set({ newWorkbenchChooser: { origin: origin ?? null } });
  },
  closeNewWorkbenchChooser() {
    set({ newWorkbenchChooser: null });
  },

  // ---- zone view prefs --------------------------------------------------

  setZoneViewPref(id, pref) {
    const current = get().zoneViewPrefs[id] || {
      view: "icons",
      sort: "name",
      dir: "asc",
    };
    const next = { ...get().zoneViewPrefs, [id]: { ...current, ...pref } };
    set({ zoneViewPrefs: next });
    try {
      localStorage.setItem(ZONE_VIEWS_KEY, JSON.stringify(next));
    } catch {
      /* storage may be unavailable */
    }
  },

  // ---- panel geometry ---------------------------------------------------

  setPanelRect(id, rect, persist = false) {
    const panelRects = { ...get().panelRects, [id]: rect };
    const panelSaved =
      persist && !get().panelSaved.includes(id)
        ? [...get().panelSaved, id]
        : get().panelSaved;
    set({ panelRects, panelSaved });
    if (persist)
      savePanelLayout(panelRects, panelSaved, get().panelOrder, get().panelMax);
  },
  resetPanelRect(id) {
    const { [id]: _dropped, ...rest } = get().panelRects;
    const panelSaved = get().panelSaved.filter((x) => x !== id);
    set({ panelRects: rest, panelSaved });
    savePanelLayout(rest, panelSaved, get().panelOrder, get().panelMax);
  },
  focusPanel(id) {
    const order = compactPanelOrder([
      ...get().panelOrder.filter((x) => x !== id),
      id,
    ]);
    set({ panelOrder: order });
    savePanelLayout(get().panelRects, get().panelSaved, order, get().panelMax);
  },
  presentPanel(id) {
    if (get().panelOrder.includes(id)) return;
    get().focusPanel(id);
  },
  retirePanel(id) {
    if (!get().panelOrder.includes(id)) return;
    const order = get().panelOrder.filter((x) => x !== id);
    set({ panelOrder: order });
    savePanelLayout(get().panelRects, get().panelSaved, order, get().panelMax);
  },
  minimizePanel(id) {
    if (get().panelMin.includes(id)) return;
    set({ panelMin: [...get().panelMin, id] });
  },
  restorePanel(id) {
    const panelMin = get().panelMin.filter((x) => x !== id);
    const order = compactPanelOrder([
      ...get().panelOrder.filter((x) => x !== id),
      id,
    ]);
    set({ panelMin, panelOrder: order });
    savePanelLayout(get().panelRects, get().panelSaved, order, get().panelMax);
  },
  toggleMaximizePanel(id) {
    const has = get().panelMax.includes(id);
    const panelMax = has
      ? get().panelMax.filter((x) => x !== id)
      : [...get().panelMax, id];
    const order = compactPanelOrder([
      ...get().panelOrder.filter((x) => x !== id),
      id,
    ]);
    set({ panelMax, panelOrder: order });
    savePanelLayout(get().panelRects, get().panelSaved, order, panelMax);
  },
  resetLayout() {
    set({
      panelRects: {},
      panelSaved: [],
      panelOrder: [],
      panelMin: [],
      panelMax: [],
    });
    savePanelLayout({}, [], [], []);
  },
});

// ---- helpers (moved from the monolith) ----------------------------------

import { PRIMITIVES, type PrimitiveKind } from "../../lib/primitives";

/** Reverse the display-name mapping from qualifiedRef back to PrimitiveKind. */
const REF_PREFIX_TO_KIND: Record<string, PrimitiveKind> = {
  knowledge: "kb",
  zone: "directory",
  persona: "recipe",
  sequence: "chain",
};

/** Resolve a raw id string to a primitive kind + the id to pass downstream. */
function resolveKindFromId(
  id: string,
  get: () => DeskState,
): { kind: PrimitiveKind; resolvedId: string } | null {
  const colonIdx = id.indexOf(":");
  if (colonIdx > 0) {
    const prefix = id.slice(0, colonIdx);
    const bareId = id.slice(colonIdx + 1);
    const kind = (REF_PREFIX_TO_KIND[prefix] ?? prefix) as PrimitiveKind;
    if (kind in PRIMITIVES) return { kind, resolvedId: bareId };
  }
  const items = get().items;
  for (const [k, list] of Object.entries(items)) {
    if (Array.isArray(list) && list.some((p: { id: string }) => p.id === id))
      return { kind: k as PrimitiveKind, resolvedId: id };
  }
  return null;
}
