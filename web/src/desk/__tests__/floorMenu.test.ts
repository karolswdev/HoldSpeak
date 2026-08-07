/** HS-111-07 — the floor right-click (owner P0): NEW > and LAUNCH >
 * derive from the registry and route the EXACT existing store paths
 * (createPrimitive / openSurfaceOr); the menu mints nothing. */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { floorMenuEntries, objectMenuEntries } from "../floorMenu";
import { DESK_TOOLS } from "../tools";
import { EMPTY_ITEMS } from "../api";
import type { Note } from "../../lib/primitives";
import { useDesk } from "../store";
import type { WorkMenuEntry } from "../components/DeskMenu";

const sub = (entries: WorkMenuEntry[], id: string) =>
  entries.find((e) => e.type === "sub" && e.id === id) as Extract<
    WorkMenuEntry,
    { type: "sub" }
  >;

beforeEach(() => {
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      note: [{ kind: "note", id: "n1", title: "Release checklist" } as Note],
    },
    selectedIds: [],
    positions: {},
    createPrimitive: vi.fn().mockResolvedValue(undefined),
    openPullout: vi.fn(),
    openInfoWindow: vi.fn(),
    openEditor: vi.fn(),
    openAsk: vi.fn(),
  });
});

describe("floorMenuEntries", () => {
  it("NEW > carries the creates and routes createPrimitive", () => {
    const entries = floorMenuEntries();
    const news = sub(entries, "floor.new");
    expect(
      news.entries.map((e) => (e.type === "item" ? e.label : e.type)),
    ).toEqual([
      "New Note",
      "New Decision",
      "New Knowledge",
      "New Agent",
      "New Workflow",
      "New Workbench",
      "New Zone",
    ]);
    const note = news.entries[0] as Extract<WorkMenuEntry, { type: "item" }>;
    note.onSelect();
    expect(useDesk.getState().createPrimitive).toHaveBeenCalledWith("note");
  });

  it("LAUNCH > is the go.* registry face (every program, no dupes)", () => {
    const launch = sub(floorMenuEntries(), "floor.launch");
    expect(
      launch.entries.map((e) => (e.type === "item" ? e.label : e.type)),
    ).toEqual(DESK_TOOLS.map((t) => t.label));
    const ask = launch.entries.find(
      (e) => e.type === "item" && e.id === "go.ask",
    ) as Extract<WorkMenuEntry, { type: "item" }>;
    expect(ask.label).toBe("Ask AI");
    ask.onSelect();
    expect(useDesk.getState().openAsk).toHaveBeenCalledOnce();
  });

  it("the floor verbs ride below a separator, ghosted honestly", () => {
    const entries = floorMenuEntries();
    expect(entries.some((e) => e.type === "sep")).toBe(true);
    const labels = entries
      .filter((e): e is Extract<WorkMenuEntry, { type: "item" }> =>
        e.type === "item",
      )
      .map((e) => e.label);
    expect(labels).toContain("Arrange desk");
    expect(labels).toContain("Overview");
    expect(labels).toContain("Reset layout");
    const arrange = entries.find(
      (e) => e.type === "item" && e.id === "desk.arrange",
    ) as Extract<WorkMenuEntry, { type: "item" }>;
    // Nothing has been moved in this seeded desk: ghost WITH a reason.
    expect(arrange.ghost).toBe("Nothing moved");
  });
});

describe("objectMenuEntries (registry-derived, parallel list #4 dead)", () => {
  it("derives Open / Get Info / Ask AI / Ask this project / Edit with honest ghosts", () => {
    const entries = objectMenuEntries({
      type: "object",
      id: "n1",
      ref: "note:n1",
      kind: "note",
      title: "Release checklist",
    });
    const byId = Object.fromEntries(
      entries.map((e) => [e.id, e as Extract<WorkMenuEntry, { type: "item" }>]),
    );
    expect(byId["object.open"].ghost).toBeNull();
    expect(byId["object.edit"].ghost).toBeNull();
    expect(byId["object.ask"].ghost).toBeNull();
    expect(byId["object.ask-project"].ghost).toBe("Select a Project");
    byId["object.ask"].onSelect();
    expect(useDesk.getState().selectedIds).toEqual(["note:n1"]);
    expect(useDesk.getState().openAsk).toHaveBeenCalledOnce();
    byId["object.open"].onSelect();
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("n1");
    byId["object.info"].onSelect();
    expect(useDesk.getState().openInfoWindow).toHaveBeenCalledWith("note:n1");
  });
});
