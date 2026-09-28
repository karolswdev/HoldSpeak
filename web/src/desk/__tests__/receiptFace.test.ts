// PHILO-9-03 (Codex Astra r1 finding 1, closed as a class; handover XXX law 9):
// the census of every outcome a Room RECEIPT can carry -- the pipeline's
// ok/error and every kernel receipt state -- and how the face draws it. Only a
// success is drawn as success; the refused mark is the attempt, not "MARKED".
import { describe, expect, it } from "vitest";
import { receiptFace, receiptLabel, refusalWord } from "../surface/egress";

// holdspeak/db/schema.py kernel_receipts.state CHECK + the pipeline outcomes
// (project_service.py _read_room_receipts: "ok" / "error"; "ok" for succeeded).
const OUTCOMES = ["ok", "error", "succeeded", "failed", "refused", "cancelled", "indeterminate"];

describe("PHILO-9-03: every receipt outcome is drawn as what happened", () => {
  it("only a success is drawn with the success chip", () => {
    const drawn = Object.fromEntries(OUTCOMES.map((o) => [o, receiptFace(o)]));
    for (const o of OUTCOMES) {
      const success = o === "ok" || o === "succeeded";
      expect(drawn[o].state === "success", o).toBe(success);
      expect(drawn[o].word === null, o).toBe(success);
    }
    expect(drawn.refused).toMatchObject({ state: "failure", icon: "✗", word: "REFUSED" });
    expect(drawn.indeterminate.word).toBe("RESULT UNKNOWN");
    expect(receiptFace("something-new").state).toBe("failure");
  });

  it("a mark that did not happen is not labelled MARKED", () => {
    expect(receiptLabel({ op: "mark_update_delivered", outcome: "ok" })).toBe("MARKED DELIVERED");
    expect(receiptLabel({ op: "mark_update_delivered", outcome: "succeeded" })).toBe("MARKED DELIVERED");
    for (const o of OUTCOMES.filter((x) => x !== "ok" && x !== "succeeded")) {
      expect(receiptLabel({ op: "mark_update_delivered", outcome: o }), o).toBe("MARK DELIVERED");
    }
  });

  it("the refusal reasons read as plain words", () => {
    expect(refusalWord("update_not_published")).toBe("NOT PUBLISHED");
    expect(refusalWord("steward_policy_required")).toBe("NO SAVED POLICY");
    expect(refusalWord("brand_new_code")).toBe("BRAND NEW CODE");
  });
});
