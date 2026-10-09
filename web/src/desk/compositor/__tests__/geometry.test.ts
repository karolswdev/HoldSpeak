// PHILO-16 (L5): shares plus pixels, resolved by each view.
import { describe, expect, it } from "vitest";
import {
  bandFor,
  cascade,
  exposeGrid,
  gather,
  inside,
  parseValue,
  plateVisual,
  record,
  resolve,
  resolveRect,
  stage,
  tile,
  zoom,
  type Rect,
} from "../geometry";

const VIEWS = [
  [1440, 900],
  [1920, 1080],
] as const;

describe("values", () => {
  it("parses shares, pixels and both", () => {
    expect(parseValue("50% + 10")).toEqual({ share: 0.5, px: 10 });
    expect(parseValue("-1/2")).toEqual({ share: -0.5, px: 0 });
    expect(parseValue("1/2 - 4")).toEqual({ share: 0.5, px: -4 });
    expect(parseValue(120)).toEqual({ share: 0, px: 120 });
    expect(parseValue("-10")).toEqual({ share: 0, px: -10 });
    expect(() => parseValue("half")).toThrow();
  });

  it("resolves against a span; the zero of a rect is the view's centre", () => {
    expect(resolve("50% + 10", 1000)).toBe(510);
    const v = { x: 0, y: 0, w: 1000, h: 800 };
    expect(resolveRect({ x: "-1/2", y: "-1/2", w: "1/1", h: "1/1" }, v)).toEqual(v);
    expect(resolveRect({ x: 0, y: 0, w: 10, h: 10 }, v)).toEqual({ x: 500, y: 400, w: 10, h: 10 });
  });

  it.each(VIEWS)("record and resolve round-trip at %ix%i", (vw, vh) => {
    const view = bandFor(vw, vh);
    for (const r of [
      { x: 10, y: 38, w: 700, h: 500 },
      { x: 333, y: 101, w: 641, h: 377 },
      { x: view.x, y: view.y, w: view.w, h: view.h },
    ] as Rect[]) {
      expect(resolveRect(record(r, view), view)).toEqual(r);
    }
  });
});

describe("arrangements", () => {
  it.each(VIEWS)("tile resolves to the two halves of the band at %ix%i", (vw, vh) => {
    const band = bandFor(vw, vh);
    const m = tile("a", "b", "left");
    const a = resolveRect(m.get("a")!, band);
    const b = resolveRect(m.get("b")!, band);
    expect(a.x).toBe(band.x);
    expect(a.w).toBe(band.w / 2);
    expect(b.x).toBe(a.x + a.w); // they touch: one boundary
    expect(b.x + b.w).toBe(band.x + band.w);
    expect(a.h).toBe(band.h);
    expect(inside(a, band) && inside(b, band)).toBe(true);
    const right = resolveRect(tile("a", null, "right").get("a")!, band);
    expect(right).toEqual(b);
  });

  it.each(VIEWS)("zoom fills the band at %ix%i", (vw, vh) => {
    const band = bandFor(vw, vh);
    expect(resolveRect(zoom(), band)).toEqual(band);
  });

  const rects: Record<string, Rect> = {
    a: { x: 14, y: 44, w: 700, h: 660 },
    b: { x: 520, y: 206, w: 900, h: 600 },
    c: { x: 650, y: 334, w: 760, h: 480 },
    d: { x: 760, y: 120, w: 560, h: 420 },
    e: { x: 100, y: 100, w: 1200, h: 700 },
  };

  it.each(VIEWS)("stage keeps the front at 76 %% and every plate inside the band at %ix%i", (vw, vh) => {
    const band = bandFor(vw, vh);
    for (const shelf of ["left", "right"] as const) {
      const m = stage("a", ["e", "d", "c", "b", "a"], shelf, rects, band);
      const main = resolveRect(m.get("a")!.rect, band);
      expect(main.w).toBe(Math.round(band.w * 0.76));
      expect(main.h).toBe(band.h);
      expect(inside(main, band)).toBe(true);
      for (const id of ["b", "c", "d", "e"]) {
        const plate = m.get(id)!;
        const vis = plateVisual(resolveRect(plate.rect, band), plate.k);
        expect(vis.w).toBeLessThanOrEqual(301);
        expect(vis.h).toBeLessThanOrEqual(171);
        expect(inside(vis, band)).toBe(true);
      }
      // the shelf sits beside the main window, not under it
      const plate = plateVisual(resolveRect(m.get("b")!.rect, band), m.get("b")!.k);
      if (shelf === "left") expect(plate.x + plate.w).toBeLessThanOrEqual(main.x);
      else expect(plate.x).toBeGreaterThanOrEqual(main.x + main.w);
    }
  });

  it("stage stacks the nearest plate on top", () => {
    const band = bandFor(1440, 900);
    const m = stage("a", ["b", "c", "a"], "left", rects, band);
    const y = (id: string) => resolveRect(m.get(id)!.rect, band).y;
    expect(y("c")).toBeLessThan(y("b"));
  });

  it.each(VIEWS)("exposé scales every plate inside the band, never overlapping, at %ix%i", (vw, vh) => {
    const band = bandFor(vw, vh);
    const ids = Object.keys(rects);
    const m = exposeGrid(ids, rects, band);
    const vis = ids.map((id) => {
      const p = m.get(id)!;
      const r = resolveRect(p.rect, band);
      expect(r.w).toBe(rects[id].w); // scaled, not reflowed
      return plateVisual(r, p.k);
    });
    for (const v of vis) expect(inside(v, band)).toBe(true);
    for (let i = 0; i < vis.length; i++)
      for (let j = i + 1; j < vis.length; j++) {
        const a = vis[i];
        const b = vis[j];
        const apart = a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y;
        expect(apart).toBe(true);
      }
  });

  it.each(VIEWS)("gather makes equal columns with 8 px gutters inside the band at %ix%i", (vw, vh) => {
    const band = bandFor(vw, vh);
    const m = gather(["a", "b", "c"]);
    const rs = ["a", "b", "c"].map((id) => resolveRect(m.get(id)!, band));
    expect(rs[0].x).toBe(band.x);
    for (const r of rs) expect(inside(r, band)).toBe(true);
    expect(Math.abs(rs[1].x - (rs[0].x + rs[0].w) - 8)).toBeLessThanOrEqual(1);
    expect(Math.abs(rs[2].x + rs[2].w - (band.x + band.w))).toBeLessThanOrEqual(1);
    expect(Math.abs(rs[0].w - rs[2].w)).toBeLessThanOrEqual(1);
  });

  it("cascade steps 26 px from the band's top-left and stays inside", () => {
    const band = bandFor(1440, 900);
    const m = cascade(["a", "b", "e"], rects, band);
    expect(m.get("a")).toMatchObject({ x: band.x + 4, y: band.y + 4 });
    expect(m.get("b")).toMatchObject({ x: band.x + 30, y: band.y + 30 });
    for (const r of m.values()) expect(inside(r, band)).toBe(true);
  });
});
