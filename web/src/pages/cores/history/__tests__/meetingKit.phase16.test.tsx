// Phase 16 (the interior kit; the canvas window "Cutover sync"): the meeting
// record heads with its title (the AppHead, once) and the strip
// (`TUE 14:00 · 42 MIN` · SUMMARISED · `4 PEOPLE`), then `Decisions · n` and
// `Commitments · n`, each a Section over a Ledger of kind-plated rows.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MeetingHeader, meetingStripItems, peopleCount } from "../MeetingHeader";
import { MeetingOutcomes, meetingOutcomes } from "../MeetingDetail";
import { useMeetingData } from "../useMeetingData";

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

  it("Decisions and Commitments: proposed ones ask, confirmed ones name their owner, settled ones are DONE", () => {
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
      ["DEC", "Freeze the old ledger on Nov 5", "TO DECIDE", "ask"],
      ["DEC", "Reconciliation runs nightly", "AVERY", undefined],
    ]);
    expect(commitments.map((c) => [c.plate, text(c.text), c.meta, c.tone])).toEqual([
      ["ACT", "Shard the reconciliation job", "UNASSIGNED", undefined],
      ["ACT", "Add the ledger freeze flag", "DONE · JORDAN", "ok"],
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
      ["Write the rollback runbook", "TO CONFIRM"],
      ["Shard the reconciliation job", "SAM"],
      ["Close the old ledger", "DONE · JORDAN"],
      ["Book the cutover window", "TO CONFIRM"],
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
      ["Write the rollback runbook", "UNASSIGNED", undefined],
      ["Add the ledger freeze flag", "DONE · SAM", "ok"],
    ]);
    const both = meetingOutcomes({ ftProposals: [], openActions: [{ id: "x", text: "Open one" }], settledActions: [] }, own);
    expect(both.commitments.map((c) => c.text)).toEqual(["Open one"]);
  });
});

// Astra r1 M2: the rendered transition. A confirmed decision stays in
// Decisions · n (TO DECIDE → its owner); a dismissed one leaves.
describe("the meeting's Decisions through Confirm (the hook and the ledger, rendered)", () => {
  it("Confirm keeps the decision on the record, decided; Dismiss removes it", async () => {
    const meeting = {
      id: "m1", title: "Cutover sync", intel_status: "complete",
      intel: { summary: "s", action_items: [{ id: "ai-1", task: "Write the rollback runbook", owner: null, status: "pending" }] },
    };
    let proposals = [
      { id: "p1", meeting_id: "m1", kind: "decision", text: "Freeze the old ledger on Nov 5", owner_hint: "Jordan", state: "proposed", created_at: "" },
      { id: "p2", meeting_id: "m1", kind: "decision", text: "Run reconciliation nightly", state: "proposed", created_at: "" },
      { id: "p3", meeting_id: "m1", kind: "action", text: "Write the rollback runbook", state: "proposed", created_at: "", action_item_id: "ai-1" },
    ];
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (init?.method === "POST") return {};
      if (url.includes("/follow-through-proposals")) return { proposals };
      if (url === "/api/meetings/m1") return meeting;
      return {};
    });
    function Harness() {
      const data = useMeetingData(meeting, () => undefined);
      return <MeetingOutcomes data={data} meeting={meeting} />;
    }
    render(<Harness />);
    const decisions = await screen.findByTestId("meeting-decisions");
    expect(decisions.querySelector("h3")?.textContent).toBe("Decisions · 2");
    expect(screen.getByTestId("meeting-commitments").querySelector("h3")?.textContent).toBe("Commitments · 1");
    fireEvent.click(within(decisions).getByRole("button", { name: "Confirm: Freeze the old ledger on Nov 5" }));
    await waitFor(() => {
      const row = within(screen.getByTestId("meeting-decisions")).getByText("Freeze the old ledger on Nov 5").closest(".surface-ledger-line");
      expect(row?.querySelector(".surface-ledger-meta")?.textContent).toBe("JORDAN");
    });
    expect(screen.getByTestId("meeting-decisions").querySelector("h3")?.textContent).toBe("Decisions · 2");
    proposals = proposals.map((p) => (p.id === "p1" ? { ...p, state: "confirmed" } : p));
    fireEvent.click(within(screen.getByTestId("meeting-decisions")).getByRole("button", { name: "Dismiss: Run reconciliation nightly" }));
    await waitFor(() => expect(screen.getByTestId("meeting-decisions").querySelector("h3")?.textContent).toBe("Decisions · 1"));
  });
});

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
      ["Run reconciliation nightly", "AVERY"],
      ["Freeze the old ledger on Nov 5", "DECIDED"],
      ["Run reconciliation nightly", "DECIDED"],
      ["Keep the old ledger", "REPLACED"],
      ["Shard the ledger", "DISPUTED"],
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
      ["ft-p1", "Freeze the old ledger on Nov 5", "REPLACED"],
      ["ft-p2", "Run reconciliation nightly", "DISPUTED"],
      ["ft-p3", "Shard the ledger", "AVERY"],
    ]);
  });

  it("the hook reads the meeting's ledger rows and the record shows them above Commitments", async () => {
    const meeting = {
      id: "m9", title: "Ledger cutover sync", intel_status: "complete",
      intel: { summary: "s", action_items: [{ id: "ai-1", task: "Write the rollback runbook", owner: null, status: "pending" }] },
    };
    apiFetch.mockImplementation(async (url: string) => {
      if (url === "/api/decisions?scope=all&limit=500&meeting_id=m9")
        return { decisions: [{ id: "d1", text: "Freeze the old ledger on Nov 5", lifecycle: "recorded" }] };
      if (url.includes("/follow-through-proposals")) return { proposals: [] };
      if (url === "/api/meetings/m9") return meeting;
      return {};
    });
    function Harness() {
      const data = useMeetingData(meeting, () => undefined);
      return <MeetingOutcomes data={data} meeting={meeting} />;
    }
    const { container } = render(<Harness />);
    const decisions = await screen.findByTestId("meeting-decisions");
    expect(decisions.querySelector("h3")?.textContent).toBe("Decisions · 1");
    expect(decisions.textContent).toContain("Freeze the old ledger on Nov 5");
    const order = [...container.querySelectorAll("[data-testid=meeting-decisions], [data-testid=meeting-commitments]")]
      .map((el) => el.getAttribute("data-testid"));
    expect(order).toEqual(["meeting-decisions", "meeting-commitments"]);
  });
});
