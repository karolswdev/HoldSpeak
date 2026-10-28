// HS-144-04 — compact chrome preserves the existing Go registry menu.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, registerSurface } from "../shell";
import { useDesk } from "../store";
import { DeskMenuBar } from "./DeskMenuBar";
import { WorkMenu } from "./DeskMenu";
import { DeskChrome } from "./DeskChrome";
import { dismissAftercare, publishAftercare } from "../intelligenceAttention";

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
}));

beforeEach(__resetSurfaces);
afterEach(() => {
  dismissAftercare();
  __resetSurfaces();
});

// jsdom has no PointerEvent constructor. Retain the native mouse-button
// fields and the pointer kind while dispatching the real pointer event path.
function pointer(target: Element, type: "pointerdown" | "pointerup", pointerType: string) {
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, button: 0 });
  Object.defineProperty(event, "pointerType", { value: pointerType });
  fireEvent(target, event);
}

it("routes a ready meeting through the one attention bell", async () => {
  publishAftercare({
    meeting_id: "meeting-ready",
    title: "Weekly review",
    proposal_total: 1,
  });
  render(<DeskChrome />);

  const bell = await screen.findByRole("button", {
    name: "Meeting ready: Weekly review",
  });
  expect(document.querySelectorAll('[data-testid="desk-bell"]')).toHaveLength(1);
  expect(bell).toHaveTextContent("READY");
  expect(document.querySelector(".ambient-aftercare")).toBeNull();
});

describe("DeskMenuBar", () => {
  it("leaves an opener pointer press to its owner and closes on an outside press", () => {
    const opener = document.createElement("button");
    document.body.append(opener);
    const close = vi.fn();
    try {
      render(<WorkMenu label="Owned menu" x={0} y={40} entries={[]} onClose={close} opener={opener} />);
      pointer(opener, "pointerdown", "touch");
      expect(close).not.toHaveBeenCalled();
      pointer(document.body, "pointerdown", "touch");
      expect(close).toHaveBeenCalledTimes(1);
    } finally {
      opener.remove();
    }
  });

  it("hands a pointer press from Go to a sibling title and preserves Escape dismissal", () => {
    render(<DeskMenuBar />);
    const go = screen.getByRole("button", { name: /^Go$/ });
    const desk = screen.getByRole("button", { name: /^Desk$/ });
    pointer(go, "pointerdown", "mouse");
    expect(screen.getByRole("menu", { name: "Go menu" })).toBeVisible();
    pointer(desk, "pointerdown", "mouse");
    expect(screen.queryByRole("menu", { name: "Go menu" })).toBeNull();
    expect(go).toHaveAttribute("aria-expanded", "false");
    expect(desk).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menu", { name: "Desk menu" })).toBeVisible();
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(screen.queryByRole("menu", { name: "Desk menu" })).toBeNull();
    expect(desk).toHaveAttribute("aria-expanded", "false");
  });

  it("marks the registry-derived Go title and launches Meetings through its real menu", () => {
    const opened: Array<string | undefined> = [];
    const off = registerSurface("review-meetings", (scope) => opened.push(scope));
    const { container } = render(<DeskMenuBar />);

    expect(
      container.querySelector('[data-menu-id="go"]'),
    ).toContainElement(screen.getByRole("button", { name: /^Go$/ }));
    // Betterment shell S0: Desk, Go, Window; Object only with a thing in front.
    expect(container.querySelectorAll("[data-menu-id]")).toHaveLength(3);

    // A keyboard click exercises the title's existing Enter/Space path.
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }));
    const menu = screen.getByRole("menu", { name: "Go menu" });
    expect(menu).toBeVisible();
    fireEvent.click(screen.getByRole("menuitem", { name: /Meetings/ }));

    expect(opened).toEqual([undefined]);
    off();
  });
});

/* PHILO-17 (doors): Go at 1440 is the application index. Its six live
 * applications are followed by Projects ▸; setup lives in HoldSpeak. */
describe("DeskMenuBar Go at 1440 (PHILO-17 doors)", () => {
  const PROJECT = (id: string, name: string) => ({ kind: "project" as const, id, name, description: "", keywords: [], teamMembers: [], meetingCount: 0, createdAt: "", updatedAt: "" });
  afterEach(() => {
    useDesk.setState((s) => ({ items: { ...s.items, project: [] } }));
  });
  const top = (menu: HTMLElement) =>
    Array.from(menu.querySelectorAll(":scope [role^=menuitem] .desk-menu-label"), (e) => e.textContent?.trim());

  it("Go is the live applications and Projects ▸", () => {
    useDesk.setState((s) => ({
      items: { ...s.items, project: [PROJECT("p-1", "Alpha"), PROJECT("p-2", "Beta"), PROJECT("p-3", "Gamma")] },
    }));
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Go menu" });
    // Betterment shell S1: Daily, then Work (Builder ▸ only behind its switch).
    expect(top(menu)).toEqual([
      "Today", "Needs you", "Capture", "Meetings", "People", "Projects", "Decisions", "Agents", "Programs", "Ask AI", "Speak",
      "Automations", "Memory", "Calls", "Recordings", "Voice commands", "Archive",
    ]);
    expect(menu.textContent).not.toMatch(/Settings|Runs on|Connections|Setup|Desk memory|List view/);
    // The ⌃ keys stay on their rows (PHILO-17 U27).
    expect(within(menu).getByRole("menuitem", { name: /Speak/ }).textContent).toContain("⌃5");

    fireEvent.click(within(menu).getByRole("menuitem", { name: /^Projects\W*$/ }));
    // Betterment P4: All projects (the Projects window) leads.
    expect(top(screen.getAllByRole("menu").at(-1)!)).toEqual(["All projects", "Alpha", "Beta", "Gamma"]);
  });

  it("does not offer a retired empty Tools ▸", () => {
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Go menu" });
    // Betterment P4: no projects: Projects ▸ is All projects alone (never empty).
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^Projects\W*$/ }));
    expect(top(screen.getAllByRole("menu").at(-1)!)).toEqual(["All projects"]);
    expect(top(menu)).not.toContain("Tools");
  });

  it("the Desk menu does not open People or Today", () => {
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: /^Desk$/ }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Desk menu" });
    expect(menu.textContent).not.toMatch(/Open People|Open Intelligence|Open Today/);
  });
});

/* PHILO-15 11 (B21, owner ruling 2026-10-07): rehearsal 1A counted 22 Go
 * rows with ⌘ keycaps at 393 and nine New kinds. At 393 Go is the Chair's
 * four windows, the Dock's places, the projects, then New ▸ with four kinds;
 * no ⌘ hint on a phone. 1440 keeps its four menus. */
describe("DeskMenuBar at 393", () => {
  beforeEach(() => {
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
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
    useDesk.setState((s) => ({ items: { ...s.items, project: [] } }));
  });

  const labels = (menu: HTMLElement) =>
    Array.from(menu.querySelectorAll("[role^=menuitem] .desk-menu-label"), (e) => e.textContent?.trim());

  it.each(["touch", "mouse"])("toggles Go on repeated %s pointer presses with the outside listener mounted", (pointerType) => {
    render(<DeskMenuBar />);
    const go = screen.getByRole("button", { name: /^Go$/ });
    const press = () => {
      pointer(go, "pointerdown", pointerType);
      pointer(go, "pointerup", pointerType);
      fireEvent.click(go, { detail: 1 });
    };
    press();
    expect(screen.getByRole("menu", { name: "Go menu" })).toBeVisible();
    expect(go).toHaveAttribute("aria-expanded", "true");
    press();
    expect(screen.queryByRole("menu", { name: "Go menu" })).toBeNull();
    expect(go).toHaveAttribute("aria-expanded", "false");
    press();
    expect(screen.getByRole("menu", { name: "Go menu" })).toBeVisible();
    expect(go).toHaveAttribute("aria-expanded", "true");
    pointer(document.body, "pointerdown", pointerType);
    expect(screen.queryByRole("menu", { name: "Go menu" })).toBeNull();
    expect(go).toHaveAttribute("aria-expanded", "false");
  });

  // PHILO-17 (doors): Settings left Go (it is in the HoldSpeak menu).
  // Betterment shell S1: the manifest's Go groups, then New ▸; no ⌘ keycap.
  it("Go is the Daily and Work rows, Projects ▸, then New; no ⌘ keycap", () => {
    useDesk.setState((s) => ({
      items: {
        ...s.items,
        project: [{ kind: "project", id: "p-1", name: "Ledger cutover", description: "", keywords: [], teamMembers: [], meetingCount: 0, createdAt: "", updatedAt: "" }],
      },
    }));
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Go menu" });
    expect(labels(menu)).toEqual([
      "Today", "Needs you", "Capture", "Meetings", "People", "Projects", "Decisions", "Agents", "Ask AI", "Speak",
      "Automations", "Memory", "Calls", "Voice commands", "Archive",
      "New",
    ]);
    expect(menu.querySelectorAll(".desk-menu-keycaps, kbd")).toHaveLength(0);
  });

  it("New has the seven shared kinds, with no ⌘ keycap", () => {
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Go menu" });
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^New\W*$/ }));
    const sub = screen.getByRole("menu");
    expect(labels(sub)).toEqual(["New", "Note", "Meeting", "Decision", "Project", "Person", "Automation", "Drawer"]);
    expect(sub.querySelectorAll(".desk-menu-keycaps, kbd")).toHaveLength(0);
  });

  it("a project row opens that project's Room", () => {
    const opened: Array<string | undefined> = [];
    const off = registerSurface("open-project-memory", (scope) => opened.push(scope));
    useDesk.setState((s) => ({
      items: {
        ...s.items,
        project: [{ kind: "project", id: "p-1", name: "Ledger cutover", description: "", keywords: [], teamMembers: [], meetingCount: 0, createdAt: "", updatedAt: "" }],
      },
    }));
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    fireEvent.click(screen.getByRole("menuitem", { name: /^Projects\W*$/ }));
    fireEvent.click(screen.getByRole("menuitem", { name: /Ledger cutover/ }));
    expect(opened).toEqual(["project:p-1"]);
    off();
  });
});
