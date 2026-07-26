/** HS-105-03 — the zone-window guard: open/close/persist grammar and the
 * per-zone remembered expression (view + sort). The window remembers —
 * that is what makes it a window. */
import { beforeEach, describe, expect, it } from "vitest";
import { useDesk } from "../../store";

describe("zone windows (HS-105-03)", () => {
  beforeEach(() => {
    localStorage.clear();
    useDesk.setState({ zoneWindows: [], zoneViewPrefs: {} });
  });

  it("opens as a coexisting window and persists the open set", () => {
    const s = useDesk.getState();
    s.openZoneWindow("z1", { x: 10, y: 20 });
    useDesk.getState().openZoneWindow("z2");
    expect(useDesk.getState().zoneWindows.map((w) => w.id)).toEqual([
      "z1",
      "z2",
    ]);
    expect(
      JSON.parse(localStorage.getItem("hs.desk.zone-windows") || "[]"),
    ).toEqual(["z1", "z2"]);
    // Reopening focuses, never duplicates.
    useDesk.getState().openZoneWindow("z1");
    expect(useDesk.getState().zoneWindows).toHaveLength(2);
  });

  it("closes one window and persists the remainder", () => {
    useDesk.getState().openZoneWindow("z1");
    useDesk.getState().openZoneWindow("z2");
    useDesk.getState().closeZoneWindow("z1");
    expect(useDesk.getState().zoneWindows.map((w) => w.id)).toEqual(["z2"]);
    expect(
      JSON.parse(localStorage.getItem("hs.desk.zone-windows") || "[]"),
    ).toEqual(["z2"]);
  });

  it("remembers view and sort per zone, persisted", () => {
    useDesk.getState().setZoneViewPref("z1", { view: "list" });
    useDesk.getState().setZoneViewPref("z1", { sort: "modified", dir: "desc" });
    useDesk.getState().setZoneViewPref("z2", { view: "icons" });
    const prefs = useDesk.getState().zoneViewPrefs;
    expect(prefs.z1).toEqual({ view: "list", sort: "modified", dir: "desc" });
    expect(prefs.z2.view).toBe("icons");
    const saved = JSON.parse(
      localStorage.getItem("hs.desk.zone-views") || "{}",
    );
    expect(saved.z1.sort).toBe("modified");
  });
});
