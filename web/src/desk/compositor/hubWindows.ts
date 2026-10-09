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
  revision: number;
  registry?: HubRegistry;
}

type Verb = "open" | "close" | "set_geometry" | "raise" | "send_back" | "seat" | "zoom";

export interface HubTransport {
  list(): Promise<HubWindowList>;
  verb(id: string, verb: Verb, body: Record<string, unknown>): Promise<HubWindowRow | { id: string; closed: true }>;
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

  /** Apply the hub's rows for `scope` (every id when "all"); ids with a
   * request in flight are left as they show. */
  function apply(list: HubWindowList, scope: Set<string> | "all"): void {
    const byId = new Map(list.windows.map((r) => [r.id, r]));
    const inScope = (id: string) => (scope === "all" || scope.has(id)) && presentations.pending(id) === 0;
    applying = true;
    try {
      for (const id of [...rows.keys()]) if (inScope(id) && !byId.has(id)) rows.delete(id);
      for (const row of list.windows) if (inScope(row.id)) rows.set(row.id, row);

      // Close here what the hub closed; open here what the hub opened.
      const local = new Set([...Object.keys(useDesk.getState().panelDepth), ...adapterOpenIds()]);
      const closed: string[] = [];
      for (const id of local) {
        if (!inScope(id) || !known(id) || byId.has(id) || !isOpenHere(id)) continue;
        adapterFor(id)?.close();
        closed.push(id);
      }
      for (const row of list.windows) {
        if (!inScope(row.id) || isOpenHere(row.id)) continue;
        adapterFor(row.id)?.open();
      }

      // One write of the stacking, the seats, the zooms and the rects.
      const s = useDesk.getState();
      const depth = { ...s.panelDepth };
      const min = new Set(s.panelMin);
      const max = new Set(s.panelMax);
      const rects = { ...s.panelRects };
      const saved = new Set(s.panelSaved);
      const zoom = { ...(s.panelZoom ?? {}) };
      for (const id of closed) {
        delete depth[id];
        min.delete(id);
        max.delete(id);
      }
      for (const row of list.windows) {
        if (!inScope(row.id)) continue;
        depth[row.id] = row.depth;
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
      const shelf = scope === "all" || scope.has("desk") ? list.stage_shelf : s.stageShelf;
      if (scope === "all" || scope.has("desk")) shelfRevision = list.revision;
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
    synced = snapshot();
    // A window open here that the hub does not hold (one no other view can
    // open, e.g. the inspector): it goes to the hub on the next sync.
    const unsent = [...synced.open].filter((id) => !rows.has(id) && presentations.pending(id) === 0);
    if (unsent.length) {
      for (const id of unsent) synced.open.delete(id);
      schedule();
    }
  }

  /** Follow one settled row (its request answered). */
  function follow(row: HubWindowRow | null, id: string): void {
    if (presentations.pending(id) > 0) return;
    const others = [...rows.values()].filter((r) => r.id !== id);
    apply(
      { windows: row ? [...others, row] : others, stage_shelf: useDesk.getState().stageShelf, revision: shelfRevision ?? 0 },
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
        const list = (answer as { windows: HubWindowRow[] }).windows;
        for (const row of list) rows.set(row.id, row);
        for (const row of list) follow(row, row.id);
      } else if (answer && typeof answer === "object" && "closed" in answer) {
        rows.delete(ids[0]);
        follow(null, ids[0]);
      } else if (answer && typeof answer === "object" && "id" in answer) {
        const row = answer as HubWindowRow;
        rows.set(row.id, row);
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

  const rev = (id: string) => rows.get(id)?.revision;
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
    const ordered = (depth: Record<string, number>) =>
      [...both].sort((a, b) => (depth[a] ?? 0) - (depth[b] ?? 0) || (a < b ? -1 : 1));
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
          if (list.windows.length === 0 && here.open.size > 0) {
            // A hub that holds no window yet (the first run of 16b): this
            // browser's open windows become the desk's.
            synced = { open: new Set(), depth: {}, min: new Set(), max: new Set(), rects: {}, zoom: {}, shelf: list.stage_shelf };
            shelfRevision = list.revision;
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
    idle,
    stop() {
      stopped = true;
      unlisten();
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

/** Test seam. */
export function __resetHubWindows(): void {
  instance?.stop();
  instance = null;
}
