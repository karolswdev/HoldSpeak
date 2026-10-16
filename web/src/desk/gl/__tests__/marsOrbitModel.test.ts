import { describe, expect, it } from "vitest";
import { MARS_MOONS, MARS_RADIUS, MARS_MEAN_RADIUS_KM, marsMoonPosition, marsRenderSize } from "../marsOrbitModel";

describe("Mars cinematic orbits", () => {
  it("starts Phobos beyond the limb and gives the moons different speeds and sizes", () => {
    const [x, y, z] = marsMoonPosition(0, 0);
    expect(Math.hypot(x, y)).toBeGreaterThan(MARS_RADIUS);
    expect(z).toBeGreaterThan(0);
    expect(MARS_MOONS[0].period).toBeLessThan(MARS_MOONS[1].period);
    expect(MARS_MOONS[0].radius).toBeGreaterThan(MARS_MOONS[1].radius);
  });

  it("maps NASA/JPL physical mean radii directly to Mars without visibility enlargement", () => {
    expect(MARS_MEAN_RADIUS_KM).toBe(3389.50);
    expect(MARS_MOONS.map(moon => moon.physicalRadiusKm)).toEqual([11.08, 6.2]);
    MARS_MOONS.forEach(moon => {
      expect(moon.radius / MARS_RADIUS).toBeCloseTo(moon.physicalRadiusKm / MARS_MEAN_RADIUS_KM, 12);
    });
  });

  it("carries each moon through real front and back depth and returns after its period", () => {
    MARS_MOONS.forEach((moon, index) => {
      const initial = marsMoonPosition(index, 0);
      marsMoonPosition(index, moon.period).forEach((value, axis) => expect(value).toBeCloseTo(initial[axis], 9));
      const front = (Math.PI * 2 + Math.PI / 2 - moon.phase) / (Math.PI * 2) * moon.period;
      expect(marsMoonPosition(index, front)[2]).toBeCloseTo(moon.orbit, 9);
      const [x, y, z] = marsMoonPosition(index, front + moon.period / 2);
      expect(z).toBeLessThan(-MARS_RADIUS);
      expect(Math.hypot(x, y)).toBeLessThan(MARS_RADIUS);
    });
    expect(marsMoonPosition(0, -1)).toEqual(marsMoonPosition(0, 0));
  });

  it("bounds framebuffer size and DPR", () => {
    expect(marsRenderSize(393, 852, 3)).toEqual({ width: 393, height: 852, dpr: 1.5 });
    expect(marsRenderSize(7680, 4320, 2)).toEqual({ width: 1600, height: 900, dpr: 1.5 });
    expect(marsRenderSize(0, 0, 0)).toEqual({ width: 1, height: 1, dpr: 1 });
  });
});
