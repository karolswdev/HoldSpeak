/** Compositor slice (HS-117-02): panel geometry, stacking order,
 * minimize/maximize, and all six window arrays. */
import { coderOpenFirst } from "../lane/coderOpen";
import { assertNever } from "../assertNever";
import type { DeskState, PanelRect, SliceCreator } from "./types";
import { SURFACE_APPLICATIONS } from "../applications";
import { meetingOfScope, meetingWindowRef, personWindowRef } from "../objectWindows";
import { clampIntoBand } from "../components/window/windowGeometry";
import {
  loadDeskWorkspace,
  saveDeskWorkspace,
} from "./workspaceStorage";
import {
  orderFromDepth,
  raise as raiseDepth,
  sendBack as sendBackDepth,
} from "../compositor/planes";
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

/** Seat a new repository view beside its opener. The source rect stays as
 * arranged; only the new rect is fitted to this screen's working band. */
function siblingRepositoryRect(source: PanelRect): PanelRect {
  const vw = typeof window === "undefined" ? 1280 : window.innerWidth || 1280;
  const vh = typeof window === "undefined" ? 800 : window.innerHeight || 800;
  const fit = (rect: PanelRect) => clampIntoBand(rect, vw, vh, 0, 0);
  const base = fit(source);
  const forward = fit({ ...base, x: base.x + 32, y: base.y + 32 });
  return {
    ...forward,
    x: forward.x === base.x ? fit({ ...base, x: base.x - 32 }).x : forward.x,
    y: forward.y === base.y ? fit({ ...base, y: base.y - 32 }).y : forward.y,
  };
}

/** PHILO-16 (L3) — the depths, at most PANEL_ORDER_LIMIT (the deepest
 * windows leave first), and the order derived from them: the two fields
 * are always written together. */
function stack(depth: Record<string, number>): Pick<DeskState, "panelDepth" | "panelOrder"> {
  const ids = orderFromDepth(depth);
  const kept = ids.length > PANEL_ORDER_LIMIT ? ids.slice(-PANEL_ORDER_LIMIT) : ids;
  const panelDepth: Record<string, number> = {};
  for (const id of kept) panelDepth[id] = depth[id];
  return { panelDepth, panelOrder: kept };
}

export interface PanelLayout {
  rects: Record<string, PanelRect>;
  autoRects?: Record<string, PanelRect>;
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
const initialSavedRects: Record<string, PanelRect> = { ...initialPanelLayout.rects };
const initialAutoRects: Record<string, PanelRect> = { ...initialPanelLayout.autoRects };
const surfaceByAction = new Map(
  SURFACE_APPLICATIONS.map((application) => [application.action, application]),
);
const surfaceByWindowId = new Map(
  SURFACE_APPLICATIONS.map((application) => [application.windowId, application]),
);
const initialWindowsByIdRaw = Object.fromEntries(
  Object.entries(initialWorkspace.windowsById).filter(([id, instance]) => {
    const application = surfaceByWindowId.get(id);
    return application?.action === instance.applicationKey;
  }),
);
const initialWindowsById = initialWindowsByIdRaw;

// PHILO-13-07 (B2) — the open object windows come back after a reload, each
// through its own family's array (the same openers then raise and close it).
const initialWindowLists = initialWorkspace.windows ?? {
  pullouts: [], info: [], roadmap: [], repository: [], workbench: [],
};
// PHILO-17 (owner answer): meeting records live inside the Meetings surface.
// Older workspaces held them as `pullout:meeting:<id>` rows. Rename the one
// authoritative surface row and its saved presentation once, preserving its
// rect, depth and maximized/minimized state. A surface has one scope, so the
// newest saved meeting wins when an old desk contains several pullouts.
const meetingRefFromPullout = (id: string): string | null =>
  id.startsWith("meeting:") ? meetingOfScope(id) : null;
const migratedMeetingRef = [...initialWindowLists.pullouts]
  .reverse()
  .find((id) => meetingRefFromPullout(id) !== null);
const migratedMeetingId = migratedMeetingRef ? meetingRefFromPullout(migratedMeetingRef) : null;
const migratedMeetingPanelId = migratedMeetingId ? `pullout:${migratedMeetingRef}` : null;
if (migratedMeetingPanelId) {
  for (const rects of [initialAutoRects, initialSavedRects]) {
    if (!rects[migratedMeetingPanelId]) continue;
    rects["surface-meetings"] ??= rects[migratedMeetingPanelId];
    delete rects[migratedMeetingPanelId];
  }
}
// A saved owner size wins over an auto-height zoom snapshot at the same id.
const initialPanelRects: Record<string, PanelRect> = { ...initialAutoRects, ...initialSavedRects };
const migratePanelId = (id: string): string => id === migratedMeetingPanelId ? "surface-meetings" : id;
const initialPanelDepth = Object.fromEntries(
  Object.entries(initialPanelLayout.depth ?? {}).map(([id, depth]) => [migratePanelId(id), depth]),
);
const migratedMax = (initialPanelLayout.max ?? []).map(migratePanelId);
const migratedMin = (initialPanelLayout.min ?? []).map(migratePanelId);
const migratedZoom = Object.fromEntries(
  Object.entries(initialPanelLayout.zoom ?? {}).map(([id, rect]) => [migratePanelId(id), rect]),
);
if (migratedMeetingId && !initialWindowsById["surface-meetings"]) {
  initialWindowsById["surface-meetings"] = {
    id: "surface-meetings",
    kind: "surface",
    applicationKey: "review-meetings",
    scope: `meeting:${migratedMeetingId}`,
    persistence: "workspace",
  };
}
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
  ...initialWindowLists.pullouts.filter((id) => !meetingRefFromPullout(id)).map((id) => `pullout:${id}`),
  ...initialWindowLists.info.map((ref) => `info:${ref}`),
  ...initialWindowLists.roadmap.map((slug) => `roadmap:${slug}`),
  ...initialWindowLists.repository.filter((id) => !id.startsWith("view:") || initialWorkspace.repositoryViews?.[id]).map((id) => `repository:${id}`),
  ...initialWindowLists.workbench.map((id) => `workbench:${id}`),
  // PHILO-17: zone windows are retired; a saved one does not return.
]);
const initialPanelMin = migratedMin.filter(
  (id) => returningIds.has(id) || id.startsWith("chair:"),
);
const rehydratedMinimized = new Set(initialPanelMin);

/** True for a window that came back minimized after a reload and has not
 * been restored or closed since: its mount keeps it minimized. */
export function isRehydratedMinimized(id: string): boolean {
  return rehydratedMinimized.has(id);
}

/** PHILO-16 (16b): a window the hub reports seated comes back seated, like
 * one rehydrated from the cache: its mount keeps it minimized. */
export function markRehydratedMinimized(id: string): void {
  rehydratedMinimized.add(id);
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
  | "panelDepth"
  | "stageShelf"
  | "setStageShelf"
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
  | "recentOpened"
  | "recordRecentOpen"
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
  | "openNewRepositoryWindow"
  | "adoptRepositoryWindow"
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
  panelSaved: Object.keys(initialSavedRects),
  // PHILO-17: a saved zone window is retired at boot (no face draws a zone).
  ...stack(Object.fromEntries(Object.entries(initialPanelDepth).filter(([id]) => !id.startsWith("zone:")))),
  stageShelf: initialPanelLayout.shelf ?? "left",
  panelMin: initialPanelMin,
  panelMax: migratedMax,
  panelZoom: migratedZoom,
  windowsById: initialWindowsById,
  pullouts: reopened("id", [
    ...initialWindowLists.pullouts.filter((id) => !meetingRefFromPullout(id)),
  ]),
  zoneWindows: [],
  zoneViewPrefs: initialWorkspace.zoneViewPrefs,
  infoWindows: reopened("ref", initialWindowLists.info),
  roadmapWindows: reopened("slug", initialWindowLists.roadmap),
  repositoryWindows: initialWindowLists.repository.flatMap((id) => {
    if (!id.startsWith("view:")) return [{ id, origin: null }];
    const view = initialWorkspace.repositoryViews?.[id];
    return view ? [{ id, ...view, origin: null }] : [];
  }),
  workbenchWindows: reopened("id", initialWindowLists.workbench),
  // Exempt (B2 story table): the chooser holds no typed text and no record;
  // one pick makes the record, so reopening is the same one gesture.
  newWorkbenchChooser: null,
  recentOpened: initialWorkspace.recentOpened ?? [],
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

  openPullout(id, origin, navigation) {
    const resolved = resolveKindFromId(id, get);
    if (!resolved) {
      console.warn(`openPullout: unknown id "${id}"`);
      return;
    }
    // Betterment Q4: Ask and Thread are one window. A thread opens in Ask
    // (the Thread window is parked).
    if (resolved.kind === "thread") {
      get().openAskThread(resolved.resolvedId, navigation);
      return;
    }
    // PHILO-14 C2: a coder session of a launch opens the agent's lane.
    if (resolved.kind === "coder") {
      const coder = (get().items.coder ?? []).find((c) => c.id === resolved.resolvedId);
      if (coder && coderOpenFirst(coder)) return;
    }
    const openCard = (key: string) => {
      const open = get().pullouts;
      // Only an open that positively resolved a Note can certify a legacy
      // bare window key. Workspace restore keeps IDs alone, so this tag is
      // deliberately live-session evidence rather than a persisted claim.
      const sourceRef = resolved.kind === "note" ? `note:${resolved.resolvedId}` as const : undefined;
      const projectReturn = resolved.kind === "note" && navigation?.projectReturn
        ? { ...navigation.projectReturn } : null;
      const current = open.find((p) => p.id === key);
      if (!current)
        set({ pullouts: [...open, { id: key, origin: origin ?? null, projectReturn, ...(sourceRef ? { sourceRef } : {}) }] });
      else if (current.sourceRef !== sourceRef ||
        (current.projectReturn?.projectId ?? null) !== (projectReturn?.projectId ?? null) ||
        (current.projectReturn?.resourceRef ?? null) !== (projectReturn?.resourceRef ?? null))
        set({ pullouts: open.map((p) => p.id === key ? { ...p, projectReturn, ...(sourceRef ? { sourceRef } : {}) } : p) });
      set({ editingId: null });
      saveDeskWorkspace(get());
      get().recordRecentOpen(key);
      // PHILO-13-06 (B1): an open asks for the window in front, also when
      // it sits iconified on its Dock chip (393: a Chair window iconifies
      // the desk windows), never a press that leaves it hidden.
      get().restorePanel(`pullout:${key}`);
    };
    // PHILO-17 (owner answer): a meeting record lives in the Meetings
    // surface. A second door updates that surface's scope and brings it to
    // the front; People keeps its one-object pullout.
    if (resolved.kind === "meeting") {
      get().openSurfaceWindow("review-meetings", `meeting:${resolved.resolvedId}`);
      return;
    }
    if (resolved.kind === "people" && resolved.resolvedId !== "people" && !resolved.resolvedId.startsWith("project:")) {
      openCard(`people:${resolved.resolvedId}`);
      return;
    }
    const desc = PRIMITIVES[resolved.kind];
    switch (desc.surface.type) {
      case "pullout": {
        // Bare and qualified doors can name the same open record. Keep its
        // existing window key so its geometry and retained drafts stay put.
        const existing = get().pullouts.find((pullout) => {
          if (pullout.sourceRef) return resolved.kind === "note" && pullout.sourceRef === `note:${resolved.resolvedId}`;
          if (resolved.kind === "note" && pullout.id === resolved.resolvedId) return false;
          const target = resolveKindFromId(pullout.id, get);
          return target?.kind === resolved.kind && target.resolvedId === resolved.resolvedId;
        });
        // An untagged restored bare key has no proved kind. A qualified
        // Note must not co-opt it; nor may another kind co-opt a tagged Note.
        const occupiedByOther = !id.includes(":") && get().pullouts.some((pullout) =>
          pullout.id === id && (resolved.kind === "note"
            ? pullout.sourceRef !== `note:${resolved.resolvedId}`
            : !!pullout.sourceRef));
        openCard(existing?.id ?? (occupiedByOther ? `${resolved.kind}:${resolved.resolvedId}` : id));
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

  // PHILO-17: no live door opens a zone window (no face draws a zone); the
  // store primitive stays for the parked Floor and its tests.
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
  openNewRepositoryWindow(id, origin, initialPath, sourceWindowId) {
    let windowId: string;
    do {
      windowId = `view:${globalThis.crypto?.randomUUID?.() ?? `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`}`;
    } while (get().repositoryWindows.some((w) => w.id === windowId));
    set({ repositoryWindows: [...get().repositoryWindows, {
      id: windowId, resourceId: id, origin: origin ?? null,
      ...(initialPath ? { initialPath } : {}),
    }] });
    const sourceId = sourceWindowId ?? `repository:${id}`;
    const rendered = typeof document === "undefined" ? null : document.getElementById(sourceId)?.getBoundingClientRect();
    const source = get().panelRects[sourceId] ?? (rendered && rendered.width && rendered.height
      ? { x: rendered.left, y: rendered.top, w: rendered.width, h: rendered.height } : null);
    if (source) get().setPanelRect(`repository:${windowId}`, siblingRepositoryRect(source), true);
    get().restorePanel(`repository:${windowId}`);
    saveDeskWorkspace(get());
    return windowId;
  },
  adoptRepositoryWindow(instanceId, resourceId) {
    if (!instanceId.startsWith("view:") || !resourceId) return;
    const current = get().repositoryWindows;
    const existing = current.find((w) => w.id === instanceId);
    if (existing?.resourceId === resourceId) return;
    set({ repositoryWindows: existing
      ? current.map((w) => w.id === instanceId ? { ...w, resourceId } : w)
      : [...current, { id: instanceId, resourceId, origin: null }],
    });
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

  recordRecentOpen(ref) {
    const clean = String(ref || "").trim();
    if (!clean) return;
    const next = [clean, ...get().recentOpened.filter((entry) => entry !== clean)].slice(0, 6);
    set({ recentOpened: next });
    saveDeskWorkspace(get());
  },

  // ---- static applications (one normalized lifecycle authority) --------

  openSurfaceWindow(key, scope) {
    // PHILO-17 (owner answer): Meetings keeps one surface window. Its
    // meeting ref is its scope, so the same rect/title survive a deep link,
    // reload and Back. People still uses an object pullout.
    const meetingScope = key === "review-meetings" ? meetingWindowRef(scope) : null;
    const objectRef = key === "open-people" ? personWindowRef(scope) : null;
    if (objectRef) {
      get().openPullout(objectRef);
      return;
    }
    // PHILO-17 (owner answer): while this desk records a meeting, its live
    // meeting door still lands in the single scoped Meetings surface.
    const liveId = get().liveMeetingId;
    if (key === "record-live" && liveId && get().recording !== "idle") {
      get().openSurfaceWindow("review-meetings", `meeting:${liveId}`);
      return;
    }
    const application = surfaceByAction.get(key);
    if (!application) {
      console.warn(`openSurfaceWindow: unknown application "${key}"`);
      return;
    }
    const instance = {
      id: application.windowId,
      kind: "surface" as const,
      applicationKey: application.action,
      scope: meetingScope ?? scope ?? null,
      persistence: "workspace" as const,
    };
    set({
      windowsById: {
        ...get().windowsById,
        [application.windowId]: instance,
      },
    });
    get().recordRecentOpen(`app:${application.action}`);
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
    // PHILO-16 (L3): a raise is `depth = ++highest`; nothing is spliced.
    const depth = raiseDepth({ depth: get().panelDepth, seated: [] }, id).depth;
    set(stack(depth));
    saveDeskWorkspace(get());
  },
  presentPanel(id) {
    if (id in get().panelDepth) return;
    get().focusPanel(id);
  },
  retirePanel(id) {
    rehydratedMinimized.delete(id);
    if (!(id in get().panelDepth)) return;
    const { [id]: _gone, ...depth } = get().panelDepth;
    set(stack(depth));
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
    const depth = raiseDepth({ depth: get().panelDepth, seated: [] }, id).depth;
    set({ panelMin, ...stack(depth) });
    saveDeskWorkspace(get());
  },
  toggleMaximizePanel(id) {
    const has = get().panelMax.includes(id);
    const panelMax = has
      ? get().panelMax.filter((x) => x !== id)
      : [...get().panelMax, id];
    const depth = raiseDepth({ depth: get().panelDepth, seated: [] }, id).depth;
    set({ panelMax, ...stack(depth) });
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
  // PHILO-16 (L3): the depth goes under the lowest SHOWN window (a seated
  // window keeps its depth and is not counted).
  sendPanelToBack(id) {
    const depth = sendBackDepth(
      { depth: get().panelDepth, seated: get().panelMin },
      id,
    ).depth;
    set(stack(depth));
    saveDeskWorkspace(get());
  },
  setStageShelf(side) {
    if (get().stageShelf === side) return;
    set({ stageShelf: side });
    saveDeskWorkspace(get());
  },
  resetLayout() {
    set({
      panelZoom: {},
      panelRects: {},
      panelSaved: [],
      panelOrder: [],
      panelDepth: {},
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
    let bareId = id.slice(colonIdx + 1);
    // ROADMAP ONLY: a Roadmap item's id is already `roadmap:<slug>`
    // (api.ts fromWireRoadmap), so its qualified ref reads
    // `roadmap:roadmap:<slug>`; the window opened on `roadmap:<slug>` and
    // showed "Roadmap not found" (B0-F4). Every other kind keeps its id
    // whole: a Workbench may be named `workbench:weekly` (Astra, #869).
    if (prefix === "roadmap" && bareId.startsWith("roadmap:")) bareId = bareId.slice("roadmap:".length);
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
