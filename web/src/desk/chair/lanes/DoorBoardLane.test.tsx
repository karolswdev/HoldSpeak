import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DoorBoardLane, commandForDoorVerb, type DoorProjection } from "./DoorBoardLane";

const apiFetch = vi.hoisted(() => vi.fn());
const newDeliveryId = vi.hoisted(() => vi.fn(() => "door-request-id"));
const openIntelligence = vi.hoisted(() => vi.fn());

vi.mock("../../../lib/api", () => ({
  apiFetch,
  newDeliveryId,
  readableError: (cause: unknown) => cause instanceof Error ? cause.message : "Request failed",
}));
vi.mock("../../intelligenceNavigation", () => ({ openIntelligence }));
vi.mock("../../surface/gadgets", () => ({
  StringGadget: ({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) => (
    <label>{label}<input aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} /></label>
  ),
}));

const projection: DoorProjection = {
  board: {
    overdue: [{
      id: "action-1", text: "Ship Door", source: "action_item", target_ref: "action_item:action-1",
      owner: "Ada", due: "2020-01-01", stale_score: 4,
      lawful_verbs: [
        { name: "follow_through.complete", arguments: { card_id: "action-1", verb: "done" } },
        { name: "follow_through.complete", arguments: { card_id: "action-1", verb: "snooze" }, required_arguments: ["payload.until"] },
        { name: "follow_through.complete", arguments: { card_id: "action-1", verb: "delegate" }, required_arguments: ["payload.to"] },
      ],
    }],
    now: [{
      id: "loop-1", text: "Close weekly loop", source: "cadence_loop", target_ref: "cadence_loop:loop-1",
      lawful_verbs: [
        { name: "cadence.set_status", arguments: { loop_id: "loop-1", status: "closed" } },
        { name: "cadence.set_status", arguments: { loop_id: "loop-1", status: "killed" } },
      ],
    }],
    waiting: [{
      id: "people-1", text: "Reply to Jordan", source: "people_commitment", target_ref: "people:relationship-1",
      lawful_verbs: [
        { name: "people.commitment.transition", arguments: { commitment_id: "commitment-1", verb: "done" } },
        { name: "unknown.route", arguments: { id: "nope" } },
      ],
    }],
    unassigned: [{ id: "plain-1", text: "No action", source: "action_item", target_ref: "action_item:plain-1", lawful_verbs: [] }],
    active: [{
      id: "thought-1", title: "Think through the Door", body_preview: "A working line", source: "thought",
      target_ref: "thought:thought-1", open_ref: "note:note-1", continuity_state: "review_ready",
      updated_at: "2026-08-27T10:00:00Z",
      lawful_verbs: [{ name: "thought.complete", arguments: { thought_id: "thought-1", expected_aggregate_revision: 7, expected_lifecycle_revision: 3 }, required_arguments: ["request_id"] }],
    }],
  },
  counts: { overdue: 7, now: 6, waiting: 5, active: 4, upcoming_today: 99 },
  upcoming: [{ title: "HS-144-04 owns this" }],
};

function mockDoor(value: DoorProjection = projection) {
  apiFetch.mockImplementation((path: string) => {
    if (path === "/api/door") return Promise.resolve(value);
    return Promise.resolve({});
  });
}

function renderLane() {
  const onOpenInWindow = vi.fn();
  return { onOpenInWindow, ...render(<DoorBoardLane onOpenInWindow={onOpenInWindow} />) };
}

beforeEach(() => {
  vi.clearAllMocks();
  mockDoor();
});
afterEach(() => vi.unstubAllGlobals());

describe("DoorBoardLane", () => {
  it("renders the exact five server columns in visual order with server counts", async () => {
    renderLane();
    await screen.findByText("Ship Door");
    expect(Array.from(document.querySelectorAll(".door-board-column h4")).map((node) => node.textContent))
      .toEqual(["Overdue", "Now", "Waiting", "Unassigned", "Active"]);
    expect(screen.getByText("7 overdue · 6 now · 5 waiting · 4 active")).toBeInTheDocument();
    expect(screen.getByLabelText("7 overdue items")).toBeInTheDocument();
    expect(screen.queryByText("HS-144-04 owns this")).toBeNull();
    expect(screen.getByText(/action item · owner Ada · overdue/)).toBeInTheDocument();
    expect(screen.getByText(/thought · review ready · updated/)).toBeInTheDocument();
  });

  it("keeps the Brief capability as an explicit Door-header entry", async () => {
    renderLane();
    await screen.findByText("Ship Door");
    fireEvent.click(screen.getByRole("button", { name: "Brief" }));
    expect(openIntelligence).toHaveBeenCalledWith({ view: "brief" });
  });

  it("uses only the fixed route adapter table", () => {
    expect(commandForDoorVerb({ name: "follow_through.complete", arguments: { card_id: "a", verb: "done" } }))
      .toEqual({ endpoint: "/api/follow-through/complete", body: { card_id: "a", verb: "done", payload: {} } });
    expect(commandForDoorVerb({ name: "follow_through.complete", arguments: { card_id: "a", verb: "snooze" } }))
      .toBeNull();
    expect(commandForDoorVerb({ name: "follow_through.complete", arguments: { card_id: "a", verb: "snooze" } }, { until: "2026-09-01" }))
      .toEqual({ endpoint: "/api/follow-through/complete", body: { card_id: "a", verb: "snooze", payload: { until: "2026-09-01" } } });
    expect(commandForDoorVerb({ name: "follow_through.complete", arguments: { card_id: "a", verb: "delegate" } }, { to: "Jordan" }))
      .toEqual({ endpoint: "/api/follow-through/complete", body: { card_id: "a", verb: "delegate", payload: { to: "Jordan" } } });
    expect(commandForDoorVerb({ name: "cadence.set_status", arguments: { loop_id: "a b", status: "closed" } }))
      .toEqual({ endpoint: "/api/cadence/loops/a%20b/close" });
    expect(commandForDoorVerb({ name: "cadence.set_status", arguments: { loop_id: "a b", status: "killed" } }))
      .toEqual({ endpoint: "/api/cadence/loops/a%20b/kill" });
    expect(commandForDoorVerb({ name: "thought.complete", arguments: { thought_id: "thought-1", expected_aggregate_revision: 7, expected_lifecycle_revision: 3 } }))
      .toEqual({ endpoint: "/api/thoughts/thought-1/complete", body: { request_id: "door-request-id", expected_aggregate_revision: 7, expected_lifecycle_revision: 3 } });
    expect(commandForDoorVerb({ name: "people.commitment.transition", arguments: { commitment_id: "people-1", verb: "dismiss" } }))
      .toEqual({ endpoint: "/api/people/commitments/people-1/transition", body: { verb: "dismiss" } });
    expect(commandForDoorVerb({ name: "unknown.route", arguments: {} })).toBeNull();
  });

  it("does not send incomplete snooze data and expands only its own card", async () => {
    renderLane();
    await screen.findByText("Ship Door");
    fireEvent.click(screen.getByRole("button", { name: "Snooze" }));
    expect(screen.getByLabelText("Until")).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByLabelText("Until"), { target: { value: "2026-09-01" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-1", verb: "snooze", payload: { until: "2026-09-01" } },
    }));
  });

  it("revalidates after a write and seats a retryable refusal in flow", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/door") return Promise.resolve(projection);
      return Promise.reject(new Error("verb refused"));
    });
    renderLane();
    await screen.findByText("Ship Door");
    fireEvent.click(within(screen.getByText("Ship Door").closest("article")!).getByRole("button", { name: "Done" }));
    expect(await screen.findByText("DONE FAILED · WRITE REFUSED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(apiFetch.mock.calls.filter(([path]) => path === "/api/follow-through/complete")).toHaveLength(2));
  });

  it("maps the visible People descriptor to the Slice 0 transition route", async () => {
    renderLane();
    await screen.findByText("Reply to Jordan");
    fireEvent.click(within(screen.getByText("Reply to Jordan").closest("article")!).getByRole("button", { name: "Done" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/people/commitments/commitment-1/transition", {
      method: "POST", json: { verb: "done" },
    }));
    expect(screen.queryByRole("button", { name: "unknown.route" })).toBeNull();
  });

  it("renders designed empty and initial-error states", async () => {
    const empty: DoorProjection = { ...projection, board: { overdue: [], now: [], waiting: [], unassigned: [], active: [] } };
    mockDoor(empty);
    const { unmount } = renderLane();
    expect(await screen.findByText("Door clear")).toBeInTheDocument();
    unmount();
    apiFetch.mockRejectedValue(new Error("Door unavailable"));
    renderLane();
    const error = await screen.findByText("Door unavailable");
    expect(error.closest(".door-board-section")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Brief" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });
});
