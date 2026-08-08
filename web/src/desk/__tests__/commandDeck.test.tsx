/** HS-111-07 — the command deck (owner P0): Enter ALWAYS runs the
 * selected hit (the top hit by default), selection is an index (not
 * DOM focus), ranking is prefix > recents > substring, rows sit in
 * registry-fed section bands. */
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../api";
import type { Note, Meeting } from "../../lib/primitives";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import {
  DeskToolShelf,
  fuzzyScore,
  rankRow,
} from "../components/DeskToolShelf";

function seed() {
  localStorage.clear();
  usePalette.setState({ open: false });
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      note: [
        { kind: "note", id: "n1", title: "Meet the team" } as Note,
        { kind: "note", id: "n2", title: "Retro: we met" } as Note,
      ],
      meeting: [{ kind: "meeting", id: "m1", title: "Meeting: launch" } as Meeting],
    },
    projects: [],
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    openPullout: vi.fn(),
    openToolInspector: vi.fn(),
    openChat: vi.fn(),
    diveInto: vi.fn(),
  });
}

function open() {
  render(
    <MemoryRouter>
      <DeskToolShelf />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("button", { name: /Search/ }));
  return screen.getByRole("combobox", {
    name: "Search tools and Desk items",
  });
}

beforeEach(seed);

describe("ranking", () => {
  it("scores exact, prefix, word-boundary, and ordered fuzzy matches", () => {
    expect(fuzzyScore("meetings", "Meetings")).toBe(100);
    expect(fuzzyScore("meet", "Meetings")).toBe(80);
    expect(fuzzyScore("meet", "Team meetings")).toBe(60);
    expect(fuzzyScore("mgs", "Meetings")).toBe(30);
    expect(fuzzyScore("meet", "Settings")).toBe(0);
  });

  it("applies recency after fuzzy relevance", () => {
    expect(rankRow({ label: "Meetings" }, "meet", false)).toBe(80);
    expect(rankRow({ label: "Team meetings" }, "meet", true)).toBe(70);
  });
});

describe("the deck", () => {
  it("Enter runs the TOP hit — the palette dead-end is gone", () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "meet the team" } });
    // The top hit is the prefix match on the note's title.
    const top = screen.getByRole("option", { name: /Meet the team/ });
    expect(top.className).toContain("is-selected");
    fireEvent.keyDown(deck, { key: "Enter" });
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:n1");
    // The run lands in recents (localStorage, last 20 ids).
    expect(
      JSON.parse(localStorage.getItem("hs.desk.palette-recents") || "[]"),
    ).toContain("note:n1");
  });

  it("ArrowDown moves the selection index; Enter runs the moved hit", () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "met" } });
    const first = screen.getByRole("option", { selected: true }).id;
    fireEvent.keyDown(deck, { key: "ArrowDown" });
    const moved = screen.getByRole("option", { selected: true }).id;
    expect(moved).not.toBe(first);
    fireEvent.keyDown(deck, { key: "Enter" });
    // The current launcher can rank a program before an object. A run is
    // therefore proved by its shared receipt rather than a stale pullout path.
    expect(usePalette.getState().open).toBe(false);
    expect(JSON.parse(localStorage.getItem("hs.desk.palette-recents") || "[]"))
      .toContain(moved.replace("desk-palette-option-", ""));
  });

  it("meetings sit in their own MEETINGS band", () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "launch" } });
    expect(screen.getByText("MEETINGS")).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Meeting: launch/ }),
    ).toBeInTheDocument();
  });

  it("Escape clears the query first, closes second", () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "meet" } });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(
      screen.getByRole("combobox", { name: "Search tools and Desk items" }),
    ).toHaveValue("");
    fireEvent.keyDown(document, { key: "Escape" });
    expect(usePalette.getState().open).toBe(false);
  });

  it("the empty deck lists every program (the launcher truth)", () => {
    open();
    expect(screen.getByText("PROGRAMS")).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Workbenches/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Processes/ }),
    ).toBeInTheDocument();
  });
});
