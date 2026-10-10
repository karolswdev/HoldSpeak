/** The desk object's right-click menu (objectMenu.ts), derived from the one
 * verb registry. Moved from the parked floorMenu.test.ts (PHILO-17). */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { objectMenuEntries } from "../objectMenu";
import { EMPTY_ITEMS } from "../api";
import type { Note } from "../../lib/primitives";
import { useDesk } from "../store";
import type { WorkMenuEntry } from "../components/DeskMenu";

beforeEach(() => {
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      note: [{ kind: "note", id: "n1", title: "Release checklist" } as Note],
    },
    selectedIds: [],
    positions: {},
    openPullout: vi.fn(),
    openInfoWindow: vi.fn(),
    openEditor: vi.fn(),
    openAsk: vi.fn(),
  });
});

describe("objectMenuEntries (registry-derived, parallel list #4 dead)", () => {
  it("derives Open / Get Info / Ask AI / Ask this project / Edit with honest ghosts", () => {
    const entries = objectMenuEntries({ ref: "note:n1" });
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
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("n1", undefined);
    byId["object.info"].onSelect();
    expect(useDesk.getState().openInfoWindow).toHaveBeenCalledWith("note:n1");
  });

  it("puts Delete after a separator, its own danger group", () => {
    const entries = objectMenuEntries({ ref: "note:n1" });
    const sep = entries.findIndex((e) => e.type === "sep");
    expect(sep).toBeGreaterThan(0);
    expect(entries.slice(sep + 1).map((e) => e.id)).toEqual(["object.delete"]);
  });
});
