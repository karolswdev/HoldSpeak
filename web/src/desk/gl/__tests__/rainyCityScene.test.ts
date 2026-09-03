import { describe, expect, it } from "vitest";
import {
  lightningIntensityAt,
  makeAtmosphereRandom,
  neonFlickerIntensityAt,
  nextNeonFlickerDelay,
  nextLightningDelay,
  nextTrafficDelay,
  trafficProgressAt,
} from "../rainyCityScene";

describe("rainy-city weather model", () => {
  it("keeps a seeded authored composition deterministic", () => {
    const first = makeAtmosphereRandom(42);
    const second = makeAtmosphereRandom(42);
    expect(Array.from({ length: 8 }, first)).toEqual(
      Array.from({ length: 8 }, second),
    );
  });

  it("uses bounded irregular intervals between lightning events", () => {
    expect(nextLightningDelay(() => 0)).toBe(9);
    expect(nextLightningDelay(() => 0.5)).toBe(17.5);
    expect(nextLightningDelay(() => 1)).toBe(26);
  });

  it("composes a brief multi-pulse lightning envelope", () => {
    expect(lightningIntensityAt(-0.1)).toBe(0);
    expect(lightningIntensityAt(0.08)).toBeGreaterThan(0.7);
    expect(lightningIntensityAt(0.2)).toBeLessThan(lightningIntensityAt(0.28));
    expect(lightningIntensityAt(0.52)).toBeGreaterThan(0.8);
    expect(lightningIntensityAt(1.2)).toBe(0);
  });

  it("spaces procedural traffic into occasional seeded passes", () => {
    expect(nextTrafficDelay(() => 0)).toBe(11);
    expect(nextTrafficDelay(() => 0.5)).toBe(20);
    expect(nextTrafficDelay(() => 1)).toBe(29);
  });

  it("clamps a car pass to its authored travel window", () => {
    expect(trafficProgressAt(4, 5, 8)).toBe(0);
    expect(trafficProgressAt(9, 5, 8)).toBe(0.5);
    expect(trafficProgressAt(15, 5, 8)).toBe(1);
  });

  it("gives neon independent irregular flicker intervals", () => {
    expect(nextNeonFlickerDelay(() => 0)).toBe(4);
    expect(nextNeonFlickerDelay(() => 0.5)).toBe(10);
    expect(nextNeonFlickerDelay(() => 1)).toBe(16);
  });

  it("keeps neon flutter deterministic and smoothly recovers", () => {
    expect(neonFlickerIntensityAt(-0.1, 0.42)).toBe(1);
    const flutter = neonFlickerIntensityAt(0.2, 0.42);
    expect(flutter).toBe(neonFlickerIntensityAt(0.2, 0.42));
    expect(flutter).toBeGreaterThanOrEqual(0.08);
    expect(flutter).toBeLessThanOrEqual(0.94);
    expect(neonFlickerIntensityAt(0.64, 0.42)).toBeCloseTo(0.725);
    expect(neonFlickerIntensityAt(0.8, 0.42)).toBe(1);
  });
});
