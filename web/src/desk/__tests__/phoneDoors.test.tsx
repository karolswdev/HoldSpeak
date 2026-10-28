/* HS-202-02 — the phone width has doors.
 *
 * The surface inventory (docs/internal/surface-inventory-2026-09-20/
 * 03-interaction-walk.md, findings 1 and 2) measured the 393 width with no
 * door at all:
 *
 *   1. the dock is laid out at desktop width inside a 393px viewport —
 *      `Overview` at x=1313, `Reset layout` at x=1343 — and all eleven of
 *      its buttons refused a press for the whole run. Two causes: the row
 *      never wraps, and at phone width the dock is demoted below the
 *      sheets that cover it (`--desk-z-dock-under` = 40 against a window
 *      base of 42).
 *   2. `Desk`, `Object` and `Window` are rendered into the DOM at 393 and
 *      then hidden by CSS, so every `New …` verb — `New Note` among them,
 *      the door to owner job 3 — is unreachable at phone width. The CSS
 *      comment already claims the design: "Go is the app door at phone
 *      width". This pins that claim: at phone width those three menus are
 *      not rendered at all, and Go carries their verbs.
 *
 * The dock's phone layout is proven by the desk sweep at 393
 * (tests/e2e/test_desk_sweep.py). The menu fold is a DOM fact and is rendered.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeskMenuBar } from "../components/DeskMenuBar";
import { GoHome } from "../screen/GoHome";
import { useDesk } from "../store";
import { EMPTY_ITEMS } from "../api";
import { VERBS } from "../verbRegistry";
import * as shell from "../shell";

describe("the phone menu bar has one door that carries every verb", () => {
  let compact = true;
  let saved: Pick<ReturnType<typeof useDesk.getState>, "items" | "projects" | "selectedIds">;

  beforeEach(() => {
    const state = useDesk.getState();
    saved = { items: state.items, projects: state.projects, selectedIds: state.selectedIds };
    useDesk.setState({ items: { ...EMPTY_ITEMS }, projects: [], selectedIds: [] });
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: compact && query.includes("720px"),
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      onchange: null,
      dispatchEvent: () => false,
    }));
  });
  afterEach(() => {
    cleanup();
    useDesk.setState(saved);
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders only Go at phone width — nothing announced it cannot open", () => {
    compact = true;
    const { container } = render(<DeskMenuBar />);
    const ids = Array.from(
      container.querySelectorAll("[data-menu-id]"),
      (el) => el.getAttribute("data-menu-id"),
    );
    expect(ids).toEqual(["go"]);
  });

  // Betterment shell S0: the Object menu is drawn only with a thing in front.
  it("keeps Desk, Go and Window at desk width (Object only with a thing in front)", () => {
    compact = false;
    const { container } = render(<DeskMenuBar />);
    const ids = Array.from(
      container.querySelectorAll("[data-menu-id]"),
      (el) => el.getAttribute("data-menu-id"),
    );
    expect(ids).toEqual(["desk", "go", "window"]);
  });

  // Betterment shell S1 (supersedes PHILO-15 11 B21): Go at 393 is the
  // manifest's Go groups, then the seven shared New kinds. No ⌘ hint.
  it("carries a new note (owner job 3's door) at Go ▸ New ▸ Note at phone width", () => {
    compact = true;
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: "Go" }), { detail: 0 });
    fireEvent.click(screen.getByRole("menuitem", { name: /^New\W*$/ }));
    expect(
      screen.getAllByRole("menuitem").map((el) => el.querySelector(".desk-menu-label")?.textContent)
        .slice(-7),
    ).toEqual(["Note", "Meeting", "Decision", "Project", "Person", "Automation", "Drawer"]);
  });

  it("renders the same phoneGo rows on the phone home face", () => {
    compact = true;
    render(<GoHome />);
    expect(screen.getByRole("menuitem", { name: "Meetings" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: "Ask AI" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: "Note" })).toBeTruthy();
    // Betterment shell S1: the manifest's Go groups, as at 1440, then New.
    // Betterment P4: Projects is drawn on an empty desk too (All projects).
    expect(screen.getAllByRole("heading").map((heading) => heading.textContent)).toEqual(["Apps", "Projects", "Work", "New"]);
    expect(screen.getByRole("menu", { name: "Go menu" })).toHaveClass("desk-menu-list");
    expect(screen.getAllByRole("menuitem").map((row) => row.querySelector(".desk-menu-label")?.textContent)).toEqual([
      "Today", "Needs you", "Capture", "Meetings", "People", "All projects", "Decisions", "Agents", "Ask AI", "Speak",
      "Automations", "Memory", "Calls", "Voice commands", "Archive", "Note", "Meeting", "Decision", "Project", "Person", "Automation", "Drawer",
    ]);
  });

  it.each(["{Enter}", " "])("native %j activates a home verb once with the current selection context", async (key) => {
    compact = true;
    const user = userEvent.setup();
    const verb = VERBS.find((candidate) => candidate.id === "go.ask")!;
    const run = vi.spyOn(verb, "run").mockImplementation(() => {});
    useDesk.setState({ selectedIds: ["note:selected"] });
    render(<GoHome />);
    const row = screen.getByRole("menuitem", { name: "Ask AI" });
    expect(row).toHaveClass("btn--chrome");
    row.focus();
    await user.keyboard(key);
    expect(run).toHaveBeenCalledTimes(1);
    expect(run).toHaveBeenLastCalledWith({ selectedRef: "note:selected" });
    act(() => useDesk.setState({ selectedIds: ["note:first", "note:second"] }));
    await user.keyboard(key);
    expect(run).toHaveBeenCalledTimes(2);
    expect(run).toHaveBeenLastCalledWith({ selectedRef: null });
  });

  // Betterment shell S0 (UX-CANON A.11): a home verb that cannot run is withheld.
  it("withholds a home verb that cannot run", () => {
    compact = true;
    const verb = VERBS.find((candidate) => candidate.id === "go.ask")!;
    vi.spyOn(verb, "ghost").mockReturnValue("Select an object");
    render(<GoHome />);
    expect(screen.queryByRole("menuitem", { name: /Ask AI/ })).toBeNull();
    expect(document.querySelector(".is-ghost,[aria-disabled='true']")).toBeNull();
  });

  it("shows each project under All projects and opens the exact project id", async () => {
    compact = true;
    const user = userEvent.setup();
    const open = vi.spyOn(shell, "openProjectRoom").mockImplementation(() => {});
    useDesk.setState({ projects: [{ id: "p-go-exact", name: "Architecture rollout", description: "", keywords: [], team_members: [], is_archived: false, meeting_count: 0, updated_at: "2026-10-16T00:00:00Z" }] });
    render(<GoHome />);
    expect(screen.getAllByRole("heading").map((heading) => heading.textContent)).toEqual(["Apps", "Projects", "Work", "New"]);
    await user.click(screen.getByRole("menuitem", { name: "Architecture rollout" }));
    expect(open).toHaveBeenCalledOnce();
    expect(open).toHaveBeenCalledWith("p-go-exact");
  });
});
