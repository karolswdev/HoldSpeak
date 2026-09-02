import { describe, expect, it } from "vitest";
import {
  lightningIntensityAt,
  makeAtmosphereRandom,
  nextLightningDelay,
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
});
