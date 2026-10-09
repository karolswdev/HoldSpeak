// Phase 16 (the interior kit; the canvas window "Cutover sync"): the meeting
// record heads with its title (the AppHead, once) and the strip
// (`TUE 14:00 · 42 MIN` · SUMMARISED · `4 PEOPLE`), then `Decisions · n` and
// `Commitments · n`, each a Section over a Ledger of kind-plated rows.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MeetingHeader, meetingStripItems, peopleCount } from "../MeetingHeader";
import { meetingOutcomes } from "../MeetingDetail";

const text = (node: unknown) => (typeof node === "string" ? node : "");

describe("the meeting on the interior kit", () => {
  it("the title is the one display fact; the strip says when, length, SUMMARISED and the people", () => {
    const meeting = { id: "m1", title: "Cutover sync", intel_status: "complete", intel: { summary: "We froze the ledger." } };
    const data = {
      detail: meeting,
      startedAt: "2026-10-06T14:00:00",
      durationS: 42 * 60,
      segments: [{ speaker: "Jordan" }, { speaker: "Avery" }, { speaker: "jordan" }, { speaker: "" }],
    };
    const { container } = render(<MeetingHeader meeting={meeting} data={data as never} />);
    expect(container.querySelectorAll(".kit-disp")).toHaveLength(1);
    expect(container.querySelector(".kit-disp")?.textContent).toBe("Cutover sync");
    const strip = container.querySelector(".meetings-detail-facts") as HTMLElement;
    expect(strip.textContent).toContain("42 MIN");
    expect(screen.getByTestId("meeting-summary-state").textContent).toBe("SUMMARISED");
    expect(screen.getByTestId("meeting-summary-state").querySelector(".kit-sq")?.getAttribute("data-tone")).toBe("ok");
    expect(strip.textContent).toContain("2 PEOPLE");
  });

  it("no people token at zero; a failed summary keeps its word with the fail lamp", () => {
    const meeting = { id: "m2", title: "Vendor call", intel_status: "failed" };
    const items = meetingStripItems(meeting, { detail: meeting, startedAt: null, durationS: 0, segments: [] });
    expect(peopleCount([])).toBe(0);
    expect(items.map((i) => i.key)).toEqual(["state"]);
    expect(items[0]).toMatchObject({ lamp: "fail", text: "SUMMARY FAILED" });
  });

  it("Decisions and Commitments: proposed ones ask, open ones name their owner, settled ones are DONE", () => {
    const { decisions, commitments } = meetingOutcomes({
      ftProposals: [
        { id: "p1", meeting_id: "m1", kind: "decision", text: "Freeze the old ledger on Nov 5", state: "proposed", created_at: "" },
        { id: "p2", meeting_id: "m1", kind: "decision", text: "Reconciliation runs nightly", owner_hint: "Avery", state: "confirmed", created_at: "" },
        { id: "p3", meeting_id: "m1", kind: "action", text: "Write the rollback runbook", due_hint: "Fri", state: "proposed", created_at: "" },
        { id: "p4", meeting_id: "m1", kind: "decision", text: "Dropped", state: "dismissed", created_at: "" },
      ],
      openActions: [{ id: "a1", text: "Shard the reconciliation job", owner: null }],
      settledActions: [{ id: "a2", text: "Add the ledger freeze flag", owner: "Jordan" }],
    });
    expect(decisions.map((d) => [d.plate, d.text, d.meta, d.tone])).toEqual([
      ["DEC", "Freeze the old ledger on Nov 5", "TO DECIDE", "ask"],
      ["DEC", "Reconciliation runs nightly", "AVERY", undefined],
    ]);
    expect(commitments.map((c) => [c.plate, text(c.text), c.meta, c.tone])).toEqual([
      ["ACT", "Write the rollback runbook", "TO CONFIRM · BY FRI", "ask"],
      ["ACT", "Shard the reconciliation job", "UNASSIGNED", undefined],
      ["ACT", "Add the ledger freeze flag", "DONE · JORDAN", "ok"],
    ]);
  });

  it("with no aftercare rows, Commitments are the meeting's own action items (never twice)", () => {
    const own = [
      { id: "a1", task: "Write the rollback runbook", owner: null, status: "pending" },
      { id: "a2", task: "Add the ledger freeze flag", owner: "Sam", status: "done" },
    ];
    const none = meetingOutcomes({ ftProposals: [], openActions: [], settledActions: [] }, own);
    expect(none.commitments.map((c) => [c.text, c.meta, c.tone])).toEqual([
      ["Write the rollback runbook", "UNASSIGNED", undefined],
      ["Add the ledger freeze flag", "DONE · SAM", "ok"],
    ]);
    const both = meetingOutcomes({ ftProposals: [], openActions: [{ id: "x", text: "Open one" }], settledActions: [] }, own);
    expect(both.commitments.map((c) => c.text)).toEqual(["Open one"]);
  });
});
