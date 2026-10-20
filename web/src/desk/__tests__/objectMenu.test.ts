/** The desk object's right-click menu (objectMenu.ts), derived from the one
 * verb registry. Moved from the parked floorMenu.test.ts (PHILO-17). */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { objectMenuEntries, windowObjectEntry } from "../objectMenu";
import { seatMounted, seatUnmounted } from "../deleteSeat";
import { OBJECT_DELETE_REQUEST } from "../verbRegistry";
import { EMPTY_ITEMS, fromWireDirectory, qualifiedRef } from "../api";
import type { Meeting, Note, Project } from "../../lib/primitives";
import { useDesk } from "../store";
import type { WorkMenuEntry } from "../components/DeskMenu";
import { useScreenMembersStore } from "../screen/members";

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
  useScreenMembersStore.setState({ people: null });
});

describe("objectMenuEntries (registry-derived, parallel list #4 dead)", () => {
  it("offers a drawer's Open and dispatches its canonical ref while File stays withheld", () => {
    const directory = fromWireDirectory({ id: "dir_b5c056b59f3e", name: "Platform", parent_id: null,
      member_ids: ["note:note_0b9ebdadf0fa"], created_at: "2026-10-16T01:39:56Z" })!;
    const ref = qualifiedRef("directory", directory.id);
    useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [directory] }, selectedIds: [ref] });
    const entries = objectMenuEntries({ ref });
    const open = entries.find((entry) => entry.id === "object.open") as Extract<WorkMenuEntry, { type: "item" }>;
    expect(open).toBeDefined();
    expect(open.ghost).toBeNull();
    expect(entries.some((entry) => entry.id === "object.file")).toBe(false);
    open.onSelect();
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith(ref, undefined);
  });

  it("offers the Note's live object verbs without kind ghosts", () => {
    const entries = objectMenuEntries({ ref: "note:n1" });
    const byId = Object.fromEntries(
      entries.map((e) => [e.id, e as Extract<WorkMenuEntry, { type: "item" }>]),
    );
    expect(byId["object.open"].ghost).toBeNull();
    expect(byId["object.edit"].ghost).toBeNull();
    // Betterment Q5: one verb, Ask about this, opens Ask with the note in About.
    expect(byId["object.ask-about"].label).toBe("Ask about this");
    expect(byId["object.ask-about"].ghost).toBeNull();
    expect(byId["object.ask"]).toBeUndefined();
    expect(byId["object.ask-project"]).toBeUndefined();
    expect(byId["object.continue-in-thread"]).toBeUndefined();
    byId["object.ask-about"].onSelect();
    expect(useDesk.getState().askThread?.about?.map((chip) => chip.ref)).toEqual(["note:n1"]);
    expect(useDesk.getState().askThread?.question).toBeUndefined();
    expect(useDesk.getState().openAsk).toHaveBeenCalledOnce();
    byId["object.open"].onSelect();
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:n1", undefined);
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
      "object.ask-about",
      "object.draft-update",
      "object.rename",
      "object.archive",
    ]);
    const archive = entries.find((entry) => entry.id === "object.archive");
    expect(archive?.type === "item" && archive.ghost).toBeNull();
  });

  it("uses the Desk ledger for Keep and sends Remove to Desk or Inbox", () => {
    const desk = fromWireDirectory({ id: "hs-seed-desk", name: "Desk", parent_id: null,
      member_ids: ["meeting:m1"], created_at: "2026-10-16T01:39:56Z" })!;
    useDesk.setState({ items: {
      ...EMPTY_ITEMS,
      note: [{ kind: "note", id: "n1", title: "Release checklist" } as Note],
      meeting: [
        { kind: "meeting", id: "m1", title: "Platform sync" } as Meeting,
        { kind: "meeting", id: "m2", title: "Vendor sync" } as Meeting,
      ],
      directory: [desk],
    } });
    const file = vi.spyOn(useDesk.getState(), "fileIntoDir").mockResolvedValue();
    const unfile = vi.spyOn(useDesk.getState(), "removeFromDir").mockResolvedValue();
    const keepMeeting = objectMenuEntries({ ref: "meeting:m2" }).find((entry) => entry.id === "object.file") as Extract<WorkMenuEntry, { type: "item" }>;
    expect(keepMeeting.label).toBe("Keep on desk");
    keepMeeting.onSelect();
    expect(file).toHaveBeenCalledWith("meeting:m2", "hs-seed-desk");
    const kept = objectMenuEntries({ ref: "meeting:m1" });
    const removeMeeting = kept.find((entry) => entry.id === "object.unfile") as Extract<WorkMenuEntry, { type: "item" }>;
    expect(removeMeeting.label).toBe("Remove from desk");
    removeMeeting.onSelect();
    expect(unfile).toHaveBeenCalledWith("meeting:m1", "hs-seed-desk", "meeting");

    const unkept = objectMenuEntries({ ref: "note:n1" });
    const removeNote = unkept.find((entry) => entry.id === "object.unfile") as Extract<WorkMenuEntry, { type: "item" }>;
    removeNote.onSelect();
    expect(file).toHaveBeenCalledWith("note:n1", "hs-seed-inbox", "note");
    file.mockRestore();
    unfile.mockRestore();
  });

  it("withholds Delete until the object has a mounted delete seat", () => {
    const entries = objectMenuEntries({ ref: "note:n1" });
    const sep = entries.findIndex((e) => e.type === "sep");
    expect(sep).toBe(-1);
    expect(entries.some((e) => e.id === "object.delete")).toBe(false);
  });

  it("offers Keep and Remove for a live protected person through the Desk membership", () => {
    useDesk.setState({ items: {
      ...EMPTY_ITEMS,
      directory: [{ kind: "directory", id: "hs-seed-desk", name: "Desk", memberIds: [] } as never],
    } });
    useScreenMembersStore.setState({
      people: { state: "ready", persons: [{ id: "p1", name: "Mira" }] },
    });
    const file = vi.spyOn(useDesk.getState(), "fileIntoDir").mockResolvedValue();
    const keep = objectMenuEntries({ ref: "people:p1" }).find((entry) => entry.id === "person.keep-on-desk") as Extract<WorkMenuEntry, { type: "item" }>;
    expect(keep.label).toBe("Keep on desk");
    keep.onSelect();
    expect(file).toHaveBeenCalledWith("p1", "hs-seed-desk", "people");
    file.mockRestore();

    useDesk.setState({ items: {
      ...useDesk.getState().items,
      directory: [{ kind: "directory", id: "hs-seed-desk", name: "Desk", memberIds: ["people:p1"] } as never],
    } });
    const removeDir = vi.spyOn(useDesk.getState(), "removeFromDir").mockResolvedValue();
    const remove = objectMenuEntries({ ref: "people:p1" }).find((entry) => entry.id === "person.remove-from-desk") as Extract<WorkMenuEntry, { type: "item" }>;
    expect(remove.label).toBe("Remove from desk");
    remove.onSelect();
    expect(removeDir).toHaveBeenCalledWith("p1", "hs-seed-desk", "people");
    removeDir.mockRestore();
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

// ── Betterment shell S0: the menu bar's Object menu IS the right-click menu ──
import { createElement } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { DeskMenuBar } from "../components/DeskMenuBar";
import { withholdGhosts } from "../components/DeskMenu";
import { objectByRef } from "../world";
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
}));

describe("S0: menu bar and right-click show the same rows", () => {
  const rightClick = (ref: string) =>
    withholdGhosts(objectMenuEntries({ ref }))
      .filter((e) => e.type === "item")
      .map((e) => (e as Extract<WorkMenuEntry, { type: "item" }>).label);
  const menuBar = (title: string) => {
    fireEvent.click(screen.getByRole("button", { name: new RegExp(`^${title}$`) }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: `${title} menu` });
    return Array.from(menu.querySelectorAll("[role^=menuitem] .desk-menu-label"), (e) => e.textContent?.trim());
  };
  beforeEach(() => {
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [{ kind: "note", id: "n1", title: "Release checklist" } as Note],
        meeting: [{ kind: "meeting", id: "m1", title: "Platform sync" } as Meeting],
        project: [{ kind: "project", id: "p1", name: "Ledger migration" } as Project],
      },
      panelOrder: [],
      panelMin: [],
    } as never);
  });

  it.each([
    ["note:n1", "Note"],
    ["meeting:m1", "Meeting"],
    ["project:p1", "Project"],
  ])("%s: the %s menu equals its right-click menu", (ref, title) => {
    useDesk.setState({ selectedIds: [ref] });
    render(createElement(DeskMenuBar));
    const rows = rightClick(ref);
    expect(rows.length).toBeGreaterThan(0);
    expect(menuBar(title)).toEqual(rows);
  });

  it("a person the desk does not hold as an object: neither face offers a menu", () => {
    // The floor's right-click opens no menu for a ref objectByRef cannot
    // resolve (screen/Screen.tsx openMenu); the menu bar draws no title.
    useDesk.setState({ selectedIds: ["people:mira"] });
    expect(objectByRef(useDesk.getState().items, "people:mira")).toBeNull();
    render(createElement(DeskMenuBar));
    expect(screen.queryByRole("button", { name: /^Person$/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /^Object$/ })).toBeNull();
  });
});
