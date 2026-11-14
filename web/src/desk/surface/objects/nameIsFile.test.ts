import { describe, expect, it } from "vitest";
import { nameIsFile } from "./fitName";

describe("nameIsFile: path/code recognition for fitting and the initials fallback", () => {
  it.each([
    "web/src/pages/cores/PeopleCore.tsx: keep the selected person",
    "~/notes/plan.md",
    "meeting_followthrough_revision",
    "node.js upgrade",
    "RoomList.tsx: the facts",
    "`quick_check` is slow",
    "C:\\Users\\k\\plan.txt",
  ])("a file: %s", (name) => expect(nameIsFile(name)).toBe(true));

  it.each(["J.R. Smith", "St.John Parker", "Priya Nair", "Dr. Okafor", "v2. The second plan", "Payments ledger cutover"])(
    "not a file: %s",
    (name) => expect(nameIsFile(name)).toBe(false),
  );
});

import { fitName } from "./fitName";

describe("fitName: a very long name is cut with few measures", () => {
  it("a 4,000-character unbroken name takes under 100 measures, in both cuts", () => {
    const name = "x".repeat(4000);
    for (const cut of ["middle", "end"] as const) {
      let measures = 0;
      const fits = (line: string) => { measures++; return line.length <= 40; };
      const out = fitName(name, 40, 1, fits, cut);
      expect(out).toHaveLength(1);
      expect(out[0].length).toBeLessThanOrEqual(40);
      expect(out[0]).toContain("…");
      expect(measures).toBeLessThan(100);
    }
  });

  it("the halving finds the same cut as trying every length", () => {
    const fits = (line: string) => line.length <= 24;
    expect(fitName("Payments ledger cutover for the platform team v2", 24, 1, fits)[0]).toBe("Payments ledger cuto… v2");
    expect(fitName("relationship_platformarchitecturedecision", 24, 1, fits)[0].length).toBeLessThanOrEqual(24);
  });
});
