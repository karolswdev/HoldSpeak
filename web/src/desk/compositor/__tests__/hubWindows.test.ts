// PHILO-16 (16b): the hub owns the desk's windows; this browser is a view.
// Seed from the hub's rows; every persisted store write goes to the hub
// through anticipate (shown at once, followed when it settles); a 409
// re-reads and follows; another client's frame re-seeds the changed ids and
// never an id with a request in flight. Rects travel as share+px. A read
// older than what this view applied is dropped (Astra r1 M1); an adopted
// empty desk stays empty (M2); a Project drawer follows (M4).
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { useChairWindows } from "../../chair/chairWindows";
import { useDrawers } from "../../drawer/store";
import { useLane } from "../../lane/laneStore";
import { useDesk } from "../../store";
import { DESK_WORKSPACE_STORAGE_KEY } from "../../store/workspaceStorage";
import { record, type Rect } from "../geometry";
import { orderFromDepth } from "../planes";
import {
  createHubWindows,
  isWindowsOnlyFrame,
  type HubTransport,
  type HubWindowList,
  type HubWindowRow,
  type HubWindows,
} from "../hubWindows";

const VIEW: Rect = { x: 10, y: 38, w: 1420, h: 772 };
const REGISTRY = {
  static: { "chair:needs": "chair", "chair:brief": "chair", "chair:week": "chair", "chair:capture": "chair", lane: "lane",
    "surface-project-memory": "surface" },
  families: { "zone:": "zone", "drawer:project:": "drawer" },
  // (lane is static on the hub)
};

function row(id: string, over: Partial<HubWindowRow> = {}): HubWindowRow {
  return {
    id, app: "chair", object_ref: null, x: null, y: null, w: null, h: null,
    depth: 1, minimized: false, zoomed: false, zoom: null, arranged: false, room: null,
    front: false, revision: 1, ...over,
  };
}

function deferred<T>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

/** A fake hub with ONE revision counter for the desk (as the service): each
 * write takes the next revision; `list` answers the rows and that counter. */
function fakeHub(initial: HubWindowRow[], adopted = true) {
  const state = { windows: initial, desk: Math.max(0, ...initial.map((w) => w.revision)), adopted };
  const calls: { verb: string; id: string; body: Record<string, unknown> }[] = [];
  const answers: ((id: string, verb: string, body: Record<string, unknown>) => Promise<unknown>)[] = [];
  const list = (): HubWindowList => ({
    windows: state.windows, stage_shelf: "left", shelf_revision: 0,
    revision: Math.max(state.desk, ...state.windows.map((w) => w.revision)), adopted: state.adopted, registry: REGISTRY,
  });
  const transport: HubTransport = {
    list: vi.fn(async () => list()),
    verb: vi.fn(async (id, verb, body) => {
      calls.push({ verb, id, body });
      const next = answers.shift();
      if (next) return next(id, verb, body) as Promise<HubWindowRow>;
      state.desk += 1;
      state.adopted = true;
      if (verb === "close") {
        state.windows = state.windows.filter((w) => w.id !== id);
        return { id, closed: true as const, revision: state.desk };
      }
      const current = state.windows.find((w) => w.id === id) ?? row(id);
      const top = Math.max(0, ...state.windows.map((w) => w.depth));
      const updated = {
        ...current,
        revision: state.desk,
        ...(verb === "raise" || verb === "open" ? { depth: top + 1 } : {}),
        ...(verb === "seat" ? { minimized: Boolean(body.seated) } : {}),
        ...(verb === "set_geometry" && body.rect ? { ...(body.rect as object), arranged: true } : {}),
      };
      state.windows = [...state.windows.filter((w) => w.id !== id), updated];
      return updated;
    }),
    arrange: vi.fn(async (rects) => {
      calls.push({ verb: "arrange", id: Object.keys(rects).join(","), body: rects as Record<string, unknown> });
      state.desk += 1;
      const out = state.windows
        .filter((w) => w.id in rects)
        .map((w) => ({ ...w, ...rects[w.id], arranged: true, revision: state.desk }));
      state.windows = [...state.windows.filter((w) => !(w.id in rects)), ...out];
      return { windows: out };
    }),
    shelf: vi.fn(async (side) => ({ stage_shelf: side, revision: 1 })),
  };
  return { state, calls, answers, transport };
}

const flush = async (hub: HubWindows) => {
  for (let i = 0; i < 4; i += 1) {
    await Promise.resolve();
    await hub.idle();
  }
};

const order = (ids: string[]) => orderFromDepth(useDesk.getState().panelDepth).filter((id) => ids.includes(id));

let hub: HubWindows | null = null;

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelDepth: {}, panelOrder: [], panelMin: [], panelRects: {}, panelSaved: [], panelMax: [],
    panelZoom: {}, windowsById: {}, zoneWindows: [], pullouts: [],
  });
  useChairWindows.setState({
    closed: { "chair:needs": true, "chair:brief": true, "chair:week": true, "chair:capture": true },
    phone: "",
  });
  useDrawers.setState({ drawers: [], infos: [], parked: null });
  useLane.setState({ launchId: null });
});

afterEach(() => {
  hub?.stop();
  hub = null;
});

function start(rows: HubWindowRow[], adopted = true, cacheOpen: string[] = [], bootDepth: Record<string, number> | null = null) {
  const fake = fakeHub(rows, adopted);
  hub = createHubWindows({ transport: fake.transport, view: () => VIEW, compact: () => false, settleMs: 0, cacheOpen,
    bootDepth: bootDepth ?? { ...useDesk.getState().panelDepth } });
  const seeded = hub;
  const begin = seeded.start.bind(seeded);
  // The windows the seed opened are quiet until the owner's first gesture;
  // each test acts as the owner, so it starts with one.
  (seeded as { start: () => Promise<void> }).start = async () => {
    await begin();
    window.dispatchEvent(new Event("pointerdown"));
  };
  return { fake, hub: seeded };
}

const CHAIR = ["chair:brief", "chair:week", "chair:needs"];

describe("hubWindows", () => {
  it("seeds the desk from the hub's rows: open, order, seat, rect as share+px", async () => {
    const { hub } = start([
      row("chair:brief", { depth: 4, arranged: true, x: "-1/2", y: "-1/2", w: "1/2", h: "100%" }),
      row("chair:week", { depth: 7, minimized: true }),
      row("chair:needs", { depth: 9 }),
    ]);
    await hub.start();
    const s = useDesk.getState();
    expect(useChairWindows.getState().closed["chair:brief"]).toBe(false);
    expect(useChairWindows.getState().closed["chair:week"]).toBe(false);
    expect(order(CHAIR)).toEqual(["chair:brief", "chair:week", "chair:needs"]);
    expect(s.panelMin).toContain("chair:week");
    // "-1/2" of the band from its centre is its left edge; "1/2" is half its width.
    expect(s.panelRects["chair:brief"]).toEqual({ x: 10, y: 38, w: 710, h: 772 });
    expect(s.panelSaved).toContain("chair:brief");
    // The cache is overwritten by the hub's rows (the next first paint).
    const cached = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(orderFromDepth(cached.panel.depth)).toEqual(["chair:brief", "chair:week", "chair:needs"]);
    expect(cached.panel.min).toContain("chair:week");
  });

  it("a raise shows at once, holds while in flight, then follows the hub", async () => {
    const { fake, hub } = start([row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2 })]);
    await hub.start();
    const answer = deferred<HubWindowRow>();
    fake.answers.push(() => answer.promise);
    useDesk.getState().focusPanel("chair:brief");
    expect(useDesk.getState().panelOrder.at(-1)).toBe("chair:brief"); // at once
    await Promise.resolve();
    await Promise.resolve();
    expect(fake.calls).toEqual([{ verb: "raise", id: "chair:brief", body: { expected_revision: 1 } }]);
    expect(hub.presentations.pending("chair:brief")).toBe(1);
    answer.resolve(row("chair:brief", { depth: 40, revision: 2 }));
    await flush(hub);
    expect(hub.presentations.pending("chair:brief")).toBe(0);
    expect(order(["chair:brief", "chair:week"])).toEqual(["chair:week", "chair:brief"]);
    expect(hub.rows.get("chair:brief")?.revision).toBe(2);
  });

  it("sends rects as share+px against this view, never pixels", async () => {
    const { fake, hub } = start([row("chair:brief", { depth: 1 })]);
    await hub.start();
    const rect = { x: 300, y: 120, w: 640, h: 480 };
    useDesk.getState().setPanelRect("chair:brief", rect, true);
    await flush(hub);
    const sent = fake.calls.find((c) => c.verb === "set_geometry");
    expect(sent?.body.rect).toEqual(record(rect, VIEW));
    for (const value of Object.values(sent?.body.rect as Record<string, unknown>)) {
      expect(typeof value).toBe("string");
      expect(String(value)).toMatch(/%/);
    }
  });

  it("two rects in one change are ONE arrange request", async () => {
    const { fake, hub } = start([row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2 })]);
    await hub.start();
    useDesk.setState({
      panelRects: { "chair:brief": { x: 10, y: 38, w: 710, h: 772 }, "chair:week": { x: 720, y: 38, w: 710, h: 772 } },
      panelSaved: ["chair:brief", "chair:week"],
    });
    useDesk.getState().setPanelRect("chair:week", { x: 720, y: 38, w: 710, h: 772 }, true);
    await flush(hub);
    expect(fake.transport.arrange).toHaveBeenCalledTimes(1);
    expect(fake.calls.filter((c) => c.verb === "set_geometry")).toEqual([]);
  });

  it("a 409 re-reads and follows the hub's row", async () => {
    const { fake, hub } = start([row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2 })]);
    await hub.start();
    fake.answers.push(async () => {
      // Another client moved and raised the window first.
      fake.state.windows = [
        row("chair:week", { depth: 2 }),
        row("chair:brief", { depth: 5, revision: 3, arranged: true, x: "0%", y: "-1/2", w: "1/2", h: "100%" }),
      ];
      throw new ApiError(409, "window_stale", { error: "window_stale" });
    });
    useDesk.getState().setPanelRect("chair:brief", { x: 100, y: 100, w: 300, h: 300 }, true);
    await flush(hub);
    expect(fake.transport.list).toHaveBeenCalledTimes(2);
    expect(useDesk.getState().panelRects["chair:brief"]).toEqual({ x: 720, y: 38, w: 710, h: 772 });
    expect(order(["chair:brief", "chair:week"])).toEqual(["chair:week", "chair:brief"]);
    expect(hub.rows.get("chair:brief")?.revision).toBe(3);
  });

  it("another client's frame re-seeds the changed ids: a raise, a seat, a close", async () => {
    const { fake, hub } = start([
      row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2 }), row("chair:needs", { depth: 3 }),
    ]);
    await hub.start();
    fake.state.windows = [row("chair:week", { depth: 2, minimized: true, revision: 5 }), row("chair:brief", { depth: 4, revision: 6 })];
    hub.onFrame({
      kind: "windows", id: "chair:brief", op: "raise",
      changes: [{ kind: "windows", id: "chair:brief" }, { kind: "windows", id: "chair:week" }, { kind: "windows", id: "chair:needs" }],
    });
    await flush(hub);
    const s = useDesk.getState();
    expect(order(CHAIR)).toEqual(["chair:week", "chair:brief"]);
    expect(s.panelMin).toContain("chair:week");
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(true);
    expect(s.panelDepth).not.toHaveProperty("chair:needs");
    // Following another client sends nothing back.
    expect(fake.calls).toEqual([]);
  });

  it("an id with a request in flight is not clobbered by a frame", async () => {
    const { fake, hub } = start([row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2 })]);
    await hub.start();
    const answer = deferred<HubWindowRow>();
    fake.answers.push(() => answer.promise);
    useDesk.getState().focusPanel("chair:brief");
    await Promise.resolve();
    await Promise.resolve();
    // A frame arrives naming both, from before the raise landed.
    fake.state.windows = [row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2, minimized: true, revision: 2 })];
    hub.onFrame({ kind: "windows", id: "chair:week", changes: [{ kind: "windows", id: "chair:brief" }, { kind: "windows", id: "chair:week" }] });
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    expect(order(["chair:brief", "chair:week"])).toEqual(["chair:week", "chair:brief"]); // held on top
    expect(useDesk.getState().panelMin).toContain("chair:week"); // the other id follows
    answer.resolve(row("chair:brief", { depth: 9, revision: 3 }));
    await flush(hub);
    expect(order(["chair:brief", "chair:week"])).toEqual(["chair:week", "chair:brief"]);
    expect(hub.rows.get("chair:brief")?.revision).toBe(3);
  });

  it("M1: a delayed read older than a settled write is dropped", async () => {
    const { fake, hub } = start([row("chair:brief", { depth: 1, revision: 1 })]);
    await hub.start();
    // A read leaves while revision 2 is current, and answers late.
    const late = deferred<HubWindowList>();
    const rev2 = row("chair:brief", { depth: 1, revision: 2, arranged: true, x: "-1/2", y: "-1/2", w: "1/2", h: "100%" });
    (fake.transport.list as ReturnType<typeof vi.fn>).mockImplementationOnce(() => late.promise);
    hub.onFrame({ kind: "windows", id: "chair:brief", changes: [{ kind: "windows", id: "chair:brief" }] });
    // This view's own move settles at revision 3.
    fake.answers.push(async () => row("chair:brief", { depth: 1, revision: 3, arranged: true, x: "0%", y: "-1/2", w: "1/2", h: "100%" }));
    useDesk.getState().setPanelRect("chair:brief", { x: 720, y: 38, w: 710, h: 772 }, true);
    for (let i = 0; i < 30; i += 1) await Promise.resolve(); // the write settles; the read is still out
    expect(hub.rows.get("chair:brief")?.revision).toBe(3);
    late.resolve({ windows: [rev2], stage_shelf: "left", revision: 2, adopted: true, registry: REGISTRY });
    await flush(hub);
    expect(useDesk.getState().panelRects["chair:brief"]).toEqual({ x: 720, y: 38, w: 710, h: 772 });
    expect(hub.rows.get("chair:brief")?.revision).toBe(3);
    const cached = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(cached.panel.rects["chair:brief"]).toEqual({ x: 720, y: 38, w: 710, h: 772 });
  });

  it("M2: an adopted empty desk stays empty; a stale cache opens nothing", async () => {
    // This view's cache still has Brief open; on the hub it was closed.
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:brief": false } }));
    useDesk.setState({ panelDepth: { "chair:brief": 3 }, panelOrder: ["chair:brief"] });
    const { fake, hub } = start([], true, ["chair:brief"]);
    fake.state.desk = 7;
    await hub.start();
    await flush(hub);
    expect(fake.calls).toEqual([]);
    expect(useChairWindows.getState().closed["chair:brief"]).toBe(true);
    expect(useDesk.getState().panelDepth).not.toHaveProperty("chair:brief");
  });

  it("an open and a close here reach the hub; a hub never adopted takes this view's windows", async () => {
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:brief": false } }));
    useDesk.setState({ panelDepth: { "chair:brief": 3 }, panelOrder: ["chair:brief"] });
    const { fake, hub } = start([], false);
    await hub.start();
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["open", "chair:brief"]]);
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:week": false } }));
    useDesk.getState().focusPanel("chair:week");
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id]).slice(1)).toEqual([["open", "chair:week"]]);
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:week": true } }));
    useDesk.getState().retirePanel("chair:week");
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id]).at(-1)).toEqual(["close", "chair:week"]);
  });

  it("M4: a Project drawer on the hub opens here through the drawer's own path", async () => {
    const { fake, hub } = start([row("drawer:project:p-ledger", { app: "drawer", object_ref: "project:p-ledger", depth: 2 })]);
    await hub.start();
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toEqual(["p-ledger"]);
    // Another view closes it: it closes here too.
    fake.state.windows = [];
    fake.state.desk = 9;
    hub.onFrame({ kind: "windows", id: "drawer:project:p-ledger", changes: [{ kind: "windows", id: "drawer:project:p-ledger" }] });
    await flush(hub);
    expect(useDrawers.getState().drawers).toEqual([]);
  });

  it("a window this view stacks alone keeps its place above the hub window it sat on", async () => {
    // `inspector` is not on the hub (no row can open it); Brief was below it.
    useDesk.setState({ panelDepth: { "chair:brief": 1, inspector: 50, "chair:week": 60 }, panelOrder: [] });
    const { fake, hub } = start([row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2 })]);
    await hub.start();
    expect(order(["chair:brief", "inspector", "chair:week"])).toEqual(["chair:brief", "inspector", "chair:week"]);
    useDesk.getState().focusPanel("chair:brief");
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["raise", "chair:brief"]]);
    expect(order(["chair:brief", "inspector", "chair:week"]).at(-1)).toBe("chair:brief");
  });

  it("a window that leaves the stacking without closing is not sent back", async () => {
    const { fake, hub } = start([row("chair:week", { depth: 2 }), row("chair:needs", { depth: 3 }), row("chair:brief", { depth: 4 })]);
    await hub.start();
    useDesk.getState().minimizePanel("chair:week");
    useDesk.getState().retirePanel("chair:week"); // an iconified Chair window unmounts
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["seat", "chair:week"]]);
    expect(useChairWindows.getState().closed["chair:week"]).toBe(false);
  });

  it("two writes queued on one window carry the first answer's revision (no self-409)", async () => {
    const { fake, hub } = start([row("chair:brief", { depth: 1, revision: 2 })]);
    await hub.start();
    useDesk.getState().toggleMaximizePanel("chair:brief");
    useDesk.getState().setPanelRect("chair:brief", { x: 100, y: 100, w: 300, h: 300 }, true);
    await flush(hub);
    const sent = fake.calls.map((c) => [c.verb, c.body.expected_revision]);
    expect(sent).toEqual([["zoom", 2], ["set_geometry", 3]]);
    expect(fake.transport.list).toHaveBeenCalledTimes(1); // no 409 re-read
    expect(useDesk.getState().panelSaved).toContain("chair:brief");
  });

  it("Astra r2 M1: a raced list never hides a live window for good", async () => {
    // Her race: the first list was read at revision 1 without Brief (written
    // at revision 1). The service now lists one snapshot; this view still
    // takes the real row at that revision when it arrives.
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:brief": false } }));
    useDesk.setState({ panelDepth: { "chair:brief": 1 }, panelOrder: ["chair:brief"] });
    const { fake, hub } = start([]);
    (fake.transport.list as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ windows: [], stage_shelf: "left", revision: 1, adopted: true, registry: REGISTRY })
      .mockResolvedValue({ windows: [row("chair:brief", { depth: 1, revision: 1 })], stage_shelf: "left", revision: 1, adopted: true, registry: REGISTRY });
    await hub.start();
    hub.onFrame({ kind: "windows", id: "chair:brief" });
    await flush(hub);
    expect(useChairWindows.getState().closed["chair:brief"]).toBe(false);
    expect(hub.rows.get("chair:brief")?.revision).toBe(1);
  });

  it("Astra r2 M2: a failed write returns to the hub's row at the same revision", async () => {
    const { fake, hub } = start([row("chair:brief", { revision: 2, arranged: true, x: "-1/2", y: "-1/2", w: "1/2", h: "100%" })]);
    await hub.start();
    const before = useDesk.getState().panelRects["chair:brief"];
    fake.answers.push(async () => {
      throw new Error("write refused");
    });
    useDesk.getState().setPanelRect("chair:brief", { x: 100, y: 100, w: 300, h: 300 }, true);
    await flush(hub);
    expect(useDesk.getState().panelRects["chair:brief"]).toEqual(before);
    const cached = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(cached.panel.rects["chair:brief"]).toEqual(before);
  });

  it("Astra r2 M3: the agent lane follows on its launch, and re-targets", async () => {
    const { fake, hub } = start([row("lane", { app: "lane", object_ref: "launch:L-1", depth: 1 })]);
    await hub.start();
    expect(useLane.getState().launchId).toBe("L-1");
    fake.state.windows = [row("lane", { app: "lane", object_ref: "launch:L-2", depth: 1, revision: 5 })];
    hub.onFrame({ kind: "windows", id: "lane" });
    await flush(hub);
    expect(useLane.getState().launchId).toBe("L-2");
    // This view opens the lane on another launch: the hub hears the launch.
    useLane.getState().open("L-3");
    useDesk.getState().focusPanel("lane");
    await flush(hub);
    expect(fake.calls.find((c) => c.verb === "open")?.body.object_ref).toBe("launch:L-3");
  });

  it("PHILO-17 U28c: a Room comes back as its Room, not as Desk memory", async () => {
    // Another view (no cache) opens the hub's row: the row's object is the scope.
    const { fake, hub } = start([row("surface-project-memory", { app: "surface", object_ref: "project:p-1", depth: 1 })]);
    await hub.start();
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope).toBe("project:p-1");
    // The Room goes to another project here: the hub hears the new object.
    useDesk.getState().openSurfaceWindow("open-project-memory", "project:p-2");
    await flush(hub);
    expect(fake.calls.filter((c) => c.verb === "open").map((c) => c.body.object_ref)).toEqual(["project:p-2"]);
    // Back to Desk memory with no project: "" says "no scope" to the hub.
    useDesk.getState().openSurfaceWindow("open-project-memory");
    await flush(hub);
    expect(fake.calls.filter((c) => c.verb === "open").map((c) => c.body.object_ref)).toEqual(["project:p-2", ""]);
    // A row with no object (never sent) leaves this view's scope as is.
    useDesk.getState().openSurfaceWindow("open-project-memory", "project:p-3");
    fake.state.windows = [row("surface-project-memory", { app: "surface", object_ref: null, depth: 9, revision: 99 })];
    hub.onFrame({ kind: "windows", id: "surface-project-memory" });
    await flush(hub);
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope).toBe("project:p-3");
  });

  it("PHILO-17 U28: a row the hub holds unarranged keeps this view's seat on the glass", async () => {
    useChairWindows.setState((st) => ({ closed: { ...st.closed, "chair:brief": false } }));
    useDesk.setState({ panelDepth: { "chair:brief": 1 }, panelRects: { "chair:brief": { x: 150, y: 80, w: 500, h: 400 } },
      panelSaved: ["chair:brief"] });
    const { hub } = start([row("chair:brief", { depth: 1 })], true, ["chair:brief"]);
    await hub.start();
    const s = useDesk.getState();
    expect(s.panelSaved).not.toContain("chair:brief");
    expect(s.panelRects["chair:brief"]).toEqual({ x: 150, y: 80, w: 500, h: 400 });
  });

  it("Astra r2 (glass B7): a window the hub opened here does not write its mount back", async () => {
    const fake = fakeHub([row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2 })]);
    hub = createHubWindows({ transport: fake.transport, view: () => VIEW, compact: () => false, settleMs: 40 });
    await hub.start();
    await new Promise((r) => setTimeout(r, 60));
    // Another view opens Needs; this view follows, and the window's mount
    // raises it and places it: none of that is sent.
    fake.state.windows = [...fake.state.windows, row("chair:needs", { depth: 0, revision: 4 })];
    hub.onFrame({ kind: "windows", id: "chair:needs" });
    await hub.idle();
    useDesk.getState().focusPanel("chair:needs"); // the mount's own raise
    await new Promise((r) => setTimeout(r, 60));
    await hub.idle();
    expect(fake.calls).toEqual([]);
    expect(order(CHAIR)[0]).toBe("chair:needs"); // the hub's order is back
  });

  it("the first seed keeps a window this load opened itself before the hub answered", async () => {
    // The arrival opened Needs you; the cache had Brief open (stale). The
    // hub holds neither: Brief closes, Needs you stays and goes to the hub.
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:brief": false, "chair:needs": false } }));
    useDesk.setState({ panelDepth: { "chair:brief": 1, "chair:needs": 2 }, panelOrder: ["chair:brief", "chair:needs"] });
    const { fake, hub } = start([], true, ["chair:brief"]);
    fake.state.desk = 3;
    await hub.start();
    await flush(hub);
    expect(useChairWindows.getState().closed["chair:brief"]).toBe(true);
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["open", "chair:needs"]]);
  });

  it("a window this load raised before the hub answered stays in front", async () => {
    // The cache had Brief over Week; a route raised Week before the seed.
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:brief": false, "chair:week": false } }));
    useDesk.setState({ panelDepth: { "chair:week": 1, "chair:brief": 2 }, panelOrder: ["chair:week", "chair:brief"] });
    const boot = { "chair:week": 1, "chair:brief": 2 };
    useDesk.getState().focusPanel("chair:week"); // the route's raise (before the hub answered)
    const { fake, hub } = start(
      [row("chair:week", { depth: 1 }), row("chair:brief", { depth: 2 })], true, ["chair:brief", "chair:week"], boot);
    await hub.start();
    await flush(hub);
    expect(order(["chair:brief", "chair:week"])).toEqual(["chair:brief", "chair:week"]);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["raise", "chair:week"]]);
  });

  it("a window frame is not a desk data change", () => {
    expect(isWindowsOnlyFrame({ kind: "windows", id: "chair:brief", changes: [{ kind: "windows", id: "chair:brief" }] })).toBe(true);
    expect(isWindowsOnlyFrame({ kind: "note", id: "n1", changes: [{ kind: "note", id: "n1" }] })).toBe(false);
    expect(isWindowsOnlyFrame({ kind: "windows", id: "a", changes: [{ kind: "windows", id: "a" }, { kind: "note", id: "n" }] })).toBe(false);
    expect(isWindowsOnlyFrame({})).toBe(false);
  });
});
