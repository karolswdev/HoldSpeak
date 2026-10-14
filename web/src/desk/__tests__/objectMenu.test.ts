/** The desk object's right-click menu (objectMenu.ts), derived from the one
 * verb registry. Moved from the parked floorMenu.test.ts (PHILO-17). */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { objectMenuEntries, windowObjectEntry } from "../objectMenu";
import { seatMounted, seatUnmounted } from "../deleteSeat";
import { OBJECT_DELETE_REQUEST } from "../verbRegistry";
import { EMPTY_ITEMS } from "../api";
import type { Note, Project } from "../../lib/primitives";
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
  it("offers the Note's live object verbs without kind ghosts", () => {
    const entries = objectMenuEntries({ ref: "note:n1" });
    const byId = Object.fromEntries(
      entries.map((e) => [e.id, e as Extract<WorkMenuEntry, { type: "item" }>]),
    );
    expect(byId["object.open"].ghost).toBeNull();
    expect(byId["object.edit"].ghost).toBeNull();
    expect(byId["object.ask"].ghost).toBeNull();
    expect(byId["object.ask-project"]).toBeUndefined();
    byId["object.ask"].onSelect();
    expect(useDesk.getState().selectedIds).toEqual(["note:n1"]);
    expect(useDesk.getState().openAsk).toHaveBeenCalledOnce();
    byId["object.open"].onSelect();
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("n1", undefined);
    byId["object.info"].onSelect();
    expect(useDesk.getState().openInfoWindow).toHaveBeenCalledWith("note:n1");
  });

  it("offers the Project rows, including Draft update and Archive", () => {
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        project: [{ kind: "project", id: "p1", name: "Ledger migration" } as Project],
      },
    });
    const entries = objectMenuEntries({ ref: "project:p1" });
    expect(entries.filter((entry) => entry.type === "item").map((entry) => entry.id)).toEqual([
      "object.open",
      "object.info",
      "object.ask-project",
      "object.draft-update",
      "object.rename",
      "object.file",
      "object.archive",
    ]);
    const archive = entries.find((entry) => entry.id === "object.archive");
    expect(archive?.type === "item" && archive.ghost).toBeNull();
  });

  it("withholds Delete until the object has a mounted delete seat", () => {
    const entries = objectMenuEntries({ ref: "note:n1" });
    const sep = entries.findIndex((e) => e.type === "sep");
    expect(sep).toBe(-1);
    expect(entries.some((e) => e.id === "object.delete")).toBe(false);
  });
});

describe("PHILO-17: a window carries its object's verbs (off-desk kinds)", () => {
  const OFF_DESK = [
    { kind: "recipe", id: "r1", ref: "persona:r1", item: { kind: "recipe", id: "r1", name: "Scout" } },
    { kind: "workflow", id: "w1", ref: "workflow:w1", item: { kind: "workflow", id: "w1", name: "Triage" } },
    { kind: "kb", id: "k1", ref: "knowledge:k1", item: { kind: "kb", id: "k1", name: "Runbooks" } },
    { kind: "chain", id: "c1", ref: "sequence:c1", item: { kind: "chain", id: "c1", name: "Steps" } },
  ] as const;

  it.each(OFF_DESK)("the $kind window's Object ▸ Delete closes the window and asks the one delete", (c) => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, [c.kind]: [c.item] } as never });
    const seat = seatMounted();
    const asked: string[] = [];
    const listen = (e: Event) => asked.push(String((e as CustomEvent<{ ref?: string }>).detail?.ref));
    window.addEventListener(OBJECT_DELETE_REQUEST, listen);
    try {
      const close = vi.fn();
      const entry = windowObjectEntry(`pullout:${c.ref}`, close);
      expect(entry?.type).toBe("sub");
      const del = (entry as Extract<WorkMenuEntry, { type: "sub" }>).entries.find(
        (e) => e.id === "object.delete",
      ) as Extract<WorkMenuEntry, { type: "item" }>;
      expect(del.ghost).toBeNull();
      del.onSelect();
      expect(close).toHaveBeenCalledOnce();
      expect(asked).toEqual([c.ref]);
    } finally {
      window.removeEventListener(OBJECT_DELETE_REQUEST, listen);
      if (seat) seatUnmounted();
    }
  });

  it("a window with no desk object has no Object ▸", () => {
    expect(windowObjectEntry("surface-settings", vi.fn())).toBeNull();
    expect(windowObjectEntry("pullout:persona:missing", vi.fn())).toBeNull();
  });
});
