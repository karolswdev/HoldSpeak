/** Characterization tests for the store split (HS-117-02).
 *
 * Verifies:
 * - openPullout routing for every surface type
 * - Panel persistence round-trip (loadPanelLayout)
 * - Close/focus ordering
 * - Recording state transitions
 * - resetDesk sweeps ghost layout keys
 * - The public API shim re-exports match the slice exports
 */
import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock the API and external modules before importing the store.
vi.mock("../../lib/api", () => ({
  apiRequest: vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({}) }),
  ),
  apiFetch: vi.fn(() => Promise.resolve({})),
  newDeliveryId: vi.fn(() => "speak:test-coder-delivery"),
}));

vi.mock("../setup", () => ({
  loadSetup: vi.fn(() => Promise.resolve(null)),
}));

vi.mock("../repository", () => ({
  registerRepository: vi.fn(() =>
    Promise.resolve({ repository: { id: "repo-1" } }),
  ),
  fetchRepositories: vi.fn(() => Promise.resolve([])),
}));

vi.mock("../roadmap", () => ({
  fetchRoadmaps: vi.fn(() => Promise.resolve([])),
}));

import { apiRequest } from "../../lib/api";
import { useDesk, GHOST_LAYOUT_KEYS, loadPanelLayout, defaultViewFor, COMPACT_LIST_THRESHOLD } from "../store";
import type { UnitPos, PanelRect, DeskView, ZoneViewPref } from "../store";

// ---- helpers ------------------------------------------------------------

function resetStore() {
  useDesk.setState({
    pullouts: [],
    zoneWindows: [],
    infoWindows: [],
    roadmapWindows: [],
    repositoryWindows: [],
    workbenchWindows: [],
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    editingId: null,
    selectedIds: [],
    recording: "idle",
    recordingExternal: false,
    recordingStartedAt: null,
    items: {
      meeting: [], artifact: [], note: [{ kind: "note", id: "n1", title: "T", bodyMarkdown: "", tags: [], createdAt: "" }],
      decision: [], recipe: [], kb: [], directory: [{ kind: "directory", id: "d1", name: "Z", parentId: null, memberIds: [], nameNormalized: "", createdAt: "" }],
      project: [{ kind: "project", id: "p1", name: "P", description: "", keywords: [], teamMembers: [], meetingCount: 0, createdAt: "", updatedAt: "" }],
      chain: [], workflow: [], coder: [], game: [], layout: [], roadmap: [],
      story: [], repository: [{ kind: "repository", id: "r1", name: "R", sourceId: "s1", branch: "main", createdAt: "" }],
      workbench: [{ kind: "workbench", id: "wb1", name: "WB", createdAt: "" }],
      intelligence: [{ kind: "intelligence", id: "desk", name: "Intelligence" }],
    },
  });
}

// ---- test suites --------------------------------------------------------

describe("store split: re-exports", () => {
  it("useDesk is a Zustand store with getState", () => {
    expect(typeof useDesk).toBe("function");
    expect(typeof useDesk.getState).toBe("function");
  });

  it("GHOST_LAYOUT_KEYS is a readonly array", () => {
    expect(Array.isArray(GHOST_LAYOUT_KEYS)).toBe(true);
    expect(GHOST_LAYOUT_KEYS.length).toBeGreaterThan(0);
  });

  it("loadPanelLayout returns a PanelLayout", () => {
    const layout = loadPanelLayout();
    expect(layout).toHaveProperty("rects");
    expect(layout).toHaveProperty("order");
    expect(layout).toHaveProperty("max");
  });

  it("defaultViewFor resolves density-aware defaults", () => {
    expect(defaultViewFor("list", 5, false)).toBe("list");
    expect(defaultViewFor("spatial", 5, false)).toBe("spatial");
    expect(defaultViewFor("unset", 5, false)).toBe("spatial");
    expect(defaultViewFor("unset", 20, true)).toBe("list");
    expect(defaultViewFor("unset", 10, true)).toBe("spatial");
  });

  it("COMPACT_LIST_THRESHOLD is a number", () => {
    expect(typeof COMPACT_LIST_THRESHOLD).toBe("number");
    expect(COMPACT_LIST_THRESHOLD).toBe(16);
  });

  it("type exports compile (compile-time guard)", () => {
    // These are compile-time checks; if the types don't exist the file won't compile.
    const _pos: UnitPos = { x: 0, y: 0 };
    const _rect: PanelRect = { x: 0, y: 0, w: 100, h: 100 };
    const _view: DeskView = "spatial";
    const _pref: ZoneViewPref = { view: "icons", sort: "name", dir: "asc" };
    expect(_pos).toBeDefined();
    expect(_rect).toBeDefined();
    expect(_view).toBeDefined();
    expect(_pref).toBeDefined();
  });
});

describe("store split: openPullout routing", () => {
  beforeEach(resetStore);

  it("routes a note (pullout surface) to pullouts", () => {
    useDesk.getState().openPullout("n1");
    expect(useDesk.getState().pullouts).toHaveLength(1);
    expect(useDesk.getState().pullouts[0].id).toBe("n1");
  });

  it("routes a note by qualified ref", () => {
    useDesk.getState().openPullout("note:n1");
    expect(useDesk.getState().pullouts).toHaveLength(1);
    expect(useDesk.getState().pullouts[0].id).toBe("note:n1");
  });

  it("routes a directory (pullout surface) to pullouts", () => {
    useDesk.getState().openPullout("zone:d1");
    expect(useDesk.getState().pullouts).toHaveLength(1);
  });

  it("routes a repository (window surface) to repositoryWindows", () => {
    useDesk.getState().openPullout("repository:r1");
    expect(useDesk.getState().repositoryWindows).toHaveLength(1);
    expect(useDesk.getState().repositoryWindows[0].id).toBe("r1");
  });

  it("routes a workbench (window surface) to workbenchWindows", () => {
    useDesk.getState().openPullout("workbench:wb1");
    expect(useDesk.getState().workbenchWindows).toHaveLength(1);
    expect(useDesk.getState().workbenchWindows[0].id).toBe("wb1");
  });

  it("routes a project (surface type) without crashing", () => {
    // Project opens a surface, which does a dynamic import. Just verify no throw.
    expect(() => useDesk.getState().openPullout("project:p1")).not.toThrow();
  });

  it("warns on unknown id", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    useDesk.getState().openPullout("unknown-id");
    expect(spy).toHaveBeenCalledWith(expect.stringContaining("unknown id"));
    spy.mockRestore();
  });

  it("does not duplicate an already-open pullout", () => {
    useDesk.getState().openPullout("n1");
    useDesk.getState().openPullout("n1");
    expect(useDesk.getState().pullouts).toHaveLength(1);
  });
});

describe("store split: panel persistence round-trip", () => {
  beforeEach(resetStore);

  it("setPanelRect with persist=true adds to panelSaved", () => {
    useDesk.getState().setPanelRect("test-panel", { x: 10, y: 20, w: 100, h: 200 }, true);
    expect(useDesk.getState().panelSaved).toContain("test-panel");
    expect(useDesk.getState().panelRects["test-panel"]).toEqual({ x: 10, y: 20, w: 100, h: 200 });
  });

  it("resetPanelRect removes the panel", () => {
    useDesk.getState().setPanelRect("test-panel", { x: 10, y: 20, w: 100, h: 200 }, true);
    useDesk.getState().resetPanelRect("test-panel");
    expect(useDesk.getState().panelSaved).not.toContain("test-panel");
    expect(useDesk.getState().panelRects["test-panel"]).toBeUndefined();
  });

  it("loadPanelLayout returns valid structure even with empty storage", () => {
    localStorage.removeItem("hs.desk.panels");
    const layout = loadPanelLayout();
    expect(layout.rects).toBeDefined();
    expect(layout.order).toBeDefined();
    expect(layout.max).toBeDefined();
  });
});

describe("store split: close/focus ordering", () => {
  beforeEach(resetStore);

  it("focusPanel puts the panel at the end of panelOrder", () => {
    useDesk.getState().focusPanel("a");
    useDesk.getState().focusPanel("b");
    useDesk.getState().focusPanel("a");
    const order = useDesk.getState().panelOrder;
    expect(order[order.length - 1]).toBe("a");
    expect(order[order.length - 2]).toBe("b");
  });

  it("presentPanel is a no-op for already-present panels", () => {
    useDesk.getState().focusPanel("a");
    const before = useDesk.getState().panelOrder.slice();
    useDesk.getState().presentPanel("a");
    expect(useDesk.getState().panelOrder).toEqual(before);
  });

  it("retirePanel removes from order", () => {
    useDesk.getState().focusPanel("a");
    useDesk.getState().focusPanel("b");
    useDesk.getState().retirePanel("a");
    expect(useDesk.getState().panelOrder).not.toContain("a");
    expect(useDesk.getState().panelOrder).toContain("b");
  });

  it("closePullout with no id closes the front-most pullout", () => {
    useDesk.setState({ pullouts: [
      { id: "n1", origin: null },
      { id: "n2", origin: null },
    ]});
    // Focus n1 last so it's "in front"
    useDesk.getState().focusPanel("pullout:n1");
    useDesk.getState().closePullout();
    const ids = useDesk.getState().pullouts.map((p) => p.id);
    expect(ids).not.toContain("n1");
    expect(ids).toContain("n2");
  });

  it("minimizePanel and restorePanel cycle correctly", () => {
    useDesk.getState().focusPanel("p");
    useDesk.getState().minimizePanel("p");
    expect(useDesk.getState().panelMin).toContain("p");
    useDesk.getState().restorePanel("p");
    expect(useDesk.getState().panelMin).not.toContain("p");
    // Restored panel is focused (at end of order)
    const order = useDesk.getState().panelOrder;
    expect(order[order.length - 1]).toBe("p");
  });

  it("toggleMaximizePanel toggles", () => {
    useDesk.getState().toggleMaximizePanel("p");
    expect(useDesk.getState().panelMax).toContain("p");
    useDesk.getState().toggleMaximizePanel("p");
    expect(useDesk.getState().panelMax).not.toContain("p");
  });
});

describe("store split: recording state transitions", () => {
  beforeEach(resetStore);

  it("applyRecordingActivity transitions idle -> recording on meeting_live", () => {
    useDesk.getState().applyRecordingActivity({ state: "meeting_live" });
    expect(useDesk.getState().recording).toBe("recording");
    expect(useDesk.getState().recordingExternal).toBe(true);
  });

  it("applyRecordingActivity transitions recording -> idle on complete", () => {
    useDesk.setState({ recording: "recording", recordingStartedAt: Date.now() });
    useDesk.getState().applyRecordingActivity({ state: "complete" });
    expect(useDesk.getState().recording).toBe("idle");
    expect(useDesk.getState().recordingExternal).toBe(false);
    expect(useDesk.getState().recordingStartedAt).toBeNull();
  });

  it("applyRecordingActivity ignores null/undefined", () => {
    useDesk.getState().applyRecordingActivity(null);
    useDesk.getState().applyRecordingActivity(undefined);
    expect(useDesk.getState().recording).toBe("idle");
  });

  it("local start is not marked external", () => {
    useDesk.setState({ recordingStartedAt: Date.now() });
    useDesk.getState().applyRecordingActivity({ state: "meeting_live" });
    expect(useDesk.getState().recordingExternal).toBe(false);
  });
});

describe("store split: committed coder delivery", () => {
  beforeEach(() => {
    resetStore();
    vi.mocked(apiRequest).mockClear();
  });

  it("mints a stable delivery claim before posting remote dictation", async () => {
    await expect(
      useDesk.getState().speakToCoder("claude", "session-1", "Ship it"),
    ).resolves.toBe(true);

    expect(apiRequest).toHaveBeenCalledTimes(2);
    const [url, init] = vi.mocked(apiRequest).mock.calls[1];
    expect(url).toBe("/api/dictation/remote");
    expect(JSON.parse(String(init?.body))).toMatchObject({
      text: "Ship it",
      target_mode: "agent",
      delivery_id: "speak:test-coder-delivery",
    });
  });
});

describe("store split: resetDesk sweeps ghost layout keys", () => {
  beforeEach(resetStore);

  it("GHOST_LAYOUT_KEYS includes the canonical set", () => {
    expect(GHOST_LAYOUT_KEYS).toContain("hs.diorama.pos");
    expect(GHOST_LAYOUT_KEYS).toContain("hs.desk.panels");
    expect(GHOST_LAYOUT_KEYS).toContain("hs.desk.zonew");
    expect(GHOST_LAYOUT_KEYS).toContain("hs.desk.zone-views");
    expect(GHOST_LAYOUT_KEYS).toContain("hs.desk.zone-windows");
  });

  it("resetLayout clears all compositor state", () => {
    useDesk.getState().setPanelRect("x", { x: 1, y: 2, w: 3, h: 4 }, true);
    useDesk.getState().focusPanel("x");
    useDesk.getState().toggleMaximizePanel("x");
    useDesk.getState().minimizePanel("x");

    useDesk.getState().resetLayout();

    const s = useDesk.getState();
    expect(s.panelRects).toEqual({});
    expect(s.panelSaved).toEqual([]);
    expect(s.panelOrder).toEqual([]);
    expect(s.panelMin).toEqual([]);
    expect(s.panelMax).toEqual([]);
  });
});

describe("store split: window factory", () => {
  beforeEach(resetStore);

  it("openZoneWindow + closeZoneWindow", () => {
    useDesk.getState().openZoneWindow("d1");
    expect(useDesk.getState().zoneWindows).toHaveLength(1);
    useDesk.getState().closeZoneWindow("d1");
    expect(useDesk.getState().zoneWindows).toHaveLength(0);
  });

  it("openInfoWindow + closeInfoWindow", () => {
    useDesk.getState().openInfoWindow("note:n1");
    expect(useDesk.getState().infoWindows).toHaveLength(1);
    useDesk.getState().closeInfoWindow("note:n1");
    expect(useDesk.getState().infoWindows).toHaveLength(0);
  });

  it("openRoadmapWindow + closeRoadmapWindow", () => {
    useDesk.getState().openRoadmapWindow("test-roadmap");
    expect(useDesk.getState().roadmapWindows).toHaveLength(1);
    expect(useDesk.getState().roadmapWindows[0].slug).toBe("test-roadmap");
    useDesk.getState().closeRoadmapWindow("test-roadmap");
    expect(useDesk.getState().roadmapWindows).toHaveLength(0);
  });

  it("openRepositoryWindow + closeRepositoryWindow", () => {
    useDesk.getState().openRepositoryWindow("r1");
    expect(useDesk.getState().repositoryWindows).toHaveLength(1);
    useDesk.getState().closeRepositoryWindow("r1");
    expect(useDesk.getState().repositoryWindows).toHaveLength(0);
  });

  it("openWorkbenchWindow + closeWorkbenchWindow", () => {
    useDesk.getState().openWorkbenchWindow("wb1");
    expect(useDesk.getState().workbenchWindows).toHaveLength(1);
    useDesk.getState().closeWorkbenchWindow("wb1");
    expect(useDesk.getState().workbenchWindows).toHaveLength(0);
  });

  it("does not duplicate open windows", () => {
    useDesk.getState().openZoneWindow("d1");
    useDesk.getState().openZoneWindow("d1");
    expect(useDesk.getState().zoneWindows).toHaveLength(1);
  });

  it("setZoneViewPref merges partial updates", () => {
    useDesk.getState().setZoneViewPref("d1", { view: "list" });
    expect(useDesk.getState().zoneViewPrefs["d1"].view).toBe("list");
    expect(useDesk.getState().zoneViewPrefs["d1"].sort).toBe("name");
    useDesk.getState().setZoneViewPref("d1", { sort: "kind" });
    expect(useDesk.getState().zoneViewPrefs["d1"].view).toBe("list");
    expect(useDesk.getState().zoneViewPrefs["d1"].sort).toBe("kind");
  });
});

describe("store split: desk interaction slice", () => {
  beforeEach(resetStore);

  it("diveInto / surface cycle", () => {
    useDesk.getState().diveInto("d1");
    expect(useDesk.getState().divedZone).toBe("d1");
    useDesk.getState().surface();
    expect(useDesk.getState().divedZone).toBeNull();
  });

  it("toggleSelected adds and removes", () => {
    useDesk.getState().toggleSelected("n1");
    expect(useDesk.getState().selectedIds).toContain("n1");
    useDesk.getState().toggleSelected("n1");
    expect(useDesk.getState().selectedIds).not.toContain("n1");
  });

  it("clearSelection clears selection and closes ask", () => {
    useDesk.setState({ selectedIds: ["n1"], askOpen: true });
    useDesk.getState().clearSelection();
    expect(useDesk.getState().selectedIds).toEqual([]);
    expect(useDesk.getState().askOpen).toBe(false);
  });

  it("openEditor keeps an existing object's pullout as its in-world host", () => {
    useDesk.setState({ pullouts: [{ id: "n1", origin: null }] });
    useDesk.getState().openEditor("n1");
    expect(useDesk.getState().editingId).toBe("n1");
    expect(useDesk.getState().pullouts).toEqual([{ id: "n1", origin: null }]);
  });
});
