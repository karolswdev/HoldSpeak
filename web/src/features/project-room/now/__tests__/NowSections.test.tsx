import { describe, expect, it } from "vitest";
import { thisWeekGroups } from "../NowSections";

describe("the Room Now page groups", () => {
  it("puts open work before decisions and keeps the page source", () => {
    const groups = thisWeekGroups(
      {
        nextDate: null,
        lastUpdateAt: null,
        meetingsThisWeek: 0,
        risks: [],
        decided: [{ id: "d1", text: "Keep the ledger read-only", at: "", ref: "", source: "", sourceRef: "decision:d1" }],
      },
      [{
        slug: "what-is-open",
        question: "What is open and who owes it?",
        sentences: [{ text: "Mira owes the rollback runbook.", refs: [{ ref: "meeting:m1", token: "1:1 WITH MIRA", opens: true }] }],
        built_at: "2026-10-19T09:00:00Z",
        stale: false,
        new_sources: 0,
        model: "pages",
        boundary: "local",
      }],
    );

    expect(groups.map((group) => group.title)).toEqual(["Open", "Decided"]);
    expect(groups[0].lines[0].refs).toEqual([{ ref: "meeting:m1", token: "1:1 WITH MIRA", opens: true }]);
  });
});
