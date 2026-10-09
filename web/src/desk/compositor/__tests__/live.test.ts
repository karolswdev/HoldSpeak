// Astra M3: forty windows keep their visible stacking. The window band is
// anchored at the top: the front is always the highest z and no window
// shares the front's z; only the deepest windows share the band's floor.
import { afterEach, describe, expect, it } from "vitest";
import { useDesk } from "../../store";
import { computePlanes, mountWindow, unmountWindow, WINDOW_BAND_SLOTS, zOfWindow } from "../live";
import { Z } from "../layers";

const ids = Array.from({ length: 40 }, (_, i) => `w${i}`);

afterEach(() => {
  for (const id of ids) unmountWindow(id);
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
