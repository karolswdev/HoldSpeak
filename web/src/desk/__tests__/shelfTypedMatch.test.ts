/* HS-202-02 job 4 — ⌘K commits the TYPED match.
 *
 * 03-interaction-walk.md finding 6: "Two of the five owner jobs cannot be
 * started by keyboard. ⌘K's Enter commits the highlighted row, not the
 * typed match: `Notes` opens `Telegram control` @393 and `Change places`
 * @1440; `Thoughts` opens `Intelligence`."
 *
 * The cause is in the scorer, not the key handler: the deck is already
 * ordered by score, but `fuzzyScore` has no singular/plural fold, so the
 * word a person types ("Notes", "Thoughts", "Meetings") scores ZERO
 * against the row that carries it ("New Note", "New Thought"), and the
 * highlighted row is whatever loose subsequence survived instead.
 */
import { describe, expect, it } from "vitest";
import { fuzzyScore, rankRow } from "../components/DeskToolShelf";

describe("the typed word finds the row that carries it", () => {
  it("scores the plural a person types against the singular row", () => {
    expect(fuzzyScore("notes", "New Note")).toBeGreaterThanOrEqual(60);
    expect(fuzzyScore("thoughts", "New Thought")).toBeGreaterThanOrEqual(60);
    expect(fuzzyScore("note", "Note")).toBe(100);
    expect(fuzzyScore("notes", "Note")).toBeGreaterThanOrEqual(80);
  });

  it("beats the loose subsequence it used to lose to", () => {
    expect(fuzzyScore("notes", "New Note")).toBeGreaterThan(
      fuzzyScore("notes", "Telegram control"),
    );
    expect(fuzzyScore("thoughts", "New Thought")).toBeGreaterThan(
      fuzzyScore("thoughts", "Intelligence"),
    );
  });

  it("does not invent a match where there is none", () => {
    expect(fuzzyScore("notes", "Settings")).toBe(0);
    expect(fuzzyScore("s", "Meetings")).toBeLessThan(60);
  });

  it("keeps the ranks the deck already proved", () => {
    expect(fuzzyScore("meetings", "Meetings")).toBe(100);
    expect(fuzzyScore("meet", "Meetings")).toBe(80);
    expect(fuzzyScore("meet", "Team meetings")).toBe(60);
    expect(fuzzyScore("mgs", "Meetings")).toBe(30);
    expect(fuzzyScore("meet", "Settings")).toBe(0);
    expect(rankRow({ label: "Meetings" }, "meet", false)).toBe(80);
    expect(rankRow({ label: "Team meetings" }, "meet", true)).toBe(70);
  });
});

/* HS-202-02 arrival item — ⌘K's `Ask AI` row and the Go menu's are one
 * door. 03-interaction-walk.md finding 8: "⌘K's `Ask AI` row is
 * permanently disabled (`aria-disabled="true"`, `desk-deck-row is-ghost`)
 * while the Go menu's `Ask AI` opens it. Two doors to the same thing, one
 * dead." Both rows reach ⌘K: the object-scoped verb (ghosted with its
 * reason whenever nothing is selected) and the live PROGRAM launcher. */
describe("the palette shows one door per name", () => {
  it("drops a ghost whose name a live row already carries", async () => {
    const { oneDoorPerName } = await import("../components/DeskToolShelf");
    const rows = oneDoorPerName([
      { id: "object.ask", label: "Ask AI", ghost: "Select an object" },
      { id: "go.ask", label: "Ask AI" },
      { id: "object.rename", label: "Rename", ghost: "Select an object" },
    ]);
    expect(rows.map((row) => row.id)).toEqual(["go.ask", "object.rename"]);
  });
});
