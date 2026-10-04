/** Inventory gap 9 (2026-10-03) — ⌘K finds a word inside a thing.
 *
 * One MEMORY band, backed by `/api/memory/search`: debounced, after the local
 * matches, each row opening its object through `refOpener`. A short query
 * reads nothing; no hits shows no band. Real store, real palette, real
 * opener; the hub transport is the double. */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
const opened = vi.hoisted(() => ({ surfaces: [] as Array<[string, string | undefined]> }));
vi.mock("../shell", async () => {
  const actual = await vi.importActual<typeof import("../shell")>("../shell");
  return {
    ...actual,
    openSurface: (key: string, scope?: string) => { opened.surfaces.push([key, scope]); return true; },
    openSurfaceOr: (key: string, _href: string, scope?: string) => { opened.surfaces.push([key, scope]); },
  };
});

import { EMPTY_ITEMS } from "../api";
import type { Meeting, Note } from "../../lib/primitives";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { DeskToolShelf, MEMORY_DEBOUNCE_MS } from "../components/DeskToolShelf";

let searches: string[] = [];
let hits: Array<Record<string, unknown>> = [];

beforeEach(() => {
  localStorage.clear();
  opened.surfaces = [];
  searches = [];
  hits = [];
  usePalette.setState({ open: false });
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string) => {
    if (path.startsWith("/api/memory/search?")) {
      searches.push(new URLSearchParams(path.split("?")[1]).get("query") ?? "");
      return Promise.resolve({ hits });
    }
    return Promise.resolve({});
  });
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      note: [{ kind: "note", id: "n-1", title: "Zircon plan", bodyMarkdown: "", tags: [], createdAt: "" } as Note],
      meeting: [{ kind: "meeting", id: "m-local", title: "Zircon review" } as Meeting],
    },
    projects: [],
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    openPullout: vi.fn(),
    refresh: vi.fn().mockResolvedValue(undefined),
    openToolInspector: vi.fn(),
    diveInto: vi.fn(),
  });
});

async function settle(ms = 0) {
  await act(async () => { await new Promise((r) => setTimeout(r, ms)); });
}

async function deck() {
  render(<MemoryRouter><DeskToolShelf /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: /Search/ }));
  await settle();
  return screen.getByRole("combobox", { name: "Search tools and Desk items" });
}

async function type(input: HTMLElement, q: string, wait = MEMORY_DEBOUNCE_MS + 60) {
  fireEvent.change(input, { target: { value: q } });
  await settle(wait);
}

const bands = () => [...document.querySelectorAll(".desk-deck-band")].map((b) => b.textContent);
const options = () => screen.queryAllByRole("option").map((o) => o.textContent ?? "");

describe("the palette finds a word inside a meeting", () => {
  it("a word that is only in a transcript shows the meeting in MEMORY; the row opens the meeting", async () => {
    hits = [{ kind: "meeting", source_ref: "meeting:m-77", title: "Cutover sync",
      snippet: "we keep the <mark>quokka</mark> ledger until Friday" }];
    const input = await deck();
    await type(input, "quokka");
    expect(searches).toEqual(["quokka"]);
    expect(bands()).toEqual(["MEMORY"]);
    const row = screen.getByRole("option", { name: /Cutover sync/ });
    expect(row.textContent).toContain("we keep the quokka ledger until Friday");
    expect(row.textContent).not.toContain("<mark>");
    expect(row.textContent).toContain("MEETING");
    fireEvent.click(row);
    expect(opened.surfaces).toContainEqual(["review-meetings", "meeting:m-77"]);
  });

  it("Enter runs the memory row when it is the only match", async () => {
    hits = [{ kind: "note", source_ref: "note:n-9", title: "Runbook", snippet: "the <mark>quokka</mark> step" }];
    const input = await deck();
    await type(input, "quokka");
    fireEvent.keyDown(input, { key: "Enter" });
    // The shell's opener refreshes the desk, then opens the pull-out.
    await vi.waitFor(() => expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:n-9"));
  });

  it("the MEMORY band comes after the local matches, and an object a local row shows is not shown twice", async () => {
    hits = [
      { kind: "meeting", source_ref: "meeting:m-local", title: "Zircon review", snippet: "<mark>zircon</mark>" },
      { kind: "meeting", source_ref: "meeting:m-77", title: "Cutover sync", snippet: "the <mark>zircon</mark> rollout" },
      { kind: "meeting", source_ref: "meeting:m-77", title: "Cutover sync", snippet: "more <mark>zircon</mark>" },
    ];
    const input = await deck();
    await type(input, "zircon");
    expect(bands().at(-1)).toBe("MEMORY");
    expect(bands().filter((b) => b === "MEMORY")).toHaveLength(1);
    const all = options();
    expect(all.filter((o) => o.includes("Zircon review"))).toHaveLength(1);
    expect(all.filter((o) => o.includes("Cutover sync"))).toHaveLength(1);
    expect(all.findIndex((o) => o.includes("Zircon review"))).toBeLessThan(all.findIndex((o) => o.includes("Cutover sync")));
    // The top hit stays a local match: late memory rows never move the selection.
    const top = screen.getAllByRole("option").find((o) => o.className.includes("is-selected"));
    expect(top?.textContent).toContain("Zircon");
    expect(top?.textContent).not.toContain("Cutover sync");
  });

  it("the search is debounced: one read for the settled query", async () => {
    const input = await deck();
    await type(input, "quo", 20);
    await type(input, "quok", 20);
    await type(input, "quokka");
    expect(searches).toEqual(["quokka"]);
  });

  it("a short query reads nothing; no hits shows no MEMORY band", async () => {
    const input = await deck();
    await type(input, "qu");
    expect(searches).toEqual([]);
    await type(input, "quokka");
    expect(searches).toEqual(["quokka"]);
    expect(bands()).not.toContain("MEMORY");
    expect(screen.getByText("No matching tools or Desk items.")).toBeTruthy();
  });

  it("a hit that opens nothing is left out; old hits never show under a new query", async () => {
    hits = [
      { kind: "cadence", source_ref: "cadence:c-1", title: "Loop", snippet: "<mark>quokka</mark>" },
      { kind: "meeting", source_ref: "meeting:m-77", title: "Cutover sync", snippet: "<mark>quokka</mark>" },
    ];
    const input = await deck();
    await type(input, "quokka");
    expect(options().some((o) => o.includes("Loop"))).toBe(false);
    expect(options().some((o) => o.includes("Cutover sync"))).toBe(true);
    hits = [];
    await type(input, "wombat", 20);
    expect(options().some((o) => o.includes("Cutover sync"))).toBe(false);
  });
});
