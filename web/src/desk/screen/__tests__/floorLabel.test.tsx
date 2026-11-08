/** The floor (owner 2026-11-08, 1440 sweep shot): a label wraps on whole
 * words and is cut once at its END; a floor object wears its kind's sprite;
 * the `Program: ` / `Note: ` prefix leaves the label for the sprite and stays
 * in the accessible name. */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { EMPTY_ITEMS } from "../../api";
import { composeScreen } from "../compose";
import { fitName } from "../../surface/objects/fitName";
import { DeskIcon } from "../../surface";

const note = (id: string, title: string) => ({ kind: "note", id, title, bodyMarkdown: "x", tags: [], createdAt: "" });
const items = {
  ...EMPTY_ITEMS,
  note: [
    note("program-p1", "Program: Wave 6 of the atlas"),
    note("n1", "Ledger cutover risks"),
    note("n2", "Note: call the bank"),
  ],
} as never;

function floor() {
  return composeScreen({
    items, projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0, sessions: [], flights: [],
    filed: new Set(), persons: [], membersLoaded: true,
  });
}

describe("the floor label is cut at the end, on whole words", () => {
  it("keeps whole words and puts one ellipsis at the end", () => {
    const lines = fitName("Program review of the hub stalling during overnight waves", 14, 2, undefined, "end");
    expect(lines).toHaveLength(2);
    const text = lines.join(" ");
    expect(text.endsWith("…")).toBe(true);
    expect(text.match(/…/g)).toHaveLength(1);
    // Every word before the ellipsis is whole.
    const source = "Program review of the hub stalling during overnight waves".split(" ");
    for (const word of text.slice(0, -1).split(" ")) expect(source).toContain(word);
  });

  it("a name that fits is untouched; a long single word is cut at its end", () => {
    expect(fitName("Weekly update", 11, 2, undefined, "end")).toEqual(["Weekly", "update"]);
    const set = fitName("Supercalifragilisticexpialidocious", 11, 2, undefined, "end");
    expect(set).toHaveLength(1);
    expect(set[0].startsWith("Supercali")).toBe(true);
    expect(set[0].endsWith("…")).toBe(true);
  });

  it("three lines hold more words than two", () => {
    const name = "The hub stalling after the overnight wave of merges";
    expect(fitName(name, 12, 3, undefined, "end").join(" ").length).toBeGreaterThan(fitName(name, 12, 2, undefined, "end").join(" ").length);
  });
});

describe("a floor object wears its kind", () => {
  it("a Program's note wears the Program sprite and drops the prefix", () => {
    const program = floor().find((o) => o.key === "note:program-p1");
    expect(program).toMatchObject({ name: "Wave 6 of the atlas", ariaName: "Program: Wave 6 of the atlas" });
    expect(program!.sprite).toMatch(/\/program\.png$/);
    expect(program!.spriteSelected).toMatch(/\/program_sel\.png$/);
  });

  it("a note wears the note sprite; a `Note: ` prefix leaves its label", () => {
    const plain = floor().find((o) => o.key === "note:n1");
    expect(plain).toMatchObject({ name: "Ledger cutover risks" });
    expect(plain!.ariaName).toBeUndefined();
    expect(plain!.sprite).toMatch(/\/note\.png$/);
    expect(floor().find((o) => o.key === "note:n2")).toMatchObject({ name: "call the bank", ariaName: "Note: call the bank" });
  });

  it("the screen reader hears the kind the label leaves out", () => {
    render(<DeskIcon id="note:program-p1" kind="note" name="Wave 6 of the atlas" ariaName="Program: Wave 6 of the atlas" labelCut="end" />);
    expect(screen.getByRole("button", { name: "Program: Wave 6 of the atlas" })).toBeTruthy();
    expect(screen.getByTitle("Wave 6 of the atlas").textContent).toBe("Wave 6 of the atlas");
  });
});
