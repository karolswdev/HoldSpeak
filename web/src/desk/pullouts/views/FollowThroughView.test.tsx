// HS-150-07 -- FollowThroughView: person chip + staleness for mapped owners,
// bare initials for unmapped.

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FollowThroughView } from "./FollowThroughView";
import HONEST_BOARD from "../../../test/wire/follow-through-board.honest-faces.wire.json";

// ---------------------------------------------------------------------------
// mocks
// ---------------------------------------------------------------------------

const apiFetch = vi.hoisted(() => vi.fn());
const openSourceRef = vi.hoisted(() => vi.fn());

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
    expect(staleness.textContent).toMatch(/^waiting \d+d$/);
  });

  it("shows bare initials for unmapped owner", async () => {
    apiFetch.mockResolvedValueOnce(makeBoard({ unmappedOwner: true }));

    render(<FollowThroughView />);

    await waitFor(() => {
      expect(screen.getByText("UP")).toBeTruthy();
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
    expect(screen.getByText("UP")).toBeTruthy();

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
    fireEvent.click(screen.getByRole("button", { name: "Open source note for Update the note" }));
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
  it("two cards to review read 2 TO REVIEW, never TO REVIEWS or NOWS", async () => {
    // replaces: tests/e2e/test_honest_faces_glass.py::test_intelligence_lane_names_and_decision_rows (the Follow-through leg)
    apiFetch.mockResolvedValue(structuredClone(HONEST_BOARD.wire));
    const { container } = render(<FollowThroughView />);
    await screen.findByText("Write the rollback runbook");
    expect(screen.getByText("Pilot OTel in billing")).toBeTruthy();
    expect(screen.getByText("2 TO REVIEW")).toBeTruthy();
    expect(container.textContent ?? "").not.toMatch(/\b\d+ (NOWS|TO REVIEWS|UNASSIGNEDS|WAITINGS|OVERDUES)\b/);
  });
});
