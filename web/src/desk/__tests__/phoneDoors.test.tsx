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

  it("wraps inside the viewport instead of running past its edge", () => {
    expect(dock).toMatch(/flex-wrap:\s*wrap/);
    expect(dock).not.toMatch(/overflow-x:\s*auto/);
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

  it("carries New Note — owner job 3's door — inside Go at phone width", () => {
    compact = true;
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: "Go" }), { detail: 0 });
    expect(
      screen.getByRole("menuitem", { name: /New Note/i }),
    ).toBeInTheDocument();
  });

  it("no longer hides a rendered menu title behind CSS", () => {
    const block = phoneBlock(chromeMenusCss);
    expect(block).not.toMatch(
      /\.desk-verbbar-item:not\(\[data-menu-id="go"\]\)\s*\{\s*display:\s*none/,
    );
  });
});
