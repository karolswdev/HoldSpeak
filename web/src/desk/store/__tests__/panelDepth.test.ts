// PHILO-16 (L3) — the stacking is `panelDepth` (a counter); `panelOrder` is
// derived for one release. The depths persist in the workspace document; a
// document from before them migrates once from its order; a legacy write of
// the order is honoured; a reload keeps the planes from the numbers alone.
import { beforeEach, describe, expect, it } from "vitest";
import { useDesk } from "../../store";
import {
  DESK_WORKSPACE_STORAGE_KEY,
  loadDeskWorkspace,
} from "../workspaceStorage";
import { assignPlanes } from "../../compositor/planes";

const stored = () => JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");

const planes = (depth: Record<string, number>, min: string[] = []) =>
  assignPlanes(Object.entries(depth).map(([id, d]) => ({ id, depth: d, minimized: min.includes(id) })));

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({ panelDepth: {}, panelOrder: [], panelMin: [], panelRects: {}, panelSaved: [], panelMax: [] });
});

describe("panelDepth", () => {
  it("a raise is ++highest and the order follows", () => {
    const s = useDesk.getState();
    s.focusPanel("a");
    s.focusPanel("b");
    s.focusPanel("c");
    s.focusPanel("a");
    const { panelDepth, panelOrder } = useDesk.getState();
    expect(panelOrder).toEqual(["b", "c", "a"]);
    expect(panelDepth.a).toBeGreaterThan(panelDepth.c);
    expect(stored().panel.depth).toEqual(panelDepth);
    expect(stored().panel.order).toEqual(["b", "c", "a"]);
  });

  it("send back goes under the lowest shown window; a seated window keeps its depth", () => {
    const s = useDesk.getState();
    for (const id of ["a", "b", "c"]) s.focusPanel(id);
    s.minimizePanel("a");
    s.sendPanelToBack("c");
    const { panelDepth, panelOrder } = useDesk.getState();
    expect(panelDepth.c).toBeLessThan(panelDepth.b);
    expect(planes(panelDepth, ["a"]).get("b")).toBe("front");
    expect(planes(panelDepth, ["a"]).get("a")).toBe("seated");
    expect(panelOrder[panelOrder.length - 1]).toBe("b");
  });

  it("retire leaves the stacking; present does not re-raise a stacked window", () => {
    const s = useDesk.getState();
    s.focusPanel("a");
    s.focusPanel("b");
    s.presentPanel("a");
    expect(useDesk.getState().panelOrder).toEqual(["a", "b"]);
    s.retirePanel("b");
    expect(useDesk.getState().panelDepth).not.toHaveProperty("b");
    expect(useDesk.getState().panelOrder).toEqual(["a"]);
  });

  it("a legacy write of the order alone moves the depths with it", () => {
    useDesk.setState({ panelOrder: ["x", "y", "z"] });
    const { panelDepth } = useDesk.getState();
    expect(planes(panelDepth).get("z")).toBe("front");
    expect(planes(panelDepth).get("y")).toBe("near");
    useDesk.getState().sendPanelToBack("z");
    expect(useDesk.getState().panelOrder).toEqual(["z", "x", "y"]);
  });

  it("a document from before the depths migrates once from its order", () => {
    localStorage.setItem(
      DESK_WORKSPACE_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        windowsById: {},
        panel: { rects: {}, order: ["a", "b", "c"], max: [] },
        zoneWindows: [],
        zoneViewPrefs: {},
      }),
    );
    const doc = loadDeskWorkspace();
    expect(doc.panel.depth).toEqual({ a: 1, b: 2, c: 3 });
    expect(doc.panel.order).toEqual(["a", "b", "c"]);
  });

  it("a reload keeps the planes from the depth numbers, not the order", () => {
    const s = useDesk.getState();
    for (const id of ["a", "b", "c"]) s.focusPanel(id);
    s.sendPanelToBack("c");
    s.focusPanel("a");
    const before = planes(useDesk.getState().panelDepth);
    // A stale order beside the depths: the depths win.
    const raw = stored();
    raw.panel.order = ["a", "b", "c"];
    localStorage.setItem(DESK_WORKSPACE_STORAGE_KEY, JSON.stringify(raw));
    const doc = loadDeskWorkspace();
    expect(planes(doc.panel.depth!)).toEqual(before);
    expect(doc.panel.order).toEqual(["c", "b", "a"]);
  });

  it("Stage's shelf side persists", () => {
    useDesk.getState().setStageShelf("right");
    expect(stored().panel.shelf).toBe("right");
    expect(loadDeskWorkspace().panel.shelf).toBe("right");
  });
});
