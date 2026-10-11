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

  it("PHILO-17: a meeting scope opens the meeting's own window, never the Meetings list", () => {
    useDesk.setState({ pullouts: [] });
    useDesk.getState().openSurfaceWindow("review-meetings", "meeting:m1?view=review");
    useDesk.getState().openSurfaceWindow("review-meetings", "meeting:m1");
    expect(useDesk.getState().windowsById["surface-meetings"]).toBeUndefined();
    expect(useDesk.getState().pullouts.map((p) => p.id)).toEqual(["meeting:m1"]);
    // A person scope opens THAT person; the roster scope stays the People window.
    useDesk.getState().openSurfaceWindow("open-people", "people:rel-1:prep");
    expect(useDesk.getState().pullouts.map((p) => p.id)).toEqual(["meeting:m1", "people:rel-1"]);
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
    // PHILO-17: the saved record comes back as the meeting's own window; the
    // Meetings window that held it does not come back (the hub's row
    // migrates the same way, Astra r1).
    expect(fresh.useDesk.getState().windowsById["surface-meetings"]).toBeUndefined();
    expect(fresh.useDesk.getState().pullouts.map((p) => p.id)).toEqual(["meeting:m1"]);
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
    expect(openSurface("configure-settings")).toBe(false);

    act(() => {
      expect(openSurface("project-setup")).toBe(true);
    });
    expect(useDesk.getState().windowsById["surface-project-setup"]?.applicationKey)
      .toBe("project-setup");
  });
});
