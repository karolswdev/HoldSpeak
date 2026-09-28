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

// PHILO-9-06 (the closing use; Muad'Dib's ruling on catalogue gap 1): the
// agent's refusals name what would change them. Outside the grant's bound no
// grant can admit it: OWNER ONLY. Inside the bound without a grant: NO GRANT,
// the Settings grant row's own word (SettingsCore GRANT_REFUSAL_TOKEN).
describe("PHILO-9-06: the Room's refusal words match the grant row's", () => {
  it("names the owner for an owner-only code and the grant for a grant code", () => {
    expect(refusalWord("owner_principal_required")).toBe("OWNER ONLY");
    expect(refusalWord("project_delegation_required")).toBe("NO GRANT");
    expect(refusalWord("project_delegation_revoked")).toBe("GRANT STOPPED");
    expect(refusalWord("project_delegation_expired")).toBe("GRANT EXPIRED");
  });
});

// PHILO-9-06: the owner's project grant in RECEIPTS reads as the grant row's
// act words, never the kernel's dotted name.
describe("PHILO-9-06: the project grant's receipts use the grant row's words", () => {
  it("draws delegation.grant and delegation.revoke as ALLOW and STOP RUN AND PUBLISH", () => {
    expect(receiptLabel({ op: "delegation.grant", outcome: "ok" })).toBe("ALLOW RUN AND PUBLISH");
    expect(receiptLabel({ op: "delegation.revoke", outcome: "ok" })).toBe("STOP RUN AND PUBLISH");
  });
});
