/** HS-105-05 — the verb-registry guard: one registry, ghosting over
 * hiding, no duplicate ids, the Go menu derived from DESK_TOOLS.
 * HS-111-07 (v2) — the registry is the ONE verb truth: scopes are
 * closed, the create set includes Workflow (the drifted parallel list
 * died), the floor verbs exist, and the keymap's bound set is exactly
 * the verbs that declare a key. */
import { describe, expect, it } from "vitest";
import { VERBS, menuVerbs, verbLabel, verbsFor, verbById } from "../verbRegistry";
import { DESK_TOOLS } from "../tools";
import { registerSurface } from "../shell";
import { THREAD_SLASH_COMMANDS } from "../components/ThreadComposer";

const CTX = { selectedRef: null };

describe("the verb registry (HS-105-05 / HS-111-07 v2)", () => {
  it("every verb has a unique id, a label, and a closed scope", () => {
    const ids = VERBS.map((v) => v.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).toContain("go.ask");
    expect(ids).toContain("object.ask");
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

  it("the create set derives Workflow too (the drifted list is dead)", () => {
    const creates = verbsFor("floor")
      .filter((v) => v.group === "new")
      .map((v) => v.id);
    expect(creates).toEqual([
      "desk.new-note",
      "desk.new-decision",
      "desk.new-knowledge",
      "desk.new-agent",
      "desk.new-workflow",
      "desk.new-workbench",
      "desk.new-zone",
      "desk.new-thread",
    ]);
    for (const v of verbsFor("floor").filter((x) => x.group === "new"))
      expect(v.ghost(CTX)).toBeNull();
  });

  it("the floor owns its verbs (arrange / overview / reset / view)", () => {
    const floor = verbsFor("floor").map((v) => v.id);
    for (const id of [
      "desk.toggle-view",
      "desk.arrange",
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

  it("the Go menu derives from DESK_TOOLS — the deck's same truth", () => {
    const go = menuVerbs("go");
    expect(go.map((v) => verbLabel(v, CTX))).toEqual(
      DESK_TOOLS.map((t) => t.label),
    );
  });

  it("the bound key set is the HS-101 grammar, declared in the registry", () => {
    const keys = VERBS.filter((v) => v.key).map((v) => [v.id, v.key]);
    expect(Object.fromEntries(keys)).toEqual({
      "desk.new-note": "⌘N",
      "desk.new-decision": "⌘⇧N",
      "desk.overview": "⌃↑",
      "object.rename": "F2",
      "object.delete": "Delete",
      "go.ask": "⌘I",
      "go.dictate": "⌘1",
      "go.review-meetings": "⌘2",
      "go.inspect-personas-and-coders": "⌘3",
      "go.configure-settings": "⌘4",
      "window.close": "⌘W",
      "window.minimize": "⌘M",
      "window.cycle": "⌃`",
      "window.cycle-reverse": "⌃⇧`",
      "system.search": "⌘K",
      "system.sheet": "⌘/",
    });
  });

  it("the view toggle names the OTHER view", () => {
    const toggle = VERBS.find((v) => v.id === "desk.toggle-view")!;
    expect(["List view", "Spatial view"]).toContain(verbLabel(toggle, CTX));
  });

  it("every THREAD_SLASH_COMMANDS entry has a registered verb id (HS-153-02)", () => {
    for (const cmd of THREAD_SLASH_COMMANDS) {
      const verb = verbById(cmd.verbId);
      expect(verb, `verb ${cmd.verbId} not found for slash command /${cmd.id}`).toBeDefined();
      expect(verb!.scope).toBe("thread");
    }
  });
});
