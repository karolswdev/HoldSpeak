import { describe, expect, it } from "vitest";
import { computeStreak, localDayKey } from "../src/server/streaks";

// QL-322 regression coverage: streak math must use the USER's local
// timezone, not server UTC. A completion at 11pm local on the US west
// coast is 7am UTC the NEXT day — UTC math would mis-bucket it.

describe("localDayKey", () => {
  it("buckets a late-night PST completion to the local day, not the UTC day", () => {
    // 2026-03-09T06:30:00Z == 2026-03-08 22:30 in America/Los_Angeles
    const instant = new Date("2026-03-09T06:30:00Z");
    expect(localDayKey(instant, "America/Los_Angeles")).toBe("2026-03-08");
    expect(localDayKey(instant, "UTC")).toBe("2026-03-09");
  });

  it("buckets an early-morning Tokyo completion to the local day", () => {
    // 2026-03-08T16:00:00Z == 2026-03-09 01:00 in Asia/Tokyo
    const instant = new Date("2026-03-08T16:00:00Z");
    expect(localDayKey(instant, "Asia/Tokyo")).toBe("2026-03-09");
  });
});

describe("computeStreak", () => {
  const at = (iso: string, timezone: string) => ({
    completedAt: new Date(iso),
    timezone,
  });

  it("counts consecutive local days as a streak", () => {
    const tz = "America/Los_Angeles";
    const result = computeStreak([
      at("2026-03-07T20:00:00Z", tz), // Mar 7 local
      at("2026-03-08T20:00:00Z", tz), // Mar 8 local
      at("2026-03-09T20:00:00Z", tz), // Mar 9 local
    ]);
    expect(result.current).toBe(3);
    expect(result.longest).toBe(3);
  });

  it("does NOT break a streak across the DST spring-forward (QL-322)", () => {
    // US DST begins 2026-03-08. Two completions on consecutive LOCAL days
    // straddling the change must remain a 2-day streak.
    const tz = "America/Los_Angeles";
    const result = computeStreak([
      at("2026-03-08T05:00:00Z", tz), // Mar 7 local (before spring-forward)
      at("2026-03-09T05:00:00Z", tz), // Mar 8 local (after spring-forward)
    ]);
    expect(result.current).toBe(2);
  });

  it("resets to 1 after a genuine missed local day", () => {
    const tz = "UTC";
    const result = computeStreak([
      at("2026-03-01T10:00:00Z", tz),
      at("2026-03-02T10:00:00Z", tz),
      at("2026-03-05T10:00:00Z", tz), // gap of 3 days
    ]);
    expect(result.current).toBe(1);
    expect(result.longest).toBe(2);
  });
});
