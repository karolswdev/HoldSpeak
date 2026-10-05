// STATUS: "Raw paths ... on some faces (SEND well ...)". A SAVED receipt
// shows the file under its destination's short token (the home folder as ~);
// the stored proof stays exact.
import { describe, expect, it } from "vitest";
import { shownPath } from "../SendWell";

describe("a SAVED receipt's path", () => {
  it("leads with the destination's short token under its folder", () => {
    const target = { folder: "/Users/karol/Documents/HoldSpeak/Team updates", display: "~/Documents/HoldSpeak/Team updates" };
    expect(shownPath("/Users/karol/Documents/HoldSpeak/Team updates/2026-10-05-ledger.md", target))
      .toBe("~/Documents/HoldSpeak/Team updates/2026-10-05-ledger.md");
  });

  it("keeps a path outside the home folder whole", () => {
    const target = { folder: "/Volumes/Team/Reports", display: "/Volumes/Team/Reports" };
    expect(shownPath("/Volumes/Team/Reports/a.md", target)).toBe("/Volumes/Team/Reports/a.md");
  });

  it("never guesses HOME from a pattern: other people's folders stay whole (Astra, #869)", () => {
    expect(shownPath("/Users/alice/Reports/weekly.md")).toBe("/Users/alice/Reports/weekly.md");
    expect(shownPath("/Users/bob/Reports/weekly.md")).toBe("/Users/bob/Reports/weekly.md");
    expect(shownPath("/home/alice/Reports/weekly.md")).toBe("/home/alice/Reports/weekly.md");
    // alice's folder is not bob's HOME: only the hub's token for THIS folder shortens.
    const bobs = { folder: "/Users/bob/Reports", display: "~/Reports" };
    expect(shownPath("/Users/alice/Reports/weekly.md", bobs)).toBe("/Users/alice/Reports/weekly.md");
    expect(shownPath("/Users/bob/Reports/weekly.md", bobs)).toBe("~/Reports/weekly.md");
  });
});
