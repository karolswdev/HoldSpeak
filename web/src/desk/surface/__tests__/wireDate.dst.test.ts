// The repeated hour (2026-11-01 01:30 America/Denver happens twice). A bare
// local stamp written now must read "just now" from either 01:30; before the
// fix the second 01:30 read it as the first and said "1h ago" (the bell's
// "a bare local ISO stamp reads just now" failed for that hour). The zone is
// pinned at module top, as bell.app.test.tsx pins it.
process.env.TZ = "America/Denver";

import { afterEach, describe, expect, it, vi } from "vitest";
import { humanTime, wireClock, wireDate } from "../format";

afterEach(() => vi.useRealTimers());

const FIRST = Date.UTC(2026, 10, 1, 7, 30);   // 01:30 MDT
const SECOND = Date.UTC(2026, 10, 1, 8, 30);  // 01:30 MST

describe("a bare local stamp in the repeated hour", () => {
  it.each([["the first 01:30", FIRST], ["the second 01:30", SECOND]])("written at %s reads just now", (_, now) => {
    vi.useFakeTimers();
    vi.setSystemTime(now);
    expect(wireDate("2026-11-01T01:30:00")!.getTime()).toBe(now);
    expect(humanTime("2026-11-01T01:30:00")).toBe("just now");
    expect(wireClock("2026-11-01T01:30:00")).toBe("01:30");
  });

  it("a stamp with its offset is exact either way; a time outside the repeated hour is unchanged", () => {
    vi.useFakeTimers();
    vi.setSystemTime(SECOND);
    expect(wireDate("2026-11-01T01:30:00-06:00")!.getTime()).toBe(FIRST);
    expect(humanTime("2026-11-01T01:30:00-06:00")).toBe("1h ago");
    expect(wireDate("2026-11-01T00:30:00")!.getTime()).toBe(Date.UTC(2026, 10, 1, 6, 30));
    expect(wireDate("2026-10-31T13:00:00")!.getTime()).toBe(Date.UTC(2026, 9, 31, 19, 0));
  });
});

describe("Settings' Saved stamp (a writer's HH:MM:SS) in the repeated hour", () => {
  it.each([["the first 01:30", FIRST], ["the second 01:30", SECOND]])("saved at %s says Saved just now", async (_, now) => {
    vi.useFakeTimers();
    vi.setSystemTime(now);
    const { sinceWord, stampDate } = await import("../../../pages/cores/settingsWindow");
    expect(sinceWord(stampDate("01:30:00")!)).toBe("just now");
  });
});
