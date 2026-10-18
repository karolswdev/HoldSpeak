// HS-150-07 -- FollowThroughView: person chip + staleness for mapped owners,
// full names for unmapped.

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FollowThroughView } from "./FollowThroughView";
import PEOPLE_CARD from "../../__tests__/wire/door-people-commitment.wire.json";
import HONEST_BOARD from "../../../test/wire/follow-through-board.honest-faces.wire.json";

// ---------------------------------------------------------------------------
// mocks
// ---------------------------------------------------------------------------

const apiFetch = vi.hoisted(() => vi.fn());
const openSourceRef = vi.hoisted(() => vi.fn());
const busRefresh = vi.hoisted(() => ({ current: null as null | (() => void) }));
vi.mock("../../useDeskChangedRefresh", () => ({ useOnDeskChanged: (callback: () => void) => { busRefresh.current = callback; } }));
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); vi.restoreAllMocks(); });

vi.mock("../../../lib/api", () => ({
  apiFetch,
  readableError: (reason: unknown) =>
    reason instanceof Error ? reason.message : "Request failed",
}));

vi.mock("../../intelligenceAttention", async () => {
  const actual = await vi.importActual<typeof import("../../intelligenceAttention")>(
    "../../intelligenceAttention",
  );
  return {
    ...actual,
    refreshIntelligenceAttention: vi.fn(),
  };
});

vi.mock("../../shell", () => ({
  openSurfaceOr: vi.fn(),
}));

vi.mock("../../surface/citations", () => ({
  openSourceRef,
}));

// ---------------------------------------------------------------------------
// fixtures
// ---------------------------------------------------------------------------

function makeBoard({
  mappedOwner = false,
  unmappedOwner = false,
}: { mappedOwner?: boolean; unmappedOwner?: boolean } = {}) {
  const now: any[] = [];
  if (mappedOwner) {
    now.push({
      id: "card-mapped",
      text: "Review proposal",
      owner: "Ewa Kowalska",
      due: null,
      source: "action_item",
      provenance: { available: false, meeting_id: null, segment_text: null, segment_speaker: null, segment_start: null },
      person_label: "Ewa",
      person_relationship_id: "rel-ewa",
      delegated_at: "2026-08-25T10:00:00",
      created_at: "2026-08-20T10:00:00",
    });
  }
  if (unmappedOwner) {
    now.push({
      id: "card-unmapped",
      text: "Check dashboard",
      owner: "Unknown Person",
      due: null,
      source: "action_item",
      provenance: { available: false, meeting_id: null, segment_text: null, segment_speaker: null, segment_start: null },
    });
  }
  return { now, waiting: [], unassigned: [], overdue: [] };
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("FollowThroughView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.removeItem("hs.follow-through.done-receipt");
  });

  it("shows person chip with display name for mapped owner", async () => {
    apiFetch.mockResolvedValueOnce(makeBoard({ mappedOwner: true }));

    render(<FollowThroughView />);

    await waitFor(() => {
      expect(screen.getByTestId("follow-through-person-chip")).toBeTruthy();
    });

    const chip = screen.getByTestId("follow-through-person-chip");
    expect(chip.textContent).toContain("Ewa");
  });

  it("shows staleness label on mapped owner chip", async () => {
    apiFetch.mockResolvedValueOnce(makeBoard({ mappedOwner: true }));

    render(<FollowThroughView />);

    await waitFor(() => {
      expect(screen.getByTestId("follow-through-staleness")).toBeTruthy();
    });

    const staleness = screen.getByTestId("follow-through-staleness");
    expect(staleness.textContent).toMatch(/^Assigned \d+ days ago$/);
  });

  it("shows the full name for an unmapped owner", async () => {
    apiFetch.mockResolvedValueOnce(makeBoard({ unmappedOwner: true }));

    render(<FollowThroughView />);

    await waitFor(() => {
      expect(screen.getByText("Unknown Person")).toBeTruthy();
    });

    // No person chip should exist.
    expect(screen.queryByTestId("follow-through-person-chip")).toBeNull();
  });

  it("renders both mapped and unmapped cards correctly side by side", async () => {
    apiFetch.mockResolvedValueOnce(makeBoard({ mappedOwner: true, unmappedOwner: true }));

    render(<FollowThroughView />);

    await waitFor(() => {
      expect(screen.getByTestId("follow-through-person-chip")).toBeTruthy();
    });

    // Mapped card has a person chip.
    expect(screen.getByTestId("follow-through-person-chip").textContent).toContain("Ewa");

    // Unmapped card shows initials.
    expect(screen.getByText("Unknown Person")).toBeTruthy();

    // Only one person chip (the mapped one).
    expect(screen.queryAllByTestId("follow-through-person-chip")).toHaveLength(1);
  });

  it("opens a verified note source and keeps a decision id as a decision", async () => {
    const note = {
      id: "card-note", text: "Update the note", owner: null, due: null, source: "action_item",
      open_ref: "note:note-7", decision_id: null,
      provenance: { available: false, meeting_id: null, segment_text: null, segment_speaker: null, segment_start: null },
    };
    const decision = {
      id: "card-decision", text: "Use the new plan", owner: null, due: null, source: "decision",
      decision_id: "decision-7",
      provenance: { available: false, meeting_id: "meeting-7", segment_text: null, segment_speaker: null, segment_start: null, moment: { segment_index: 3 } },
    };
    const meeting = {
      id: "card-meeting", text: "Confirm the date", owner: null, due: null, source: "action_item",
      provenance: { available: false, meeting_id: "meeting-8", segment_text: null, segment_speaker: null, segment_start: null, moment: { segment_index: 4 } },
    };
    apiFetch.mockResolvedValueOnce({ now: [note, decision, meeting], waiting: [], unassigned: [], overdue: [] });
    render(<FollowThroughView />);

    await screen.findByText("Update the note");
    fireEvent.click(screen.getByRole("button", { name: "Open note for Update the note" }));
    fireEvent.click(screen.getByRole("button", { name: "Open decision for Use the new plan" }));
    fireEvent.click(screen.getByRole("button", { name: "Open meeting for Confirm the date" }));

    expect(openSourceRef).toHaveBeenNthCalledWith(1, "note:note-7");
    expect(openSourceRef).toHaveBeenNthCalledWith(2, "decision:decision-7");
    expect(openSourceRef).toHaveBeenNthCalledWith(3, "meeting:meeting-8?view=review&segment=4");
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });

  it("keeps the completed card id in the Done receipt and reopens that card on Undo", async () => {
    const card = {
      id: "card-done", text: "Publish the update", owner: null, due: null, source: "action_item",
      provenance: { available: false, meeting_id: "meeting-3", segment_text: null, segment_speaker: null, segment_start: null },
    };
    const board = { now: [card], waiting: [], unassigned: [], overdue: [] };
    const empty = { now: [], waiting: [], unassigned: [], overdue: [] };
    apiFetch
      .mockResolvedValueOnce(board)
      .mockResolvedValueOnce({ card_id: card.id, verb: "done" })
      .mockResolvedValueOnce(empty)
      .mockResolvedValueOnce(empty)
      .mockResolvedValueOnce({ card_id: card.id, verb: "reopen" })
      .mockResolvedValueOnce(board);
    const view = render(<FollowThroughView />);

    const row = await screen.findByRole("button", { name: "Publish the update. meeting follow-through." });
    fireEvent.click(row);
    fireEvent.click(screen.getByRole("button", { name: "Mark done" }));

    await waitFor(() => expect(screen.getByTestId("follow-through-done-receipt")).toHaveTextContent("Publish the update"));
    view.unmount();
    render(<FollowThroughView />);
    await screen.findByTestId("follow-through-done-receipt");
    fireEvent.click(screen.getByRole("button", { name: "Undo" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: card.id, verb: "reopen", payload: {} },
    }));
  });
});

// Honest faces (inventory 2026-10-03): a lane name is a state, not a counted
// noun. The hub's own board for the honest-faces seed: two unowned meeting
// actions in To review (tests/integration/test_face_wire_fences.py).
describe("FollowThroughView lane counts on the recorded hub", () => {
  it("two cards to review have one honest heading and no repeated ledger count", async () => {
    // replaces: tests/e2e/test_honest_faces_glass.py::test_intelligence_lane_names_and_decision_rows (the Follow-through leg)
    apiFetch.mockResolvedValue(structuredClone(HONEST_BOARD.wire));
    const { container } = render(<FollowThroughView />);
    await screen.findByText("Write the rollback runbook");
    expect(screen.getByText("Pilot OTel in billing")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "To review · 2" })).toBeTruthy();
    expect(container.querySelectorAll(".surface-ledger-head")).toHaveLength(0);
    expect(container.textContent ?? "").not.toMatch(/\b\d+ (NOWS|TO REVIEWS|UNASSIGNEDS|WAITINGS|OVERDUES)\b/);
  });
});

// Recorded from root's isolated Note + Door producer walk, 2026-10-15.
// .tmp/follow-through/before-1440/observation.json initial_board.
const WALK_BOARD = {
  "now": [
    {
      "id": "ai_8451840b66a04339a436981e71c37ab9",
      "text": "Confirm rollback ownership",
      "owner": "Karol",
      "due": "2026-10-15",
      "status": "open",
      "meeting_id": null,
      "decision_id": null,
      "stale_score": null,
      "source": "action_item",
      "lane": "now",
      "provenance": {
        "meeting_id": null,
        "segment_text": null,
        "segment_speaker": null,
        "segment_start": null,
        "moment": null,
        "available": false,
        "thread_id": null,
        "source_ref": "note:note_dc8520cc9864"
      },
      "target_ref": null,
      "delegated_at": "2026-10-15T19:17:31.708321+00:00",
      "created_at": "2026-10-15T19:17:31.708321+00:00"
    }
  ],
  "waiting": [
    {
      "id": "ai_32afe9b9a6d3438ab90fc54fd4069149",
      "text": "Review the architecture decision with the platform team",
      "owner": "Alexandra Montgomery",
      "due": "2026-10-24",
      "status": "open",
      "meeting_id": null,
      "decision_id": null,
      "stale_score": null,
      "source": "action_item",
      "lane": "waiting",
      "provenance": {
        "meeting_id": null,
        "segment_text": null,
        "segment_speaker": null,
        "segment_start": null,
        "moment": null,
        "available": false,
        "thread_id": null,
        "source_ref": "note:note_dc8520cc9864"
      },
      "target_ref": null,
      "delegated_at": "2026-10-15T19:17:31.709680+00:00",
      "created_at": "2026-10-15T19:17:31.709680+00:00"
    }
  ],
  "unassigned": [
    {
      "id": "ai_19db15756313494084e25b3b26961ba0",
      "text": "Name the migration owner",
      "owner": null,
      "due": null,
      "status": "open",
      "meeting_id": null,
      "decision_id": null,
      "stale_score": null,
      "source": "action_item",
      "lane": "unassigned",
      "provenance": {
        "meeting_id": null,
        "segment_text": null,
        "segment_speaker": null,
        "segment_start": null,
        "moment": null,
        "available": false,
        "thread_id": null,
        "source_ref": null
      },
      "target_ref": null,
      "delegated_at": null,
      "created_at": "2026-10-15T19:17:31.712356+00:00"
    }
  ],
  "overdue": [
    {
      "id": "ai_27777504ee3544eeafbd3dd8aee38003",
      "text": "Write the release checklist",
      "owner": "Karol",
      "due": "2026-10-12",
      "status": "open",
      "meeting_id": null,
      "decision_id": null,
      "stale_score": null,
      "source": "action_item",
      "lane": "overdue",
      "provenance": {
        "meeting_id": null,
        "segment_text": null,
        "segment_speaker": null,
        "segment_start": null,
        "moment": null,
        "available": false,
        "thread_id": null,
        "source_ref": "note:note_dc8520cc9864"
      },
      "target_ref": null,
      "delegated_at": "2026-10-15T19:17:31.710941+00:00",
      "created_at": "2026-10-15T19:17:31.710941+00:00"
    }
  ]
};

const EMPTY_BOARD = { now: [], waiting: [], unassigned: [], overdue: [] };

describe("Follow-through settled face", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    openSourceRef.mockReset();
    localStorage.clear();
  });

  it("draws each populated group once, with wrapped tasks, full owners and verified source words", async () => {
    apiFetch.mockResolvedValue(structuredClone(WALK_BOARD));
    const { container } = render(<FollowThroughView />);
    await screen.findByText("Alexandra Montgomery");
    expect([...container.querySelectorAll(".surface-section-head h3")].map((h) => h.textContent))
      .toEqual(["Overdue · 1", "To review · 1", "Due soon · 1", "Later · 1"]);
    expect(container.querySelectorAll(".surface-ledger-head")).toHaveLength(0);
    expect(container.querySelectorAll(".surface-ledger-row[data-wrap]")).toHaveLength(4);
    const unowned = screen.getByText("Name the migration owner").closest(".surface-ledger-row")!;
    expect(within(unowned as HTMLElement).getByText("No owner")).toBeInTheDocument();
    expect(within(unowned as HTMLElement).queryByRole("button", { name: /Open meeting/ })).toBeNull();
    expect(screen.queryByText(/SOURCE MOMENT UNAVAILABLE/i)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Open note for Write the release checklist" }));
    expect(openSourceRef).toHaveBeenCalledWith(WALK_BOARD.overdue[0].provenance.source_ref);
  });

  it("keeps People Done and Undo in memory, and discards a legacy persisted private receipt", async () => {
    const card = structuredClone(PEOPLE_CARD.wire);
    localStorage.setItem("hs.follow-through.done-receipt", JSON.stringify({ cardId: card.id, label: card.text, createdAt: Date.now() }));
    let closed = false;
    apiFetch.mockImplementation(async (path: string, init?: any) => {
      if (path === "/api/follow-through/board") return closed ? EMPTY_BOARD : { ...EMPTY_BOARD, now: [card] };
      if (init?.json?.verb === "done") closed = true;
      if (init?.json?.verb === "reopen") closed = false;
      return { card_id: card.id, verb: init?.json?.verb };
    });
    render(<FollowThroughView />);
    await screen.findByText(card.text, { selector: "strong" });
    expect(localStorage.getItem("hs.follow-through.done-receipt")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Mark done" }));
    await screen.findByText("No follow-through yet");
    expect(screen.getByTestId("follow-through-done-receipt")).toHaveTextContent(card.text);
    expect(localStorage.getItem("hs.follow-through.done-receipt")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Undo" }));
    await screen.findByText(card.text, { selector: "strong" });
    expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: card.id, verb: "reopen", payload: {} },
    });
  });

  it("shows a last-row Undo refusal on an empty board and Retry repeats that exact write", async () => {
    const card = structuredClone(HONEST_BOARD.wire.unassigned[0]);
    let closed = false;
    let refused = true;
    apiFetch.mockImplementation(async (path: string, init?: any) => {
      if (path === "/api/follow-through/board") return closed ? EMPTY_BOARD : { ...EMPTY_BOARD, unassigned: [card] };
      if (init.json.verb === "reopen" && refused) throw new Error("Reopen refused by owner policy");
      closed = init.json.verb === "done";
      return { card_id: card.id, verb: init.json.verb };
    });
    render(<FollowThroughView />);
    await screen.findByText(card.text, { selector: "strong" });
    fireEvent.click(screen.getByRole("button", { name: "Mark done" }));
    await screen.findByText("No follow-through yet");
    fireEvent.click(screen.getByRole("button", { name: "Undo" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Reopen refused by owner policy");
    refused = false;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByText(card.text, { selector: "strong" });
    expect(apiFetch.mock.calls.filter(([path, init]) => path.endsWith("/complete") && init.json.verb === "reopen")).toHaveLength(2);
  });
});


function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

describe("Follow-through writer and draft custody", () => {
  beforeEach(() => { apiFetch.mockReset(); openSourceRef.mockReset(); localStorage.clear(); });

  it("reads and expands the exact held source despite the ordinary overdue filter without a lifecycle write", async () => {
    const target = { ...WALK_BOARD.waiting[0], snoozed_until: "2026-10-17", deferred_until: "2026-10-18T00:00:00Z" };
    apiFetch.mockResolvedValue({ ...structuredClone(WALK_BOARD), waiting: [target] });
    render(<FollowThroughView focusCardId={target.id} overdueOnly />);
    const details = await screen.findByRole("button", { name: `Details for ${target.text}` });
    await waitFor(() => expect(details).toHaveAttribute("aria-expanded", "true"));
    expect(screen.getByLabelText("Snoozed until 2026-10-17")).toBeInTheDocument();
    expect(screen.getByLabelText("Deferred until 2026-10-18")).toBeInTheDocument();
    expect(screen.queryByText(WALK_BOARD.now[0].text, { selector: "strong" })).toBeNull();
    expect(apiFetch).toHaveBeenCalledWith(`/api/follow-through/board?focus_id=${target.id}`);
    expect(apiFetch.mock.calls.every(([, init]) => !init?.method)).toBe(true);
  });

  it("missing focus and refused focus reads each retry the same canonical source", async () => {
    apiFetch.mockResolvedValueOnce(EMPTY_BOARD).mockRejectedValueOnce(new Error("Read refused")).mockResolvedValueOnce(EMPTY_BOARD);
    render(<FollowThroughView focusCardId="held/id" />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Task unavailable");
    fireEvent.click(screen.getByRole("button", { name: "Retry read" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Read refused");
    fireEvent.click(screen.getByRole("button", { name: "Retry read" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Task unavailable"));
    expect(apiFetch.mock.calls.map(([path]) => path)).toEqual(Array(3).fill("/api/follow-through/board?focus_id=held%2Fid"));
  });

  it("Assign uses the existing writer once, keeps the board visible, and preserves a newer owner draft across a lane move", async () => {
    const card = structuredClone(WALK_BOARD.now[0]);
    let board: Record<keyof typeof EMPTY_BOARD, (typeof card)[]> = { ...EMPTY_BOARD, now: [card] };
    const write = deferred<unknown>();
    apiFetch.mockImplementation((path: string, init?: any) => path.endsWith("/board") ? Promise.resolve(board) : write.promise);
    render(<FollowThroughView />);
    fireEvent.click(await screen.findByRole("button", { name: `Details for ${card.text}` }));
    fireEvent.change(screen.getByRole("textbox", { name: "Owner" }), { target: { value: "Avery" } });
    fireEvent.click(screen.getByRole("button", { name: "Assign" }));
    fireEvent.click(screen.getByRole("button", { name: "Assign" }));
    expect(screen.getByRole("button", { name: "Mark done" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Save date" })).toBeDisabled();
    expect(screen.getByText(card.text, { selector: "strong" })).toBeInTheDocument();
    expect(apiFetch.mock.calls.filter(([path]) => path.endsWith("/complete"))).toHaveLength(1);
    fireEvent.change(screen.getByRole("textbox", { name: "Owner" }), { target: { value: "Newer draft" } });
    board = { ...EMPTY_BOARD, now: [], waiting: [{ ...card, owner: "Avery" }] };
    await act(async () => { write.resolve({ card_id: card.id, verb: "delegate" }); });
    await screen.findByText("Assigned to Avery");
    expect(screen.getByRole("textbox", { name: "Owner" })).toHaveValue("Newer draft");
    expect(screen.getByText("Avery")).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", { method: "POST", json: { card_id: card.id, verb: "delegate", payload: { to: "Avery" } } });
  });

  it("a held task write follows the current focused source after another source opens while it is pending", async () => {
    const first = { ...structuredClone(WALK_BOARD.waiting[0]), snoozed_until: "2026-10-17" };
    const second = { ...structuredClone(WALK_BOARD.now[0]), deferred_until: "2026-10-18T00:00:00Z" };
    const write = deferred<unknown>();
    apiFetch.mockImplementation((path: string) => {
      if (path === `/api/follow-through/board?focus_id=${first.id}`) return Promise.resolve({ ...EMPTY_BOARD, waiting: [first] });
      if (path === `/api/follow-through/board?focus_id=${second.id}`) return Promise.resolve({ ...EMPTY_BOARD, now: [second] });
      if (path === "/api/follow-through/complete") return write.promise;
      throw new Error(`Unexpected request: ${path}`);
    });
    const view = render(<FollowThroughView focusCardId={first.id} />);
    await waitFor(() => expect(screen.getByRole("button", { name: `Details for ${first.text}` })).toHaveAttribute("aria-expanded", "true"));
    fireEvent.change(screen.getByRole("textbox", { name: "Owner" }), { target: { value: "Avery" } });
    fireEvent.click(screen.getByRole("button", { name: "Assign" }));
    view.rerender(<FollowThroughView focusCardId={second.id} />);
    await waitFor(() => expect(screen.getByRole("button", { name: `Details for ${second.text}` })).toHaveAttribute("aria-expanded", "true"));
    await act(async () => { first.owner = "Avery"; write.resolve({ card_id: first.id, verb: "delegate" }); });
    expect(await screen.findByLabelText("Assigned to Avery")).toBeInTheDocument();
    expect(screen.getByText(first.text, { selector: ".surface-action-notice span" })).toBeInTheDocument();
    expect(screen.getByText(second.text, { selector: "strong" })).toBeInTheDocument();
    expect(screen.queryByText(first.text, { selector: "strong" })).toBeNull();
    expect(screen.getByRole("button", { name: `Details for ${second.text}` })).toHaveAttribute("aria-expanded", "true");
    expect(screen.queryByLabelText("Task unavailable")).toBeNull();
    const reads = apiFetch.mock.calls.filter(([path]) => path.startsWith("/api/follow-through/board"));
    expect(reads.map(([path]) => path)).toEqual([
      `/api/follow-through/board?focus_id=${first.id}`,
      `/api/follow-through/board?focus_id=${second.id}`,
      `/api/follow-through/board?focus_id=${second.id}`,
    ]);
    const writes = apiFetch.mock.calls.filter(([path]) => path === "/api/follow-through/complete");
    expect(writes).toHaveLength(1);
    expect(writes[0][1]).toEqual({ method: "POST", json: { card_id: first.id, verb: "delegate", payload: { to: "Avery" } } });
  });

  it("a refused date keeps the draft and Retry sends the rejected date without replacing newer input", async () => {
    const originalScroll = HTMLElement.prototype.scrollIntoView;
    const scroll = vi.fn();
    HTMLElement.prototype.scrollIntoView = scroll;
    try {
      const card = structuredClone(WALK_BOARD.now[0]);
      let refused = true;
      apiFetch.mockImplementation(async (path: string, init?: any) => {
        if (path.endsWith("/board")) return { ...EMPTY_BOARD, now: [card] };
        if (refused) throw new Error("Date change refused");
        card.due = init.json.payload.due_at;
        return { card_id: card.id, verb: "due" };
      });
      render(<FollowThroughView />);
      fireEvent.click(await screen.findByRole("button", { name: `Details for ${card.text}` }));
      const date = screen.getByLabelText("Due date", { selector: "input" });
      fireEvent.change(date, { target: { value: "2026-10-20" } });
      fireEvent.click(screen.getByRole("button", { name: "Save date" }));
      const alert = await screen.findByRole("alert");
      expect(alert).toHaveTextContent("Date change refused");
      expect(within(alert).getByText(card.text)).toBeInTheDocument();
      expect(within(alert).getByLabelText("Save date failed")).toBeInTheDocument();
      expect(scroll).toHaveBeenCalledTimes(1);
      expect(scroll).toHaveBeenCalledWith({ block: "nearest" });
      expect(scroll.mock.contexts[0]).toContainElement(alert);
      expect(date).toHaveValue("2026-10-20");
      fireEvent.change(date, { target: { value: "2026-10-21" } });
      await act(async () => { busRefresh.current?.(); });
      expect(scroll).toHaveBeenCalledTimes(1);
      expect(screen.getByLabelText("Due date", { selector: "input" })).toHaveValue("2026-10-21");
      refused = false;
      fireEvent.click(screen.getByRole("button", { name: "Retry" }));
      await screen.findByText("Date saved: 2026-10-20");
      expect(screen.getByLabelText("Due date", { selector: "input" })).toHaveValue("2026-10-21");
      const writes = apiFetch.mock.calls.filter(([path]) => path.endsWith("/complete"));
      expect(writes.map(([, init]) => init.json)).toEqual([1, 2].map(() => ({ card_id: card.id, verb: "due", payload: { due_at: "2026-10-20" } })));
      fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
      expect(screen.queryByRole("textbox", { name: "Owner" })).toBeNull();
      expect(apiFetch.mock.calls.filter(([path]) => path.endsWith("/complete"))).toHaveLength(2);
    } finally { HTMLElement.prototype.scrollIntoView = originalScroll; }
  });

  it("Tomorrow sends the next local day during a Denver evening, and Dismiss is a separate receipted write", async () => {
    vi.stubEnv("TZ", "America/Denver");
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-15T23:30:00-06:00"));
    const card = structuredClone(WALK_BOARD.now[0]);
    apiFetch.mockImplementation(async (path: string, init?: any) => path.endsWith("/board") ? { ...EMPTY_BOARD, now: [card] } : { card_id: card.id, verb: init.json.verb });
    render(<FollowThroughView />);
    fireEvent.click(await screen.findByRole("button", { name: `Details for ${card.text}` }));
    fireEvent.click(screen.getByRole("button", { name: "Tomorrow" }));
    await screen.findByText("Until 2026-10-16");
    expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", { method: "POST", json: { card_id: card.id, verb: "snooze", payload: { until: "2026-10-16" } } });
    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    await screen.findByText("Dismissed");
    expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", { method: "POST", json: { card_id: card.id, verb: "dismiss", payload: {} } });
  });

  it("People exposes only its existing Done, Dismiss and source authorities", async () => {
    const card = structuredClone(PEOPLE_CARD.wire);
    apiFetch.mockResolvedValue({ ...EMPTY_BOARD, now: [card] });
    render(<FollowThroughView />);
    fireEvent.click(await screen.findByRole("button", { name: `Details for ${card.text}` }));
    expect(screen.getByRole("button", { name: "Mark done" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: `Open People for ${card.text}` })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tomorrow" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Assign" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Save date" })).toBeNull();
    expect(screen.queryByText(/moment unavailable/i)).toBeNull();
  });

  it("an addressed task scrolls and expands after its read, while refresh neither re-scrolls nor accepts an old answer", async () => {
    const target = WALK_BOARD.waiting[0];
    const oldScroll = HTMLElement.prototype.scrollIntoView;
    const scroll = vi.fn();
    HTMLElement.prototype.scrollIntoView = scroll;
    const initial = deferred<unknown>();
    const older = deferred<unknown>();
    const newer = deferred<unknown>();
    apiFetch.mockReturnValueOnce(initial.promise).mockReturnValueOnce(older.promise).mockReturnValueOnce(newer.promise);
    try {
      const { container } = render(<FollowThroughView focusCardId={target.id} />);
      expect(screen.queryByText(target.text)).toBeNull();
      await act(async () => { initial.resolve(structuredClone(WALK_BOARD)); });
      expect(container.querySelector('[data-selected="true"]')).toHaveTextContent(target.text);
      expect(screen.getByRole("button", { name: `Details for ${target.text}` })).toHaveAttribute("aria-expanded", "true");
      expect(scroll).toHaveBeenCalledWith({ block: "nearest" });
      const scrolls = scroll.mock.calls.length;
      act(() => { busRefresh.current?.(); busRefresh.current?.(); });
      const current = structuredClone(WALK_BOARD);
      current.waiting[0].owner = "Latest owner";
      await act(async () => { newer.resolve(current); });
      expect(screen.getByText("Latest owner")).toBeInTheDocument();
      await act(async () => { older.resolve(structuredClone(WALK_BOARD)); });
      expect(screen.getByText("Latest owner")).toBeInTheDocument();
      expect(screen.queryByText("Alexandra Montgomery")).toBeNull();
      expect(scroll.mock.calls).toHaveLength(scrolls);
    } finally { HTMLElement.prototype.scrollIntoView = oldScroll; }
  });
});

// Real HTTP board from root isolated hub, 2026-10-15.
// Producer: CadenceRepository.upsert_loop(OpenLoop(source_type=manual));
// declared repository seed, not collector/model evidence.
// .tmp/follow-through/loop-wire/{board,provenance}.json
const LOOP_BOARD = {
  "now": [
    {
      "id": "55ef85a6bf494daeb5047084eb079063",
      "text": "Review the release checklist",
      "owner": "Karol",
      "due": "2026-10-15",
      "status": "open",
      "meeting_id": null,
      "decision_id": null,
      "stale_score": 0.0,
      "source": "cadence_loop",
      "lane": "now",
      "provenance": {
        "meeting_id": null,
        "segment_text": null,
        "segment_speaker": null,
        "segment_start": null,
        "moment": null,
        "available": false,
        "thread_id": null,
        "source_ref": null
      },
      "target_ref": null,
      "delegated_at": null,
      "created_at": null
    }
  ],
  "waiting": [],
  "unassigned": [],
  "overdue": []
};

describe("Follow-through cadence authority", () => {
  beforeEach(() => { apiFetch.mockReset(); localStorage.clear(); });
  it.each([
    ["Close loop", "close", "Closed"],
    ["Stop", "kill", "Stopped"],
    ["Tomorrow", "snooze", "Until"],
  ])("%s uses its actual cadence writer and never offers an action Undo", async (name, endpoint, receipt) => {
    const card = LOOP_BOARD.now[0];
    let closed = false;
    apiFetch.mockImplementation(async (path: string) => {
      if (path.endsWith("/board")) return closed ? EMPTY_BOARD : structuredClone(LOOP_BOARD);
      closed = true;
      return { ...card, status: endpoint === "close" ? "closed" : endpoint === "kill" ? "killed" : "snoozed" };
    });
    render(<FollowThroughView />);
    fireEvent.click(await screen.findByRole("button", { name: `Details for ${card.text}` }));
    expect(screen.queryByRole("button", { name: "Mark done" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Assign" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Save date" })).toBeNull();
    expect(screen.queryByRole("button", { name: /Open meeting/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name }));
    await screen.findByText("No follow-through yet");
    expect(screen.getByLabelText(new RegExp(`^${receipt}`))).toBeInTheDocument();
    const writes = apiFetch.mock.calls.filter(([path]) => !path.endsWith("/board"));
    expect(writes).toHaveLength(1);
    expect(writes[0][0]).toBe(`/api/cadence/loops/${card.id}/${endpoint}`);
    expect(writes[0][1].method).toBe("POST");
    if (endpoint === "snooze") expect(writes[0][1].json.until).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(screen.queryByRole("button", { name: "Undo" })).toBeNull();
    expect(localStorage.getItem("hs.follow-through.done-receipt")).toBeNull();
  });
});

// Betterment daily D1: on the recon week (the hub's recorded board,
// tests/unit/test_desk_needs_you.py::test_the_one_number_is_mine_due_today_and_to_decide),
// a kept action opens its meeting, never "Open decision", and its due shows
// once, as a date ("Tue 20 Oct"), never "Friday nex".
import DAILY_WEEK from "../../__tests__/fixtures/daily-week/needs-you.json";

describe("FollowThroughView: the daily week's labels", () => {
  beforeEach(() => apiFetch.mockReset());

  it("every kept action reads Open meeting and one whole date", async () => {
    apiFetch.mockResolvedValue(DAILY_WEEK.followThrough);
    render(<FollowThroughView />);
    const board = DAILY_WEEK.followThrough as Record<string, Array<{ text: string; due: string | null }>>;
    const cards = ["now", "waiting", "unassigned", "overdue"].flatMap((lane) => board[lane]);
    expect(cards).toHaveLength(7);
    for (const card of cards) {
      expect(await screen.findByRole("button", { name: `Open meeting for ${card.text}` })).toBeTruthy();
      expect(screen.queryByRole("button", { name: `Open decision for ${card.text}` })).toBeNull();
      const day = new Date(`${card.due}T00:00:00`).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
      const row = screen.getByText(card.text).closest("li, [role='row'], .surface-ledger-row") as HTMLElement;
      expect(within(row).getAllByText(day)).toHaveLength(1);
      expect(row.textContent).not.toMatch(/Due in|\d{4}-\d{2}-\d{2}/);
    }
  });
});
