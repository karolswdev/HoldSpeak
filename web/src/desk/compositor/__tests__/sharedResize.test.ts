// PHILO-16 (L8): touching edges are one boundary.
import { describe, expect, it } from "vitest";
import { boundaries, MIN_W, resizeBoundary } from "../sharedResize";

const w = (id: string, x: number, y: number, ww: number, h: number) => ({ id, rect: { x, y, w: ww, h }, depth: 1 });

describe("shared resize", () => {
  it("two tiled windows share one vertical boundary", () => {
    const ws = [w("a", 10, 54, 700, 700), w("b", 710, 54, 700, 700)];
    const bs = boundaries(ws);
    expect(bs).toHaveLength(1);
    expect(bs[0]).toMatchObject({ axis: "v", at: 710, before: ["a"], after: ["b"] });
  });

  it("three in a row make two boundaries", () => {
    const ws = [w("a", 0, 0, 400, 500), w("b", 400, 0, 400, 500), w("c", 800, 0, 400, 500)];
    expect(boundaries(ws).filter((b) => b.axis === "v")).toHaveLength(2);
  });

  it("windows with a gutter do not touch; 1 px of rounding does", () => {
    expect(boundaries([w("a", 0, 0, 400, 500), w("b", 408, 0, 400, 500)])).toHaveLength(0);
    expect(boundaries([w("a", 0, 0, 400, 500), w("b", 401, 0, 400, 500)])).toHaveLength(1);
  });

  it("two stacked windows against one tall window group into one boundary", () => {
    const ws = [w("a", 0, 0, 400, 300), w("a2", 0, 300, 400, 300), w("b", 400, 0, 400, 600)];
    const v = boundaries(ws).filter((b) => b.axis === "v");
    expect(v).toHaveLength(1);
    expect(v[0].before.sort()).toEqual(["a", "a2"]);
    expect(v[0].after).toEqual(["b"]);
  });

  it("dragging moves the shared edge and keeps the far edges", () => {
    const ws = [w("a", 10, 54, 700, 700), w("b", 710, 54, 700, 700)];
    const [b] = boundaries(ws);
    const out = resizeBoundary(b, ws, 50);
    expect(out.get("a")).toEqual({ x: 10, y: 54, w: 750, h: 700 });
    expect(out.get("b")).toEqual({ x: 760, y: 54, w: 650, h: 700 });
  });

  it("the delta is clamped at the minimum width", () => {
    const ws = [w("a", 0, 0, 400, 500), w("b", 400, 0, 600, 500)];
    const [b] = boundaries(ws);
    const left = resizeBoundary(b, ws, -1000);
    expect(left.get("a")!.w).toBe(MIN_W);
    expect(left.get("b")!.x + left.get("b")!.w).toBe(1000);
    const right = resizeBoundary(b, ws, 1000);
    expect(right.get("b")!.w).toBe(MIN_W);
    expect(right.get("a")!.x).toBe(0);
  });
});

describe("shared resize respects each window's real minimum and the band (Astra M2)", () => {
  const band = { x: 10, y: 54, w: 1420, h: 700 };

  it("a frame with min-width 420 stops at 420, not at the module 320", () => {
    const ws = [
      { id: "people", rect: { x: 10, y: 54, w: 710, h: 700 }, depth: 1, minW: 420 },
      { id: "meetings", rect: { x: 720, y: 54, w: 710, h: 700 }, depth: 2, minW: 420 },
    ];
    const [b] = boundaries(ws);
    const out = resizeBoundary(b, ws, 1000, { band });
    const m = out.get("meetings")!;
    expect(m.w).toBe(420);
    expect(m.x + m.w).toBe(1430); // the far edge stays on the band's edge
    expect(out.get("people")!.w).toBe(1000);
  });

  it("no edge leaves the band", () => {
    const ws = [
      { id: "a", rect: { x: 10, y: 54, w: 700, h: 700 }, depth: 1 },
      { id: "b", rect: { x: 710, y: 54, w: 720, h: 700 }, depth: 2 },
    ];
    const [b] = boundaries(ws);
    for (const delta of [-5000, 5000]) {
      for (const r of resizeBoundary(b, ws, delta, { band }).values()) {
        expect(r.x).toBeGreaterThanOrEqual(band.x);
        expect(r.x + r.w).toBeLessThanOrEqual(band.x + band.w);
      }
    }
  });

  it("a boundary that cannot move does not move", () => {
    const ws = [
      { id: "a", rect: { x: 10, y: 54, w: 700, h: 700 }, depth: 1 },
      { id: "b", rect: { x: 710, y: 54, w: 400, h: 700 }, depth: 2, minW: 420 },
    ];
    const [b] = boundaries(ws);
    expect(resizeBoundary(b, ws, 50, { band }).size).toBe(0);
  });
});
