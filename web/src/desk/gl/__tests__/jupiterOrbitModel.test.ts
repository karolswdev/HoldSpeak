import { describe, expect, it } from "vitest";
import {
  JUPITER_CLOUD_FLOW, JUPITER_ENCOUNTER_WINDOW_SECONDS, JUPITER_MOONS, JUPITER_RADIUS,
  jupiterEncounterAtTime, jupiterEncounterForWindow, jupiterMoonPosition,
  jupiterRenderSize, jupiterZonalDisplacement, makeJupiterRandom,
} from "../jupiterOrbitModel";

const seed = 0x4a555049;

describe("Jupiter orbital composition", () => {
  it("starts with one foreground moon and three behind the planet", () => {
    const positions = JUPITER_MOONS.map((_, index) => jupiterMoonPosition(index, 0));
    expect(positions[0][2]).toBeGreaterThan(0);
    for (const [x, y, z] of positions.slice(1)) {
      expect(z).toBeLessThan(-JUPITER_RADIUS);
      expect(Math.hypot(x, y)).toBeLessThan(JUPITER_RADIUS);
    }
    expect(new Set(JUPITER_MOONS.map(moon => moon.radius)).size).toBe(4);
  });

  it("takes each moon in front of and behind Jupiter on its own period", () => {
    JUPITER_MOONS.forEach((moon, index) => {
      const initial = jupiterMoonPosition(index, 0);
      const fullTurn = jupiterMoonPosition(index, moon.period);
      fullTurn.forEach((value, axis) => expect(value).toBeCloseTo(initial[axis], 9));
      const front = (Math.PI * 2 + Math.PI / 2 - moon.phase) / (Math.PI * 2) * moon.period;
      const back = front + moon.period / 2;
      expect(jupiterMoonPosition(index, front)[2]).toBeCloseTo(moon.orbit, 9);
      expect(jupiterMoonPosition(index, back)[2]).toBeCloseTo(-moon.orbit, 9);
      expect(Math.abs(jupiterMoonPosition(index, front)[0])).toBeLessThan(0.001);
    });
  });

  it("keeps seeded layout repeatable without sharing another scene RNG", () => {
    const a = makeJupiterRandom(seed), b = makeJupiterRandom(seed);
    expect(Array.from({ length: 12 }, a)).toEqual(Array.from({ length: 12 }, b));
  });

  it("moves neighbouring cloud zones in different directions without growing shear over hours", () => {
    expect(jupiterZonalDisplacement(0.25, 60) * jupiterZonalDisplacement(-0.25, 60)).toBeLessThan(0);
    expect(jupiterZonalDisplacement(0.25, 0)).toBeCloseTo(0);
    expect(jupiterZonalDisplacement(1, 60)).toBeCloseTo(0);
    for (const elapsed of [5, 30, 60, 3600, 86_400, 100_000_000]) {
      for (let index = -100; index <= 100; index++) {
        expect(Math.abs(jupiterZonalDisplacement(index / 100, elapsed)))
          .toBeLessThanOrEqual(JUPITER_CLOUD_FLOW.jetAmplitude);
      }
    }
    expect(Math.abs(jupiterZonalDisplacement(0.25, 60))).toBeGreaterThan(0.001);
  });

  it("bounds render size and DPR while retaining the viewport proportions", () => {
    expect(jupiterRenderSize(393, 852, 3)).toEqual({ width: 393, height: 852, dpr: 1.5 });
    const large = jupiterRenderSize(7680, 4320, 2);
    expect(large.width).toBe(1600);
    expect(large.height).toBe(900);
    expect(jupiterRenderSize(0, 0, 0)).toEqual({ width: 1, height: 1, dpr: 1 });
  });
});

describe("rare Jupiter encounters", () => {
  it("has no encounter before ten minutes, including invalid elapsed values", () => {
    for (const elapsed of [0, 42, 599.999, -100, Number.NaN, Number.POSITIVE_INFINITY]) {
      expect(jupiterEncounterAtTime(seed, 91, elapsed)).toBeNull();
    }
    expect(jupiterEncounterForWindow(seed, 91, 0)).toBeNull();
  });

  it("selects only the authored rare bands, with most windows fully quiet", () => {
    const counts = { pioneer: 0, voyager: 0, monolith: 0, none: 0 };
    for (let index = 1; index <= 100_000; index++) {
      const encounter = jupiterEncounterForWindow(seed, 91, index);
      counts[encounter?.kind ?? "none"]++;
      if (encounter) {
        expect(encounter.duration).toBeGreaterThanOrEqual(45);
        expect(encounter.duration).toBeLessThanOrEqual(75);
        expect(encounter.start).toBeGreaterThanOrEqual(index * 600);
        expect(encounter.start + encounter.duration).toBeLessThanOrEqual((index + 1) * 600);
      }
    }
    expect(counts.pioneer / 100_000).toBeCloseTo(0.02, 2);
    expect(counts.voyager / 100_000).toBeCloseTo(0.01, 2);
    expect(counts.monolith / 100_000).toBeCloseTo(0.002, 3);
    expect(counts.none).toBeGreaterThan(96_000);
  });

  it("is deterministic within a session, changes across sessions and stays offscreen between passes", () => {
    let window = 1;
    while (!jupiterEncounterForWindow(seed, 91, window)) window++;
    const encounter = jupiterEncounterForWindow(seed, 91, window)!;
    expect(jupiterEncounterForWindow(seed, 91, window)).toEqual(encounter);
    expect(jupiterEncounterForWindow(seed, 92, window)).not.toEqual(encounter);
    expect(jupiterEncounterAtTime(seed, 91, encounter.start - 0.01)).toBeNull();
    expect(jupiterEncounterAtTime(seed, 91, encounter.start + encounter.duration + 0.01)).toBeNull();
    const midpoint = jupiterEncounterAtTime(seed, 91, encounter.start + encounter.duration * 0.5)!;
    expect(midpoint.progress).toBeCloseTo(0.5);
    expect(midpoint.kind).toBe(encounter.kind);
    const reflected = jupiterEncounterAtTime(seed, 91, encounter.start + encounter.duration * 0.48)!;
    expect(reflected.glint).toBeCloseTo(1);
    expect(midpoint.glint).toBe(0);
    expect(JUPITER_ENCOUNTER_WINDOW_SECONDS).toBe(600);
  });
});
