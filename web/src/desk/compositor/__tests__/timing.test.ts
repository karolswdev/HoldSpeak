// PHILO-16 (L6): one timing.
import { describe, expect, it } from "vitest";
import { BASE_MS, EASE, timing } from "../timing";

describe("timing", () => {
  it("the four moments keep their base durations and one easing", () => {
    expect(timing("raise")).toEqual({ duration: 180, easing: EASE });
    expect(timing("open").duration).toBe(240);
    expect(timing("seat").duration).toBe(200);
    expect(timing("arrange").duration).toBe(220);
    expect(EASE).toBe("cubic-bezier(.2,.8,.2,1)");
  });

  it("the duration scales with the distance, clamped to 120-360 ms", () => {
    const near = timing("arrange", { distance: 0 }).duration;
    const mid = timing("arrange", { distance: 400 }).duration;
    const far = timing("arrange", { distance: 4000 }).duration;
    expect(near).toBeLessThan(mid);
    expect(mid).toBe(BASE_MS.arrange);
    expect(far).toBe(360);
    expect(timing("raise", { distance: 0 }).duration).toBeGreaterThanOrEqual(120);
  });

  it("a box that leaves sight does not animate (seenOnly)", () => {
    expect(timing("arrange", { distance: 300, leaving: true }).duration).toBe(0);
  });

  it("tempo multiplies the speed within 0.5-2", () => {
    expect(timing("arrange", { tempo: 2 }).duration).toBe(120);
    expect(timing("arrange", { tempo: 0.5 }).duration).toBe(360);
    expect(timing("arrange", { tempo: 9 }).duration).toBe(timing("arrange", { tempo: 2 }).duration);
  });

  it("reduced motion makes every moment instant", () => {
    for (const k of ["raise", "open", "seat", "arrange"] as const)
      expect(timing(k, { reducedMotion: true, distance: 500 }).duration).toBe(0);
  });
});
