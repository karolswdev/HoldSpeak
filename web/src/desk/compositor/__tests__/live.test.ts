// Astra M3: forty windows keep their visible stacking. The window band is
// anchored at the top: the front is always the highest z and no window
// shares the front's z; only the deepest windows share the band's floor.
import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../store";
import { computePlanes, frontId, mountWindow, unmountWindow, WINDOW_BAND_SLOTS, zOfWindow } from "../live";
import { Z } from "../layers";
import {
  announceWindow,
  cycleWindows,
  closeFrontWindow,
  focusOrRestoreApp,
  frontWindowId,
  retractWindow,
  useFrontWindowId,
} from "../../components/window/windowRegistry";

const ids = Array.from({ length: 40 }, (_, i) => `w${i}`);

afterEach(() => {
  for (const id of ids) unmountWindow(id);
  unmountWindow("remote");
  unmountWindow("arriving");
  unmountWindow("mounted");
  unmountWindow("back");
  unmountWindow("front");
  retractWindow("remote");
  retractWindow("tombstoned");
  retractWindow("mounted");
  useDesk.setState({ panelDepth: {}, panelOrder: [], panelMin: [] });
});

function mountAll(n: number) {
  const depth: Record<string, number> = {};
  ids.slice(0, n).forEach((id, i) => {
    mountWindow(id, { layer: "window" });
    depth[id] = i + 1;
  });
  useDesk.setState({ panelDepth: depth, panelMin: [] });
}

describe("window z from the shown order", () => {
  it("up to the band's slots, z is 42 + rank (unchanged)", () => {
    mountAll(3);
    expect(ids.slice(0, 3).map((id) => zOfWindow(id))).toEqual([42, 43, 44]);
  });

  it("uses the mounted live snapshot for front, excluding an unmounted row and a tombstone", () => {
    mountWindow("back", { layer: "window" });
    mountWindow("front", { layer: "window" });
    announceWindow("remote", "Remote", "R", () => {});
    announceWindow("tombstoned", "Tombstoned", "T", () => {});
    useDesk.setState({ panelDepth: { back: 1, front: 2, remote: 99, tombstoned: 100 }, panelMin: [] });

    expect(computePlanes().shown).toEqual(["back", "front"]);
    expect(frontId()).toBe("front");
    expect(frontWindowId()).toBe("front");

    // Minimize retires the frame's depth while the mounted frame stays
    // available for restore. It remains seated, but cannot win front.
    useDesk.setState({ panelDepth: { back: 1, remote: 99 }, panelMin: ["front"] });
    expect(computePlanes().planes.get("front")).toBe("seated");
    expect(frontId()).toBe("back");
    expect(frontWindowId()).toBe("back");
  });

  it("keeps a mounted frame through depth arrival, then drops it on unmount", () => {
    mountWindow("back", { layer: "window" });
    useDesk.setState({ panelDepth: { back: 1 }, panelMin: [] });
    mountWindow("arriving", { layer: "window" });

    expect(computePlanes().shown).toEqual(["arriving", "back"]);
    expect(frontId()).toBe("back");

    useDesk.setState({ panelDepth: { back: 1, arriving: 2 }, panelMin: [] });
    expect(frontId()).toBe("arriving");

    unmountWindow("arriving");
    expect(computePlanes().shown).toEqual(["back"]);
    expect(frontId()).toBe("back");
  });

  it("uses the mounted target for close and focus while an unmounted row has depth", () => {
    const closeMounted = vi.fn();
    mountWindow("mounted", { layer: "window" });
    announceWindow("mounted", "Mounted", "M", closeMounted);
    announceWindow("remote", "Remote", "R", vi.fn());
    useDesk.setState({ panelDepth: { mounted: 1, remote: 99 }, panelMin: [] });

    expect(frontWindowId()).toBe("mounted");
    expect(focusOrRestoreApp("remote")).toBe(false);
    closeFrontWindow();
    expect(closeMounted).toHaveBeenCalledTimes(1);
  });

  it("does not fall back to an announced row when no frame is mounted", () => {
    const closeRemote = vi.fn();
    announceWindow("remote", "Remote", "R", closeRemote);
    useDesk.setState({ panelDepth: { remote: 99 }, panelMin: [] });

    const hook = renderHook(() => useFrontWindowId());
    expect(frontWindowId()).toBeNull();
    expect(hook.result.current).toBeNull();
    expect(focusOrRestoreApp("remote")).toBe(false);
    closeFrontWindow();
    expect(closeRemote).not.toHaveBeenCalled();
    hook.unmount();
  });

  it("cycles the mounted registry rows while preserving store MRU order", () => {
    const flash = vi.fn();
    mountWindow("mounted", { layer: "window" });
    announceWindow("mounted", "Mounted", "M", vi.fn());
    announceWindow("remote", "Remote", "R", vi.fn());
    useDesk.setState({ panelDepth: { mounted: 1, remote: 99 }, panelOrder: ["remote", "mounted"], panelMin: [] });

    cycleWindows(flash);
    expect(flash).toHaveBeenCalledWith("mounted");
  });

  it("forty windows: the front has the highest z, alone, and z never falls toward the front", () => {
    mountAll(40);
    // Raise the FIRST mounted window (the first in DOM order).
    useDesk.getState().focusPanel("w0");
    const live = computePlanes();
    expect(live.front).toBe("w0");
    const z = new Map(ids.map((id) => [id, zOfWindow(id, live)]));
    expect(z.get("w0")).toBe(Z.windowTop);
    const ties = ids.filter((id) => id !== "w0" && z.get(id) === z.get("w0"));
    expect(ties).toEqual([]);
    // Back to front, z never decreases; the top WINDOW_BAND_SLOTS are distinct.
    const zs = live.shown.map((id) => z.get(id)!);
    for (let i = 1; i < zs.length; i++) expect(zs[i]).toBeGreaterThanOrEqual(zs[i - 1]);
    const top = zs.slice(-WINDOW_BAND_SLOTS);
    expect(new Set(top).size).toBe(WINDOW_BAND_SLOTS);
    // No window rises over the waveform or the dock.
    expect(Math.max(...zs)).toBeLessThanOrEqual(Z.windowTop);
    expect(Math.min(...zs)).toBe(Z.windowBase);
  });
});
