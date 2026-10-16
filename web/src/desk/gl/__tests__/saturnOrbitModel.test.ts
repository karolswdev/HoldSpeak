import { describe, expect, it } from "vitest";
import {
  SATURN_MOONS, SATURN_RADIUS, SATURN_EQUATORIAL_RADIUS_KM, SATURN_RING_INNER, SATURN_RING_OUTER,
  SATURN_CASSINI_INNER, SATURN_CASSINI_OUTER, saturnFraming,
  saturnMoonPosition, saturnRenderSize,
} from "../saturnOrbitModel";

describe("Saturn cinematic model", () => {
  it("scales solid moon radii against Saturn's physical equatorial radius", () => {
    expect(SATURN_EQUATORIAL_RADIUS_KM).toBe(60_268);
    expect(SATURN_MOONS.map(moon => moon.physicalRadiusKm)).toEqual([2574.76, 252.10]);
    expect(SATURN_MOONS[0].radius / SATURN_RADIUS).toBeCloseTo(2574.76 / 60_268, 14);
    expect(SATURN_MOONS[1].radius / SATURN_RADIUS).toBeCloseTo(252.10 / 60_268, 14);
  });

  it("keeps two distinct staggered passes with front and back depth", () => {
    expect(SATURN_MOONS.map(moon => moon.name)).toEqual(["Titan", "Enceladus"]);
    expect(SATURN_MOONS[0].radius).toBeGreaterThan(SATURN_MOONS[1].radius * 2);
    expect(SATURN_MOONS[0].period).toBeGreaterThan(SATURN_MOONS[1].period * 2);
    for (let index = 0; index < SATURN_MOONS.length; index++) {
      const moon = SATURN_MOONS[index];
      const initial = saturnMoonPosition(index, 0);
      expect(saturnMoonPosition(index, moon.period)).toEqual(initial.map(value => expect.closeTo(value, 8)));
      expect(saturnMoonPosition(index, moon.period / 2)[2] * initial[2]).toBeLessThan(0);
      expect(Math.hypot(initial[0], initial[2])).toBeCloseTo(moon.orbit);
    }
    expect(saturnMoonPosition(0, 0)[2]).toBeGreaterThan(SATURN_RADIUS);
    expect(saturnMoonPosition(0, -10)).toEqual(saturnMoonPosition(0, 0));
    expect(() => saturnMoonPosition(2, 0)).toThrow(RangeError);
  });

  it("fits rings and the first Titan pass at both supported widths", () => {
    expect(SATURN_RING_INNER).toBeGreaterThan(SATURN_RADIUS);
    expect(SATURN_CASSINI_INNER).toBeGreaterThan(SATURN_RING_INNER);
    expect(SATURN_CASSINI_OUTER).toBeLessThan(SATURN_RING_OUTER);
    for (const [width, height] of [[1440, 900], [393, 852]]) {
      const framing = saturnFraming(width, height);
      expect(framing.halfWidth).toBeGreaterThan(SATURN_RING_OUTER);
      expect(framing.halfWidth - framing.x).toBeGreaterThan(SATURN_RING_OUTER);
      expect(Math.abs(saturnMoonPosition(0, 0)[0] + framing.x)).toBeLessThan(framing.halfWidth);
    }
  });

  it("caps framebuffer size and DPR independently of camera aspect", () => {
    expect(saturnRenderSize(393, 852, 3)).toEqual({ width: 393, height: 852, dpr: 1.5 });
    expect(saturnRenderSize(3840, 2160, 2)).toEqual({ width: 1600, height: 900, dpr: 1.5 });
    expect(saturnRenderSize(0, 0, 0)).toEqual({ width: 1, height: 1, dpr: 1 });
  });
});
