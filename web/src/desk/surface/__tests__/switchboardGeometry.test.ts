// PHILO-16 (C) — the Switchboard's pure geometry.
import { describe, expect, it } from "vitest";
import { patchChain, plugPoint, wirePath } from "../switchboardGeometry";

const origin = { left: 300, top: 100, right: 500, bottom: 700 };

describe("plugPoint", () => {
  it("reads a job's right edge and an engine's left edge, centred, in the layer's space", () => {
    const job = { left: 0, top: 120, right: 300, bottom: 160 };
    const engine = { left: 500, top: 200, right: 830, bottom: 250 };
    expect(plugPoint(job, "right", origin)).toEqual({ x: 0, y: 40 });
    expect(plugPoint(engine, "left", origin)).toEqual({ x: 200, y: 125 });
  });
});

describe("wirePath", () => {
  it("is one cubic whose control points share the horizontal midpoint (canvas draw())", () => {
    expect(wirePath({ x: 0, y: 40 }, { x: 200, y: 125 })).toBe("M6,40 C100,40 100,125 194,125");
  });

  it("is a straight run when the plugs are level", () => {
    expect(wirePath({ x: 0, y: 50 }, { x: 100, y: 50 }, 0)).toBe("M0,50 C50,50 50,50 100,50");
  });

  it("rounds to a tenth so a re-measure of the same layout is the same string", () => {
    expect(wirePath({ x: 0.333, y: 10.06 }, { x: 99.94, y: 20.04 }, 0)).toBe("M0.3,10.1 C50.1,10.1 50.1,20 99.9,20");
  });
});

describe("patchChain", () => {
  it("a drop puts the engine first and keeps the rest in order", () => {
    expect(patchChain(["a", "b", "c"], "c", false)).toEqual(["c", "a", "b"]);
  });

  it("an ⌥-drop appends a fallback after the others", () => {
    expect(patchChain(["a", "b"], "c", true)).toEqual(["a", "b", "c"]);
    expect(patchChain(["a", "b"], "a", true)).toEqual(["b", "a"]);
  });

  it("never duplicates and never holds more than four", () => {
    expect(patchChain(["a", "b", "c", "d"], "e", false)).toEqual(["e", "a", "b", "c"]);
    expect(patchChain(["a", "b", "c", "d"], "e", true)).toEqual(["a", "b", "c", "d"]);
    expect(patchChain([], "a", false)).toEqual(["a"]);
  });
});
