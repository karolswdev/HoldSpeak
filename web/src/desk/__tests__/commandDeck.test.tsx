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
    // Keep the opener double, but retain the canonical recent-open receipt
    // that a real opener writes at its successful seam.
    openPullout: vi.fn((id: string) => useDesk.getState().recordRecentOpen(id)),
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
    name: "Find, open or ask",
  });
}

beforeEach(seed);

/** PHILO-17 (palette-rank): the list draws once its ranking inputs (the
 *  needs-you and people reads) resolve, or at its cap. */
const drawn = () => screen.findByRole("listbox", {}, { timeout: 2000 });

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
  it("Enter runs the TOP hit — the palette dead-end is gone", async () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "meet the team" } });
    await drawn();
    // The top hit is the prefix match on the note's title.
    const top = screen.getByRole("option", { name: /Meet the team/ });
    expect(top.className).toContain("is-selected");
    fireEvent.keyDown(deck, { key: "Enter" });
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:n1");
    // The run lands in the desk store's canonical recent-open list.
    expect(useDesk.getState().recentOpened).toContain("note:n1");
  });

  // DELIGHT 2 (small joys): ⌘K's first result is the thing he opened last.
  it("with the field empty, the first row is the last thing opened, and Enter opens it again", async () => {
    useDesk.getState().recordRecentOpen("note:n2");
    useDesk.getState().recordRecentOpen("meeting:m1");
    useDesk.getState().recordRecentOpen("note:n1");
    const deck = open();
    await drawn();
    const options = screen.getAllByRole("option");
    expect(options[0].textContent).toContain("Meet the team");
    expect(options[0].className).toContain("is-selected");
    fireEvent.keyDown(deck, { key: "Enter" });
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:n1");
  });

  it("ArrowDown moves the selection index; Enter runs the moved hit", async () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "met" } });
    await drawn();
    const first = screen.getByRole("option", { selected: true }).id;
    fireEvent.keyDown(deck, { key: "ArrowDown" });
    const moved = screen.getByRole("option", { selected: true }).id;
    expect(moved).not.toBe(first);
    fireEvent.keyDown(deck, { key: "Enter" });
    // The current launcher can rank a program before an object. A run is
    // therefore proved by its shared receipt rather than a stale pullout path.
    expect(usePalette.getState().open).toBe(false);
    expect(useDesk.getState().recentOpened).toContain(moved.replace("desk-palette-option-", ""));
  });

  it("meetings sit in their own sentence-case Meeting band", async () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "launch" } });
    await drawn();
    expect(screen.getByText("Meeting")).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Meeting: launch/ }),
    ).toBeInTheDocument();
  });

  // PHILO-13-14 (C4): one Escape closes the deck, also with a query typed
  // (the two-press ladder is gone; the query goes with the deck).
  it("one Escape closes the deck, also with a query typed", () => {
    const deck = open();
    fireEvent.change(deck, { target: { value: "meet" } });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(usePalette.getState().open).toBe(false);
  });

  it("the empty deck lists every program (the launcher truth)", async () => {
    open();
    await drawn();
    expect(screen.getAllByText("App").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("option", { name: /Automations/ }),
    ).toBeInTheDocument();
    // Betterment shell S1: Processes is a builder tool, listed only when
    // Builder tools is on (Settings ▸ System).
    expect(screen.queryByRole("option", { name: /Processes/ })).toBeNull();
  });

  // Betterment A1: "automation" and "automations" find the Automations
  // program, and the program comes before the automations of that kind.
  it.each(["automation", "automations", "Automation"])("%s finds the Automations program first", async (query) => {
    useDesk.setState({
      items: {
        ...useDesk.getState().items,
        workbench: [{ kind: "workbench", id: "wb1", name: "Friday update", title: "Friday update" } as never],
      },
    });
    const deck = open();
    fireEvent.change(deck, { target: { value: query } });
    await drawn();
    const options = screen.getAllByRole("option").map((o) => o.textContent ?? "");
    const program = options.findIndex((t) => /Automations/.test(t) && /App/.test(t));
    const object = options.findIndex((t) => /Friday update/.test(t));
    expect(program, options.join(" / ")).toBe(0);
    expect(object).toBeGreaterThan(program);
  });

  it("the name matches in either number", () => {
    expect(rankRow({ label: "Automations", name: "Automations" }, "automation", false)).toBe(100);
    expect(rankRow({ label: "Automations", name: "Automations" }, "automations", false)).toBe(100);
  });
});
