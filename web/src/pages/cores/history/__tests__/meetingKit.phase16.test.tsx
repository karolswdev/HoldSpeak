// Phase 16 (the interior kit; the canvas window "Cutover sync"): the meeting
// record heads with its title (the AppHead, once) and the strip
// (`TUE 14:00 · 42 MIN` · SUMMARISED · `4 PEOPLE`), then `Decisions · n` and
// `Commitments · n`, each a Section over a Ledger of kind-plated rows.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MeetingHeader, meetingOutcomeFact, meetingReviewCount, meetingStripItems, meetingSummaryState, peopleCount } from "../MeetingHeader";
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
  // Window grammar (2026-10-24): the title bar names the meeting; the head
  // is its glyph and one muted line; the state is the status bar's word.
  it("no headline: the compact head says when, length and the people; the state is Summary stored", () => {
    const meeting = { id: "m1", title: "Cutover sync", intel_status: "complete", intel: { summary: "We froze the ledger." } };
    const data = {
      detail: meeting,
      startedAt: "2026-10-06T14:00:00",
      durationS: 42 * 60,
      segments: [{ speaker: "Jordan" }, { speaker: "Avery" }, { speaker: "jordan" }, { speaker: "" }],
    };
    const { container } = render(<MeetingHeader meeting={meeting} data={data as never} />);
    expect(container.querySelectorAll(".kit-disp")).toHaveLength(0);
    expect(container.textContent).not.toContain("Cutover sync");
    expect(screen.getByTestId("meeting-head-when").textContent).toBe("Oct 06 · 42 min");
    expect(screen.getByTestId("meeting-head-people").getAttribute("aria-label")).toBe("With Jordan, Avery");
    expect(container.querySelector(".meeting-head-glyph")).toBeTruthy();
    expect(meetingSummaryState(meeting)).toEqual({ text: "Summary stored", lamp: "ok" });
  });

  it("saved Outcomes: one review count, the compact head, no static step ladder", () => {
    const meeting = { id: "m-saved", title: "Cutover sync", intel_status: "complete", intel: { summary: "We froze the ledger." } };
    const data = {
      detail: meeting,
      needsCount: 0,
      ftProposals: [{ id: "p1", meeting_id: "m-saved", kind: "action" as const, text: "Write the runbook", state: "proposed" as const, created_at: "" }],
      startedAt: "2026-10-06T14:00:00",
      durationS: 42 * 60,
      segments: [],
    };
    const { container } = render(
      <MeetingHeader meeting={meeting} data={data as never} compact />,
    );
    expect(meetingOutcomeFact(meeting, data as never)).toBe("1 to review");
    expect(meetingReviewCount(data as never)).toBe(1);
    expect(container.querySelector(".meetings-detail-facts")).toBeTruthy();
    expect(screen.queryByTestId("meeting-steps")).toBeNull();
  });

  it("does not expose a zero review counter when the saved record is settled", () => {
    const meeting = { id: "m-done", title: "Cutover sync", intel_status: "complete", intel: { summary: "We froze the ledger." } };
    expect(meetingOutcomeFact(meeting, { detail: meeting, needsCount: 0, ftProposals: [] })).toBe("Outcomes");
  });

  it("no people token at zero; a failed summary keeps its word with the fail lamp", () => {
    const meeting = { id: "m2", title: "Vendor call", intel_status: "failed" };
    const items = meetingStripItems(meeting, { detail: meeting, startedAt: null, durationS: 0, segments: [] });
    expect(peopleCount([])).toBe(0);
    expect(items.map((i) => i.key)).toEqual(["state"]);
    expect(items[0]).toMatchObject({ lamp: "fail", text: "SUMMARY FAILED" });
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
      ["ACT", "Shard the reconciliation job", "no owner · no date", undefined],
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
      ["Write the rollback runbook", "no owner · no date"],
      ["Shard the reconciliation job", "no owner · no date"],
      ["Book the cutover window", "no owner · no date"],
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
      ["Write the rollback runbook", "no owner · no date", undefined],
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
describe("the meeting's Decisions through Confirm (the hook and the ledger, rendered)", () => {
  it("opens owner and date wells automatically when a proposed action has gaps", async () => {
    apiFetch.mockResolvedValue({ relationships: [] });
    const data = {
      ftProposals: [{
        id: "p-gap", meeting_id: "m-gap", kind: "action" as const, text: "Name the owner",
        state: "proposed" as const, created_at: "", owner: null, due: null,
      }],
      openActions: [], settledActions: [], segments: [], busy: false,
      outcomeRefreshFailed: false, retryOutcomeReview: async () => undefined,
      confirmProposal: async () => undefined, dismissProposal: async () => undefined,
      deferProposal: async () => undefined, confirmAll: async () => undefined,
      completeAction: async () => undefined,
    };
    render(<MeetingOutcomes data={data as never} meeting={{ id: "m-gap" }} />);
    expect(await screen.findByTestId("outcome-gap")).toBeTruthy();
    expect(screen.getByLabelText("Who?")).toBeTruthy();
    expect(screen.getByLabelText("When?")).toBeTruthy();
  });

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
      if (init?.method === "POST") {
        if (url.endsWith("/confirm")) proposals = proposals.map((p) => (p.id === "p1" ? { ...p, state: "confirmed" } : p));
        return {};
      }
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
    expect(screen.getByTestId("meeting-commitments").querySelector("h3")?.textContent).toBe("Who owes what · 1");
    fireEvent.click(within(decisions).getByRole("button", { name: "Confirm: Freeze the old ledger on Nov 5" }));
    await waitFor(() => {
      const row = within(screen.getByTestId("meeting-decisions")).getByText("Freeze the old ledger on Nov 5").closest(".surface-ledger-line");
      expect(row?.querySelector(".surface-ledger-meta")?.textContent).toBe("Jordan");
    });
    expect(screen.getByTestId("meeting-decisions").querySelector("h3")?.textContent).toBe("Decisions · 2");
    proposals = proposals.map((p) => (p.id === "p1" ? { ...p, state: "confirmed" } : p));
    const secondDecision = within(screen.getByTestId("meeting-decisions"))
      .getByText("Run reconciliation nightly")
      .closest(".surface-ledger-line") as HTMLElement;
    fireEvent.click(within(secondDecision).getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Dismiss" }));
    await waitFor(() => expect(screen.getByTestId("meeting-decisions").querySelector("h3")?.textContent).toBe("Decisions · 1"));
  });


  it.each([
    [null, false], [undefined, false], [-1, false], [1, false], [0.5, false], ["0", false], [0, true],
  ])("only stored segment %s offers an exact transcript destination", async (segment, expected) => {
    const meeting = { id: "m-source", title: "Source check", segments: [{ text: "Move the cutover to Friday." }] };
    const proposal = { id: "p-source", meeting_id: "m-source", kind: "decision", text: "Freeze on Nov 12", state: "proposed", segment_index: segment, support: "unknown" };
    apiFetch.mockImplementation(async (url: string) => {
      if (url.includes("/outcome-review") || url.includes("/follow-through-proposals")) return { proposals: [proposal] };
      if (url === "/api/meetings/m-source") return meeting;
      return {};
    });
    function Harness() {
      const data = useMeetingData(meeting, () => undefined);
      return <MeetingOutcomes data={data} meeting={meeting} />;
    }
    render(<Harness />);
    const decisions = await screen.findByTestId("meeting-decisions");
    expect(decisions.querySelector("h3")?.textContent).toBe("Decisions · 1");
    fireEvent.click(within(decisions).getByTestId("proposal-more-btn"));
    expect(Boolean(screen.queryByRole("menuitem", { name: "Show in transcript" }))).toBe(expected);
    if (!expected) expect(decisions).toHaveTextContent("Not in the transcript");
  });

  it("edits a populated row through More and keeps a grounded source", async () => {
    const meeting = {
      id: "m-outcomes", title: "Cutover sync", intel_status: "complete", segments: [{ text: "Jordan owns the runbook" }],
    };
    let proposals: FollowThroughProposal[] = [{
      id: "p-action", meeting_id: "m-outcomes", kind: "action" as const, text: "Write the runbook",
      owner: "Jordan", due: "2026-11-05", state: "proposed" as const, created_at: "",
      support: "source_linked", unknowns: [], project_id: "prj-cutover", segment_index: 0,
      action_item_id: null,
    }];
    const calls: Array<{ url: string; init?: { method?: string; json?: Record<string, unknown> } }> = [];
    apiFetch.mockImplementation(async (url: string, init?: { method?: string; json?: Record<string, unknown> }) => {
      calls.push({ url, init });
      if (init?.method === "POST" && url.includes("/confirm")) {
        proposals = proposals.map((proposal) => ({
          ...proposal,
          ...init.json,
          state: "confirmed" as const,
          action_item_id: "action-1",
        }));
        return { proposal: proposals[0] };
      }
      if (url === "/api/people/relationships") return { relationships: [{ id: "rel-jordan", display_name: "Jordan" }] };
      if (url === "/api/door") return {
        board: { now: [{ id: "action-1", source: "action_item", person_relationship_id: "rel-jordan" }] },
      };
      if (url.includes("/outcome-review") || url.includes("/follow-through-proposals")) return { proposals, revision: "r1" };
      if (url === "/api/meetings/m-outcomes") return meeting;
      return {};
    });
    const opened: unknown[] = [];
    const onOpen = (event: Event) => opened.push((event as CustomEvent).detail);
    window.addEventListener(MEETING_OPEN_EVENT, onOpen);
    function Harness() {
      const data = useMeetingData(meeting, () => undefined);
      return <MeetingOutcomes data={data} meeting={meeting} />;
    }
    render(<Harness />);

    const row = await screen.findByText("Write the runbook");
    const line = row.closest(".surface-ledger-line") as HTMLElement;
    fireEvent.click(within(line).getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Show in transcript" }));
    expect(opened.at(-1)).toMatchObject({ meetingId: "m-outcomes", view: "outcomes", segment: 0 });
    fireEvent.click(within(line).getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Task"), { target: { value: "Ship the runbook" } });
    fireEvent.change(screen.getByLabelText("Who?"), { target: { value: "Jordan" } });
    fireEvent.change(screen.getByLabelText("When?"), { target: { value: "2026-11-12" } });
    fireEvent.click(within(line).getByRole("button", { name: "Confirm: Ship the runbook" }));
    await waitFor(() => expect(calls.some((call) => call.url === "/api/proposals/p-action/confirm" && call.init?.json)).toBe(true));
    expect(calls.find((call) => call.url === "/api/proposals/p-action/confirm")?.init?.json).toEqual({
      text: "Ship the runbook", owner: "Jordan", due: "2026-11-12",
    });

    await waitFor(() => expect(screen.getByTestId("proposal-follow-through-btn")).toBeTruthy());
    const confirmedLine = screen.getByText("Ship the runbook").closest(".surface-ledger-line") as HTMLElement;
    fireEvent.click(within(confirmedLine).getByTestId("proposal-more-btn"));
    expect(screen.getByRole("menuitem", { name: "Project" })).toBeTruthy();
    await waitFor(() => expect(screen.getByRole("menuitem", { name: "People" })).toBeTruthy());
    expect(calls.filter((call) => call.url === "/api/door")).toHaveLength(1);
    expect(screen.queryByLabelText("Task")).toBeNull();
    window.removeEventListener(MEETING_OPEN_EVENT, onOpen);
  });

  it("holds Confirm all until an edited proposal is confirmed individually", async () => {
    const first: FollowThroughProposal = {
      id: "p-one", meeting_id: "m-bulk", kind: "action", text: "Write the runbook",
      owner: "Jordan", due: "2026-11-05", state: "proposed", created_at: "",
      support: "source_linked", unknowns: [], extraction_revision: "r1",
    };
    const second: FollowThroughProposal = {
      id: "p-two", meeting_id: "m-bulk", kind: "action", text: "Review the runbook",
      owner: "Avery", due: "2026-11-06", state: "proposed", created_at: "",
      support: "source_linked", unknowns: [], extraction_revision: "r1",
    };
    const confirmProposal = vi.fn(async () => undefined);
    const confirmAll = vi.fn(async () => undefined);
    const meeting = { id: "m-bulk", title: "Bulk review" };
    const data = {
      detail: meeting, ftProposals: [first, second], openActions: [], settledActions: [], segments: [], busy: false,
      reviewRevision: "r1", outcomeRefreshFailed: false, retryOutcomeReview: async () => undefined,
      confirmProposal, confirmAll, dismissProposal: async () => undefined, deferProposal: async () => undefined,
      completeAction: async () => undefined,
    };
    apiFetch.mockResolvedValue({ relationships: [] });
    const { rerender } = render(<MeetingOutcomes data={data as never} meeting={meeting} />);

    const all = await screen.findByTestId("proposal-confirm-all-btn");
    expect(all).not.toBeDisabled();
    const line = screen.getByText("Write the runbook").closest(".surface-ledger-line") as HTMLElement;
    fireEvent.click(within(line).getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Task"), { target: { value: "Ship the runbook" } });
    fireEvent.change(screen.getByLabelText("Who?"), { target: { value: "Me" } });
    fireEvent.change(screen.getByLabelText("When?"), { target: { value: "2026-11-12" } });
    fireEvent.click(within(line).getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Close edit" }));

    expect(within(line).getByText("Ship the runbook")).toBeTruthy();
    expect(within(line).getByText("Me · by 2026-11-12")).toBeTruthy();
    expect(screen.getByTestId("proposal-confirm-all-btn")).toBeDisabled();
    expect(confirmAll).not.toHaveBeenCalled();
    fireEvent.click(within(line).getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Task"), { target: { value: "" } });
    expect(within(line).getByTestId("proposal-confirm-btn")).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Task"), { target: { value: "Ship the runbook" } });
    fireEvent.change(screen.getByLabelText("Who?"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("When?"), { target: { value: "" } });
    expect(within(line).getByRole("button", { name: "Confirm: Ship the runbook" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Who?"), { target: { value: "Me" } });
    fireEvent.change(screen.getByLabelText("When?"), { target: { value: "2026-11-12" } });
    fireEvent.click(within(line).getByRole("button", { name: "Confirm: Ship the runbook" }));
    await waitFor(() => expect(confirmProposal).toHaveBeenCalledWith("p-one", {
      text: "Ship the runbook", owner: "Me", due: "2026-11-12",
    }));

    const settled = { ...first, text: "Durable runbook", owner: "Avery", due: "2026-11-13", state: "confirmed" as const };
    rerender(<MeetingOutcomes data={{ ...data, ftProposals: [settled, second] } as never} meeting={meeting} />);
    expect(screen.getByText("Durable runbook")).toBeTruthy();
    expect(screen.getByText("Avery · by 2026-11-13")).toBeTruthy();
    expect(screen.queryByText("Ship the runbook")).toBeNull();
    const restored = await screen.findByTestId("proposal-confirm-all-btn");
    expect(restored).not.toBeDisabled();
    fireEvent.click(restored);
    await waitFor(() => expect(confirmAll).toHaveBeenCalledTimes(1));
  });

  it("withholds People when the Door has no unambiguous read-time relationship", async () => {
    apiFetch.mockImplementation(async (url: string) => {
      if (url === "/api/people/relationships") {
        return {
          relationships: [
            { id: "rel-one", display_name: "Jordan" },
            { id: "rel-two", display_name: "Jordan" },
          ],
        };
      }
      if (url === "/api/door") {
        return { board: { now: [{ id: "action-ambiguous", source: "action_item" }] } };
      }
      return {};
    });
    const data = {
      ftProposals: [{
        id: "p-ambiguous", meeting_id: "m-ambiguous", kind: "action" as const,
        text: "Resolve the owner", owner: "Jordan", due: "2026-11-05", state: "confirmed" as const,
        created_at: "", action_item_id: "action-ambiguous",
      }],
      openActions: [], settledActions: [], segments: [], busy: false,
      outcomeRefreshFailed: false, retryOutcomeReview: async () => undefined,
      confirmProposal: async () => undefined, dismissProposal: async () => undefined,
      deferProposal: async () => undefined, confirmAll: async () => undefined,
      completeAction: async () => undefined,
    };
    render(<MeetingOutcomes data={data as never} meeting={{ id: "m-ambiguous" }} />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/door"));
    expect(screen.queryByTestId("proposal-person-btn")).toBeNull();
  });

  it("withholds People when the Door projection is unavailable", async () => {
    apiFetch.mockImplementation(async (url: string) => {
      if (url === "/api/people/relationships") {
        return { relationships: [{ id: "rel-jordan", display_name: "Jordan" }] };
      }
      if (url === "/api/door") throw new Error("door unavailable");
      return {};
    });
    const data = {
      ftProposals: [{
        id: "p-unavailable", meeting_id: "m-unavailable", kind: "action" as const,
        text: "Keep the destination grounded", owner: "Jordan", due: "2026-11-05", state: "confirmed" as const,
        created_at: "", action_item_id: "action-unavailable",
      }],
      openActions: [], settledActions: [], segments: [], busy: false,
      outcomeRefreshFailed: false, retryOutcomeReview: async () => undefined,
      confirmProposal: async () => undefined, dismissProposal: async () => undefined,
      deferProposal: async () => undefined, confirmAll: async () => undefined,
      completeAction: async () => undefined,
    };
    render(<MeetingOutcomes data={data as never} meeting={{ id: "m-unavailable" }} />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/door"));
    expect(screen.queryByTestId("proposal-person-btn")).toBeNull();
  });

  it("keeps a confirmed row and the next row draft when the follow-up read fails", async () => {
    const meeting = { id: "m-retry", title: "Release sync", intel_status: "complete" };
    let proposals: FollowThroughProposal[] = [
      {
        id: "p-confirm", meeting_id: "m-retry", kind: "action" as const, text: "Ship release",
        owner: "Jordan", due: "2026-11-05", state: "proposed" as const, created_at: "",
        action_item_id: "action-confirm",
      },
      {
        id: "p-next", meeting_id: "m-retry", kind: "action" as const, text: "Prepare announcement",
        owner: null, due: null, state: "proposed" as const, created_at: "", action_item_id: "action-next",
      },
    ];
    let rereadFailed = false;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string; json?: Record<string, unknown> }) => {
      if (init?.method === "POST" && url.endsWith("/confirm")) {
        proposals = proposals.map((proposal) => proposal.id === "p-confirm"
          ? { ...proposal, ...init.json, state: "confirmed" as const }
          : proposal);
        rereadFailed = true;
        return { proposal: proposals[0] };
      }
      if (url === "/api/people/relationships") return { relationships: [{ id: "rel-jordan", display_name: "Jordan" }] };
      if (url === "/api/door") return { board: { now: [] } };
      if (url.includes("/outcome-review") || url.includes("/follow-through-proposals")) {
        if (rereadFailed) throw new Error("temporary outcome read failure");
        return { proposals, revision: "r1" };
      }
      if (url === "/api/meetings/m-retry") return meeting;
      return {};
    });
    function Harness() {
      const data = useMeetingData(meeting, () => undefined);
      return <MeetingOutcomes data={data} meeting={meeting} />;
    }
    render(<Harness />);

    const nextOwner = await screen.findByLabelText("Who?");
    fireEvent.change(nextOwner, { target: { value: "Jordan" } });
    const firstLine = screen.getByText("Ship release").closest(".surface-ledger-line") as HTMLElement;
    fireEvent.click(within(firstLine).getByRole("button", { name: "Confirm: Ship release" }));
    await waitFor(() => expect(screen.getByTestId("outcome-refresh-retry-btn")).toBeTruthy());
    expect(screen.getByText("Ship release")).toBeTruthy();
    const nextLine = screen.getByText("Prepare announcement").closest(".surface-ledger-line") as HTMLElement;
    fireEvent.click(within(nextLine).getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    expect(screen.getByLabelText("Who?")).toHaveValue("Jordan");
  });

  it("keeps bulk confirmation after a successful write when its reread fails", async () => {
    const meeting = { id: "m-bulk-retry", title: "Bulk review" };
    let proposals: FollowThroughProposal[] = [{
      id: "p-bulk", meeting_id: "m-bulk-retry", kind: "action", text: "Ship release",
      owner: "Jordan", due: "2026-11-05", state: "proposed", created_at: "",
      support: "source_linked", unknowns: [], action_item_id: "action-bulk",
    }];
    let rereadFailed = false;
    const receipts: Array<{ text?: string; tone?: string }> = [];
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url === "/api/people/relationships") return { relationships: [] };
      if (init?.method === "POST" && url.endsWith("/accept-reviewed")) {
        proposals = proposals.map((proposal) => ({ ...proposal, state: "confirmed" as const }));
        rereadFailed = true;
        return { accepted_count: 1 };
      }
      if (url.includes("/outcome-review") || url.includes("/follow-through-proposals")) {
        if (rereadFailed) throw new Error("temporary outcome read failure");
        return { proposals, revision: "r1" };
      }
      return {};
    });
    function Harness() {
      const data = useMeetingData(meeting, (receipt) => { receipts.push(receipt); });
      return <MeetingOutcomes data={data} meeting={meeting} />;
    }
    render(<Harness />);

    fireEvent.click(await screen.findByTestId("proposal-confirm-all-btn"));
    await waitFor(() => expect(receipts.some((receipt) => receipt.text === "CONFIRMED 1")).toBe(true));
    expect(receipts.some((receipt) => receipt.text?.startsWith("REFUSED"))).toBe(false);
    expect(await screen.findByTestId("outcome-refresh-retry-btn")).toBeTruthy();

    rereadFailed = false;
    fireEvent.click(screen.getByTestId("outcome-refresh-retry-btn"));
    await waitFor(() => expect(screen.getByTestId("action-done-btn")).toBeTruthy());
    expect(receipts.at(-1)?.text).toBe("REFRESHED");
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
      ["Run reconciliation nightly", "Avery"],
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
      ["ft-p3", "Shard the ledger", "Avery"],
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


describe("Meeting People read recovery", () => {
  it("shows a pending lookup and retries failure without clearing the task or date draft", async () => {
    let failRead: (cause: unknown) => void = () => {};
    let reads = 0;
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/people/relationships") return ++reads === 1
        ? new Promise((_resolve, reject) => { failRead = reject; })
        : Promise.resolve({ relationships: [{ id: "priya", display_name: "Priya" }] });
      return Promise.resolve({});
    });
    const data = {
      ftProposals: [{ id: "people-gap", meeting_id: "m-people", kind: "action", text: "Write the runbook", state: "proposed", created_at: "", owner: null, due: null }],
      openActions: [], settledActions: [], segments: [], busy: false,
      confirmProposal: vi.fn(), dismissProposal: vi.fn(), deferProposal: vi.fn(), confirmAll: vi.fn(),
    };
    render(<MeetingOutcomes data={data as never} meeting={{ id: "m-people" }} />);
    expect(screen.getByTestId("meeting-people-read")).toHaveAttribute("aria-busy", "true");
    fireEvent.click(screen.getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Task"), { target: { value: "Ship the runbook draft" } });
    fireEvent.change(screen.getByLabelText("When?"), { target: { value: "2026-11-12" } });
    await act(async () => { failRead(new TypeError("offline")); });
    expect(screen.getByRole("alert")).toHaveTextContent("PEOPLE DID NOT LOAD");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("option", { name: "Priya" })).toBeTruthy();
    expect(screen.getByLabelText("Task")).toHaveValue("Ship the runbook draft");
    expect(screen.getByLabelText("When?")).toHaveValue("2026-11-12");
    expect(data.confirmProposal).not.toHaveBeenCalled();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

// W2-LIVE-2 (canvas betterment/canvases/live-direction-2026-10-27.html, A,
// After): a decided row carries its one verb, Decide…: the record when it has
// one, else New decision on the record. A proposed decision keeps Confirm.
describe("the meeting's decided rows carry Decide… (W2-LIVE-2)", () => {
  it("opens the record a decision has, asks for New decision when it has none, and keeps Confirm on a proposal", async () => {
    apiFetch.mockResolvedValue({ relationships: [] });
    const { useDesk } = await import("../../../../desk/store");
    const openSurfaceWindow = vi.fn();
    useDesk.setState({ openSurfaceWindow } as never);
    const onDecide = vi.fn();
    const data = {
      ftProposals: [
        { id: "p-dec", meeting_id: "m-dec", kind: "decision" as const, text: "Freeze the ledger on Nov 12", state: "confirmed" as const, created_at: "", owner: "Karol" },
        { id: "p-ask", meeting_id: "m-dec", kind: "decision" as const, text: "Move the backup job to 22:00", state: "proposed" as const, created_at: "" },
      ],
      meetingDecisions: [{ id: "d-rec", text: "Shard the reconciliation job", lifecycle: "active", record_id: "record-abc" }],
      openActions: [], settledActions: [], segments: [], busy: false,
      outcomeRefreshFailed: false, retryOutcomeReview: async () => undefined,
      confirmProposal: async () => undefined, dismissProposal: async () => undefined,
      deferProposal: async () => undefined, confirmAll: async () => undefined,
      completeAction: async () => undefined,
    };
    render(<MeetingOutcomes data={data as never} meeting={{ id: "m-dec" }} onDecide={onDecide} />);
    const decisions = await screen.findByTestId("meeting-decisions");
    expect(within(decisions).getByRole("button", { name: "Confirm: Move the backup job to 22:00" })).toBeTruthy();
    expect(within(decisions).queryByRole("button", { name: "Decide: Move the backup job to 22:00" })).toBeNull();

    fireEvent.click(within(decisions).getByRole("button", { name: "Decide: Shard the reconciliation job" }));
    expect(openSurfaceWindow).toHaveBeenCalledWith("open-decisions", "record:record-abc");

    fireEvent.click(within(decisions).getByRole("button", { name: "Decide: Freeze the ledger on Nov 12" }));
    expect(onDecide).toHaveBeenCalledTimes(1);
  });
});
