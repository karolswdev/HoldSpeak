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
 * jsdom cannot evaluate a media query against a real layout, so the dock
 * rules are read from the stylesheet source — the house pattern from
 * `footSlot.test.tsx`. The menu fold is a DOM fact and is rendered.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import dockCss from "../components/dock.css?raw";
import chromeMenusCss from "../components/chrome-menus.css?raw";
import { DeskMenuBar } from "../components/DeskMenuBar";

/** The body of the LAST `@media (max-width: 720px)` block in a stylesheet
 *  that declares one — the phone block. Brace-counted, not regex-guessed. */
function phoneBlock(css: string): string {
  const at = css.lastIndexOf("@media (max-width: 720px)");
  expect(at, "the stylesheet declares a 720px phone block").toBeGreaterThan(-1);
  const start = css.indexOf("{", at);
  let depth = 0;
  for (let i = start; i < css.length; i += 1) {
    if (css[i] === "{") depth += 1;
    else if (css[i] === "}") {
      depth -= 1;
      if (depth === 0) return css.slice(start + 1, i);
    }
  }
  throw new Error("unbalanced phone block");
}

/** One rule body by selector, inside a block. */
function rule(block: string, selector: string): string {
  const at = block.indexOf(selector);
  expect(at, `${selector} is declared in the phone block`).toBeGreaterThan(-1);
  const start = block.indexOf("{", at);
  const end = block.indexOf("}", start);
  return block.slice(start + 1, end);
}

describe("the dock lays out for the phone (HS-202-02)", () => {
  const block = phoneBlock(dockCss);
  const dock = rule(block, ".desk-next .desk-dock {");

  // PHILO-13-11 (C1, R2; owner-ratified 2026-10-02): the phone shelf is ONE
  // 56 px row so a window keeps ≥ 700 px of content; a full shelf scrolls
  // INSIDE itself (the Dock is the one strip allowed to). It still never
  // runs past the viewport's edge: pinned to both sides, no max width.
  it("stays inside the viewport: one 56 px row that scrolls inside itself", () => {
    expect(dock).toMatch(/left:\s*0/);
    expect(dock).toMatch(/right:\s*0/);
    expect(dock).toMatch(/max-width:\s*none/);
    expect(dock).toMatch(/flex-wrap:\s*nowrap/);
    expect(dock).toMatch(/height:\s*calc\(56px/);
    expect(dock).toMatch(/overflow-x:\s*auto/);
  });

  it("keeps the shell layer, so a sheet no longer buries every button", () => {
    expect(dock).toMatch(/z-index:\s*var\(--desk-z-dock\)/);
    expect(dock).not.toMatch(/--desk-z-dock-under/);
  });

  it("reserves its own height under every sheet", () => {
    const sheet = rule(block, ".desk-next .desk-window-shell.is-sheet {");
    expect(sheet).toMatch(/bottom:\s*var\(--desk-dock-h/);
  });

  it("gives every dock verb a real target at phone width", () => {
    const launch = rule(block, ".desk-next .desk-dock-launch {");
    expect(launch).toMatch(/min-height:\s*44px/);
    expect(launch).toMatch(/min-width:\s*44px/);
    // The close X is 0px wide until hover — there is no hover on a phone.
    const close = rule(block, ".desk-next .desk-dock-x {");
    expect(close).toMatch(/width:\s*(?!0)/);
  });
});

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

  // PHILO-13-17 (C7, Q3; ratified 2026-10-03): Go is grouped at 393 —
  // Chair ▸ Desk ▸ Object ▸ Window ▸, then its own rows. New Note is one
  // tap deeper (Go ▸ Desk ▸ New Note), and every menu stays a menu.
  it("carries New Note — owner job 3's door — at Go ▸ Desk at phone width", () => {
    compact = true;
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: "Go" }), { detail: 0 });
    fireEvent.click(screen.getByRole("menuitem", { name: /^Desk\W*$/ }));
    expect(
      screen.getByRole("menuitem", { name: /New Note/i }),
    ).toBeInTheDocument();
  });

  it("carries the Desk, Object and Window menus, in that order, after the Chair's windows", () => {
    compact = true;
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: "Go" }), { detail: 0 });
    const heads = screen
      .getAllByRole("menuitem")
      .filter((el) => el.getAttribute("aria-haspopup") === "menu")
      .map((el) => el.querySelector(".desk-menu-label")?.textContent ?? "");
    // PHILO-14 A1 (#939): the Chair's windows are Go's first rows, not a group.
    expect(heads).toEqual(["Desk", "Object", "Window"]);
    expect(screen.getAllByRole("menuitemcheckbox").slice(0, 3).map((el) => el.querySelector(".desk-menu-label")?.textContent))
      .toEqual(["Needs you", "Brief", "The week"]);
    const open = (name: string, needle: RegExp) => {
      fireEvent.click(screen.getByRole("menuitem", { name: new RegExp(`^${name}`) }));
      expect(screen.getAllByRole("menuitem").some((el) => needle.test(el.textContent ?? ""))).toBe(true);
      fireEvent.click(screen.getByRole("menuitem", { name: new RegExp(`^◂?\\s*${name}`) }));
    };
    open("Object", /Get Info/);
    open("Window", /Close window/);
    open("Window", /Cycle windows/);
  });

  it("lets the folded menu scroll, so its tail is reachable at 393", () => {
    const block = phoneBlock(chromeMenusCss);
    const panel = rule(block, ".desk-next .desk-work-menu {");
    expect(panel).toMatch(/max-height:/);
    expect(panel).toMatch(/overflow-y:\s*auto/);
  });

  it("no longer hides a rendered menu title behind CSS", () => {
    const block = phoneBlock(chromeMenusCss);
    expect(block).not.toMatch(
      /\.desk-verbbar-item:not\(\[data-menu-id="go"\]\)\s*\{\s*display:\s*none/,
    );
  });
});
