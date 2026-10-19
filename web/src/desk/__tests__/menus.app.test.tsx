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
    // Betterment shell S1: Engines and Accounts open their Settings wings
    // (the Settings wing verbs), never the parked surfaces.
    expect(opened).toEqual([
      ["configure-settings", undefined],
      ["configure-settings", "models"],
      ["configure-settings", "integrations"],
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
    expect(within(menu).queryAllByRole("menuitem")).toHaveLength(0);
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

  it("Today as the target: the third title is Today, never Intelligence (Betterment D4)", () => {
    // EMPTY_ITEMS holds the one Today object (`intelligence:desk`), as the hub's desk does.
    // The front Today window names the same object (windowObjectRef); the
    // title is the same function either way.
    useDesk.setState({ items: { ...useDesk.getState().items, intelligence: EMPTY_ITEMS.intelligence },
      selectedIds: ["intelligence:desk"] } as never);
    render(<DeskMenuBar />);
    expect(titles()).toContain("Today");
    expect(titles()).not.toContain("Intelligence");
    expect(objectMenuTitle("intelligence")).toBe("Today");
  });
});

// ── Betterment shell S1: Go lists every app; Builder tools switch ──
import { GO_GROUPS, goRows } from "../applications";
import { useBuilderTools } from "../builderTools";
import { GoHome } from "../screen/GoHome";
import { announceLauncher, retractLauncher } from "../components/window/launcherRegistry";
import { CHAIR_WINDOWS, useChairWindows } from "../chair/chairWindows";
import { openWindowCount } from "../components/window/windowRegistry";

describe.each([[1440, false], [393, true]] as const)("S1: Go at %i is the manifest's Go groups", (_width, isPhone) => {
  const goMenu = () => {
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    return screen.getByRole("menu", { name: "Go menu" });
  };
  /** The top-level rows of the open Go menu (a submenu by its own name). */
  const top = (menu: HTMLElement) =>
    Array.from(menu.querySelectorAll(":scope > [role^=menuitem] .desk-menu-label"), (e) => e.textContent?.trim());
  beforeEach(() => {
    useBuilderTools.getState().setOn(false);
    useDesk.setState({
      items: { ...EMPTY_ITEMS, project: [{ kind: "project", id: "p1", name: "Ledger migration" } as Project] },
      projects: [{ id: "p1", name: "Ledger migration" }],
      selectedIds: [],
    } as never);
    announceLauncher({ id: "delivery-board", label: "Delivery", glyph: "▤", open: false, activate: () => {} });
    announceLauncher({ id: "panes", label: "Terminals", glyph: "⧉", open: false, activate: () => {} });
  });
  afterEach(() => {
    useBuilderTools.getState().setOn(false);
    retractLauncher("delivery-board");
    retractLauncher("panes");
    useDesk.setState({ items: { ...EMPTY_ITEMS }, projects: [] } as never);
  });

  // Betterment daily D5: Brief and The week retired into Today.
  // Betterment P4 (projects): Projects ▸ (All projects, then each) and Decisions.
  const DAILY_WORK = ["Today", "Needs you", "Capture", "Meetings", "People", "Projects", "Decisions", "Agents",
    "Ask AI", "Speak", "Automations", "Memory", "Voice commands"];

  it("Go shows Daily then Work; Builder ▸ only when Builder tools is on, with eight rows", () => {
    phone(isPhone);
    render(<DeskMenuBar />);
    const expected = isPhone ? [...DAILY_WORK, "New"] : DAILY_WORK;
    expect(top(goMenu())).toEqual(expected);
    fireEvent.keyDown(document.body, { key: "Escape" });

    act(() => useBuilderTools.getState().setOn(true));
    const menu = goMenu();
    const withBuilder = isPhone ? [...DAILY_WORK, "Builder", "New"] : [...DAILY_WORK, "Builder"];
    expect(top(menu)).toEqual(withBuilder);
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^Builder\W*$/ }));
    const builder = screen.getAllByRole("menu").at(-1)!;
    expect(labels(builder).filter((l) => l !== "Builder")).toEqual([
      "Activity", "Processes", "Context", "Components", "Calendar snapshot", "Delivery board", "Terminals",
      "Refresh from hub",
    ]);
  });

  // S0 left the Window menu with one line on an empty desk, so Go is the
  // door to every Chair window there (PLAN: no app only by a detour).
  it("on an empty desk, each Chair window has a Go row that opens it", () => {
    phone(isPhone);
    expect(openWindowCount()).toBe(0);
    render(<DeskMenuBar />);
    const menu = goMenu();
    for (const w of CHAIR_WINDOWS) {
      const row = Array.from(menu.querySelectorAll<HTMLElement>("[role^=menuitem]")).find(
        (el) => el.querySelector(".desk-menu-label")?.textContent?.trim() === w.title);
      expect(row, w.title).toBeTruthy();
      expect(row!.getAttribute("aria-disabled"), w.title).not.toBe("true");
    }
    // Betterment daily D5: no Go row offers the retired Brief or The week.
    expect(top(menu)).not.toContain("Brief");
    expect(top(menu)).not.toContain("The week");
    // The desktop row opens the Chair window itself.
    if (!isPhone) {
      const capture = Array.from(menu.querySelectorAll<HTMLElement>("[role^=menuitem]")).find(
        (el) => el.querySelector(".desk-menu-label")?.textContent?.trim() === "Capture")!;
      fireEvent.click(capture);
      expect(useChairWindows.getState().closed["chair:capture"]).toBe(false);
    }
  });

  it("every Go row comes from goRows (no hand list)", () => {
    phone(isPhone);
    const fromManifest = GO_GROUPS.flatMap(goRows).length;
    // Daily: Today, Needs you, Capture, Projects ▸ and six applications
    // (daily D5 retired Brief and The week into Today; P4 added Decisions).
    expect(fromManifest).toBe(10 + 4 + 8);
  });

  // Betterment P4 (projects): Projects and Decisions are one press from Go,
  // also on a desk with no project yet (the old Projects ▸ was not drawn).
  it("Projects ▸ All projects and Decisions open their own windows, also with no project on the desk", () => {
    phone(isPhone);
    useDesk.setState({ items: { ...EMPTY_ITEMS }, projects: [] } as never);
    const opened: string[] = [];
    const offs = ["open-projects", "open-decisions"].map((action) =>
      registerSurface(action, () => opened.push(action)));
    render(<DeskMenuBar />);
    let menu = goMenu();
    expect(top(menu)).toEqual(expect.arrayContaining(["Projects", "Decisions"]));
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^Projects\W*$/ }));
    const projects = screen.getAllByRole("menu").at(-1)!;
    expect(labels(projects).filter((l) => l !== "Projects")).toEqual(["All projects"]);
    fireEvent.click(within(projects).getByRole("menuitem", { name: /All projects/ }));
    menu = screen.queryByRole("menu", { name: "Go menu" }) ?? goMenu();
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^Decisions/ }));
    expect(opened).toEqual(["open-projects", "open-decisions"]);
    offs.forEach((off) => off());
  });

  it("Projects ▸ is All projects, then each project; a project opens its own window", () => {
    phone(isPhone);
    render(<DeskMenuBar />);
    const menu = goMenu();
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^Projects\W*$/ }));
    const projects = screen.getAllByRole("menu").at(-1)!;
    expect(labels(projects).filter((l) => l !== "Projects")).toEqual(["All projects", "Ledger migration"]);
  });
});

describe("S1: at 393 the phone home and Go show the same rows in the same order", () => {
  beforeEach(() => {
    useDesk.setState({
      items: { ...EMPTY_ITEMS, project: [{ kind: "project", id: "p1", name: "Ledger migration" } as Project] },
      projects: [{ id: "p1", name: "Ledger migration" }],
    } as never);
  });
  afterEach(() => useDesk.setState({ items: { ...EMPTY_ITEMS }, projects: [] } as never));

  it("home rows equal Go rows (a submenu's name stands for its rows)", () => {
    phone(true);
    const { unmount } = render(<GoHome />);
    const home = screen.getByRole("menu", { name: "Go menu" });
    // A top-level row is a home row; a submenu is its name: a nested group
    // (Projects, Drawers) or a section of its own (Builder, New).
    const homeTop: string[] = [];
    for (const section of home.querySelectorAll(":scope > .desk-go-home-group")) {
      if (section.classList.contains("is-sub")) {
        homeTop.push(section.querySelector(":scope > header h3")?.textContent?.trim() ?? "");
        continue;
      }
      for (const el of section.querySelectorAll("[role=menuitem] .desk-menu-label, .desk-go-home-sub > header h3")) {
        if (el.tagName !== "H3" && el.closest(".desk-go-home-sub")) continue;
        homeTop.push(el.textContent?.trim() ?? "");
      }
    }
    unmount();
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    const go = screen.getByRole("menu", { name: "Go menu" });
    const goTop = Array.from(go.querySelectorAll(":scope > [role^=menuitem] .desk-menu-label"), (e) => e.textContent?.trim());
    expect(homeTop).toEqual(goTop);
  });
});
