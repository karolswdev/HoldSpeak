/** Compositor slice (HS-117-02): panel geometry, stacking order,
 * minimize/maximize, and all six window arrays. */
import { assertNever } from "../assertNever";
import type { DeskState, PanelRect, SliceCreator } from "./types";
import { SURFACE_APPLICATIONS } from "../applications";
import {
  loadDeskWorkspace,
  saveDeskWorkspace,
} from "./workspaceStorage";
import {
  ZONE_WINDOW_CONFIG,
  INFO_WINDOW_CONFIG,
  ROADMAP_WINDOW_CONFIG,
  REPOSITORY_WINDOW_CONFIG,
  WORKBENCH_WINDOW_CONFIG,
  makeOpenWindow,
  makeCloseWindow,
} from "./windowFactory";

// ---- localStorage persistence -------------------------------------------

const PANEL_ORDER_LIMIT = 100;

function compactPanelOrder(order: string[]): string[] {
  const unique = Array.from(new Set(order));
  return unique.length > PANEL_ORDER_LIMIT
    ? unique.slice(-PANEL_ORDER_LIMIT)
    : unique;
}

export interface PanelLayout {
  rects: Record<string, PanelRect>;
  order: string[];
  max: string[];
}

export function loadPanelLayout(): PanelLayout {
  return loadDeskWorkspace().panel;
}

// ---- pre-computed initial values ----------------------------------------

const initialWorkspace = loadDeskWorkspace();
const initialPanelLayout = initialWorkspace.panel;
const initialPanelRects = initialPanelLayout.rects;
const surfaceByAction = new Map(
  SURFACE_APPLICATIONS.map((application) => [application.action, application]),
);
const surfaceByWindowId = new Map(
  SURFACE_APPLICATIONS.map((application) => [application.windowId, application]),
);
const initialWindowsById = Object.fromEntries(
  Object.entries(initialWorkspace.windowsById).filter(([id, instance]) => {
    const application = surfaceByWindowId.get(id);
    return application?.action === instance.applicationKey;
  }),
);

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
  | "windowsById"
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
  | "openSurfaceWindow"
  | "closeSurfaceWindow"
  | "clearSurfaceWindows"
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
  windowsById: initialWindowsById,
  pullouts: [],
  zoneWindows: initialWorkspace.zoneWindows.map((id) => ({ id, origin: null })),
  zoneViewPrefs: initialWorkspace.zoneViewPrefs,
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
    saveDeskWorkspace(get());
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

  // ---- static applications (one normalized lifecycle authority) --------

  openSurfaceWindow(key, scope) {
    const application = surfaceByAction.get(key);
    if (!application) {
      console.warn(`openSurfaceWindow: unknown application "${key}"`);
      return;
    }
    const instance = {
      id: application.windowId,
      kind: "surface" as const,
      applicationKey: application.action,
      scope: scope ?? null,
      persistence: "workspace" as const,
    };
    set({
      windowsById: {
        ...get().windowsById,
        [application.windowId]: instance,
      },
    });
    get().focusPanel(application.windowId);
    if (application.surface.maximized && !get().panelMax.includes(application.windowId))
      get().toggleMaximizePanel(application.windowId);
  },
  closeSurfaceWindow(key) {
    const application = surfaceByAction.get(key) ?? surfaceByWindowId.get(key);
    if (!application) return;
    const { [application.windowId]: _closed, ...windowsById } = get().windowsById;
    set({ windowsById });
    get().retirePanel(application.windowId);
    saveDeskWorkspace(get());
  },
  clearSurfaceWindows() {
    set({ windowsById: {} });
    saveDeskWorkspace(get());
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
    saveDeskWorkspace(get());
  },

  // ---- panel geometry ---------------------------------------------------

  setPanelRect(id, rect, persist = false) {
    const panelRects = { ...get().panelRects, [id]: rect };
    const panelSaved =
      persist && !get().panelSaved.includes(id)
        ? [...get().panelSaved, id]
        : get().panelSaved;
    set({ panelRects, panelSaved });
    if (persist) saveDeskWorkspace(get());
  },
  resetPanelRect(id) {
    const { [id]: _dropped, ...rest } = get().panelRects;
    const panelSaved = get().panelSaved.filter((x) => x !== id);
    set({ panelRects: rest, panelSaved });
    saveDeskWorkspace(get());
  },
  focusPanel(id) {
    const order = compactPanelOrder([
      ...get().panelOrder.filter((x) => x !== id),
      id,
    ]);
    set({ panelOrder: order });
    saveDeskWorkspace(get());
  },
  presentPanel(id) {
    if (get().panelOrder.includes(id)) return;
    get().focusPanel(id);
  },
  retirePanel(id) {
    if (!get().panelOrder.includes(id)) return;
    const order = get().panelOrder.filter((x) => x !== id);
    set({ panelOrder: order });
    saveDeskWorkspace(get());
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
    saveDeskWorkspace(get());
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
    saveDeskWorkspace(get());
  },
  resetLayout() {
    set({
      panelRects: {},
      panelSaved: [],
      panelOrder: [],
      panelMin: [],
      panelMax: [],
    });
    saveDeskWorkspace(get());
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
