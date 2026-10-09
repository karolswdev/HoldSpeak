// Astra M1 and M4 on the compositor's DOM side (jsdom: no WAAPI, so every
// transition is its end state).
//  M1: Stage never writes the saved arrangement; a resize of the staged
//      front writes the stage rect only; Esc restores BOTH remembered rects
//      (free and zoom) and the zoom flag exactly; Zoom during Stage leaves
//      Stage first.
//  M4: no lift under a held pointer.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../store";
import { getPresentation, mountWindow, modeNow, setPresentation, unmountWindow } from "../live";
import { back, bandNow, liftOnRaise, plateOf, resizePlate, stageOn, tileFront } from "../useCompositor";
import { zoomWindow } from "../../components/window/windowCommands";

const FREE = { x: 300, y: 120, w: 600, h: 400 };
const ZOOM = { x: 10, y: 28, w: 1420, h: 796 };
const B = { x: 700, y: 200, w: 500, h: 380 };

beforeEach(() => {
  localStorage.clear();
  setPresentation({ mode: "free", plates: {}, saved: {}, staged: null });
  mountWindow("a", { layer: "window" });
  mountWindow("b", { layer: "window" });
  useDesk.setState({
    panelDepth: { b: 1, a: 2 },
    panelMin: [],
    panelRects: { a: FREE, b: B },
    panelSaved: ["a", "b"],
    panelMax: ["a"],
    panelZoom: { a: ZOOM },
  });
});
afterEach(() => {
  unmountWindow("a");
  unmountWindow("b");
  setPresentation({ mode: "free", plates: {}, saved: {}, staged: null });
});

const geometry = () => {
  const s = useDesk.getState();
  return { rects: s.panelRects, saved: s.panelSaved, max: s.panelMax, zoom: s.panelZoom };
};

describe("Stage keeps the saved arrangement (M1)", () => {
  it("a zoomed window: Stage, resize the staged front, Esc -> both rects and the zoom flag exactly", () => {
    const before = JSON.parse(JSON.stringify(geometry()));
    stageOn(null);
    expect(modeNow()).toBe("stage");
    expect(getPresentation().staged).toBe("a");
    resizePlate("a", { x: 351, y: 54, w: 999, h: 710 });
    expect(plateOf("a")!.rect).toEqual({ x: 351, y: 54, w: 999, h: 710 });
    expect(geometry()).toEqual(before); // nothing saved changed
    expect(back()).toBe(true);
    expect(modeNow()).toBe("free");
    expect(geometry()).toEqual(before);
  });

  it("a shelf plate (scaled) is not resized", () => {
    stageOn(null);
    const plate = plateOf("b")!;
    expect(plate.k).toBeLessThan(1);
    resizePlate("b", { x: 0, y: 0, w: 900, h: 900 });
    expect(plateOf("b")).toEqual(plate);
  });

  it("Zoom pressed during Stage leaves Stage first, with the saved rects back", () => {
    stageOn(null);
    resizePlate("a", { x: 351, y: 54, w: 999, h: 710 });
    zoomWindow("a"); // unzoom: a was zoomed
    expect(modeNow()).toBe("free");
    const s = useDesk.getState();
    expect(s.panelMax).not.toContain("a");
    expect(s.panelRects.a).toEqual(FREE);
    expect(s.panelZoom.a).toEqual(ZOOM);
  });
});

describe("no lift under a held pointer (M4)", () => {
  it("a raise under the pointer does not lift; one by a key does", () => {
    const el = document.createElement("div");
    const animate = vi.fn(() => ({ addEventListener: () => {}, finish: () => {} }));
    (el as unknown as { animate: unknown }).animate = animate;
    document.dispatchEvent(new Event("pointerdown"));
    liftOnRaise(el);
    expect(animate).not.toHaveBeenCalled();
    document.dispatchEvent(new Event("pointerup"));
    liftOnRaise(el);
    expect(animate).toHaveBeenCalledTimes(1);
  });
});

describe("Tile gives each window at least its real minimum (M2)", () => {
  it("the seam moves so the wider minimum fits; the two still touch inside the band", () => {
    useDesk.setState({ panelMax: [], panelZoom: {} });
    mountWindow("a", { layer: "window", minW: 600, minH: 220 });
    mountWindow("b", { layer: "window", minW: 320, minH: 220 });
    tileFront("left"); // a is front: left
    const band = bandNow();
    const { a, b } = useDesk.getState().panelRects;
    expect(a.w).toBeGreaterThanOrEqual(600);
    expect(b.w).toBeGreaterThanOrEqual(320);
    expect(a.x).toBe(band.x);
    expect(b.x).toBe(a.x + a.w);
    expect(b.x + b.w).toBe(band.x + band.w);
    back();
    expect(useDesk.getState().panelRects).toEqual({ a: FREE, b: B });
  });
});
