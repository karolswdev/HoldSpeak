// HS-144-04 — compact chrome preserves the existing Go registry menu.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, registerSurface } from "../shell";
import { useChairState } from "../chairState";
import { useDesk } from "../store";
import { DeskMenuBar } from "./DeskMenuBar";

beforeEach(__resetSurfaces);
afterEach(__resetSurfaces);

describe("DeskMenuBar", () => {
  it("marks the registry-derived Go title and launches Meetings through its real menu", () => {
    const opened: Array<string | undefined> = [];
    const off = registerSurface("review-meetings", (scope) => opened.push(scope));
    const { container } = render(<DeskMenuBar />);

    expect(
      container.querySelector('[data-menu-id="go"]'),
    ).toContainElement(screen.getByRole("button", { name: /^Go$/ }));
    expect(container.querySelectorAll("[data-menu-id]")).toHaveLength(4);

    // A keyboard click exercises the title's existing Enter/Space path.
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }));
    const menu = screen.getByRole("menu", { name: "Go menu" });
    expect(menu).toBeVisible();
    fireEvent.click(screen.getByRole("menuitem", { name: /Meetings/ }));

    expect(opened).toEqual([undefined]);
    off();
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
    useChairState.setState({ surface: "chair" });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
    useDesk.setState((s) => ({ items: { ...s.items, project: [] } }));
  });

  const labels = (menu: HTMLElement) =>
    Array.from(menu.querySelectorAll("[role^=menuitem] .desk-menu-label"), (e) => e.textContent?.trim());

  it("Go is ten rows: Chair windows, places, the projects, New; no ⌘ keycap", () => {
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
      "Needs you", "Brief", "The week", "Capture",
      "Meetings", "People", "Conductor", "Settings",
      "Ledger cutover",
      "New",
    ]);
    expect(menu.querySelectorAll(".desk-menu-keycaps, kbd")).toHaveLength(0);
  });

  it("New is Thought / Meeting / Project / Person, with no ⌘ keycap", () => {
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Go menu" });
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^New\W*$/ }));
    const sub = screen.getByRole("menu");
    expect(labels(sub)).toEqual(["New", "Thought", "Meeting", "Project", "Person"]);
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
    fireEvent.click(screen.getByRole("menuitem", { name: /Ledger cutover/ }));
    expect(opened).toEqual(["project:p-1"]);
    off();
  });
});
