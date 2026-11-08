/** HS-105-02 — the drop-matrix guard: contract data, named verbs,
 * refusal by omission. Components never hardcode kind pairs. */
import { describe, expect, it } from "vitest";
import { DROP_MATRIX, dropRule } from "../dropMatrix";

describe("the drop matrix (HS-105-02)", () => {
  it("groundables land on capability kinds with the named verb", () => {
    for (const target of ["recipe", "chain", "workflow"]) {
      const rule = dropRule(target, "note");
      expect(rule?.action).toBe("ground-into");
      expect(rule?.verb).toBe("Hold as source");
    }
    expect(dropRule("recipe", "meeting")?.action).toBe("ground-into");
  });

  it("knowledge accepts filables with the named verb", () => {
    expect(dropRule("kb", "note")?.action).toBe("file-knowledge");
    expect(dropRule("kb", "note")?.verb).toBe("Add to Knowledge");
  });

  it("unlisted pairs refuse (inert, never a guess)", () => {
    expect(dropRule("note", "note")).toBeNull();
    expect(dropRule("recipe", "coder")).toBeNull();
    expect(dropRule("kb", "kb")).toBeNull();
    expect(dropRule("meeting", "note")).toBeNull();
  });

  it("every rule names a verb and an action (no silent drops)", () => {
    for (const rule of Object.values(DROP_MATRIX)) {
      expect(rule.verb.length).toBeGreaterThan(0);
      expect(["ground-into", "file-knowledge"]).toContain(rule.action);
    }
  });
});
