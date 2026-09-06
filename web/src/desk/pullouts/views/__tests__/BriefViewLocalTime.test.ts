import { describe, expect, it } from "vitest";
import { dayToken, generatedLabelLocal, parseLocal, periodLabelLocal, sinceFridayLabel } from "../BriefView";

// HS-175 counsel C8: the brief's clocks print in the VIEWER's zone.
// Expectations are computed with Date so they hold in any zone the suite
// runs in; the west-of-UTC cases are what the owner (-06:00) sees.
const pad = (n: number) => String(n).padStart(2, "0");
const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

describe("parseLocal", () => {
  it("reads a bare YYYY-MM-DD as a local calendar day, not UTC midnight", () => {
    const d = parseLocal("2026-09-04")!;
    expect([d.getFullYear(), d.getMonth(), d.getDate()]).toEqual([2026, 8, 4]);
    expect(dayToken("2026-09-04")).toBe("FRI");
  });
  it("reads an instant with an offset", () => {
    const d = parseLocal("2026-09-05T23:47:00Z")!;
    expect(d.getTime()).toBe(Date.UTC(2026, 8, 5, 23, 47));
  });
  it("is null for nothing", () => {
    expect(parseLocal(null)).toBeNull();
    expect(parseLocal("nope")).toBeNull();
  });
});

describe("generatedLabelLocal / periodLabelLocal", () => {
  it("prints GENERATED in the viewer's local clock", () => {
    const iso = "2026-09-05T14:00:00Z";
    const d = new Date(iso);
    expect(generatedLabelLocal(iso)).toBe(`GENERATED ${MONTHS[d.getMonth()]} ${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`);
  });
  it("spans the local Monday of the week through the generated day", () => {
    // Friday 2026-09-04 local
    expect(periodLabelLocal("2026-09-04T08:00:00")).toBe("AUG 31 - SEP 04");
    expect(periodLabelLocal("2026-09-09T08:00:00")).toBe("SEP 07-09");
  });
  it("is null with no generated_at", () => {
    expect(generatedLabelLocal(undefined)).toBeNull();
    expect(periodLabelLocal(undefined)).toBeNull();
  });
});

describe("sinceFridayLabel", () => {
  it("names the local lookback start day", () => {
    expect(sinceFridayLabel("2026-09-04")).toBe("SINCE FRIDAY");
    expect(sinceFridayLabel("2026-09-03T00:00:00")).toBe("SINCE THURSDAY");
    expect(sinceFridayLabel(undefined)).toBe("SINCE FRIDAY");
  });
});
