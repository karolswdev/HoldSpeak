import { describe, expect, it } from "vitest";
import {
  gardenBreezeAt,
  lanternGlowAt,
  makeGardenRandom,
} from "../lanternGardenScene";

describe("lantern-garden motion model", () => {
  it("keeps the authored landscaping deterministic for a seed", () => {
    const first = makeGardenRandom(1667);
    const second = makeGardenRandom(1667);
    expect(Array.from({ length: 10 }, first)).toEqual(
      Array.from({ length: 10 }, second),
    );
  });

  it("keeps the lantern output subtle and phase-dependent", () => {
    const glow = lanternGlowAt(4.2, 0.7);
    expect(glow).toBeGreaterThan(0.92);
    expect(glow).toBeLessThan(1.01);
    expect(glow).not.toBe(lanternGlowAt(4.2, 1.7));
  });

  it("composes a bounded non-mechanical breeze", () => {
    expect(Math.abs(gardenBreezeAt(8.5, 0.2))).toBeLessThanOrEqual(1);
    expect(gardenBreezeAt(8.5, 0.2)).not.toBe(gardenBreezeAt(8.5, 1.2));
  });
});
