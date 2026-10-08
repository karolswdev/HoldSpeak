/* PHILO-15 11 (B21; Astra r1 on #986): a phone has no ⌘ key, so no menu at
 * 393 draws a keycap: the window menu and its Desk ▸ submenu (the route to
 * New Note at 393) included. 1440 keeps them. */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { WorkMenu } from "../components/DeskMenu";
import { headMenuEntries } from "../windowMenuAdapter";

const entries = () =>
  headMenuEntries({
    maximized: false,
    compact: true,
    requestMinimize: () => {},
    toggleMaximize: () => {},
    requestClose: () => {},
    toBack: () => {},
  });

const keycaps = (el: HTMLElement) => el.querySelectorAll(".desk-menu-keycaps, kbd").length;

afterEach(() => {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1024 });
});

describe("no keycap on a phone", () => {
  it("393: the window menu and its Desk ▸ draw no keycap", () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 393 });
    render(<WorkMenu label="Window menu" x={0} y={40} entries={entries()} onClose={() => {}} />);
    const menu = screen.getByRole("menu");
    expect(keycaps(menu)).toBe(0);
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^Desk\W*$/ }));
    const desk = screen.getByRole("menu");
    expect(within(desk).getByRole("menuitem", { name: /New Note/ })).toBeTruthy();
    expect(keycaps(desk)).toBe(0);
  });

  it("1440: the same window menu keeps its keycaps (the control)", () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
    render(<WorkMenu label="Window menu" x={0} y={40} entries={entries()} onClose={() => {}} />);
    expect(keycaps(screen.getByRole("menu"))).toBeGreaterThan(0);
  });
});
