import { describe, expect, it } from "vitest";
import { nameIsFile } from "./fitName";

describe("nameIsFile: the one rule for a name that wears the file object", () => {
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
