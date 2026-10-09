// PHILO-16 (16b): the hub owns the desk's windows; this browser is a view.
// Seed from the hub's rows; every persisted store write goes to the hub
// through anticipate (shown at once, followed when it settles); a 409
// re-reads and follows; another client's frame re-seeds the changed ids and
// never an id with a request in flight. Rects travel as share+px.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { useChairWindows } from "../../chair/chairWindows";
import { useDesk } from "../../store";
import { DESK_WORKSPACE_STORAGE_KEY } from "../../store/workspaceStorage";
import { record, type Rect } from "../geometry";
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
  static: { "chair:needs": "chair", "chair:brief": "chair", "chair:week": "chair", "chair:capture": "chair" },
  families: { "zone:": "zone" },
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

/** A fake hub: `list` answers `state`; each verb is recorded and answered
 * by `answer` (default: the row with the change applied and revision + 1). */
function fakeHub(initial: HubWindowRow[]) {
  const state: { windows: HubWindowRow[] } = { windows: initial };
  const calls: { verb: string; id: string; body: Record<string, unknown> }[] = [];
  const answers: ((id: string, verb: string, body: Record<string, unknown>) => Promise<unknown>)[] = [];
  const list = (): HubWindowList => ({ windows: state.windows, stage_shelf: "left", revision: 0, registry: REGISTRY });
  const transport: HubTransport = {
    list: vi.fn(async () => list()),
    verb: vi.fn(async (id, verb, body) => {
      calls.push({ verb, id, body });
      const next = answers.shift();
      if (next) return next(id, verb, body) as Promise<HubWindowRow>;
      const current = state.windows.find((w) => w.id === id) ?? row(id);
      const top = Math.max(0, ...state.windows.map((w) => w.depth));
      const updated = {
        ...current,
        revision: current.revision + 1,
        ...(verb === "raise" || verb === "open" ? { depth: top + 1 } : {}),
        ...(verb === "seat" ? { minimized: Boolean(body.seated) } : {}),
        ...(verb === "set_geometry" && body.rect ? { ...(body.rect as object), arranged: true } : {}),
      };
      state.windows = [...state.windows.filter((w) => w.id !== id), updated];
      return updated;
    }),
    arrange: vi.fn(async (rects) => {
      calls.push({ verb: "arrange", id: Object.keys(rects).join(","), body: rects as Record<string, unknown> });
      const out = state.windows
        .filter((w) => w.id in rects)
        .map((w) => ({ ...w, ...rects[w.id], arranged: true, revision: w.revision + 1 }));
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
});

afterEach(() => {
  hub?.stop();
  hub = null;
});

function start(rows: HubWindowRow[]) {
  const fake = fakeHub(rows);
  hub = createHubWindows({ transport: fake.transport, view: () => VIEW, compact: () => false });
  return { fake, hub };
}

describe("hubWindows", () => {
  it("seeds the desk from the hub's rows: open, depth, seat, rect as share+px", async () => {
    const { hub } = start([
      row("chair:brief", { depth: 4, arranged: true, x: "-1/2", y: "-1/2", w: "1/2", h: "100%" }),
      row("chair:week", { depth: 7, minimized: true }),
      row("chair:needs", { depth: 9 }),
    ]);
    await hub.start();
    const s = useDesk.getState();
    expect(useChairWindows.getState().closed["chair:brief"]).toBe(false);
    expect(useChairWindows.getState().closed["chair:week"]).toBe(false);
    expect(s.panelDepth).toMatchObject({ "chair:brief": 4, "chair:week": 7, "chair:needs": 9 });
    expect(s.panelOrder.slice(-3)).toEqual(["chair:brief", "chair:week", "chair:needs"]);
    expect(s.panelMin).toContain("chair:week");
    // "-1/2" of the band from its centre is its left edge; "1/2" is half its width.
    expect(s.panelRects["chair:brief"]).toEqual({ x: 10, y: 38, w: 710, h: 772 });
    expect(s.panelSaved).toContain("chair:brief");
    // The cache is overwritten by the hub's rows (the next first paint).
    const cached = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(cached.panel.depth).toMatchObject({ "chair:brief": 4, "chair:week": 7, "chair:needs": 9 });
    expect(cached.panel.min).toContain("chair:week");
  });

  it("a raise shows at once, holds while in flight, then follows the hub's depth", async () => {
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
    expect(useDesk.getState().panelDepth["chair:brief"]).toBe(40);
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
    expect(useDesk.getState().panelDepth["chair:brief"]).toBe(5);
    expect(hub.rows.get("chair:brief")?.revision).toBe(3);
  });

  it("another client's frame re-seeds the changed ids: a raise, a seat, a close", async () => {
    const { fake, hub } = start([
      row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2 }), row("chair:needs", { depth: 3 }),
    ]);
    await hub.start();
    fake.state.windows = [row("chair:week", { depth: 2, minimized: true }), row("chair:brief", { depth: 4 })];
    hub.onFrame({
      kind: "windows", id: "chair:brief", op: "raise",
      changes: [{ kind: "windows", id: "chair:brief" }, { kind: "windows", id: "chair:week" }, { kind: "windows", id: "chair:needs" }],
    });
    await flush(hub);
    const s = useDesk.getState();
    expect(s.panelDepth["chair:brief"]).toBe(4);
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
    const anticipated = useDesk.getState().panelDepth["chair:brief"];
    expect(anticipated).toBeGreaterThan(2);
    // A frame arrives naming both, from before the raise landed.
    fake.state.windows = [row("chair:brief", { depth: 1 }), row("chair:week", { depth: 2, minimized: true })];
    hub.onFrame({ kind: "windows", id: "chair:week", changes: [{ kind: "windows", id: "chair:brief" }, { kind: "windows", id: "chair:week" }] });
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    expect(useDesk.getState().panelDepth["chair:brief"]).toBe(anticipated); // held
    expect(useDesk.getState().panelMin).toContain("chair:week"); // the other id follows
    answer.resolve(row("chair:brief", { depth: 9, revision: 2 }));
    await flush(hub);
    expect(useDesk.getState().panelDepth["chair:brief"]).toBe(9);
  });

  it("an open and a close here reach the hub; an empty hub adopts this view's windows", async () => {
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:brief": false } }));
    useDesk.setState({ panelDepth: { "chair:brief": 3 }, panelOrder: ["chair:brief"] });
    const { fake, hub } = start([]);
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

  it("a window frame is not a desk data change", () => {
    expect(isWindowsOnlyFrame({ kind: "windows", id: "chair:brief", changes: [{ kind: "windows", id: "chair:brief" }] })).toBe(true);
    expect(isWindowsOnlyFrame({ kind: "note", id: "n1", changes: [{ kind: "note", id: "n1" }] })).toBe(false);
    expect(isWindowsOnlyFrame({ kind: "windows", id: "a", changes: [{ kind: "windows", id: "a" }, { kind: "note", id: "n" }] })).toBe(false);
    expect(isWindowsOnlyFrame({})).toBe(false);
  });
});
