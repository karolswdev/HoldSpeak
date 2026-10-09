// PHILO-16 (L4): the layer type and its rules.
import { describe, expect, it } from "vitest";
import { canMove, canRaise, compositorDraws, LAYERS, Z, zFor } from "../layers";

describe("layers", () => {
  it("derives the existing --desk-z-* numbers", () => {
    expect(zFor("floor")).toBe(0);
    expect(zFor("world")).toBe(25);
    expect(zFor("chrome")).toBe(30);
    expect(zFor("window", 0)).toBe(42);
    expect(zFor("window", 3)).toBe(45);
    expect(zFor("chrome", 1)).toBe(78);
    expect(zFor("chrome", 2)).toBe(80);
    expect(zFor("transient")).toBe(81);
    expect(zFor("transient", 1)).toBe(82);
  });

  it("no window rank rises over the waveform, the dock or a transient", () => {
    expect(zFor("window", 500)).toBe(Z.windowTop);
    expect(zFor("window", 500)).toBeLessThan(zFor("chrome", 1));
    expect(zFor("window", -4)).toBe(42);
  });

  it("chrome and transient stops clamp to their ladder", () => {
    expect(zFor("chrome", 9)).toBe(80);
    expect(zFor("transient", 9)).toBe(82);
  });

  it("only a window moves, raises, and is drawn by the compositor", () => {
    for (const layer of LAYERS) {
      expect(canMove(layer)).toBe(layer === "window");
      expect(canRaise(layer)).toBe(layer === "window");
      expect(compositorDraws(layer)).toBe(layer === "window");
    }
  });
});
