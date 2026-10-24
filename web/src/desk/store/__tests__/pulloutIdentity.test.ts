import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../store";
import { EMPTY_ITEMS } from "../../api";
import { windowObjectEntry } from "../../objectMenu";
import type { WorkMenuEntry } from "../../components/DeskMenu";
import type { Decision, Note } from "../../../lib/primitives";

const decision: Decision = {
  kind: "decision", id: "same-id", title: "Freeze the old ledger", status: "proposed",
  deciders: [], contextMarkdown: "", decisionMarkdown: "Freeze writes on Nov 5.",
  alternatives: [], consequencesMarkdown: "", tags: [], createdAt: "2026-10-16T12:00:00Z",
};
let previous: ReturnType<typeof useDesk.getState>;

beforeEach(() => {
  previous = useDesk.getState();
  useDesk.setState({
    items: { ...EMPTY_ITEMS, decision: [decision] },
    pullouts: [], panelMin: [], panelOrder: [], panelDepth: {}, panelRects: {}, panelSaved: [],
    drafts: { "decision:same-id": "Owner's unsaved words" },
  });
});
afterEach(() => useDesk.setState(previous, true));

describe("pullout identity across bare and qualified doors", () => {
  it.each([
    { initial: "same-id", next: "decision:same-id", objectOpen: true },
    { initial: "decision:same-id", next: "same-id", objectOpen: false },
  ])("retains $initial when the second door requests $next", ({ initial, next, objectOpen }) => {
    const panelId = `pullout:${initial}`;
    const rect = { x: 120, y: 90, w: 640, h: 480 };
    const drafts = useDesk.getState().drafts;
    useDesk.getState().openPullout(initial, { x: 100, y: 80 });
    useDesk.getState().setPanelRect(panelId, rect, true);
    useDesk.getState().minimizePanel(panelId);
    useDesk.getState().focusPanel("chair:needs");
    const window = useDesk.getState().pullouts[0];
    expect(useDesk.getState().panelMin).toContain(panelId);

    if (objectOpen) {
      const menu = windowObjectEntry(panelId, vi.fn()) as Extract<WorkMenuEntry, { type: "sub" }>;
      const open = menu.entries.find((entry) => entry.id === "object.open") as Extract<WorkMenuEntry, { type: "item" }>;
      expect(open.ghost).toBeNull();
      open.onSelect();
    } else {
      useDesk.getState().openPullout(next);
    }

    expect(useDesk.getState().pullouts).toEqual([window]);
    expect(useDesk.getState().pullouts[0]).toBe(window);
    expect(useDesk.getState().panelMin).not.toContain(panelId);
    expect(useDesk.getState().panelOrder.at(-1)).toBe(panelId);
    expect(useDesk.getState().panelRects).toEqual({ [panelId]: rect });
    expect(useDesk.getState().panelSaved).toEqual([panelId]);
    expect(useDesk.getState().drafts).toBe(drafts);
    expect(useDesk.getState().items.decision).toEqual([decision]);
  });

  it("keeps two different kinds with the same bare id in distinct windows", () => {
    const note: Note = {
      kind: "note", id: decision.id, title: "Rollback notes", bodyMarkdown: "Retain this note.",
      tags: [], createdAt: decision.createdAt,
    };
    useDesk.setState({ items: { ...EMPTY_ITEMS, decision: [decision], note: [note] } });
    useDesk.getState().openPullout("note:same-id");
    useDesk.getState().openPullout("decision:same-id");

    expect(useDesk.getState().pullouts.map((window) => window.id)).toEqual(["note:same-id", "decision:same-id"]);
    expect(useDesk.getState().panelOrder.at(-1)).toBe("pullout:decision:same-id");
  });

  it("reuses a bare Note only after its live open confirmed the Note ref", () => {
    const note: Note = {
      kind: "note", id: decision.id, title: "Rollback notes", bodyMarkdown: "Retain this note.",
      tags: [], createdAt: decision.createdAt,
    };
    const fromA = { projectId: "project-a", resourceRef: "note:same-id" as const };
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note] } });
    useDesk.getState().openPullout("same-id", { x: 18, y: 27 }, { projectReturn: fromA });
    const opened = useDesk.getState().pullouts[0];
    expect(opened.sourceRef).toBe("note:same-id");
    useDesk.setState({ items: EMPTY_ITEMS });

    useDesk.getState().openPullout("note:same-id", undefined, { projectReturn: fromA });
    expect(useDesk.getState().pullouts).toEqual([opened]);
    expect(useDesk.getState().pullouts[0]).toBe(opened);
  });

  it("leaves an unknown bare window and its draft alone when a Note has the same id", () => {
    const fromA = { projectId: "project-a", resourceRef: "note:same-id" as const };
    useDesk.getState().openPullout("same-id", { x: 18, y: 27 });
    const decisionWindow = useDesk.getState().pullouts[0];
    const drafts = useDesk.getState().drafts;
    useDesk.setState({ items: EMPTY_ITEMS });

    useDesk.getState().openPullout("note:same-id", undefined, { projectReturn: fromA });
    expect(useDesk.getState().pullouts.map((row) => row.id)).toEqual(["same-id", "note:same-id"]);
    expect(useDesk.getState().pullouts[0]).toBe(decisionWindow);
    expect(useDesk.getState().pullouts[0].sourceRef).toBeUndefined();
    expect(useDesk.getState().pullouts[0].projectReturn).toBeNull();
    expect(useDesk.getState().pullouts[1].projectReturn).toEqual(fromA);
    expect(useDesk.getState().drafts).toBe(drafts);
  });
});
