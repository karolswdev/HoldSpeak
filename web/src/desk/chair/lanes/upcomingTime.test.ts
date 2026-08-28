import { describe, expect, it } from "vitest";
import { upcomingTimeLabel } from "./upcomingTime";

const now = new Date("2026-08-27T10:00:00Z");

describe("upcomingTimeLabel", () => {
  it("keeps the Phase-136 under-a-day relative grammar", () => {
    expect(upcomingTimeLabel("2026-08-27T11:42:00Z", now)).toBe("in 1h 42m");
    expect(upcomingTimeLabel("2026-08-27T10:08:00Z", now)).toBe("in 8m");
  });

  it("uses the existing compact local absolute grammar thereafter", () => {
    expect(upcomingTimeLabel("2026-08-29T14:05:00Z", now)).toMatch(/^AUG 29 \d{2}:05$/);
  });

  it("does not invent a time fact for absent or invalid input", () => {
    expect(upcomingTimeLabel(null, now)).toBe("");
    expect(upcomingTimeLabel("not-a-time", now)).toBe("");
  });
});
