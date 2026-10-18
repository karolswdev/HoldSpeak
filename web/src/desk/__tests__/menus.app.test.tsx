// The desk menus app (test diet, 2026-10-11): the HoldSpeak menu, moved off
// the browser.
//
// PHILO-17 (doors): the HoldSpeak menu is "Refresh from hub", then the four
// setup applications (Settings, Runs on, Connections, Setup), at 1440 and at
// 393; each row opens its own application with its own scope; "Desk memory"
// and "List view" are nowhere in the chrome or its menus.
//
// The real DeskChrome, the real verb registry and the real opener path
// (`openSurfaceOr` -> the surface a window registers). Go's rows are
// components/DeskMenuBar.test.tsx (1440 and 393). Only `fetch` is stubbed: the
// hub gives no answer (a TypeError), so no hub field is typed here.
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, registerSurface } from "../shell";
import { DeskChrome } from "../components/DeskChrome";

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", subscribe: () => () => undefined }),
}));

const MARK_ROWS = ["Refresh from hub", "Settings", "Engines", "Accounts", "Setup"];

function phone(on: boolean) {
  if (!on) return;
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query.includes("720px"),
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    onchange: null,
    dispatchEvent: () => false,
  }));
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 393 });
}

/** The words a user can read or hear in the chrome now (its text, its names). */
function words(): string {
  const out = [document.body.textContent ?? ""];
  for (const e of document.querySelectorAll("[aria-label],[title]"))
    out.push(e.getAttribute("aria-label") ?? "", e.getAttribute("title") ?? "");
  return out.join("\n").toLowerCase();
}

function openMark(): HTMLElement {
  const mark = document.querySelector(".desk-mark") as HTMLElement;
  expect(mark, "the HoldSpeak mark is in the screen bar").toBeTruthy();
  fireEvent.click(mark, { detail: 0 });
  return screen.getByRole("menu", { name: "HoldSpeak" });
}

const labels = (menu: HTMLElement) =>
  Array.from(menu.querySelectorAll("[role^=menuitem] .desk-menu-label"), (e) => e.textContent?.trim());

beforeEach(() => {
  __resetSurfaces();
  localStorage.clear();
  vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
});
afterEach(() => {
  vi.unstubAllGlobals();
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
  __resetSurfaces();
});

describe.each([[1440, false], [393, true]] as const)("the HoldSpeak menu at %i", (_width, isPhone) => {
  it("is Refresh from hub, then the four setup applications; each row opens its own application", async () => {
    // replaces: tests/e2e/test_philo17_doors_glass.py::TestDoors::test_one_door_per_application (D2 "the HoldSpeak menu is Refresh + the four setup rows"; D4 "393 the HoldSpeak menu is the setup rows"; D3 the HoldSpeak doors' scopes)
    phone(isPhone);
    const opened: Array<[string, string | undefined]> = [];
    const offs = ["configure-settings", "configure-runs-on", "configure-integrations", "configure-setup"]
      .map((action) => registerSurface(action, (scope) => opened.push([action, scope])));
    render(<MemoryRouter><DeskChrome /></MemoryRouter>);
    await act(async () => { await Promise.resolve(); });

    expect(labels(openMark())).toEqual(MARK_ROWS);
    for (const row of ["Settings", "Engines", "Accounts", "Setup"]) {
      const menu = screen.queryByRole("menu", { name: "HoldSpeak" }) ?? openMark();
      fireEvent.click(within(menu).getByRole("menuitem", { name: new RegExp(`^${row}`) }));
    }
    expect(opened).toEqual([
      ["configure-settings", undefined],
      ["configure-runs-on", undefined],
      // Connections opens Settings on the destinations scope; Settings opens it plain.
      ["configure-integrations", "integration:destinations"],
      ["configure-setup", undefined],
    ]);
    offs.forEach((off) => off());
  });

  it("no 'Desk memory' and no 'List view' in the chrome, with Go and the HoldSpeak menu open", async () => {
    // replaces: tests/e2e/test_philo17_doors_glass.py::TestDoors::test_one_door_per_application (D5 with Go and the HoldSpeak menu open; the Missed shade and the Memory window stay in the browser file)
    phone(isPhone);
    render(<MemoryRouter><DeskChrome /></MemoryRouter>);
    await act(async () => { await Promise.resolve(); });
    const banned = (where: string) => {
      for (const old of ["desk memory", "list view"]) expect(words(), `${where}: '${old}'`).not.toContain(old);
    };
    banned("at rest");
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    expect(screen.getByRole("menu", { name: "Go menu" })).toBeTruthy();
    banned("Go open");
    fireEvent.keyDown(document.activeElement ?? document.body, { key: "Escape" });
    openMark();
    banned("HoldSpeak menu open");
  });
});

// ── HS-201-01: the chrome over a hub open to the network ──
// The hub's own status for a real 0.0.0.0 bind (tests/integration/test_desk_trust.py
// `test_the_open_to_network_wire`), set in the desk store the chrome reads.
// A served off-loopback hub always has a token (start() refuses the bind
// without one), so OPEN TO NETWORK (open, no token) stays dark over it; the
// lit rule is setup.test.ts `inboundBadge`.
import { useDesk } from "../store";
import statusOpen from "./fixtures/trust-wire/status-open.json";

describe.each([[1440, false], [393, true]] as const)("the chrome over an open hub at %i", (_width, isPhone) => {
  it("keeps OPEN TO NETWORK dark when a token guards the bind, and the egress chip reads This device", async () => {
    // replaces: tests/e2e/test_hs201_one_thing_glass.py::TestOneThing::test_open_to_network_is_its_own_token (the chrome half; the Trust line is components/__tests__/trustInbound.test.tsx)
    phone(isPhone);
    expect(statusOpen.trust.web_bind).toBe("0.0.0.0");
    expect(statusOpen.trust.auth_token_set).toBe(true);
    useDesk.setState({ setup: structuredClone(statusOpen) } as never);
    render(<MemoryRouter><DeskChrome /></MemoryRouter>);
    await act(async () => { await Promise.resolve(); });
    expect(screen.queryByTestId("chrome-inbound")).toBeNull();
    const chip = document.querySelector(".egress-badge") as HTMLElement;
    expect(chip.textContent?.toUpperCase()).toContain("THIS DEVICE");
    useDesk.setState({ setup: null } as never);
  });
});

// ── Betterment shell S0: menus show only what works (UX-CANON A.11) ──
// The real DeskMenuBar over the real registry and the real objectMenu. The
// desk objects are the store's own shapes (as objectMenu.test.ts seeds them).
import { DeskMenuBar, objectMenuTitle } from "../components/DeskMenuBar";
import { EMPTY_ITEMS } from "../api";
import type { Meeting, Note, Project } from "../../lib/primitives";

describe("S0: the menu bar withholds what cannot run", () => {
  const titles = () =>
    Array.from(document.querySelectorAll(".desk-verbbar [data-menu-id] .desk-verbbar-title"), (e) => e.textContent?.trim());
  const openTitle = (name: string) => {
    fireEvent.click(screen.getByRole("button", { name: new RegExp(`^${name}$`) }), { detail: 0 });
    return screen.getByRole("menu", { name: `${name} menu` });
  };
  const noDeadRow = (menu: HTMLElement) => {
    expect(menu.querySelectorAll("[aria-disabled='true']"), "a dead row is drawn").toHaveLength(0);
    expect(menu.querySelector(".is-ghost, .desk-menu-ghost-hint")).toBeNull();
  };
  beforeEach(() => {
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [{ kind: "note", id: "n1", title: "On-call handbook idea" } as Note],
        meeting: [{ kind: "meeting", id: "m1", title: "Platform sync" } as Meeting],
        project: [{ kind: "project", id: "p1", name: "Ledger migration" } as Project],
      },
      selectedIds: [],
      panelOrder: [],
      panelMin: [],
    } as never);
  });
  afterEach(() => {
    useDesk.setState({ items: { ...EMPTY_ITEMS }, selectedIds: [] } as never);
  });

  it("with nothing selected the bar reads Desk Go Window; no menu draws a dead row", () => {
    render(<DeskMenuBar />);
    expect(titles()).toEqual(["Desk", "Go", "Window"]);
    for (const name of ["Desk", "Go"]) {
      noDeadRow(openTitle(name));
      fireEvent.keyDown(document.body, { key: "Escape" });
    }
  });

  it("the Window menu with no window open is one line, No windows open", () => {
    render(<DeskMenuBar />);
    const menu = openTitle("Window");
    expect(menu.textContent).toBe("No windows open");
    expect(within(menu).queryAllByRole(/menuitem/)).toHaveLength(0);
  });

  it.each([
    ["note:n1", "Note"],
    ["meeting:m1", "Meeting"],
    ["project:p1", "Project"],
  ])("select %s: the third title is %s, and its rows all run", (ref, title) => {
    useDesk.setState({ selectedIds: [ref] });
    render(<DeskMenuBar />);
    expect(titles()).toEqual(["Desk", title, "Go", "Window"]);
    const menu = openTitle(title);
    noDeadRow(menu);
    expect(labels(menu).length).toBeGreaterThan(0);
    // A note never offers a project's verbs.
    if (title === "Note") expect(menu.textContent).not.toMatch(/Draft update|Ask this project|Archive/);
  });

  it("names each kind in words", () => {
    expect(["note", "meeting", "people", "project", "decision", "directory"].map(objectMenuTitle))
      .toEqual(["Note", "Meeting", "Person", "Project", "Decision", "Drawer"]);
  });
});
