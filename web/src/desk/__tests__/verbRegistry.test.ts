/** HS-105-05 — the verb-registry guard: one registry, ghosting over
 * hiding, no duplicate ids, the Go menu derived from DESK_TOOLS.
 * HS-111-07 (v2) — the registry is the ONE verb truth: scopes are
 * closed, the create set includes Workflow (the drifted parallel list
 * died), the floor verbs exist, and the keymap's bound set is exactly
 * the verbs that declare a key. */
import { describe, expect, it, vi } from "vitest";
import { VERBS, menuVerbs, verbLabel, verbsFor, verbById } from "../verbRegistry";
import { DESK_TOOLS } from "../tools";
import { GO_GROUPS, applicationForAction, applicationVerbId, goRows } from "../applications";
import { registerSurface } from "../shell";
import { THREAD_SLASH_COMMANDS } from "../components/ThreadComposer";
import { EMPTY_ITEMS, fromWireDirectory, qualifiedRef } from "../api";
import { useDesk } from "../store";
import { windowObjectEntry } from "../objectMenu";
import type { Decision } from "../../lib/primitives";
import type { WorkMenuEntry } from "../components/DeskMenu";

const CTX = { selectedRef: null };

describe("the verb registry (HS-105-05 / HS-111-07 v2)", () => {
  it("Object Open restores an existing qualified decision as one canonical pullout", () => {
    const decision: Decision = {
      kind: "decision", id: "d-freeze", title: "Freeze the old ledger on Nov 5", status: "proposed",
      deciders: [], contextMarkdown: "", decisionMarkdown: "Freeze writes on Nov 5.",
      alternatives: [], consequencesMarkdown: "", tags: [], createdAt: "2026-10-16T12:00:00Z",
    };
    const ref = qualifiedRef(decision.kind, decision.id);
    const panelId = `pullout:${ref}`;
    const previous = useDesk.getState();
    useDesk.setState({
      items: { ...EMPTY_ITEMS, decision: [decision] },
      pullouts: [], panelMin: [], panelOrder: [], panelDepth: {},
    });
    try {
      useDesk.getState().openPullout(ref);
      useDesk.getState().minimizePanel(panelId);
      useDesk.getState().focusPanel("chair:needs");
      expect(useDesk.getState().panelMin).toContain(panelId);
      const menu = windowObjectEntry(panelId, vi.fn()) as Extract<WorkMenuEntry, { type: "sub" }>;
      const open = menu.entries.find((entry) => entry.id === "object.open") as Extract<WorkMenuEntry, { type: "item" }>;
      expect(open.ghost).toBeNull();

      open.onSelect();

      expect(useDesk.getState().pullouts.map((pullout) => pullout.id)).toEqual([ref]);
      expect(useDesk.getState().panelMin).not.toContain(panelId);
      expect(useDesk.getState().panelOrder.at(-1)).toBe(panelId);
      expect(useDesk.getState().items.decision).toEqual([decision]);
    } finally {
      useDesk.setState(previous, true);
    }
  });

  it("opens a selected drawer by canonical ref and preserves its pointer origin", () => {
    const directory = fromWireDirectory({ id: "dir_b5c056b59f3e", name: "Platform", parent_id: null,
      member_ids: ["note:note_0b9ebdadf0fa"], created_at: "2026-10-16T01:39:56Z" })!;
    const ref = qualifiedRef("directory", directory.id);
    const previous = useDesk.getState();
    const openPullout = vi.fn();
    useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [directory] }, selectedIds: [ref], openPullout });
    try {
      const open = verbById("object.open")!;
      const ctx = { selectedRef: ref, origin: { x: 120, y: 90 } };
      expect(open.ghost(ctx)).toBeNull();
      open.run(ctx);
      expect(openPullout).toHaveBeenCalledWith(ref, ctx.origin);
    } finally {
      useDesk.setState({ items: previous.items, selectedIds: previous.selectedIds, openPullout: previous.openPullout });
    }
  });

  it("every verb has a unique id, a label, and a closed scope", () => {
    const ids = VERBS.map((v) => v.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).toContain("go.ask");
    expect(ids).toContain("object.ask-about");
    for (const v of VERBS) {
      expect(verbLabel(v, CTX).length).toBeGreaterThan(0);
      expect(["floor", "object", "go", "window", "system", "thread"]).toContain(v.scope);
      if (v.menu) expect(["desk", "object", "go", "window"]).toContain(v.menu);
    }
  });

  it("object verbs ghost WITH a reason when nothing is selected", () => {
    for (const v of menuVerbs("object")) {
      const ghost = v.ghost({ selectedRef: null });
      expect(typeof ghost).toBe("string");
      expect((ghost as string).length).toBeGreaterThan(0);
    }
  });

  it("the create set is derived from the registry (the drifted list is dead)", () => {
    const creates = verbsFor("floor")
      .filter((v) => v.group === "new")
      .map((v) => v.id);
    expect(creates).toEqual([
      "desk.new-note", // Betterment Q8: also ⌃T (Write a thought is parked)
      "desk.new-decision",
      // Betterment A8: one way to automate; New Workflow is parked.
      "desk.new-workbench",
      "desk.new-project",
      "desk.new-meeting",
      "desk.new-person",
      "desk.new-drawer",
    ]);
    for (const v of verbsFor("floor").filter((x) => x.group === "new"))
      expect(v.ghost(CTX)).toBeNull();
  });

  // PHILO-17: List view, Arrange desk, New Zone and Focus are parked with the Floor.
  it("the desk owns its verbs (overview / reset / refresh); the Floor's are parked", () => {
    const floor = verbsFor("floor").map((v) => v.id);
    for (const id of ["desk.toggle-view", "desk.arrange", "desk.new-zone", "zone.focus"])
      expect(VERBS.map((v) => v.id)).not.toContain(id);
    for (const id of [
      "desk.overview",
      "desk.reset-layout",
      "desk.reset-to-seed",
      "desk.refresh",
    ])
      expect(floor).toContain(id);
  });

  it("reset-to-seed opens the Prefs Desk module — never destroys directly (HS-112-03)", () => {
    const verb = VERBS.find((v) => v.id === "desk.reset-to-seed")!;
    expect(verb.scope).toBe("floor");
    expect(verb.ghost(CTX)).toBeNull();
    const opened: Array<string | undefined> = [];
    const off = registerSurface("configure-settings", (scope) =>
      opened.push(scope),
    );
    verb.run(CTX);
    off();
    // The verb's whole act is opening the armed confirm face.
    expect(opened).toEqual(["desk"]);
  });

  it("PHILO-17 (doors): the Go verbs are the manifest's Go rows", () => {
    const go = new Set(menuVerbs("go").map((v) => v.id));
    const placed = GO_GROUPS.flatMap(goRows).flatMap((r) => (r.kind === "app" ? [applicationVerbId(r.app)] : []));
    expect([...go].sort()).toEqual([...placed].sort());
    // Every DESK_TOOLS row has the verb that opens it (⌘K, keys, the HoldSpeak menu).
    for (const tool of DESK_TOOLS)
      expect(verbById(applicationVerbId(applicationForAction(tool.action)!)), tool.action).toBeTruthy();
  });

  it("the bound key set is the HS-101 grammar, declared in the registry", () => {
    const keys = VERBS.filter((v) => v.key).map((v) => [v.id, v.key]);
    expect(Object.fromEntries(keys)).toEqual({
      "desk.new-note": "⌃N",
      "desk.new-decision": "⌃⇧N",
      "desk.overview": "⌘⇧E",
      "object.rename": "F2",
      "object.delete": "Delete",
      "go.ask": "⌘I",
      "desk.open-intelligence": "⌃1",
      "go.review-meetings": "⌃2",
      "desk.open-people": "⌃3",
      "go.open-conductor": "⌃4",
      "go.dictate": "⌃5",
      "go.open-programs": "⌃7",
      "go.configure-settings": "⌃,",
      "chair.window.needs": "⌃J",
      "window.close": "⌃W",
      "window.minimize": "⌃M",
      // PHILO-16 §5: the compositor's keys (the C2 keys ⌃M, ⌃B, ⌃` stay
      // bound one release as altKeys; the reverse cycle has no key now).
      "window.maximize": "⌘⇧Z",
      "window.depth": "⌘⇧`",
      "window.cycle": "⌘`",
      "window.snap-left": "⌘⌥←",
      "window.snap-right": "⌘⌥→",
      "window.stage": "⌘⏎",
      "window.gather": "⌘G",
      "window.back": "Esc",
      "system.search": "⌘K",
      "system.sheet": "⌘/",
    });
  });

  it("every THREAD_SLASH_COMMANDS entry has a registered verb id (HS-153-02)", () => {
    for (const cmd of THREAD_SLASH_COMMANDS) {
      const verb = verbById(cmd.verbId);
      expect(verb, `verb ${cmd.verbId} not found for slash command /${cmd.id}`).toBeDefined();
      expect(verb!.scope).toBe("thread");
    }
  });
});

// Betterment setup ST1: the parked Rhythm and Change places rows open
// through Settings aliases (SurfaceWindows: DESK_APPLICATION_ALIASES) at
// their sections. Search keeps both historical names; neither owns a key.
describe("Betterment setup ST1: one home each", () => {
  it("parked rows keep their Settings aliases without a retired key", () => {
    const opened: Array<[string, string | undefined]> = [];
    const offs = ["change-places", "configure-cadence"].map((key) =>
      registerSurface(key, (scope) => opened.push([key, scope])));
    try {
      expect(verbById("go.change-places")?.key).toBeUndefined();
      verbById("go.change-places")!.run(CTX);
      verbById("go.configure-cadence")!.run(CTX);
      expect(opened).toEqual([["change-places", undefined], ["configure-cadence", undefined]]);
      // No live window answers for them: the Settings verbs exist instead.
      expect(verbById("settings.rhythm")).toBeTruthy();
      expect(verbById("settings.wallpaper")).toBeTruthy();
    } finally {
      offs.forEach((off) => off());
    }
  });
});
