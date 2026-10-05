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

  it("shortens a home path with no target to read", () => {
    expect(shownPath("/Users/karol/Documents/a.md")).toBe("~/Documents/a.md");
    expect(shownPath("/home/karol/Documents/a.md")).toBe("~/Documents/a.md");
    expect(shownPath("/Users/karolx")).toBe("~");
  });
});
