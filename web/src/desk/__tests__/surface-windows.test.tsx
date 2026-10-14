// Desk application lifecycle belongs to the compositor and round-trips in
// the one versioned workspace document.
import { act, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, openSurface, stageSurfaceOpen } from "../shell";
import { SurfaceWindows } from "../components/SurfaceWindows";
import { DESK_WORKSPACE_STORAGE_KEY, useDesk } from "../store";

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  useDesk.setState({
    windowsById: {},
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    zoneWindows: [],
    zoneViewPrefs: {},
  });
  __resetSurfaces();
});

afterEach(__resetSurfaces);

describe("surface windows use the compositor workspace", () => {
  it("opening writes normalized application instances with scope", () => {
    useDesk.getState().openSurfaceWindow("dictate");
    useDesk.getState().openSurfaceWindow("open-project-memory", "project:p1");
    const raw = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(raw.version).toBe(1);
    expect(raw.windowsById["surface-dictation"]).toMatchObject({
      id: "surface-dictation",
      kind: "surface",
      applicationKey: "dictate",
      scope: null,
    });
    expect(raw.windowsById["surface-project-memory"].scope).toBe("project:p1");
  });

  it("PHILO-17: a meeting scope opens the Meetings detail window", () => {
    useDesk.setState({ pullouts: [] });
    useDesk.getState().openSurfaceWindow("review-meetings", "meeting:m1?view=review");
    useDesk.getState().openSurfaceWindow("review-meetings", "meeting:m1");
    expect(useDesk.getState().windowsById["surface-meetings"]?.scope).toBe("meeting:m1");
    expect(useDesk.getState().pullouts).toEqual([]);
    // A person scope opens THAT person; the roster scope stays the People window.
    useDesk.getState().openSurfaceWindow("open-people", "people:rel-1:prep");
    expect(useDesk.getState().pullouts.map((p) => p.id)).toEqual(["people:rel-1"]);
    useDesk.getState().openSurfaceWindow("open-people", "people:project:p1");
    expect(useDesk.getState().windowsById["surface-people"]?.scope).toBe("people:project:p1");
  });

  it("closing drops the key from storage", () => {
    useDesk.getState().openSurfaceWindow("dictate");
    useDesk.getState().closeSurfaceWindow("dictate");
    const raw = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(raw.windowsById).toEqual({});
  });

  it("a fresh module load rehydrates the same windows (the reload case)", async () => {
    localStorage.setItem(
      DESK_WORKSPACE_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        windowsById: {
          "surface-meetings": {
            id: "surface-meetings",
            kind: "surface",
            applicationKey: "review-meetings",
            scope: "meeting:m1",
            persistence: "workspace",
          },
        },
        panel: { rects: {}, order: ["surface-meetings"], max: [] },
        zoneWindows: [],
        zoneViewPrefs: {},
      }),
    );
    vi.resetModules();
    const fresh = await import("../store");
    // PHILO-17: the saved record comes back as the scoped Meetings window;
    // the old pullout identity is retired once.
    expect(fresh.useDesk.getState().windowsById["surface-meetings"]?.scope).toBe("meeting:m1");
    expect(fresh.useDesk.getState().pullouts).toEqual([]);
  });

  it("boot migrates only explicit meeting pullouts and preserves generic pullouts and presentation", async () => {
    localStorage.setItem(
      DESK_WORKSPACE_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        windowsById: {},
        panel: {
          rects: {
            "pullout:intelligence:desk": { x: 20, y: 30, w: 420, h: 260 },
            "pullout:people:rel-1": { x: 40, y: 50, w: 430, h: 280 },
            "pullout:meeting:m1": { x: 60, y: 70, w: 720, h: 600 },
          },
          order: ["pullout:intelligence:desk", "pullout:people:rel-1", "pullout:meeting:m1"],
          depth: { "pullout:intelligence:desk": 1, "pullout:people:rel-1": 2, "pullout:meeting:m1": 3 },
          max: ["pullout:meeting:m1"],
          min: ["pullout:people:rel-1"],
          zoom: { "pullout:meeting:m1": { x: 0, y: 0, w: 900, h: 700 } },
        },
        zoneWindows: [],
        zoneViewPrefs: {},
        windows: { pullouts: ["intelligence:desk", "people:rel-1", "meeting:m1"], info: [], roadmap: [], repository: [], workbench: [] },
      }),
    );
    vi.resetModules();
    const fresh = await import("../store");
    const state = fresh.useDesk.getState();
    expect(state.pullouts.map((p) => p.id)).toEqual(["intelligence:desk", "people:rel-1"]);
    expect(state.windowsById["surface-meetings"]).toMatchObject({
      applicationKey: "review-meetings",
      scope: "meeting:m1",
    });
    expect(state.panelRects["surface-meetings"]).toEqual({ x: 60, y: 70, w: 720, h: 600 });
    expect(state.panelMax).toContain("surface-meetings");
    expect(state.panelMin).toContain("pullout:people:rel-1");
    expect(state.panelZoom["surface-meetings"]).toEqual({ x: 0, y: 0, w: 900, h: 700 });
  });

  it("a corrupt workspace starts with nothing open", async () => {
    localStorage.setItem(DESK_WORKSPACE_STORAGE_KEY, "not json");
    vi.resetModules();
    const fresh = await import("../store");
    expect(fresh.useDesk.getState().windowsById).toEqual({});
  });

  it("does not migrate the retired open-window slot", async () => {
    localStorage.setItem("hs.desk.open-windows", JSON.stringify({ dictate: null }));
    vi.resetModules();
    const fresh = await import("../store");
    expect(fresh.useDesk.getState().windowsById).toEqual({});
  });

  it("publishes normal registry completion only after a staged Meetings open can land", async () => {
    stageSurfaceOpen("review-meetings");
    const { container } = render(<SurfaceWindows />);

    await waitFor(() => {
      expect(
        container.querySelector("[data-surface-registry-state]"),
      ).toHaveAttribute("data-surface-registry-state", "registered");
      expect(useDesk.getState().windowsById["surface-meetings"]?.applicationKey)
        .toBe("review-meetings");
    });
  });

  it("arrival clears stale windows and registers only explicit Setup recovery", async () => {
    useDesk.getState().openSurfaceWindow("configure-settings");
    const { container } = render(<SurfaceWindows firstValueRecoveryOnly />);

    expect(
      container.querySelector("[data-surface-registry-state]"),
    ).toHaveAttribute("data-surface-registry-state", "recovery-only");
    await waitFor(() =>
      expect(useDesk.getState().windowsById).toEqual({}),
    );
    const cleared = JSON.parse(localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "{}");
    expect(cleared.windowsById).toEqual({});
    // Settings is an explicit first value recovery door alongside Setup.
    expect(openSurface("configure-settings")).toBe(true);
    expect(useDesk.getState().windowsById["surface-settings"]?.applicationKey)
      .toBe("configure-settings");

    act(() => {
      expect(openSurface("project-setup")).toBe(true);
    });
    expect(useDesk.getState().windowsById["surface-project-setup"]?.applicationKey)
      .toBe("project-setup");
  });
});
