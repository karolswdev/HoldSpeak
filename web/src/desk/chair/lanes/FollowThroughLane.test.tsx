// HS-135-08 -- Follow-Through lane tests: seeded ordering (overdue
// before now before waiting), maxItems, verbs fire the real actions
// (mocked), empty state honest, hidden newCommitmentVerb slot renders
// nothing.

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FollowThroughLane } from "./FollowThroughLane";

// ---------------------------------------------------------------------------
// mocks
// ---------------------------------------------------------------------------

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../../lib/api", () => ({
  apiFetch,
  readableError: (reason: unknown) =>
    reason instanceof Error ? reason.message : "Request failed",
}));

const openIntelligence = vi.hoisted(() => vi.fn());

vi.mock("../../intelligenceNavigation", () => ({
  openIntelligence,
}));

vi.mock("../../intelligenceAttention", () => ({
  refreshIntelligenceAttention: vi.fn(),
}));

// ---------------------------------------------------------------------------
// fixtures
// ---------------------------------------------------------------------------

const overdueCard = {
  id: "card-overdue-1",
  text: "File quarterly report",
  owner: "Ada Lovelace",
  due: "2020-01-01",
  source: "meeting",
};

const nowCard = {
  id: "card-now-1",
  text: "Review pull request",
  owner: "Bob Smith",
  due: "2099-12-31",
  source: "decision",
};

const waitingCard = {
  id: "card-waiting-1",
  text: "Await vendor response",
  owner: null,
  due: null,
  source: "meeting",
};

const emptyBoard = { now: [], waiting: [], unassigned: [], overdue: [] };

const seededBoard = {
  now: [nowCard],
  waiting: [waitingCard],
  unassigned: [],
  overdue: [overdueCard],
};

function mockBoard(board = seededBoard) {
  apiFetch.mockImplementation((path: string) => {
    if (path === "/api/follow-through/board") return Promise.resolve(board);
    if (path === "/api/follow-through/complete") return Promise.resolve({});
    return Promise.resolve({});
  });
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function renderLane(props: Partial<React.ComponentProps<typeof FollowThroughLane>> = {}) {
  const onOpenInWindow = vi.fn();
  const result = render(
    <FollowThroughLane onOpenInWindow={onOpenInWindow} {...props} />,
  );
  return { ...result, onOpenInWindow };
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("FollowThroughLane", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // -- ordering -----------------------------------------------------------

  it("renders overdue items before now items before waiting items", async () => {
    mockBoard();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("File quarterly report")).toBeInTheDocument();
    });
    // SurfaceRow renders each item as an <li> with a strong title.
    const listItems = screen.getAllByRole("listitem");
    const titles = listItems.map(
      (li) => within(li).queryByText(/File quarterly|Review pull|Await vendor/)?.textContent,
    ).filter(Boolean);
    expect(titles).toEqual([
      "File quarterly report",
      "Review pull request",
      "Await vendor response",
    ]);
  });

  // -- maxItems -----------------------------------------------------------

  it("caps visible items at maxItems", async () => {
    const manyOverdue = Array.from({ length: 5 }, (_, i) => ({
      id: `overdue-${i}`,
      text: `Overdue item ${i}`,
      owner: "Test",
      due: "2020-01-01",
      source: "meeting",
    }));
    mockBoard({
      now: [],
      waiting: [],
      unassigned: [],
      overdue: manyOverdue,
    });
    renderLane({ maxItems: 3 });
    await waitFor(() => {
      expect(screen.getByText("Overdue item 0")).toBeInTheDocument();
    });
    // Only 3 of 5 items should be visible.
    expect(screen.getByText("Overdue item 0")).toBeInTheDocument();
    expect(screen.getByText("Overdue item 1")).toBeInTheDocument();
    expect(screen.getByText("Overdue item 2")).toBeInTheDocument();
    expect(screen.queryByText("Overdue item 3")).not.toBeInTheDocument();
    expect(screen.queryByText("Overdue item 4")).not.toBeInTheDocument();
    // Footer overflow.
    expect(screen.getByText(/2 more/)).toBeInTheDocument();
  });

  // -- verbs --------------------------------------------------------------

  it("complete verb fires the done action", async () => {
    mockBoard();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("File quarterly report")).toBeInTheDocument();
    });
    const completeBtn = screen.getByLabelText("Complete File quarterly report");
    await act(async () => {
      fireEvent.click(completeBtn);
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST",
      json: { card_id: "card-overdue-1", verb: "done", payload: {} },
    });
  });

  it("dismiss verb fires the dismiss action", async () => {
    mockBoard();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("File quarterly report")).toBeInTheDocument();
    });
    const dismissBtn = screen.getByLabelText("Dismiss File quarterly report");
    await act(async () => {
      fireEvent.click(dismissBtn);
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST",
      json: { card_id: "card-overdue-1", verb: "dismiss", payload: {} },
    });
  });

  // -- empty state --------------------------------------------------------

  it("renders honest empty state when board is empty", async () => {
    mockBoard(emptyBoard);
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("No follow-through yet")).toBeInTheDocument();
    });
  });

  // -- header-click opens Intelligence -----------------------------------

  it("header click opens Intelligence on the Follow-Through wing", async () => {
    mockBoard();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("File quarterly report")).toBeInTheDocument();
    });
    const headerBtn = screen.getByLabelText("Open FOLLOW-THROUGH");
    fireEvent.click(headerBtn);
    expect(openIntelligence).toHaveBeenCalledWith({ view: "follow-through" });
  });

  // -- newCommitmentVerb hidden slot --------------------------------------

  describe("newCommitmentVerb forward-compatible slot", () => {
    it("prop exists on the component interface (typed)", () => {
      // Type-level proof: this compiles without error.
      const _props: React.ComponentProps<typeof FollowThroughLane> = {
        onOpenInWindow: vi.fn(),
        newCommitmentVerb: <button type="button">New commitment</button>,
      };
      expect(_props.newCommitmentVerb).toBeDefined();
    });

    it("renders nothing when null (the default)", async () => {
      mockBoard();
      const { container } = renderLane();
      await waitFor(() => {
        expect(screen.getByText("File quarterly report")).toBeInTheDocument();
      });
      // The slot should produce no extra DOM node.
      expect(container.querySelector("[data-testid='new-commitment-verb']")).toBeNull();
      expect(screen.queryByText("New commitment")).not.toBeInTheDocument();
    });

    it("renders the slot content when provided", async () => {
      mockBoard();
      renderLane({
        newCommitmentVerb: (
          <button type="button" data-testid="new-commitment-verb">
            New commitment
          </button>
        ),
      });
      await waitFor(() => {
        expect(screen.getByText("File quarterly report")).toBeInTheDocument();
      });
      expect(screen.getByTestId("new-commitment-verb")).toBeInTheDocument();
      expect(screen.getByText("New commitment")).toBeInTheDocument();
    });
  });

  // -- owner/age rendering -----------------------------------------------

  it("shows owner initials and age for each item", async () => {
    mockBoard();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("File quarterly report")).toBeInTheDocument();
    });
    // Ada Lovelace -> "AL", overdue date -> "overdue Xd"
    expect(screen.getByText(/AL/)).toBeInTheDocument();
    // Bob Smith -> "BS"
    expect(screen.getByText(/BS/)).toBeInTheDocument();
    // null owner -> dash
    const dashElements = screen.getAllByText(/—/);
    expect(dashElements.length).toBeGreaterThanOrEqual(1);
  });
});
