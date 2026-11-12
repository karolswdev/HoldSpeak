// Phase 16 (the interior kit; the canvas window "Cutover sync"): the meeting
// record heads with its title (the AppHead, once) and the strip
// (`TUE 14:00 · 42 MIN` · SUMMARISED · `4 PEOPLE`), then `Decisions · n` and
// `Commitments · n`, each a Section over a Ledger of kind-plated rows.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { mastFacts, meetingPlate, meetingReviewCount, meetingSpine, meetingSummaryState, peopleNames } from "../plate";
import { MeetingOutcomes, meetingOutcomes } from "../MeetingDetail";
import { useMeetingData, type FollowThroughProposal } from "../useMeetingData";
import { MEETING_OPEN_EVENT } from "../../../../desk/objectWindows";

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../lib/api")>("../../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

const text = (node: unknown) => (typeof node === "string" ? node : "");

describe("the meeting on the interior kit", () => {
  // The language (2026-11-08): the mast names the meeting (sprite, title,
  // one mono facts line: when, who, how long); the state is the status
  // bar's word; the spine says where it stands.
  it("the mast's facts say when, who and how long; the state is Summary stored", () => {
    const meeting = {
      id: "m1", title: "Cutover sync", intel_status: "complete", intel: { summary: "We froze the ledger." },
      started_at: "2026-10-06T14:00:00", duration_seconds: 42 * 60,
      segments: [{ speaker: "Jordan" }, { speaker: "Avery" }, { speaker: "jordan" }, { speaker: "" }],
    };
    const facts = mastFacts(meeting);
    expect(facts).toContain("Jordan, Avery");
    expect(facts).toContain("42 min");
    expect(facts).not.toContain("Cutover sync");
    expect(meetingSummaryState(meeting)).toEqual({ text: "Summary stored", lamp: "ok" });
  });

  it("saved Outcomes: one review count; the spine's last mark waits on him", () => {
    const meeting = { id: "m-saved", title: "Cutover sync", intel_status: "complete", intel: { summary: "We froze the ledger." }, segments: [{ speaker: "A" }] };
    const data = {
      needsCount: 0,
      ftProposals: [{ id: "p1", meeting_id: "m-saved", kind: "action" as const, text: "Write the runbook", state: "proposed" as const, created_at: "" }],
    };
    expect(meetingReviewCount(data as never)).toBe(1);
    const spine = meetingSpine(meeting, 1);
    expect(spine.segments.map((part) => part.tone)).toEqual(["moss", "moss", "moss", "brass"]);
    expect(spine.label).toBe("captured, transcribed, intelligence run, 1 to file");
  });

  it("does not say a zero review counter when the saved record is settled", () => {
    const meeting = { id: "m-done", title: "Cutover sync", intel_status: "complete", intel: { summary: "We froze the ledger." }, segments: [{ speaker: "A" }] };
    expect(meetingSpine(meeting, 0).label).not.toMatch(/0 to file/);
    expect(meetingPlate(meeting, { pending: 0 }).kind).toBe("send");
  });

  it("no people at zero; a failed summary keeps its word with the fail lamp and a coral plate", () => {
    const meeting = { id: "m2", title: "Vendor call", intel_status: "failed", segments: [{ speaker: "" }, { text: "x" }] };
    expect(peopleNames([])).toEqual([]);
    expect(mastFacts({ id: "m2", intel_status: "failed" })).toBe("");
    expect(meetingSummaryState(meeting)).toMatchObject({ lamp: "fail", text: "Summary failed" });
    expect(meetingPlate(meeting, {})).toMatchObject({ kind: "failed", tone: "coral" });
  });

  it("Decisions and Commitments: proposed rows leave gaps visible, confirmed rows name their owner, settled rows are Done", () => {
    const { decisions, commitments } = meetingOutcomes({
      ftProposals: [
        { id: "p1", meeting_id: "m1", kind: "decision", text: "Freeze the old ledger on Nov 5", state: "proposed", created_at: "" },
        { id: "p2", meeting_id: "m1", kind: "decision", text: "Reconciliation runs nightly", owner_hint: "Avery", state: "confirmed", created_at: "" },
        { id: "p4", meeting_id: "m1", kind: "decision", text: "Dropped", state: "dismissed", created_at: "" },
      ],
      openActions: [{ id: "a1", text: "Shard the reconciliation job", owner: null }],
      settledActions: [{ id: "a2", text: "Add the ledger freeze flag", owner: "Jordan", status: "done" }],
    });
    expect(decisions.map((d) => [d.plate, d.text, d.meta, d.tone])).toEqual([
      ["DEC", "Freeze the old ledger on Nov 5", "", "ask"],
      ["DEC", "Reconciliation runs nightly", "Avery", undefined],
    ]);
    expect(commitments.map((c) => [c.plate, text(c.text), c.meta, c.tone])).toEqual([
      ["ACT", "Shard the reconciliation job", "No owner · No date", undefined],
      ["ACT", "Add the ledger freeze flag", "Jordan · Done", "ok"],
    ]);
  });

  // Astra r1 M1: the producer's shape. The summary mints an action proposal
  // per action item and links them (`action_item_id`,
  // proposal_bridge_service.py); Decline sets the item's status to
  // `dismissed`. One obligation is ONE row; dismissed work is never drawn.
  it("a proposal and the action item it names are ONE row; dismissed work is never drawn", () => {
    const items = [
      { id: "ai-1", task: "Write the rollback runbook", owner: null, status: "pending" },
      { id: "ai-2", task: "Shard the reconciliation job", owner: "Sam", status: "pending" },
      { id: "ai-3", task: "Add the ledger freeze flag", owner: null, status: "dismissed" },
      { id: "ai-4", task: "Close the old ledger", owner: "Jordan", status: "done" },
    ];
    const proposal = (id: string, itemId: string | null, text: string, state: "proposed" | "confirmed" | "dismissed") => ({
      id, meeting_id: "m1", kind: "action" as const, text, state, created_at: "", action_item_id: itemId, due_hint: null,
    });
    const { commitments } = meetingOutcomes(
      {
        ftProposals: [
          proposal("p-1", "ai-1", "Write the rollback runbook", "proposed"),
          proposal("p-2", "ai-2", "Shard the reconciliation job", "confirmed"),
          proposal("p-3", "ai-3", "Add the ledger freeze flag", "dismissed"),
          proposal("p-5", null, "Book the cutover window", "proposed"),
        ],
        openActions: [],
        settledActions: [],
      },
      items,
    );
    expect(commitments.map((c) => [text(c.text), c.meta])).toEqual([
      ["Write the rollback runbook", "No owner · No date"],
      ["Shard the reconciliation job", "No owner · No date"],
      ["Book the cutover window", "No owner · No date"],
      ["Close the old ledger", "Jordan · Done"],
    ]);
    expect(commitments.filter((c) => text(c.text) === "Write the rollback runbook")).toHaveLength(1);
  });

  it("with no aftercare rows, Commitments are the meeting's own action items (never twice)", () => {
    const own = [
      { id: "a1", task: "Write the rollback runbook", owner: null, status: "pending" },
      { id: "a2", task: "Add the ledger freeze flag", owner: "Sam", status: "done" },
    ];
    const none = meetingOutcomes({ ftProposals: [], openActions: [], settledActions: [] }, own);
    expect(none.commitments.map((c) => [c.text, c.meta, c.tone])).toEqual([
      ["Write the rollback runbook", "No owner · No date", undefined],
      ["Add the ledger freeze flag", "Sam · Done", "ok"],
    ]);
    const both = meetingOutcomes({ ftProposals: [], openActions: [{ id: "x", text: "Open one" }], settledActions: [] }, own);
    expect(both.commitments.map((c) => c.text)).toEqual(["Open one"]);
    const afterDone = meetingOutcomes(
      { ftProposals: [], openActions: [], settledActions: [], completedActionIds: new Set(["a1"]) },
      own,
    );
    expect(afterDone.commitments[0]).toMatchObject({ text: "Write the rollback runbook", meta: "Done", tone: "ok" });
  });
});

// Astra r1 M2: the rendered transition. A confirmed decision stays in
// Decisions · n (TO DECIDE → its owner); a dismissed one leaves.


// PHILO-17 ("what did we decide yesterday?"): the decisions the meeting
// recorded (the `decisions` table) are on its record, above Commitments,
// even when no proposal names them.
describe("the meeting's recorded decisions (PHILO-17)", () => {
  it("meetingOutcomes draws recorded decisions; a proposal's own row once (by identity); a rejected one never", () => {
    const { decisions } = meetingOutcomes({
      ftProposals: [
        { id: "p1", meeting_id: "m1", kind: "decision", text: "Run reconciliation nightly", state: "confirmed", owner_hint: "Avery", created_at: "", decision_record_id: "rec-1" },
      ],
      openActions: [],
      settledActions: [],
      meetingDecisions: [
        { id: "d1", text: "Freeze the old ledger on Nov 5", lifecycle: "recorded" },
        // The row the confirmed proposal wrote (its record): drawn once, as the proposal.
        { id: "d2", text: "Run reconciliation nightly", lifecycle: "active", record_id: "rec-1" },
        // Astra r1 (6): the same words from another artifact are a second decision.
        { id: "d5", text: "Run reconciliation nightly", lifecycle: "recorded", source_artifact_id: "art-2" },
        { id: "d3", text: "Keep the old ledger", lifecycle: "superseded" },
        { id: "d6", text: "Shard the ledger", lifecycle: "disputed" },
        { id: "d4", text: "Drop the ledger", lifecycle: "rejected" },
      ],
    });
    expect(decisions.map((d) => [d.text, d.meta])).toEqual([
      ["Run reconciliation nightly", "Avery"],
      ["Freeze the old ledger on Nov 5", "Decided"],
      ["Run reconciliation nightly", "Decided"],
      ["Keep the old ledger", "Replaced"],
      ["Shard the ledger", "Disputed"],
    ]);
  });

  // Astra r2 (1): a confirmed proposal and its ledger row are ONE row, and
  // that row says the RECORD's state once the record is replaced or disputed.
  it("a confirmed proposal paired with its record reads REPLACED / DISPUTED, never DECIDED", () => {
    const proposal = (id: string, text: string, record: string) => ({
      id, meeting_id: "m1", kind: "decision" as const, text, state: "confirmed" as const,
      owner_hint: "Avery", created_at: "", decision_record_id: record,
    });
    const { decisions } = meetingOutcomes({
      ftProposals: [
        proposal("p1", "Freeze the old ledger on Nov 5", "rec-1"),
        proposal("p2", "Run reconciliation nightly", "rec-2"),
        proposal("p3", "Shard the ledger", "rec-3"),
      ],
      openActions: [],
      settledActions: [],
      meetingDecisions: [
        { id: "d1", text: "Freeze the old ledger on Nov 5", lifecycle: "superseded", record_id: "rec-1" },
        { id: "d2", text: "Run reconciliation nightly", lifecycle: "disputed", record_id: "rec-2" },
        { id: "d3", text: "Shard the ledger", lifecycle: "active", record_id: "rec-3" },
      ],
    });
    expect(decisions.map((d) => [d.key, d.text, d.meta])).toEqual([
      ["ft-p1", "Freeze the old ledger on Nov 5", "Replaced"],
      ["ft-p2", "Run reconciliation nightly", "Disputed"],
      ["ft-p3", "Shard the ledger", "Avery"],
    ]);
  });


});
