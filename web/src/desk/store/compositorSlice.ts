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
  zoom?: Record<string, PanelRect>;
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

// PHILO-13-07 (B2) — the open object windows come back after a reload, each
// through its own family's array (the same openers then raise and close it).
const initialWindowLists = initialWorkspace.windows ?? {
  pullouts: [], info: [], roadmap: [], repository: [], workbench: [],
};
const reopened = <K extends string>(key: K, values: string[]) =>
  values.map((value) => ({ [key]: value, origin: null }) as Record<K, string> & {
    origin: null;
  });

// A minimized window comes back minimized only when its window comes back
// too; a stale id (a window that does not return) is dropped. The frame's
// "an open presents the window" rule then skips these ids once, on the
// window's mount after the reload (`isRehydratedMinimized`), until a restore
// or a close ends that state (idempotent, so a double-run effect agrees).
const returningIds = new Set<string>([
  ...Object.keys(initialWindowsById),
  ...initialWindowLists.pullouts.map((id) => `pullout:${id}`),
  ...initialWindowLists.info.map((ref) => `info:${ref}`),
  ...initialWindowLists.roadmap.map((slug) => `roadmap:${slug}`),
  ...initialWindowLists.repository.map((id) => `repository:${id}`),
  ...initialWindowLists.workbench.map((id) => `workbench:${id}`),
  ...initialWorkspace.zoneWindows.map((id) => `zone:${id}`),
]);
const initialPanelMin = (initialPanelLayout.min ?? []).filter(
  (id) => returningIds.has(id) || id.startsWith("chair:"),
);
const rehydratedMinimized = new Set(initialPanelMin);

/** True for a window that came back minimized after a reload and has not
 * been restored or closed since: its mount keeps it minimized. */
export function isRehydratedMinimized(id: string): boolean {
  return rehydratedMinimized.has(id);
}

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
  | "panelZoom"
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
  | "setZoomRect"
  | "sendPanelToBack"
  | "resetLayout"
  | "drafts"
  | "places"
  | "setDraft"
  | "setPlace"
>;

export const createCompositorSlice: SliceCreator<CompositorSlice> = (set, get) => ({
  panelRects: initialPanelRects,
  panelSaved: Object.keys(initialPanelRects),
  panelOrder: initialPanelLayout.order,
  panelMin: initialPanelMin,
  panelMax: initialPanelLayout.max,
  panelZoom: initialPanelLayout.zoom ?? {},
  windowsById: initialWindowsById,
  pullouts: reopened("id", initialWindowLists.pullouts),
  zoneWindows: initialWorkspace.zoneWindows.map((id) => ({ id, origin: null })),
  zoneViewPrefs: initialWorkspace.zoneViewPrefs,
  infoWindows: reopened("ref", initialWindowLists.info),
  roadmapWindows: reopened("slug", initialWindowLists.roadmap),
  repositoryWindows: reopened("id", initialWindowLists.repository),
  workbenchWindows: reopened("id", initialWindowLists.workbench),
  // Exempt (B2 story table): the chooser holds no typed text and no record;
  // one pick makes the record, so reopening is the same one gesture.
  newWorkbenchChooser: null,
  drafts: initialWorkspace.drafts ?? {},
  places: initialWorkspace.places ?? {},

  // ---- drafts and places (PHILO-13-07 B2) ------------------------------

  setDraft(key, text) {
    const current = get().drafts;
    // null forgets the draft; "" keeps an emptied field as its own state.
    if (text === null ? !(key in current) : current[key] === text) return;
    const { [key]: _old, ...rest } = current;
    set({ drafts: text === null ? rest : { ...rest, [key]: text } });
    saveDeskWorkspace(get());
  },
  setPlace(key, value) {
    const current = get().places;
    if ((current[key] ?? "") === value) return;
    const { [key]: _old, ...rest } = current;
    set({ places: value ? { ...rest, [key]: value } : rest });
    saveDeskWorkspace(get());
  },

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
        saveDeskWorkspace(get());
        // PHILO-13-06 (B1): an open asks for the window in front, also when
        // it sits iconified on its Dock chip (393: a Chair window iconifies
        // the desk windows), never a press that leaves it hidden.
        get().restorePanel(`pullout:${id}`);
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
    saveDeskWorkspace(get());
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
    saveDeskWorkspace(get());
  },
  closeInfoWindow(ref) {
    closeInfo(ref, set, get);
    saveDeskWorkspace(get());
  },
  openRoadmapWindow(slug, origin) {
    openRoadmap(slug, origin, set, get);
    saveDeskWorkspace(get());
  },
  closeRoadmapWindow(slug) {
    closeRoadmap(slug, set, get);
    saveDeskWorkspace(get());
  },
  openRepositoryWindow(id, origin) {
    openRepository(id, origin, set, get);
    saveDeskWorkspace(get());
  },
  closeRepositoryWindow(id) {
    closeRepository(id, set, get);
    saveDeskWorkspace(get());
  },
  openWorkbenchWindow(id, origin) {
    openWorkbench(id, origin, set, get);
    saveDeskWorkspace(get());
  },
  closeWorkbenchWindow(id) {
    closeWorkbench(id, set, get);
    saveDeskWorkspace(get());
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
    // PHILO-13-06 (B1): in front, also from its Dock chip (iconified).
    get().restorePanel(application.windowId);
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
    rehydratedMinimized.delete(id);
    if (!get().panelOrder.includes(id)) return;
    const order = get().panelOrder.filter((x) => x !== id);
    set({ panelOrder: order });
    saveDeskWorkspace(get());
  },
  minimizePanel(id) {
    if (get().panelMin.includes(id)) return;
    set({ panelMin: [...get().panelMin, id] });
    saveDeskWorkspace(get());
  },
  restorePanel(id) {
    rehydratedMinimized.delete(id);
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
  // PHILO-13-12 (C2) — zoom as Intuition does it: the window alternates
  // between two remembered rects. `panelRects` holds the normal one (never
  // touched while zoomed, so zoom back restores it exactly); `panelZoom`
  // holds the zoomed one once the user sizes or moves the zoomed window.
  setZoomRect(id, rect, persist = false) {
    set({ panelZoom: { ...(get().panelZoom ?? {}), [id]: rect } });
    if (persist) saveDeskWorkspace(get());
  },
  // PHILO-13-12 (C2) — depth: the window goes behind every other window;
  // the next one in the order becomes the front window.
  sendPanelToBack(id) {
    const order = compactPanelOrder([
      id,
      ...get().panelOrder.filter((x) => x !== id),
    ]);
    set({ panelOrder: order });
    saveDeskWorkspace(get());
  },
  resetLayout() {
    set({
      panelZoom: {},
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
