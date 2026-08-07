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
import { DeskToolShelf, rankRow } from "../components/DeskToolShelf";

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
  return screen.getByRole("textbox", {
    name: "Search tools and Desk items",
  });
}

beforeEach(seed);

describe("ranking", () => {
  it("prefix(3) beats recents(2) beats substring(1)", () => {
    expect(rankRow({ label: "Meetings" }, "meet", false)).toBe(3);
    expect(rankRow({ label: "Team meet" }, "meet", true)).toBe(2);
    expect(rankRow({ label: "Team meet" }, "meet", false)).toBe(1);
    expect(rankRow({ label: "Settings" }, "meet", false)).toBe(0);
  });
});

describe("the deck", () => {
  it("Enter runs the TOP hit — the palette dead-end is gone", () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "meet the team" } });
    // The top hit is the prefix match on the note's title.
    const top = screen.getByRole("button", { name: /Meet the team/ });
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
    fireEvent.keyDown(deck, { key: "ArrowDown" });
    fireEvent.keyDown(deck, { key: "Enter" });
    expect(useDesk.getState().openPullout).toHaveBeenCalled();
  });

  it("meetings sit in their own MEETINGS band", () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "launch" } });
    expect(screen.getByText("MEETINGS")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Meeting: launch/ }),
    ).toBeInTheDocument();
  });

  it("Escape clears the query first, closes second", () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "meet" } });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(
      screen.getByRole("textbox", { name: "Search tools and Desk items" }),
    ).toHaveValue("");
    fireEvent.keyDown(document, { key: "Escape" });
    expect(usePalette.getState().open).toBe(false);
  });

  it("the empty deck lists every program (the launcher truth)", () => {
    open();
    expect(screen.getByText("PROGRAMS")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Workbenches/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Processes/ }),
    ).toBeInTheDocument();
  });
});
