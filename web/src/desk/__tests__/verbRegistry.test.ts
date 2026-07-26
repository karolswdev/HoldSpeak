/** HS-105-05 — the verb-registry guard: one registry, ghosting over
 * hiding, no duplicate ids, the Go menu derived from DESK_TOOLS (the
 * palette face's same truth — two faces, one registry). */
import { describe, expect, it } from "vitest";
import { VERBS, menuVerbs } from "../verbRegistry";
import { DESK_TOOLS } from "../components/DeskToolShelf";

describe("the verb registry (HS-105-05)", () => {
  it("every verb has a unique id, a label, and a menu", () => {
    const ids = VERBS.map((v) => v.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const v of VERBS) {
      expect(v.label.length).toBeGreaterThan(0);
      expect(["desk", "object", "go"]).toContain(v.menu);
    }
  });

  it("object verbs ghost WITH a reason when nothing is selected", () => {
    for (const v of menuVerbs("object")) {
      const ghost = v.ghost({ selectedRef: null });
      expect(typeof ghost).toBe("string");
      expect((ghost as string).length).toBeGreaterThan(0);
    }
  });

  it("desk verbs are always runnable", () => {
    for (const v of menuVerbs("desk"))
      expect(v.ghost({ selectedRef: null })).toBeNull();
  });

  it("the Go menu derives from DESK_TOOLS — the shelf's same truth", () => {
    const go = menuVerbs("go");
    expect(go.map((v) => v.label)).toEqual(DESK_TOOLS.map((t) => t.label));
  });
});
