/** PHILO-16 (16b, COMPOSITOR.md §13 L1) — the hub owns the desk's windows.
 *
 * Every browser is one view of the same desk; an agent reaches the same
 * windows over MCP. The hub's rows (`GET /api/desk/windows`) are the state;
 * the browser store is a presentation of them, and the workspace document in
 * localStorage is a cache for the first paint (no flash) that the hub's rows
 * overwrite on load.
 *
 *   seed     on load, the hub's rows open, place (share+px resolved against
 *            this view's band, L5), stack (the hub's depth, L3) and seat the
 *            windows here.
 *   write    every store write that persists to the workspace document also
 *            goes to the hub: the change shows at once and holds while its
 *            request is in flight (`anticipate`, L2); when it settles the
 *            hub's row replaces it; a 409 re-reads and follows. Rects are
 *            SENT as share+px (`record` against this view), so the Mac and
 *            the iPad resolve the same arrangement.
 *   follow   a `desk_changed` frame of kind `windows` re-reads and re-seeds
 *            the changed ids, never an id with a request in flight.
 *
 * One transport (the hub's HTTP routes and its one bus); no second store. */
import { ApiError, apiFetch } from "../../lib/api";
import { SURFACE_APPLICATIONS } from "../applications";
import { CHAIR_WINDOW_IDS, closeChairWindow, useChairWindows } from "../chair/chairWindows";
import { workBand } from "../components/window/windowGeometry";
import { CONDUCTOR_WINDOW_ID, useConductor } from "../conductor/store";
import { PARKED_WINDOW_ID, drawerWindowId, useDrawers } from "../drawer/store";
import { markRehydratedMinimized, useDesk, type PanelRect } from "../store";
import { onWorkspaceSaved, saveDeskWorkspace } from "../store/workspaceStorage";
import { anticipate, createPresentations, type Change, type Presentations } from "./anticipate";
import { bandFor, record, resolveRect, type Rect, type Value, type ValueRect } from "./geometry";
import { orderFromDepth } from "./planes";
import { frameChanges } from "./windowFrames";

export { isWindowsOnlyFrame } from "./windowFrames";

// ---- the hub's shapes -------------------------------------------------------

export interface HubWindowRow {
  id: string;
  app: string;
  object_ref: string | null;
  x: Value | null;
  y: Value | null;
  w: Value | null;
  h: Value | null;
  depth: number;
  minimized: boolean;
  zoomed: boolean;
  zoom: ValueRect | null;
  arranged: boolean;
  room: string | null;
  front: boolean;
  revision: number;
  updated_at?: string;
}

export interface HubRegistry {
  static: Record<string, string>;
  families: Record<string, string>;
}

export interface HubWindowList {
  windows: HubWindowRow[];
  stage_shelf: "left" | "right";
  /** The desk's revision when the list was read (one counter per desk). */
  revision: number;
  shelf_revision?: number;
  /** False until the hub first held this desk's windows. */
  adopted?: boolean;
  registry?: HubRegistry;
}

type Verb = "open" | "close" | "set_geometry" | "raise" | "send_back" | "seat" | "zoom";

export interface HubTransport {
  list(): Promise<HubWindowList>;
  verb(id: string, verb: Verb, body: Record<string, unknown>): Promise<HubWindowRow | { id: string; closed: true; revision?: number }>;
  arrange(rects: Record<string, ValueRect>, expected: Record<string, number>): Promise<{ windows: HubWindowRow[] }>;
  shelf(side: "left" | "right", expected?: number): Promise<{ stage_shelf: "left" | "right"; revision: number }>;
}

export const httpTransport: HubTransport = {
  list: () => apiFetch<HubWindowList>("/api/desk/windows"),
  verb: (id, verb, body) =>
    apiFetch(`/api/desk/windows/${encodeURIComponent(id)}/${verb}`, { method: "POST", json: body }),
  arrange: (rects, expected) =>
    apiFetch("/api/desk/windows/arrange", { method: "POST", json: { rects, expected_revisions: expected } }),
  shelf: (side, expected) =>
    apiFetch("/api/desk/windows/stage-shelf", { method: "POST", json: { side, expected_revision: expected } }),
};

// ---- the local families: how a hub row opens and closes here ---------------

interface Adapter {
  isOpen(): boolean;
  open(): void;
  close(): void;
}

const surfaceByWindowId = new Map(SURFACE_APPLICATIONS.map((a) => [a.windowId, a]));

function listAdapter<K extends string>(
  prefix: string,
  id: string,
  read: () => { [key in K]: string }[],
  key: K,
  open: (value: string) => void,
  close: (value: string) => void,
): Adapter | null {
  if (!id.startsWith(prefix)) return null;
  const value = id.slice(prefix.length);
  if (!value || value.startsWith("__")) return null;
  return {
    isOpen: () => read().some((w) => w[key] === value),
    open: () => open(value),
    close: () => close(value),
  };
}

/** The family that opens and closes window `id` in this browser, or null
 * (a window another surface opens; its stacking still follows the hub). */
export function adapterFor(id: string): Adapter | null {
  const d = () => useDesk.getState();
  if (CHAIR_WINDOW_IDS.includes(id)) {
    return {
      isOpen: () => !useChairWindows.getState().closed[id],
      open: () => useChairWindows.setState((s) => ({ closed: { ...s.closed, [id]: false } })),
      close: () => closeChairWindow(id),
    };
  }
  // The Project drawers and the Parked drawer (drawer/store.ts): the row's
  // object is the Project; the drawer's own open path opens it.
  if (id.startsWith("drawer:project:") && id.length > "drawer:project:".length) {
    const projectId = id.slice("drawer:project:".length);
    return {
      isOpen: () => useDrawers.getState().drawers.some((x) => x.projectId === projectId),
      open: () => useDrawers.getState().openDrawer(projectId),
      close: () => useDrawers.getState().closeDrawer(projectId),
    };
  }
  if (id === PARKED_WINDOW_ID) {
    return {
      isOpen: () => useDrawers.getState().parked !== null,
      open: () => useDrawers.getState().openParked(),
      close: () => useDrawers.getState().closeParked(),
    };
  }
  if (id === CONDUCTOR_WINDOW_ID) {
    return {
      isOpen: () => useConductor.getState().open,
      open: () => useConductor.getState().openWindow(),
      close: () => useConductor.getState().closeWindow(),
    };
  }
  const surface = surfaceByWindowId.get(id);
  if (surface) {
    return {
      isOpen: () => id in d().windowsById,
      open: () => d().openSurfaceWindow(surface.action),
      close: () => d().closeSurfaceWindow(surface.action),
    };
  }
  return (
    listAdapter("pullout:", id, () => d().pullouts, "id",
      (v) => useDesk.setState({ pullouts: [...d().pullouts, { id: v, origin: null }] }),
      (v) => d().closePullout(v)) ??
    listAdapter("zone:", id, () => d().zoneWindows, "id", (v) => d().openZoneWindow(v), (v) => d().closeZoneWindow(v)) ??
    listAdapter("info:", id, () => d().infoWindows, "ref", (v) => d().openInfoWindow(v), (v) => d().closeInfoWindow(v)) ??
    listAdapter("roadmap:", id, () => d().roadmapWindows, "slug", (v) => d().openRoadmapWindow(v), (v) => d().closeRoadmapWindow(v)) ??
    listAdapter("repository:", id, () => d().repositoryWindows, "id", (v) => d().openRepositoryWindow(v), (v) => d().closeRepositoryWindow(v)) ??
    listAdapter("workbench:", id, () => d().workbenchWindows, "id", (v) => d().openWorkbenchWindow(v), (v) => d().closeWorkbenchWindow(v))
  );
}

/** Every window an adapter says is open here. */
function adapterOpenIds(): string[] {
  const s = useDesk.getState();
  const chair = useChairWindows.getState().closed;
  return [
    ...CHAIR_WINDOW_IDS.filter((id) => !chair[id]),
    ...Object.keys(s.windowsById),
    ...s.pullouts.map((w) => `pullout:${w.id}`),
    ...s.zoneWindows.map((w) => `zone:${w.id}`),
    ...s.infoWindows.map((w) => `info:${w.ref}`),
    ...s.roadmapWindows.map((w) => `roadmap:${w.slug}`),
    ...s.repositoryWindows.map((w) => `repository:${w.id}`),
    ...s.workbenchWindows.map((w) => `workbench:${w.id}`),
    ...useDrawers.getState().drawers.map((d) => drawerWindowId(d.projectId)),
    ...(useDrawers.getState().parked ? [PARKED_WINDOW_ID] : []),
    ...(useConductor.getState().open ? [CONDUCTOR_WINDOW_ID] : []),
  ];
}

// ---- the snapshot: what this browser shows of the desk ----------------------

interface Snapshot {
  open: Set<string>;
  depth: Record<string, number>;
  min: Set<string>;
  max: Set<string>;
  rects: Record<string, PanelRect>;
  zoom: Record<string, PanelRect>;
  shelf: "left" | "right";
}

const sameRect = (a?: PanelRect, b?: PanelRect) =>
  !!a && !!b && a.x === b.x && a.y === b.y && a.w === b.w && a.h === b.h;

export interface HubWindowsOptions {
  transport?: HubTransport;
  /** The view a share resolves against: the working band (L5). */
  view?: () => Rect;
  /** At phone width the windows are sheets: no rect is sent from there. */
  compact?: () => boolean;
}

const defaultView = (): Rect => {
  const vw = typeof window === "undefined" ? 1280 : window.innerWidth || 1280;
  const vh = typeof window === "undefined" ? 800 : window.innerHeight || 800;
  return bandFor(vw, vh, workBand());
};

const defaultCompact = () =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia("(max-width: 720px)").matches;

export interface HubWindows {
  /** Read the hub and seed this desk (hub wins; an empty hub adopts this
   * browser's open windows). Resolves when seeded; never rejects. */
  start(): Promise<void>;
  /** A `desk_changed` frame's data. */
  onFrame(data: unknown): void;
  /** Send this browser's persisted changes to the hub now. */
  sync(): void;
  /** True once the hub's rows seeded this desk (its order is the desk's). */
  seeded(): boolean;
  /** Resolves when every request in flight has settled (tests, the glass). */
  idle(): Promise<void>;
  readonly presentations: Presentations;
  readonly rows: ReadonlyMap<string, HubWindowRow>;
  stop(): void;
}

export function createHubWindows(options: HubWindowsOptions = {}): HubWindows {
  const transport = options.transport ?? httpTransport;
  const view = options.view ?? defaultView;
  const compact = options.compact ?? defaultCompact;
  const rows = new Map<string, HubWindowRow>();
  let registry: HubRegistry | null = null;
  let shelfRevision: number | undefined;
  let synced: Snapshot | null = null;
  let applying = false;
  let started: Promise<void> | null = null;
  let stopped = false;
  let scheduled = false;
  let queue: Promise<unknown> = Promise.resolve();
  let inflight = 0;
  let idleWaiters: (() => void)[] = [];
  let reading: Promise<void> | null = null;
  let readAgain: Set<string> | "all" | null = null;

  const presentations = createPresentations((id) => {
    const row = rows.get(id);
    return row ? { depth: row.depth, minimized: row.minimized } : undefined;
  });

  const known = (id: string): boolean => {
    if (!registry) return false;
    if (id in registry.static) return true;
    return Object.keys(registry.families).some((p) => id.startsWith(p) && id.length > p.length);
  };

  const isOpenHere = (id: string): boolean => {
    const adapter = adapterFor(id);
    return adapter ? adapter.isOpen() : id in useDesk.getState().panelDepth;
  };

  function snapshot(): Snapshot {
    const s = useDesk.getState();
    const candidates = new Set([...Object.keys(s.panelDepth), ...adapterOpenIds()]);
    const open = new Set([...candidates].filter((id) => known(id) && isOpenHere(id)));
    const rects: Record<string, PanelRect> = {};
    for (const id of s.panelSaved) if (open.has(id) && s.panelRects[id]) rects[id] = s.panelRects[id];
    const zoom: Record<string, PanelRect> = {};
    for (const [id, r] of Object.entries(s.panelZoom ?? {})) if (open.has(id)) zoom[id] = r;
    return {
      open,
      depth: { ...s.panelDepth },
      min: new Set(s.panelMin.filter((id) => open.has(id))),
      max: new Set(s.panelMax.filter((id) => open.has(id))),
      rects,
      zoom,
      shelf: s.stageShelf,
    };
  }

  const rectOf = (row: { x: Value | null; y: Value | null; w: Value | null; h: Value | null }): PanelRect | null => {
    if (row.x == null || row.y == null || row.w == null || row.h == null) return null;
    try {
      return resolveRect({ x: row.x, y: row.y, w: row.w, h: row.h }, view());
    } catch {
      return null;
    }
  };

  // ---- seed / follow: the hub's rows onto this desk ------------------------

  /** The revision this view last applied per window: a row (its last
   * write's revision) or a close (the desk's revision of the close). A read
   * or an answer OLDER than it is dropped (L2): a delayed read never moves a
   * window back from a settled write. */
  const applied = new Map<string, number>();

  /** Apply the hub's rows for `scope` (every id when "all"). An id with a
   * request in flight is left as it shows; a row is applied only when it is
   * newer than what this view applied; an id absent from the list closes here
   * only when the list was read after what this view applied. */
  function apply(list: HubWindowList, scope: Set<string> | "all"): void {
    const byId = new Map(list.windows.map((r) => [r.id, r]));
    const free = (id: string) => (scope === "all" || scope.has(id)) && presentations.pending(id) === 0;
    const accepted = list.windows.filter((r) => free(r.id) && r.revision > (applied.get(r.id) ?? -1));
    const ids = scope === "all" ? new Set([...rows.keys(), ...adapterOpenIds(), ...Object.keys(useDesk.getState().panelDepth)]) : scope;
    const gone = [...ids].filter(
      (id) => free(id) && known(id) && !byId.has(id) && list.revision > (applied.get(id) ?? -1),
    );
    applying = true;
    try {
      for (const row of accepted) {
        rows.set(row.id, row);
        applied.set(row.id, row.revision);
        see(row.id, row.revision);
      }
      for (const id of gone) {
        rows.delete(id);
        applied.set(id, list.revision);
      }

      // Close here what the hub closed; open here what the hub opened.
      const closed: string[] = [];
      for (const id of gone) {
        if (!isOpenHere(id)) continue;
        adapterFor(id)?.close();
        closed.push(id);
      }
      for (const row of accepted) {
        if (!isOpenHere(row.id)) adapterFor(row.id)?.open();
      }

      // One write of the stacking, the seats, the zooms and the rects.
      const s = useDesk.getState();
      const min = new Set(s.panelMin);
      const max = new Set(s.panelMax);
      const rects = { ...s.panelRects };
      const saved = new Set(s.panelSaved);
      const zoom = { ...(s.panelZoom ?? {}) };
      for (const id of [...closed, ...gone]) {
        min.delete(id);
        max.delete(id);
      }
      for (const row of accepted) {
        if (row.minimized) {
          min.add(row.id);
          markRehydratedMinimized(row.id);
        } else min.delete(row.id);
        if (row.zoomed) max.add(row.id);
        else max.delete(row.id);
        const rect = row.arranged ? rectOf(row) : null;
        if (rect) {
          rects[row.id] = rect;
          saved.add(row.id);
        } else if (!row.arranged && saved.has(row.id)) {
          saved.delete(row.id);
          delete rects[row.id];
        }
        const zr = row.zoom ? rectOf(row.zoom) : null;
        if (zr) zoom[row.id] = zr;
      }
      const depth = mergeStacking(s.panelDepth, new Set(gone));
      const shelf = scope === "all" || scope.has("desk") ? list.stage_shelf : s.stageShelf;
      if ((scope === "all" || scope.has("desk")) && list.shelf_revision !== undefined) shelfRevision = list.shelf_revision;
      useDesk.setState({
        panelDepth: depth,
        panelOrder: orderFromDepth(depth),
        panelMin: [...min],
        panelMax: [...max],
        panelRects: rects,
        panelSaved: [...saved],
        panelZoom: zoom,
        stageShelf: shelf,
      });
      saveDeskWorkspace(useDesk.getState());
    } finally {
      applying = false;
    }
    const band = view();
    lastBand = `${band.x},${band.y},${band.w},${band.h}`;
    synced = snapshot();
    // A window open here that the hub does not hold yet: it goes to the hub
    // on the next sync.
    const unsent = [...synced.open].filter((id) => !rows.has(id) && presentations.pending(id) === 0);
    if (unsent.length) {
      for (const id of unsent) synced.open.delete(id);
      schedule();
    }
  }

  /** L3: the hub's windows stack in the hub's depth order; a window this
   * view stacks on its own (one no row can open, or one with a request in
   * flight) keeps its place just above the hub window it sat above. The
   * numbers are this view's (1..n); the ORDER is the hub's. */
  function mergeStacking(local: Record<string, number>, gone: Set<string>): Record<string, number> {
    const governed = (id: string) => rows.has(id) && presentations.pending(id) === 0;
    const before = orderFromDepth(local).filter((id) => !gone.has(id));
    const anchored = new Map<string, string[]>();
    let anchor = "";
    for (const id of before) {
      if (governed(id)) {
        anchor = id;
        continue;
      }
      anchored.set(anchor, [...(anchored.get(anchor) ?? []), id]);
    }
    const hubOrder = [...rows.values()]
      .filter((r) => governed(r.id))
      .sort((a, b) => a.depth - b.depth || (a.id < b.id ? -1 : 1))
      .map((r) => r.id);
    const order = [...(anchored.get("") ?? [])];
    for (const id of hubOrder) order.push(id, ...(anchored.get(id) ?? []));
    const depth: Record<string, number> = {};
    order.forEach((id, i) => {
      depth[id] = i + 1;
    });
    return depth;
  }

  /** Follow this view's own settled answer: a row, or a close. */
  function follow(row: HubWindowRow | null, id: string, closedAt?: number): void {
    if (presentations.pending(id) > 0) return;
    apply(
      { windows: row ? [row] : [], stage_shelf: useDesk.getState().stageShelf, revision: row ? -1 : closedAt ?? -1 },
      new Set([id]),
    );
  }

  // ---- re-read (a frame, a 409) -------------------------------------------

  function reread(scope: Set<string> | "all"): Promise<void> {
    if (reading) {
      readAgain = readAgain === "all" || scope === "all" ? "all" : new Set([...(readAgain ?? []), ...scope]);
      return reading;
    }
    reading = transport
      .list()
      .then((list) => {
        if (list.registry) registry = list.registry;
        if (!stopped) apply(list, scope);
      })
      .catch(() => undefined)
      .finally(() => {
        reading = null;
        const again = readAgain;
        readAgain = null;
        if (again) void reread(again);
      });
    return reading;
  }

  // ---- write: this browser's changes to the hub ----------------------------

  function enqueue(ids: string[], change: Change, send: () => Promise<unknown>): void {
    inflight += 1;
    let settle!: (row: unknown) => void;
    const request = new Promise<unknown>((resolve) => {
      settle = resolve;
    });
    for (const id of ids) void anticipate(presentations, id, change, request);
    queue = queue.then(async () => {
      let answer: unknown = null;
      try {
        answer = await send();
      } catch (err) {
        answer = err;
      }
      settle(answer);
      await Promise.resolve(); // the holds release (anticipate's settle) first
      if (answer instanceof ApiError || answer instanceof Error) {
        // 409: the hub has another revision; 404: it closed. Re-read, follow.
        await reread(new Set(ids));
      } else if (answer && typeof answer === "object" && "windows" in answer) {
        for (const row of (answer as { windows: HubWindowRow[] }).windows) see(row.id, row.revision);
        for (const row of (answer as { windows: HubWindowRow[] }).windows) follow(row, row.id);
      } else if (answer && typeof answer === "object" && "closed" in answer) {
        follow(null, ids[0], Number((answer as { revision?: unknown }).revision ?? Infinity));
      } else if (answer && typeof answer === "object" && "id" in answer) {
        const row = answer as HubWindowRow;
        see(row.id, row.revision);
        follow(row, row.id);
      }
      inflight -= 1;
      if (inflight === 0) {
        const waiters = idleWaiters;
        idleWaiters = [];
        for (const w of waiters) w();
      }
    });
  }

  /** The newest revision this view has seen per window (its own answers
   * included, before they are applied): the next write's expected revision,
   * so two queued writes on one window never refuse each other. */
  const seen = new Map<string, number>();
  const see = (id: string, revision: unknown) => {
    const n = Number(revision);
    if (Number.isFinite(n) && n > (seen.get(id) ?? -1)) seen.set(id, n);
  };
  const rev = (id: string) => seen.get(id) ?? rows.get(id)?.revision;
  const shares = (rect: PanelRect): ValueRect => record(rect, view());

  function sync(): void {
    scheduled = false;
    if (stopped || applying || !synced || !registry) return;
    const prev = synced;
    const cur = snapshot();
    synced = cur;
    const sendRects = !compact();
    const geometry: Record<string, ValueRect | null> = {};

    const opened = [...cur.open]
      .filter((id) => !prev.open.has(id))
      .sort((a, b) => (cur.depth[a] ?? 0) - (cur.depth[b] ?? 0));
    for (const id of opened) {
      const rect = sendRects ? cur.rects[id] : undefined;
      enqueue([id], { front: true }, () =>
        transport.verb(id, "open", { ...(rect ? { geometry: shares(rect) } : {}) }),
      );
      if (cur.min.has(id)) enqueue([id], { minimized: true }, () => transport.verb(id, "seat", { seated: true, expected_revision: rev(id) }));
    }
    const onHub = (id: string) => rows.has(id) || presentations.pending(id) > 0;
    for (const id of prev.open) {
      if (cur.open.has(id) || !onHub(id)) continue;
      enqueue([id], {}, () => transport.verb(id, "close", { expected_revision: rev(id) }));
    }
    const both = [...cur.open].filter((id) => prev.open.has(id) && onHub(id));
    const unseated = new Set<string>();
    for (const id of both) {
      const seated = cur.min.has(id);
      if (seated === prev.min.has(id)) continue;
      if (!seated) unseated.add(id);
      enqueue([id], seated ? { minimized: true } : { front: true }, () =>
        transport.verb(id, "seat", { seated, expected_revision: rev(id) }),
      );
    }
    // The stacking, by ORDER (a legacy order write renumbers the depths):
    // one window to the top is a raise, one to the bottom a send back; any
    // other reorder raises each window from the first difference up, which
    // rebuilds the same order on the hub.
    // A window that left the stacking here without closing (an iconified
    // Chair window unmounts; a sheet) has no depth: not a send back.
    const stacked = both.filter((id) => id in cur.depth && id in prev.depth);
    const ordered = (depth: Record<string, number>) =>
      [...stacked].sort((a, b) => (depth[a] ?? 0) - (depth[b] ?? 0) || (a < b ? -1 : 1));
    const before = ordered(prev.depth);
    const after = ordered(cur.depth);
    const first = after.findIndex((id, i) => before[i] !== id);
    if (first >= 0) {
      const top = after[after.length - 1];
      const bottom = after[0];
      const without = (x: string) => before.filter((id) => id !== x).join("|");
      const raise = (id: string) => {
        if (!unseated.has(id)) enqueue([id], { front: true }, () => transport.verb(id, "raise", { expected_revision: rev(id) }));
      };
      if (after.slice(0, -1).join("|") === without(top)) raise(top);
      else if (after.slice(1).join("|") === without(bottom))
        enqueue([bottom], {}, () => transport.verb(bottom, "send_back", { expected_revision: rev(bottom) }));
      else for (const id of after.slice(first)) raise(id);
    }
    // A window that rejoins the stacking here presents on top (a remount).
    for (const id of both) {
      if (id in cur.depth && !(id in prev.depth) && !unseated.has(id))
        enqueue([id], { front: true }, () => transport.verb(id, "raise", { expected_revision: rev(id) }));
    }
    for (const id of both) {
      const zoomed = cur.max.has(id);
      const zoomRect = sendRects && cur.zoom[id] && !sameRect(cur.zoom[id], prev.zoom[id]) ? cur.zoom[id] : undefined;
      if (zoomed !== prev.max.has(id) || (zoomed && zoomRect)) {
        enqueue([id], zoomed ? { front: true } : {}, () =>
          transport.verb(id, "zoom", {
            zoomed,
            ...(zoomRect ? { rect: shares(zoomRect) } : {}),
            expected_revision: rev(id),
          }),
        );
      }
      if (!sendRects) continue;
      if (cur.rects[id] && !sameRect(cur.rects[id], prev.rects[id])) geometry[id] = shares(cur.rects[id]);
      else if (!cur.rects[id] && prev.rects[id]) geometry[id] = null;
    }

    const placed = Object.entries(geometry).filter((e): e is [string, ValueRect] => e[1] !== null);
    if (placed.length > 1) {
      // A tile, a gather: ONE request, one transaction, one frame.
      const ids = placed.map(([id]) => id);
      enqueue(ids, {}, () =>
        transport.arrange(
          Object.fromEntries(placed),
          Object.fromEntries(ids.map((id) => [id, rev(id) ?? 0])),
        ),
      );
    }
    for (const [id, rect] of Object.entries(geometry)) {
      if (rect && placed.length > 1) continue;
      enqueue([id], {}, () => transport.verb(id, "set_geometry", { rect, expected_revision: rev(id) }));
    }
    if (cur.shelf !== prev.shelf) {
      inflight += 1;
      queue = queue.then(async () => {
        try {
          const out = await transport.shelf(cur.shelf, shelfRevision);
          shelfRevision = out.revision;
        } catch {
          await reread(new Set(["desk"]));
        }
        inflight -= 1;
        if (inflight === 0) {
          const waiters = idleWaiters;
          idleWaiters = [];
          for (const w of waiters) w();
        }
      });
    }
  }

  function schedule(): void {
    if (scheduled || applying) return;
    scheduled = true;
    queueMicrotask(sync);
  }

  /** L5: a share is resolved by each view at draw. When this view's band
   * changes (the Dock publishes its height, the window resizes), the hub's
   * arranged rects are resolved again; nothing is sent (the shares did not
   * change). */
  let lastBand = "";
  function rebase(): void {
    if (!synced || applying || stopped) return;
    const band = view();
    const key = `${band.x},${band.y},${band.w},${band.h}`;
    if (key === lastBand) return;
    lastBand = key;
    const s = useDesk.getState();
    const rects = { ...s.panelRects };
    const zoom = { ...(s.panelZoom ?? {}) };
    let changed = false;
    for (const row of rows.values()) {
      if (presentations.pending(row.id) > 0) continue;
      const rect = row.arranged ? rectOf(row) : null;
      if (rect && !sameRect(rect, rects[row.id])) {
        rects[row.id] = rect;
        changed = true;
      }
      const zr = row.zoom ? rectOf(row.zoom) : null;
      if (zr && !sameRect(zr, zoom[row.id])) {
        zoom[row.id] = zr;
        changed = true;
      }
    }
    if (!changed) return;
    applying = true;
    try {
      useDesk.setState({ panelRects: rects, panelZoom: zoom });
    } finally {
      applying = false;
    }
    synced = { ...synced, rects: { ...synced.rects, ...pick(rects, Object.keys(synced.rects)) }, zoom: { ...synced.zoom, ...pick(zoom, Object.keys(synced.zoom)) } };
  }
  const pick = (from: Record<string, PanelRect>, keys: string[]) =>
    Object.fromEntries(keys.filter((k) => from[k]).map((k) => [k, from[k]]));
  let observer: MutationObserver | null = null;
  const onResize = () => rebase();
  if (typeof window !== "undefined" && typeof MutationObserver !== "undefined" && typeof document !== "undefined") {
    observer = new MutationObserver(() => rebase());
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["style"] });
    window.addEventListener("resize", onResize);
  }

  /** Resolves when no request is in flight and no re-read is running. */
  function idle(): Promise<void> {
    if (reading) return reading.then(idle);
    if (inflight === 0) return Promise.resolve();
    return new Promise<void>((resolve) => idleWaiters.push(resolve)).then(idle);
  }

  const unlisten = onWorkspaceSaved(schedule);

  return {
    presentations,
    rows,
    start() {
      if (started) return started;
      started = transport
        .list()
        .then((list) => {
          if (stopped) return;
          registry = list.registry ?? { static: {}, families: {} };
          const here = snapshot();
          if (list.adopted === false && list.windows.length === 0 && here.open.size > 0) {
            // The hub has never held this desk's windows (it records the
            // first write once, `adopted`): this view's cache seeds it. After
            // that, an empty list is an empty desk.
            synced = { open: new Set(), depth: {}, min: new Set(), max: new Set(), rects: {}, zoom: {}, shelf: list.stage_shelf };
            shelfRevision = list.shelf_revision;
            sync();
            return;
          }
          apply(list, "all");
        })
        .catch(() => undefined);
      return started;
    },
    onFrame(data) {
      if (!synced) return;
      const changes = frameChanges(data);
      if (!changes) return;
      const ids = changes.filter((c) => c.kind === "windows").map((c) => c.id);
      if (!ids.length) return;
      void reread(ids.some((id) => !id) ? "all" : new Set(ids));
    },
    sync,
    seeded: () => synced !== null,
    idle,
    stop() {
      stopped = true;
      unlisten();
      observer?.disconnect();
      if (typeof window !== "undefined") window.removeEventListener("resize", onResize);
    },
  };
}

// ---- the one instance the desk mounts ------------------------------------

let instance: HubWindows | null = null;

/** The desk's hub windows (created on first use). */
export function hubWindows(): HubWindows {
  if (!instance) instance = createHubWindows();
  return instance;
}

/** True once the hub seeded this desk: a local mount rule must not reorder
 * the hub's stacking (a reload keeps the hub's order, L3). */
export function hubSeeded(): boolean {
  return instance?.seeded() ?? false;
}

/** Test seam. */
export function __resetHubWindows(): void {
  instance?.stop();
  instance = null;
}
