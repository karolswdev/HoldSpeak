// PHILO-16 (16b): the hub owns the desk's windows; this browser is a view.
// Seed from the hub's rows; every persisted store write goes to the hub
// through anticipate (shown at once, followed when it settles); a 409
// re-reads and follows; another client's frame re-seeds the changed ids and
// never an id with a request in flight. Rects travel as share+px. A read
// older than what this view applied is dropped (Astra r1 M1); an adopted
// empty desk stays empty (M2); a Project drawer follows (M4).
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { useChairWindows } from "../../chair/chairWindows";
import { useDrawers } from "../../drawer/store";
import { useLane } from "../../lane/laneStore";
import { __resetConductor, useConductor } from "../../conductor/store";
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
beforeAll(() => {
  if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: vi.fn((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      })),
    });
  }
});
const REGISTRY = {
  static: { "chair:needs": "chair", "chair:brief": "chair", "chair:week": "chair", "chair:capture": "chair", "drawer:parked": "drawer", lane: "lane", conductor: "conductor",
    "surface-project-memory": "surface", "surface-calendar-snapshot": "surface", "surface-concierge": "open-concierge" },
  families: { "zone:": "zone", "drawer:project:": "drawer", "pullout:": "pullout" },
  retired: { zone: "no face", "surface-concierge": "Settings owns Engines", "open-concierge": "Settings owns Engines" },
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
      // As the service: an object_ref over 400 chars is refused.
      if (typeof body.object_ref === "string" && body.object_ref.length > 400)
        throw new ApiError(400, "object_ref is too long", { error: "window_ref_invalid" });
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
        // As the service: an open with an object puts it on the row.
        ...(verb === "open" && typeof body.object_ref === "string" ? { object_ref: body.object_ref } : {}),
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
    closed: { "chair:needs": true, "chair:capture": true },
    phone: "",
  });
  useDrawers.setState({ drawers: [], infos: [], parked: null });
  useLane.setState({ launchId: null });
  __resetConductor();
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

const CHAIR = ["chair:capture", "drawer:parked", "chair:needs"];

describe("hubWindows", () => {
  // PHILO-17 (mainreds3, Astra r1): a hub open is passive. The real Conductor
  // adapter mounts the window and keeps the hub's seat and depth; only a
  // gesture (Go, the drawer, /conductor) fronts it.
  it("a Conductor seated on the hub stays seated after boot, below what the hub put over it", async () => {
    __resetConductor();
    const { hub } = start([
      row("conductor", { app: "conductor", depth: 3, minimized: true }),
      row("chair:capture", { depth: 5 }),
    ]);
    await hub.start();
    await flush(hub);
    await new Promise((r) => setTimeout(r, 0));
    expect(useConductor.getState().open).toBe(true);
    expect(useDesk.getState().panelMin).toContain("conductor");
    expect(order(["conductor", "chair:capture"])).toEqual(["conductor", "chair:capture"]);
  });

  // PHILO-17 (the desk sweep, needs-393; Astra r1 on #1108): the phone draws
  // only the Chair window `phone` names. A hub-opened Chair window takes the
  // work area only when NO window of any family is active there; else it
  // waits behind the active window (its plane below), and is not drawn over
  // the owner's work.
  describe("a hub-opened Chair window at 393", () => {
    const phoneWidth = (narrow: boolean) =>
      vi.spyOn(window, "matchMedia").mockImplementation((query: string) => ({
        matches: narrow && query.includes("max-width: 720px"),
        media: query, onchange: null,
        addListener: () => {}, removeListener: () => {},
        addEventListener: () => {}, removeEventListener: () => {}, dispatchEvent: () => false,
      }) as MediaQueryList);
    afterEach(() => vi.restoreAllMocks());
    /** The hub opens chair:needs over what this view shows (another client). */
    const hubOpensNeeds = async (fake: ReturnType<typeof fakeHub>, seeded: HubWindows) => {
      fake.state.windows = [...fake.state.windows, row("chair:needs", { depth: 50, revision: 40 })];
      seeded.onFrame({ kind: "windows", id: "chair:needs" });
      await flush(seeded);
    };
    const front = () => useDesk.getState().panelOrder.at(-1);

    it("takes the phone's work area when no window is active there", async () => {
      phoneWidth(true);
      const { fake, hub } = start([]);
      await hub.start();
      await hubOpensNeeds(fake, hub);
      expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
      expect(useChairWindows.getState().phone).toBe("chair:needs");
      expect(front()).toBe("chair:needs");
    });

    it("takes it from a phone window that is closed", async () => {
      phoneWidth(true);
      useChairWindows.setState({ phone: "chair:capture" }); // closed in beforeEach
      const { fake, hub } = start([]);
      await hub.start();
      await hubOpensNeeds(fake, hub);
      expect(useChairWindows.getState().phone).toBe("chair:needs");
    });

    it("waits behind an active Meetings detail window: its plane stays below", async () => {
      phoneWidth(true);
      const { fake, hub } = start([row("pullout:meeting:m-1", { app: "pullout", depth: 2, revision: 2 })]);
      await hub.start();
      expect(front()).toBe("surface-meetings");
      await hubOpensNeeds(fake, hub);
      expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
      expect(front()).toBe("surface-meetings");
      expect(order(["surface-meetings", "chair:needs"])).toEqual(["chair:needs", "surface-meetings"]);
    });

    it("keeps generic pullouts out of the Meetings migration", async () => {
      const { fake, hub } = start([
        row("pullout:intelligence:desk", { app: "pullout", depth: 1, revision: 2 }),
        row("pullout:people:rel-1", { app: "pullout", depth: 2, revision: 3 }),
      ]);
      await hub.start();
      expect(useDesk.getState().windowsById["surface-meetings"]).toBeUndefined();
      expect(useDesk.getState().pullouts.map((pullout) => pullout.id)).toEqual([
        "intelligence:desk",
        "people:rel-1",
      ]);
      expect(fake.calls.some((call) => call.verb === "close")).toBe(false);
    });

    it("waits behind an active application window", async () => {
      phoneWidth(true);
      const { fake, hub } = start([row("surface-project-memory", { app: "surface", depth: 2, revision: 2 })]);
      await hub.start();
      await hubOpensNeeds(fake, hub);
      expect(front()).toBe("surface-project-memory");
      expect(order(["surface-project-memory", "chair:needs"])).toEqual(["chair:needs", "surface-project-memory"]);
    });

    it("waits behind the Chair window the phone shows: the ring keeps it", async () => {
      phoneWidth(true);
      useChairWindows.setState((s) => ({ phone: "chair:capture", closed: { ...s.closed, "chair:capture": false } }));
      const { fake, hub } = start([row("chair:capture", { depth: 2, revision: 2 })]);
      await hub.start();
      await hubOpensNeeds(fake, hub);
      expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
      expect(useChairWindows.getState().phone).toBe("chair:capture");
      expect(front()).toBe("chair:capture");
    });

    it("comes to the front when the window it waited behind closes", async () => {
      phoneWidth(true);
      const { fake, hub } = start([row("surface-project-memory", { app: "surface", depth: 2, revision: 2 })]);
      await hub.start();
      await hubOpensNeeds(fake, hub);
      fake.state.windows = fake.state.windows.filter((w) => w.id !== "surface-project-memory");
      fake.state.desk = 60;
      hub.onFrame({ kind: "windows", id: "surface-project-memory" });
      await flush(hub);
      expect(front()).toBe("chair:needs");
      expect(useChairWindows.getState().phone).toBe("chair:needs");
    });

    it("leaves the phone's window alone at 1440", async () => {
      phoneWidth(false);
      const { fake, hub } = start([]);
      await hub.start();
      await hubOpensNeeds(fake, hub);
      expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
      expect(useChairWindows.getState().phone).toBe("");
    });
  });

  it("seeds the desk from the hub's rows: open, order, seat, rect as share+px", async () => {
    const { hub } = start([
      row("chair:capture", { depth: 4, arranged: true, x: "-1/2", y: "-1/2", w: "1/2", h: "100%" }),
      row("drawer:parked", { depth: 7, minimized: true }),
      row("chair:needs", { depth: 9 }),
    ]);
    await hub.start();
    const s = useDesk.getState();
    expect(useChairWindows.getState().closed["chair:capture"]).toBe(false);
    expect(useDrawers.getState().parked).not.toBeNull();
    expect(order(CHAIR)).toEqual(["chair:capture", "drawer:parked", "chair:needs"]);
    expect(s.panelMin).toContain("drawer:parked");
    // "-1/2" of the band from its centre is its left edge; "1/2" is half its width.
    expect(s.panelRects["chair:capture"]).toEqual({ x: 10, y: 38, w: 710, h: 772 });
    expect(s.panelSaved).toContain("chair:capture");
    // The cache is overwritten by the hub's rows (the next first paint).
    const cached = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(orderFromDepth(cached.panel.depth)).toEqual(["chair:capture", "drawer:parked", "chair:needs"]);
    expect(cached.panel.min).toContain("drawer:parked");
  });

  it("a raise shows at once, holds while in flight, then follows the hub", async () => {
    const { fake, hub } = start([row("chair:capture", { depth: 1 }), row("drawer:parked", { depth: 2 })]);
    await hub.start();
    const answer = deferred<HubWindowRow>();
    fake.answers.push(() => answer.promise);
    useDesk.getState().focusPanel("chair:capture");
    expect(useDesk.getState().panelOrder.at(-1)).toBe("chair:capture"); // at once
    await Promise.resolve();
    await Promise.resolve();
    expect(fake.calls).toEqual([{ verb: "raise", id: "chair:capture", body: { expected_revision: 1 } }]);
    expect(hub.presentations.pending("chair:capture")).toBe(1);
    answer.resolve(row("chair:capture", { depth: 40, revision: 2 }));
    await flush(hub);
    expect(hub.presentations.pending("chair:capture")).toBe(0);
    expect(order(["chair:capture", "drawer:parked"])).toEqual(["drawer:parked", "chair:capture"]);
    expect(hub.rows.get("chair:capture")?.revision).toBe(2);
  });

  it("sends rects as share+px against this view, never pixels", async () => {
    const { fake, hub } = start([row("chair:capture", { depth: 1 })]);
    await hub.start();
    const rect = { x: 300, y: 120, w: 640, h: 480 };
    useDesk.getState().setPanelRect("chair:capture", rect, true);
    await flush(hub);
    const sent = fake.calls.find((c) => c.verb === "set_geometry");
    expect(sent?.body.rect).toEqual(record(rect, VIEW));
    for (const value of Object.values(sent?.body.rect as Record<string, unknown>)) {
      expect(typeof value).toBe("string");
      expect(String(value)).toMatch(/%/);
    }
  });

  it("two rects in one change are ONE arrange request", async () => {
    const { fake, hub } = start([row("chair:capture", { depth: 1 }), row("drawer:parked", { depth: 2 })]);
    await hub.start();
    useDesk.setState({
      panelRects: { "chair:capture": { x: 10, y: 38, w: 710, h: 772 }, "drawer:parked": { x: 720, y: 38, w: 710, h: 772 } },
      panelSaved: ["chair:capture", "drawer:parked"],
    });
    useDesk.getState().setPanelRect("drawer:parked", { x: 720, y: 38, w: 710, h: 772 }, true);
    await flush(hub);
    expect(fake.transport.arrange).toHaveBeenCalledTimes(1);
    expect(fake.calls.filter((c) => c.verb === "set_geometry")).toEqual([]);
  });

  it("a 409 re-reads and follows the hub's row", async () => {
    const { fake, hub } = start([row("chair:capture", { depth: 1 }), row("drawer:parked", { depth: 2 })]);
    await hub.start();
    fake.answers.push(async () => {
      // Another client moved and raised the window first.
      fake.state.windows = [
        row("drawer:parked", { depth: 2 }),
        row("chair:capture", { depth: 5, revision: 3, arranged: true, x: "0%", y: "-1/2", w: "1/2", h: "100%" }),
      ];
      throw new ApiError(409, "window_stale", { error: "window_stale" });
    });
    useDesk.getState().setPanelRect("chair:capture", { x: 100, y: 100, w: 300, h: 300 }, true);
    await flush(hub);
    expect(fake.transport.list).toHaveBeenCalledTimes(2);
    expect(useDesk.getState().panelRects["chair:capture"]).toEqual({ x: 720, y: 38, w: 710, h: 772 });
    expect(order(["chair:capture", "drawer:parked"])).toEqual(["drawer:parked", "chair:capture"]);
    expect(hub.rows.get("chair:capture")?.revision).toBe(3);
  });

  it("another client's frame re-seeds the changed ids: a raise, a seat, a close", async () => {
    const { fake, hub } = start([
      row("chair:capture", { depth: 1 }), row("drawer:parked", { depth: 2 }), row("chair:needs", { depth: 3 }),
    ]);
    await hub.start();
    fake.state.windows = [row("drawer:parked", { depth: 2, minimized: true, revision: 5 }), row("chair:capture", { depth: 4, revision: 6 })];
    hub.onFrame({
      kind: "windows", id: "chair:capture", op: "raise",
      changes: [{ kind: "windows", id: "chair:capture" }, { kind: "windows", id: "drawer:parked" }, { kind: "windows", id: "chair:needs" }],
    });
    await flush(hub);
    const s = useDesk.getState();
    expect(order(CHAIR)).toEqual(["drawer:parked", "chair:capture"]);
    expect(s.panelMin).toContain("drawer:parked");
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(true);
    expect(s.panelDepth).not.toHaveProperty("chair:needs");
    // Following another client sends nothing back.
    expect(fake.calls).toEqual([]);
  });

  it("an id with a request in flight is not clobbered by a frame", async () => {
    const { fake, hub } = start([row("chair:capture", { depth: 1 }), row("drawer:parked", { depth: 2 })]);
    await hub.start();
    const answer = deferred<HubWindowRow>();
    fake.answers.push(() => answer.promise);
    useDesk.getState().focusPanel("chair:capture");
    await Promise.resolve();
    await Promise.resolve();
    // A frame arrives naming both, from before the raise landed.
    fake.state.windows = [row("chair:capture", { depth: 1 }), row("drawer:parked", { depth: 2, minimized: true, revision: 2 })];
    hub.onFrame({ kind: "windows", id: "drawer:parked", changes: [{ kind: "windows", id: "chair:capture" }, { kind: "windows", id: "drawer:parked" }] });
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    expect(order(["chair:capture", "drawer:parked"])).toEqual(["drawer:parked", "chair:capture"]); // held on top
    expect(useDesk.getState().panelMin).toContain("drawer:parked"); // the other id follows
    answer.resolve(row("chair:capture", { depth: 9, revision: 3 }));
    await flush(hub);
    expect(order(["chair:capture", "drawer:parked"])).toEqual(["drawer:parked", "chair:capture"]);
    expect(hub.rows.get("chair:capture")?.revision).toBe(3);
  });

  it("M1: a delayed read older than a settled write is dropped", async () => {
    const { fake, hub } = start([row("chair:capture", { depth: 1, revision: 1 })]);
    await hub.start();
    // A read leaves while revision 2 is current, and answers late.
    const late = deferred<HubWindowList>();
    const rev2 = row("chair:capture", { depth: 1, revision: 2, arranged: true, x: "-1/2", y: "-1/2", w: "1/2", h: "100%" });
    (fake.transport.list as ReturnType<typeof vi.fn>).mockImplementationOnce(() => late.promise);
    hub.onFrame({ kind: "windows", id: "chair:capture", changes: [{ kind: "windows", id: "chair:capture" }] });
    // This view's own move settles at revision 3.
    fake.answers.push(async () => row("chair:capture", { depth: 1, revision: 3, arranged: true, x: "0%", y: "-1/2", w: "1/2", h: "100%" }));
    useDesk.getState().setPanelRect("chair:capture", { x: 720, y: 38, w: 710, h: 772 }, true);
    for (let i = 0; i < 30; i += 1) await Promise.resolve(); // the write settles; the read is still out
    expect(hub.rows.get("chair:capture")?.revision).toBe(3);
    late.resolve({ windows: [rev2], stage_shelf: "left", revision: 2, adopted: true, registry: REGISTRY });
    await flush(hub);
    expect(useDesk.getState().panelRects["chair:capture"]).toEqual({ x: 720, y: 38, w: 710, h: 772 });
    expect(hub.rows.get("chair:capture")?.revision).toBe(3);
    const cached = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(cached.panel.rects["chair:capture"]).toEqual({ x: 720, y: 38, w: 710, h: 772 });
  });

  it("M2: an adopted empty desk stays empty; a stale cache opens nothing", async () => {
    // This view's cache still has Capture open; on the hub it was closed.
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:capture": false } }));
    useDesk.setState({ panelDepth: { "chair:capture": 3 }, panelOrder: ["chair:capture"] });
    const { fake, hub } = start([], true, ["chair:capture"]);
    fake.state.desk = 7;
    await hub.start();
    await flush(hub);
    expect(fake.calls).toEqual([]);
    expect(useChairWindows.getState().closed["chair:capture"]).toBe(true);
    expect(useDesk.getState().panelDepth).not.toHaveProperty("chair:capture");
  });

  it("an open and a close here reach the hub; a hub never adopted takes this view's windows", async () => {
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:capture": false } }));
    useDesk.setState({ panelDepth: { "chair:capture": 3 }, panelOrder: ["chair:capture"] });
    const { fake, hub } = start([], false);
    await hub.start();
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["open", "chair:capture"]]);
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:needs": false } }));
    useDesk.getState().focusPanel("chair:needs");
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id]).slice(1)).toEqual([["open", "chair:needs"]]);
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:needs": true } }));
    useDesk.getState().retirePanel("chair:needs");
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id]).at(-1)).toEqual(["close", "chair:needs"]);
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
    // `inspector` is not on the hub (no row can open it); Capture was below it.
    useDesk.setState({ panelDepth: { "chair:capture": 1, inspector: 50, "drawer:parked": 60 }, panelOrder: [] });
    const { fake, hub } = start([row("chair:capture", { depth: 1 }), row("drawer:parked", { depth: 2 })]);
    await hub.start();
    expect(order(["chair:capture", "inspector", "drawer:parked"])).toEqual(["chair:capture", "inspector", "drawer:parked"]);
    useDesk.getState().focusPanel("chair:capture");
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["raise", "chair:capture"]]);
    expect(order(["chair:capture", "inspector", "drawer:parked"]).at(-1)).toBe("chair:capture");
  });

  it("a window that leaves the stacking without closing is not sent back", async () => {
    const { fake, hub } = start([row("chair:needs", { depth: 2 }), row("chair:capture", { depth: 4 })]);
    await hub.start();
    useDesk.getState().minimizePanel("chair:needs");
    useDesk.getState().retirePanel("chair:needs"); // an iconified Chair window unmounts
    await flush(hub);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["seat", "chair:needs"]]);
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
  });

  it("two writes queued on one window carry the first answer's revision (no self-409)", async () => {
    const { fake, hub } = start([row("chair:capture", { depth: 1, revision: 2 })]);
    await hub.start();
    useDesk.getState().toggleMaximizePanel("chair:capture");
    useDesk.getState().setPanelRect("chair:capture", { x: 100, y: 100, w: 300, h: 300 }, true);
    await flush(hub);
    const sent = fake.calls.map((c) => [c.verb, c.body.expected_revision]);
    expect(sent).toEqual([["zoom", 2], ["set_geometry", 3]]);
    expect(fake.transport.list).toHaveBeenCalledTimes(1); // no 409 re-read
    expect(useDesk.getState().panelSaved).toContain("chair:capture");
  });

  it("Astra r2 M1: a raced list never hides a live window for good", async () => {
    // Her race: the first list was read at revision 1 without Capture (written
    // at revision 1). The service now lists one snapshot; this view still
    // takes the real row at that revision when it arrives.
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:capture": false } }));
    useDesk.setState({ panelDepth: { "chair:capture": 1 }, panelOrder: ["chair:capture"] });
    const { fake, hub } = start([]);
    (fake.transport.list as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ windows: [], stage_shelf: "left", revision: 1, adopted: true, registry: REGISTRY })
      .mockResolvedValue({ windows: [row("chair:capture", { depth: 1, revision: 1 })], stage_shelf: "left", revision: 1, adopted: true, registry: REGISTRY });
    await hub.start();
    hub.onFrame({ kind: "windows", id: "chair:capture" });
    await flush(hub);
    expect(useChairWindows.getState().closed["chair:capture"]).toBe(false);
    expect(hub.rows.get("chair:capture")?.revision).toBe(1);
  });

  it("Astra r2 M2: a failed write returns to the hub's row at the same revision", async () => {
    const { fake, hub } = start([row("chair:capture", { revision: 2, arranged: true, x: "-1/2", y: "-1/2", w: "1/2", h: "100%" })]);
    await hub.start();
    const before = useDesk.getState().panelRects["chair:capture"];
    fake.answers.push(async () => {
      throw new Error("write refused");
    });
    useDesk.getState().setPanelRect("chair:capture", { x: 100, y: 100, w: 300, h: 300 }, true);
    await flush(hub);
    expect(useDesk.getState().panelRects["chair:capture"]).toEqual(before);
    const cached = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(cached.panel.rects["chair:capture"]).toEqual(before);
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
    // Settled: the hub's answer is applied, and the window shows p-2.
    const hubRef = () => fake.state.windows.find((w) => w.id === "surface-project-memory")?.object_ref;
    expect(hubRef()).toBe("project:p-2");
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope).toBe("project:p-2");
    // Back to Desk memory with no project: "" says "no scope" to the hub.
    useDesk.getState().openSurfaceWindow("open-project-memory");
    await flush(hub);
    expect(fake.calls.filter((c) => c.verb === "open").map((c) => c.body.object_ref)).toEqual(["project:p-2", ""]);
    expect(hubRef()).toBe("");
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope ?? null).toBeNull();
    // A row with no object (never sent) leaves this view's scope as is.
    useDesk.getState().openSurfaceWindow("open-project-memory", "project:p-3");
    fake.state.windows = [row("surface-project-memory", { app: "surface", object_ref: null, depth: 9, revision: 99 })];
    hub.onFrame({ kind: "windows", id: "surface-project-memory" });
    await flush(hub);
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope).toBe("project:p-3");
  });

  it("PHILO-17 U28c (Astra r1 M1): a payload scope stays in this view; the window stays open", async () => {
    const { fake, hub } = start([]);
    await hub.start();
    const payload = JSON.stringify({ events: Array.from({ length: 40 }, (_, i) => ({ title: `Event ${i}`, at: "09:00" })) });
    expect(payload.length).toBeGreaterThan(400);
    useDesk.getState().openSurfaceWindow("review-calendar-snapshot", payload);
    await flush(hub);
    const opens = fake.calls.filter((c) => c.id === "surface-calendar-snapshot" && c.verb === "open");
    expect(opens.length).toBe(1);
    expect(opens[0].body.object_ref).toBeUndefined();
    expect(fake.calls.some((c) => c.verb === "close")).toBe(false);
    expect(useDesk.getState().windowsById["surface-calendar-snapshot"]?.scope).toBe(payload);
  });

  it("PHILO-17 U28: a row the hub holds unarranged keeps this view's seat on the glass", async () => {
    useChairWindows.setState((st) => ({ closed: { ...st.closed, "chair:capture": false } }));
    useDesk.setState({ panelDepth: { "chair:capture": 1 }, panelRects: { "chair:capture": { x: 150, y: 80, w: 500, h: 400 } },
      panelSaved: ["chair:capture"] });
    const { hub } = start([row("chair:capture", { depth: 1 })], true, ["chair:capture"]);
    await hub.start();
    const s = useDesk.getState();
    expect(s.panelSaved).not.toContain("chair:capture");
    expect(s.panelRects["chair:capture"]).toEqual({ x: 150, y: 80, w: 500, h: 400 });
  });

  it("Astra r2 (glass B7): a window the hub opened here does not write its mount back", async () => {
    const fake = fakeHub([row("chair:capture", { depth: 1 }), row("drawer:parked", { depth: 2 })]);
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
    // The arrival opened Needs you; the cache had Capture open (stale). The
    // hub holds neither: Capture closes, Needs you stays and goes to the hub.
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:capture": false, "chair:needs": false } }));
    useDesk.setState({ panelDepth: { "chair:capture": 1, "chair:needs": 2 }, panelOrder: ["chair:capture", "chair:needs"] });
    const { fake, hub } = start([], true, ["chair:capture"]);
    fake.state.desk = 3;
    await hub.start();
    await flush(hub);
    expect(useChairWindows.getState().closed["chair:capture"]).toBe(true);
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["open", "chair:needs"]]);
  });

  it("a window this load raised before the hub answered stays in front", async () => {
    // The cache had Capture over Needs you; a route raised Needs you before the seed.
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:capture": false, "chair:needs": false } }));
    useDesk.setState({ panelDepth: { "chair:needs": 1, "chair:capture": 2 }, panelOrder: ["chair:needs", "chair:capture"] });
    const boot = { "chair:needs": 1, "chair:capture": 2 };
    useDesk.getState().focusPanel("chair:needs"); // the route's raise (before the hub answered)
    const { fake, hub } = start(
      [row("chair:needs", { depth: 1 }), row("chair:capture", { depth: 2 })], true, ["chair:capture", "chair:needs"], boot);
    await hub.start();
    await flush(hub);
    expect(order(["chair:capture", "chair:needs"])).toEqual(["chair:capture", "chair:needs"]);
    expect(fake.calls.map((c) => [c.verb, c.id])).toEqual([["raise", "chair:needs"]]);
  });

  it("a window frame is not a desk data change", () => {
    expect(isWindowsOnlyFrame({ kind: "windows", id: "chair:capture", changes: [{ kind: "windows", id: "chair:capture" }] })).toBe(true);
    expect(isWindowsOnlyFrame({ kind: "note", id: "n1", changes: [{ kind: "note", id: "n1" }] })).toBe(false);
    expect(isWindowsOnlyFrame({ kind: "windows", id: "a", changes: [{ kind: "windows", id: "a" }, { kind: "note", id: "n" }] })).toBe(false);
    expect(isWindowsOnlyFrame({})).toBe(false);
  });
});

// PHILO-17 (owner 2026-10-10, "Yes, everything must become one desk"):
// zone windows are retired (no face draws a zone). Astra r2: retirement is
// a close the hub took, a refused close is tried again (bounded), and the
// row never opens or counts here.
describe("PHILO-17: retired zone windows", () => {
  const zoneRows = () => [row("zone:z1", { app: "zone", object_ref: "z1", depth: 1, revision: 2 })];
  const closes = (fake: ReturnType<typeof fakeHub>) => fake.calls.filter((c) => c.verb === "close" && c.id === "zone:z1");

  it("a saved zone row is closed on the hub and never opens here", async () => {
    const { fake, hub } = start(zoneRows());
    await hub.start();
    await flush(hub);
    expect(closes(fake)).toHaveLength(1);
    expect(fake.state.windows.map((w) => w.id)).not.toContain("zone:z1");
    expect(useDesk.getState().zoneWindows).toEqual([]);
    expect(Object.keys(useDesk.getState().panelDepth)).not.toContain("zone:z1");
    expect(hub.rows.has("zone:z1")).toBe(false);
  });

  it("a refused close re-reads and closes with the hub's revision", async () => {
    const { fake, hub } = start(zoneRows());
    fake.answers.push(async () => {
      // An older view moved the row first: the close's revision is stale.
      fake.state.windows = [row("zone:z1", { app: "zone", object_ref: "z1", depth: 3, revision: 5 })];
      throw new ApiError(409, "window_stale", { error: "window_stale" });
    });
    await hub.start();
    await flush(hub);
    await flush(hub);
    const sent = closes(fake);
    expect(sent).toHaveLength(2);
    expect(sent[1].body.expected_revision).toBe(5);
    expect(fake.state.windows.map((w) => w.id)).not.toContain("zone:z1");
  });

  it("a close the hub always refuses is tried at most three times (no loop)", async () => {
    const { fake, hub } = start(zoneRows());
    for (let i = 0; i < 10; i += 1)
      fake.answers.push(async () => {
        throw new ApiError(409, "window_stale", { error: "window_stale" });
      });
    await hub.start();
    for (let i = 0; i < 6; i += 1) await flush(hub);
    expect(closes(fake)).toHaveLength(3);
    expect(useDesk.getState().zoneWindows).toEqual([]);
  });

  it("closes a parked static application by its registry app name", async () => {
    const { fake, hub } = start([
      row("surface-concierge", { app: "open-concierge", depth: 1, revision: 2 }),
    ]);
    await hub.start();
    await flush(hub);
    expect(fake.calls.filter((call) => call.verb === "close" && call.id === "surface-concierge")).toHaveLength(1);
    expect(fake.state.windows.map((window) => window.id)).not.toContain("surface-concierge");
    expect(useDesk.getState().windowsById["surface-concierge"]).toBeUndefined();
  });
});

// Betterment daily D5: Brief and The week retired into Today. A desk restored
// with one of them open closes it on the hub and opens Today in its place,
// once; nothing is refused and nothing loops.
describe("Betterment daily D5: Brief and The week give way to Today", () => {
  const todayOpens = () => {
    const opens: string[] = [];
    const real = useDesk.getState().openPullout;
    useDesk.setState({ openPullout: ((id: string, ...rest: unknown[]) => {
      opens.push(id);
      return (real as (...a: unknown[]) => unknown)(id, ...rest);
    }) as typeof real });
    return opens;
  };

  it("a restored chair:week and chair:brief close on the hub and Today opens once", async () => {
    const opens = todayOpens();
    const { fake, hub } = start([
      row("chair:week", { depth: 2, revision: 2 }),
      row("chair:brief", { depth: 3, revision: 3 }),
      row("chair:needs", { depth: 4, revision: 4 }),
    ]);
    await hub.start();
    await flush(hub);
    const closes = fake.calls.filter((c) => c.verb === "close").map((c) => c.id).sort();
    expect(closes).toEqual(["chair:brief", "chair:week"]);
    expect(fake.state.windows.map((w) => w.id)).not.toContain("chair:week");
    expect(fake.state.windows.map((w) => w.id)).not.toContain("chair:brief");
    expect(opens).toEqual(["intelligence:desk"]);
    expect(Object.keys(useDesk.getState().panelDepth)).not.toContain("chair:week");
    expect(hub.rows.has("chair:week")).toBe(false);
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
    // A later frame (another client re-reads) opens nothing again.
    hub.onFrame({ kind: "windows", id: "chair:needs" });
    await flush(hub);
    expect(opens).toEqual(["intelligence:desk"]);
  });

  it("a hub that refuses the close does not open Today again on every read", async () => {
    const opens = todayOpens();
    const { fake, hub } = start([row("chair:week", { depth: 2, revision: 2 })]);
    const verb = fake.transport.verb;
    fake.transport.verb = vi.fn(async (id, v, body) => {
      if (v === "close") {
        fake.calls.push({ verb: v, id, body });
        throw new ApiError(409, "window_stale", { error: "window_stale" });
      }
      return verb(id, v, body);
    });
    await hub.start();
    for (let i = 0; i < 6; i += 1) await flush(hub);
    expect(fake.calls.filter((c) => c.verb === "close")).toHaveLength(3);
    expect(opens).toEqual(["intelligence:desk"]);
  });
});

// Betterment setup ST1: one home each. A desk saved with the Rhythm window or
// Change places open closes that row on the hub and opens Settings at Rhythm
// or at Wallpaper in its place, once; the hub never reopens the old window.
describe("Betterment setup ST1: Rhythm and Change places open their Settings section", () => {
  const settingsOpens = () => {
    const opens: Array<[string, string | undefined]> = [];
    const real = useDesk.getState().openSurfaceWindow;
    useDesk.setState({ openSurfaceWindow: ((key: string, scope?: string, ...rest: unknown[]) => {
      opens.push([key, scope]);
      return (real as (...a: unknown[]) => unknown)(key, scope, ...rest);
    }) as typeof real });
    return opens;
  };
  const RETIRED = {
    ...REGISTRY,
    static: { ...REGISTRY.static, "surface-cadence": "configure-cadence", "surface-places": "change-places", "surface-settings": "configure-settings" },
    retired: { ...REGISTRY.retired, "surface-cadence": "Rhythm is a section of Settings", "surface-places": "Wallpaper is a section of Settings" },
  };

  it("a saved surface-cadence and surface-places close on the hub; Settings opens at Rhythm and at Wallpaper, once each", async () => {
    const opens = settingsOpens();
    const { fake, hub } = start([
      row("surface-cadence", { app: "configure-cadence", depth: 2, revision: 2 }),
      row("surface-places", { app: "change-places", depth: 3, revision: 3 }),
    ]);
    const list = fake.transport.list;
    fake.transport.list = vi.fn(async () => ({ ...(await list()), registry: RETIRED }));
    await hub.start();
    await flush(hub);
    const closes = fake.calls.filter((c) => c.verb === "close").map((c) => c.id).sort();
    expect(closes).toEqual(["surface-cadence", "surface-places"]);
    expect(opens).toEqual([["configure-settings", "rhythm"], ["configure-settings", "wallpaper"]]);
    expect(useDesk.getState().windowsById["surface-cadence"]).toBeUndefined();
    expect(useDesk.getState().windowsById["surface-places"]).toBeUndefined();
    // A later read opens nothing again.
    hub.onFrame({ kind: "windows", id: "surface-settings" });
    await flush(hub);
    expect(opens).toHaveLength(2);
  });
});


it("moves a saved Commands row to Speak Voice commands once", async () => {
  const opens: Array<[string, string | undefined]> = [];
  const real = useDesk.getState().openSurfaceWindow;
  useDesk.setState({ openSurfaceWindow: ((key: string, scope?: string, ...rest: unknown[]) => {
    opens.push([key, scope]);
    return (real as (...args: unknown[]) => unknown)(key, scope, ...rest);
  }) as typeof real });
  const { fake, hub } = start([row("surface-commands", { app: "configure-commands", revision: 2 })]);
  const list = fake.transport.list;
  fake.transport.list = vi.fn(async () => ({ ...(await list()), registry: {
    ...REGISTRY, static: { ...REGISTRY.static, "surface-commands": "configure-commands" },
    retired: { ...REGISTRY.retired, "surface-commands": "Voice commands is a wing of Speak" },
  } }));
  await hub.start();
  await flush(hub);
  expect(fake.calls.filter((call) => call.verb === "close").map((call) => call.id)).toEqual(["surface-commands"]);
  expect(opens).toEqual([["dictate", "commands"]]);
  hub.onFrame({ kind: "windows", id: "surface-dictation" });
  await flush(hub);
  expect(opens).toHaveLength(1);
});
