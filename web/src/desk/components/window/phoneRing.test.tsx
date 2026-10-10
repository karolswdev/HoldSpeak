/* PHILO-13-17 (C7) — the phone desk, as state and as a rendered switcher.
 *
 * Ratified 2026-10-03 ("Ratify, build it"; all six defaults stand):
 *   Q1 a touch swipe moves around the ring of open windows: the open Chair
 *      windows (Capture once it opened at 393), then the desk windows in
 *      the order they opened; it wraps. A Chair window iconifies the desk
 *      window in front, never closes it.
 *   Q2 the screen title is the switcher `<window> ▾`: any window in 2 taps.
 *   Q3 Go at 393: superseded by PHILO-15 11 (B21, owner ruling 2026-10-07):
 *      the Chair's four windows, the Dock's places, the projects, New ▸.
 *   Q4b Capture stays in the ring until it is closed.
 * Red on main: phoneRing.ts, ScreenSwitcher.tsx and groupGoForPhone do not
 * exist there (the import fails), and Go is one flat list.
 */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../store";
import { closeChairWindow, openChairWindow, useChairWindows } from "../../chair/chairWindows";
import { announceWindow, retractWindow } from "./windowRegistry";
import { phoneRing, phoneCurrent, stepRing, swipeDirection } from "./phoneRing";
import { ScreenSwitcher } from "./ScreenSwitcher";
import { DeskMenuBar, phoneGo } from "../DeskMenuBar";
import type { WorkMenuEntry } from "../DeskMenu";
import chromeMenusCss from "../chrome-menus.css?raw";

let compact = true;
const opened: string[] = [];

function openDeskWindow(id: string, label: string) {
  announceWindow(id, label, "", () => retractWindow(id));
  opened.push(id);
  useDesk.getState().focusPanel(id);
}

beforeEach(() => {
  compact = true;
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
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 393 });
  useChairWindows.setState({ closed: {}, phone: "chair:needs", captureInRing: false });
  useDesk.setState({ panelOrder: [], panelMin: [] });
});

afterEach(() => {
  for (const id of opened.splice(0)) retractWindow(id);
  vi.unstubAllGlobals();
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
  document.querySelectorAll("body > .desk-window-shell").forEach((e) => e.remove());
});

const ids = () => phoneRing().map((w) => w.label);

describe("Q1 the ring and the swipe", () => {
  it("orders the Chair windows, then the desk windows as they opened", () => {
    openDeskWindow("surface:meetings", "Meetings");
    openDeskWindow("pullout:meeting:ledger", "Ledger cutover sync");
    expect(ids()).toEqual(["Needs you", "Brief", "The week", "Meetings", "Ledger cutover sync"]);
  });

  it("walks 5 of 5 forward, wraps, and comes back", () => {
    openDeskWindow("surface:meetings", "Meetings");
    openDeskWindow("pullout:meeting:ledger", "Ledger cutover sync");
    act(() => openChairWindow("chair:needs"));
    const seen: (string | null)[] = [];
    for (let i = 0; i < 5; i++) act(() => void seen.push(stepRing(1)));
    expect(seen).toEqual(["chair:brief", "chair:week", "surface:meetings", "pullout:meeting:ledger", "chair:needs"]);
    act(() => void stepRing(-1));
    expect(phoneCurrent()).toBe("pullout:meeting:ledger");
  });

  it("a Chair window iconifies the desk window in front; it is never closed", () => {
    openDeskWindow("surface:meetings", "Meetings");
    expect(phoneCurrent()).toBe("surface:meetings");
    act(() => void stepRing(1)); // wraps to Needs you
    expect(phoneCurrent()).toBe("chair:needs");
    expect(useDesk.getState().panelMin).toContain("surface:meetings");
    expect(ids()).toContain("Meetings");
  });

  it("reads a horizontal swipe only: 64 px and twice as wide as tall", () => {
    expect(swipeDirection(-120, 10)).toBe(1);
    expect(swipeDirection(120, 10)).toBe(-1);
    expect(swipeDirection(-40, 0)).toBe(0);
    expect(swipeDirection(-100, 60)).toBe(0);
  });

  it("a touch drag on the front window moves to the next one; on a field it does not", () => {
    render(<ScreenSwitcher name="Needs you" />);
    const shell = document.createElement("div");
    shell.className = "desk-window-shell";
    const field = document.createElement("textarea");
    shell.append(field);
    document.body.append(shell);
    const touch = (el: Element, type: string, x: number) => {
      const e = new Event(type, { bubbles: true });
      const pt = [{ clientX: x, clientY: 400 }];
      Object.defineProperty(e, type === "touchend" ? "changedTouches" : "touches", { value: pt });
      if (type === "touchend") Object.defineProperty(e, "touches", { value: [] });
      el.dispatchEvent(e);
    };
    act(() => { touch(shell, "touchstart", 300); touch(shell, "touchend", 120); });
    expect(phoneCurrent()).toBe("chair:brief");
    act(() => { touch(shell, "touchstart", 120); touch(shell, "touchend", 300); });
    expect(phoneCurrent()).toBe("chair:needs");
    act(() => { touch(field, "touchstart", 300); touch(field, "touchend", 120); });
    expect(phoneCurrent()).toBe("chair:needs");
  });
});

describe("Astra r1 #751: the ring keeps the opening order", () => {
  it("a title change (retract + announce in one commit) keeps the window's place", async () => {
    openDeskWindow("surface-project-memory", "Payments ledger cutover");
    openDeskWindow("surface:meetings", "Meetings");
    openDeskWindow("pullout:meeting:ledger", "Ledger cutover sync");
    // DeskWindow re-announces on a title change: the Map puts it last
    retractWindow("surface-project-memory");
    announceWindow("surface-project-memory", "Payments ledger cutover", "", () => {});
    await Promise.resolve();
    expect(ids().slice(3)).toEqual(["Payments ledger cutover", "Meetings", "Ledger cutover sync"]);
  });

  it("a window really closed and opened again is the newest", async () => {
    openDeskWindow("surface:meetings", "Meetings");
    openDeskWindow("pullout:meeting:ledger", "Ledger cutover sync");
    retractWindow("surface:meetings");
    await Promise.resolve();
    openDeskWindow("surface:meetings", "Meetings");
    expect(ids().slice(3)).toEqual(["Ledger cutover sync", "Meetings"]);
  });
});

describe("Q4b Capture stays in the ring until it is closed", () => {
  it("joins when it opens at 393, survives a swipe away, leaves on Close", () => {
    expect(ids()).not.toContain("Capture");
    act(() => openChairWindow("chair:capture"));
    expect(ids()).toEqual(["Needs you", "Brief", "The week", "Capture"]);
    act(() => void stepRing(1)); // wraps to Needs you
    expect(phoneCurrent()).toBe("chair:needs");
    expect(ids()).toContain("Capture");
    act(() => void stepRing(-1));
    expect(phoneCurrent()).toBe("chair:capture");
    act(() => closeChairWindow("chair:capture"));
    expect(ids()).not.toContain("Capture");
  });
});

describe("Q2 the switcher in the screen title", () => {
  it("draws `<window> ▾` with the ▾ as its own mark, and reaches any window in 2 taps", () => {
    openDeskWindow("surface:meetings", "Meetings");
    act(() => openChairWindow("chair:week"));
    render(<ScreenSwitcher name="The week" />);
    const button = screen.getByTestId("desk-screen-switcher");
    expect(button).toHaveAccessibleName("Windows: The week");
    const mark = screen.getByTestId("desk-screen-switcher-mark");
    expect(mark.closest(".desk-screen-name")).toBeNull();
    // The ▾ is painted by CSS, so the title's text stays the window's name.
    expect(screen.getByTestId("desk-screen-title").textContent).toBe("The week");
    expect(chromeMenusCss).toMatch(/\.desk-screen-switcher-mark::before\s*\{\s*content:\s*"\\25BE"/);
    expect(chromeMenusCss).toMatch(/\.desk-screen-switcher-mark\s*\{[^}]*flex:\s*0 0 auto/);
    fireEvent.pointerDown(button, { button: 0 }); // tap 1
    const menu = screen.getByRole("menu", { name: "Open windows" });
    const rows = within(menu).getAllByRole("menuitemcheckbox");
    expect(rows.map((r) => r.textContent?.replace("✓", "").trim())).toEqual(
      ["Needs you", "Brief", "The week", "Meetings"]);
    expect(rows.map((r) => r.getAttribute("aria-checked"))).toEqual(["false", "false", "true", "false"]);
    act(() => fireEvent.click(rows[0])); // tap 2
    expect(phoneCurrent()).toBe("chair:needs");
  });

  it("a second tap on the open switcher closes it (Astra r1 #751)", () => {
    render(<ScreenSwitcher name="Needs you" />);
    const button = screen.getByTestId("desk-screen-switcher");
    act(() => void fireEvent.pointerDown(button, { button: 0 }));
    expect(screen.getByRole("menu", { name: "Open windows" })).toBeInTheDocument();
    act(() => void fireEvent.pointerDown(button, { button: 0 }));
    expect(screen.queryByRole("menu", { name: "Open windows" })).toBeNull();
    act(() => void fireEvent.pointerDown(button, { button: 0 }));
    expect(screen.getByRole("menu", { name: "Open windows" })).toBeInTheDocument();
  });
});

describe("Go at 393 is the owner's short list (PHILO-15 11, B21; supersedes C7 Q3)", () => {
  it("the pure phone Go: the Chair's four windows, the Dock's places, the projects, then New ▸", () => {
    const row = (id: string, label?: string): WorkMenuEntry => ({ type: "item", id, label: label ?? id, onSelect: () => {} });
    const out = phoneGo(row, [{ id: "p-1", name: "Ledger cutover" }], () => {});
    expect(out.map((e) => (e.type === "sep" ? "—" : e.label))).toEqual([
      "chair.window.needs", "chair.window.brief", "chair.window.week", "chair.window.capture", "—",
      "Meetings", "People", "Conductor", "Settings", "—",
      "Ledger cutover", "—", "New"]);
    const nu = out[out.length - 1] as Extract<WorkMenuEntry, { type: "sub" }>;
    expect(nu.entries.map((e) => (e.type === "sep" ? "—" : e.label))).toEqual(["Thought", "Meeting", "Project", "Person"]);
  });

  it("renders on the real menu bar: no Desk ▸ Object ▸ Window ▸, and New opens as a menu", () => {
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: "Go" }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Go menu" });
    const rows = within(menu).getAllByRole("menuitemcheckbox").slice(0, 4);
    expect(rows.map((h) => h.querySelector(".desk-menu-label")?.textContent?.trim())).toEqual(
      ["Needs you", "Brief", "The week", "Capture"]);
    const heads = within(menu).getAllByRole("menuitem").filter((h) => h.getAttribute("aria-haspopup") === "menu");
    expect(heads.map((h) => h.querySelector(".desk-menu-label")?.textContent?.trim())).toEqual(["New"]);
    fireEvent.click(heads[0]);
    expect(within(menu).getByRole("menuitem", { name: /Thought/ })).toBeInTheDocument();
  });

  it("keeps all four menus flat at 1440 (the control)", () => {
    compact = false;
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
    const { container } = render(<DeskMenuBar />);
    expect(Array.from(container.querySelectorAll("[data-menu-id]"), (e) => e.getAttribute("data-menu-id")))
      .toEqual(["desk", "object", "go", "window"]);
    fireEvent.click(screen.getByRole("button", { name: "Go" }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Go menu" });
    expect(within(menu).queryByRole("menuitem", { name: /^Desk$/ })).toBeNull();
  });
});
