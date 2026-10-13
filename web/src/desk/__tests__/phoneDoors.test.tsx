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
import { fireEvent, render, screen } from "@testing-library/react";
import { DeskMenuBar } from "../components/DeskMenuBar";

describe("the phone menu bar has one door that carries every verb", () => {
  let compact = true;

  beforeEach(() => {
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

  it("keeps all four menus at desk width", () => {
    compact = false;
    const { container } = render(<DeskMenuBar />);
    const ids = Array.from(
      container.querySelectorAll("[data-menu-id]"),
      (el) => el.getAttribute("data-menu-id"),
    );
    expect(ids).toEqual(["desk", "object", "go", "window"]);
  });

  // PHILO-15 11 (B21, owner ruling 2026-10-07; supersedes C7 Q3): Go at 393
  // is Needs you / Brief / The week / Capture, the Dock's places, the
  // projects, then New ▸ Thought / Meeting / Project / Person. No ⌘ hint.
  it("carries a new thought (owner job 3's door) at Go ▸ New ▸ Thought at phone width", () => {
    compact = true;
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: "Go" }), { detail: 0 });
    fireEvent.click(screen.getByRole("menuitem", { name: /^New\W*$/ }));
    expect(
      screen.getAllByRole("menuitem").map((el) => el.querySelector(".desk-menu-label")?.textContent)
        .slice(-4),
    ).toEqual(["Thought", "Meeting", "Project", "Person"]);
  });
});
