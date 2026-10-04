// The ONE parse of a wire time (inventory A defect 3, 2026-10-03): the
// owner is in America/Denver and three faces printed UTC. vitest runs in
// the zone the process has, so this file pins it.
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { humanTime, wireClock, wireDate } from "../format";

const previous = process.env.TZ;
beforeAll(() => {
  process.env.TZ = "America/Denver";
});
afterAll(() => {
  if (previous === undefined) delete process.env.TZ;
  else process.env.TZ = previous;
});

describe("wireDate", () => {
  it("reads a UTC ISO stamp and prints the local clock", () => {
    // Rhythm: the hub stamped 03:06 UTC; it is 21:06 in Denver.
    expect(wireClock("2026-10-04T03:06:10+00:00")).toBe("21:06");
    expect(wireClock("2026-10-04T03:06:10Z", true)).toBe("21:06:10");
  });

  it("reads a bare SQLite stamp as UTC", () => {
    expect(wireDate("2026-10-04 03:06:10")?.toISOString()).toBe("2026-10-04T03:06:10.000Z");
    expect(wireClock("2026-10-04 03:06:10")).toBe("21:06");
  });

  it("reads a bare ISO stamp as the hub's local wall time", () => {
    expect(wireClock("2026-10-03T21:32:00")).toBe("21:32");
  });

  it("reads a bare date as that local day", () => {
    const day = wireDate("2026-10-06");
    expect(day?.getDate()).toBe(6);
    expect(day?.getDay()).toBe(2);
  });

  it("reads epoch seconds and epoch milliseconds as the same instant", () => {
    // Processes: epoch seconds read as milliseconds printed a 1970 clock.
    expect(wireClock(1791084068, true)).toBe("21:21:08");
    expect(wireClock(1791084068000, true)).toBe("21:21:08");
  });

  it("refuses junk", () => {
    expect(wireDate("soon")).toBeNull();
    expect(wireDate("")).toBeNull();
    expect(wireClock(null)).toBe("");
  });

  it("humanTime measures a bare SQLite stamp from UTC", () => {
    const stamp = new Date(Date.now() - 5 * 60_000).toISOString().slice(0, 19).replace("T", " ");
    expect(humanTime(stamp)).toBe("5m ago");
  });
});
