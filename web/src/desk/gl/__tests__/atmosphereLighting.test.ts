import { describe, expect, it } from "vitest";
import { captureLightBoost } from "../atmosphereLighting";

const idle = { recording: false, speaking: false, level: 0, arrival: 0 };

describe("outdoor atmosphere capture light", () => {
  it("does not invent capture from time, arrivals, or stray level samples", () => {
    expect(captureLightBoost()).toBe(1);
    expect(captureLightBoost({ ...idle, arrival: 8, level: 1 })).toBe(1);
  });
  it("gives either real capture source a restrained warm lift", () => {
    expect(captureLightBoost({ ...idle, recording: true })).toBeCloseTo(1.12);
    expect(
      captureLightBoost({ ...idle, speaking: true, level: 0.5 }),
    ).toBeCloseTo(1.17);
    expect(captureLightBoost(idle)).toBe(1);
  });
  it("bounds invalid or excessive levels", () => {
    for (const level of [NaN, Infinity, -2]) {
      expect(
        captureLightBoost({ ...idle, recording: true, level }),
      ).toBeCloseTo(1.12);
    }
    expect(
      captureLightBoost({ ...idle, recording: true, level: 10 }),
    ).toBeCloseTo(1.22);
  });
});
