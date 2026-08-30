// HS-150-07 -- FollowThroughView: person chip + staleness for mapped owners,
// bare initials for unmapped.

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FollowThroughView } from "./FollowThroughView";

// ---------------------------------------------------------------------------
// mocks
// ---------------------------------------------------------------------------

const apiFetch = vi.hoisted(() => vi.fn());

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
});
