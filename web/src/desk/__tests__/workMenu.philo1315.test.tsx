/** PHILO-13-15 (C5) — the two named build obligations of the ratified canvas
 * (Astra canvas r1, conditions 2 and 4; story-15-canvas/harness/seats-common.mjs):
 *  (a) 393: a submenu inside a submenu opens (Go ▸ Object ▸ Send to ▸), and
 *      the back row climbs one level. Main stopped after the first level
 *      (the replaced panel's rows got `setOpenSub={() => {}}`).
 *  (b) 1440: a submenu opens NEXT TO its parent panel — the right side if it
 *      fits, else the left side. Main clamped it to the viewport's right edge. */
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";

const wide = window.innerWidth;
const setWidth = (w: number) => Object.defineProperty(window, "innerWidth", { configurable: true, value: w });
afterEach(() => { setWidth(wide); vi.restoreAllMocks(); });

const pick = vi.fn();
const go = (): WorkMenuEntry[] => [
  {
    type: "sub", id: "go-object", label: "Object",
    entries: [
      {
        type: "sub", id: "send-to", label: "Send to",
        entries: [{ type: "item", id: "send-to.chd_f", label: "Team updates · FILE", onSelect: pick }],
      },
      { type: "sep" },
      { type: "item", id: "object.open", label: "Open", onSelect: vi.fn() },
    ],
  },
  { type: "item", id: "go.desk", label: "Desk", onSelect: vi.fn() },
];

describe("393: nested submenus (obligation a)", () => {
  beforeEach(() => { setWidth(393); pick.mockReset(); });

  it("Go ▸ Object ▸ Send to ▸ opens the second level and its row runs", () => {
    const onClose = vi.fn();
    render(<WorkMenu label="Go menu" x={0} y={40} entries={go()} onClose={onClose} />);
    fireEvent.click(screen.getByText("Object"));
    fireEvent.click(screen.getByText("Send to"));
    // The panel is replaced again by the second level.
    fireEvent.click(screen.getByText("Team updates · FILE"));
    expect(pick).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalled();
  });

  it("the back row and the panel's name follow the level (a label names its panel)", () => {
    render(<WorkMenu label="Go menu" x={0} y={40} entries={go()} onClose={() => {}} />);
    fireEvent.click(screen.getByText("Object"));
    expect(screen.getByRole("menu").getAttribute("aria-label")).toBe("Object submenu");
    fireEvent.click(screen.getByText("Send to"));
    expect(document.querySelector(".desk-menu-back")?.textContent).toContain("Send to");
    expect(screen.getByRole("menu").getAttribute("aria-label")).toBe("Send to submenu");
  });

  it("the back row climbs ONE level, then to the top panel", () => {
    render(<WorkMenu label="Go menu" x={0} y={40} entries={go()} onClose={() => {}} />);
    fireEvent.click(screen.getByText("Object"));
    fireEvent.click(screen.getByText("Send to"));
    fireEvent.click(document.querySelector(".desk-menu-back")!);
    expect(document.querySelector(".desk-menu-back")?.textContent).toContain("Object");
    expect(screen.getByText("Open")).toBeTruthy();
    fireEvent.click(document.querySelector(".desk-menu-back")!);
    expect(document.querySelector(".desk-menu-back")).toBeNull();
    expect(screen.getByText("Desk")).toBeTruthy();
    expect(screen.getByRole("menu").getAttribute("aria-label")).toBe("Go menu");
  });
});

/** jsdom has no layout: each panel reports the rect a 1440 desk gives it. */
function layout(panel: { left: number; right: number }, subWidth = 220) {
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
    const rect = (left: number, top: number, width: number, height: number) =>
      ({ left, top, width, height, right: left + width, bottom: top + height, x: left, y: top, toJSON: () => ({}) }) as DOMRect;
    if (this.classList.contains("desk-work-submenu"))
      return rect(parseFloat(this.style.left) || 0, parseFloat(this.style.top) || 0, subWidth, 120);
    if (this.classList.contains("desk-work-menu")) return rect(panel.left, 100, panel.right - panel.left, 200);
    // A row sits inside the panel's 4 px padding (its right edge is NOT the panel's).
    return rect(panel.left + 4, 110, panel.right - panel.left - 12, 28);
  });
}
const subLeft = () => parseFloat((document.querySelector(".desk-work-submenu") as HTMLElement).style.left);

describe("1440: a submenu opens next to its parent panel (obligation b)", () => {
  beforeEach(() => setWidth(1440));
  const one = (): WorkMenuEntry[] => [
    { type: "sub", id: "send-to", label: "Send to", entries: [{ type: "item", id: "x", label: "Team updates · FILE", onSelect: vi.fn() }] },
    { type: "item", id: "close", label: "Close window", onSelect: vi.fn() },
  ];

  it("the right side when it fits: its left edge touches the parent's right edge", () => {
    layout({ left: 200, right: 430 });
    render(<WorkMenu label="Meeting window menu" x={200} y={100} entries={one()} onClose={() => {}} />);
    fireEvent.click(screen.getByText("Send to"));
    expect(Math.abs(subLeft() - 430)).toBeLessThanOrEqual(3);
  });

  it("the left side when the right does not fit: its right edge touches the parent's left edge", () => {
    layout({ left: 1100, right: 1330 });
    render(<WorkMenu label="Meeting window menu" x={1100} y={100} entries={one()} onClose={() => {}} />);
    fireEvent.click(screen.getByText("Send to"));
    expect(Math.abs(subLeft() + 220 - 1100)).toBeLessThanOrEqual(3);
  });
});
