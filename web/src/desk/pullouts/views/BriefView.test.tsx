// HS-150-03 -- BriefView tests: person sections render with the correct
// manager verbs (Add to 1:1 agenda, Open person); receipt items keep
// Acknowledge/Defer/Speak; absence renders as L2 honesty line.

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BriefView } from "./BriefView";

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

const openSurfaceOr = vi.hoisted(() => vi.fn());

vi.mock("../../shell", () => ({
  openSurfaceOr,
}));

vi.mock("../../hooks/useWriteReceipt", () => ({
  useWriteReceipt: () => ({ attempt: vi.fn().mockResolvedValue({ ok: true }), receipt: null }),
}));

// ---------------------------------------------------------------------------
// fixtures
// ---------------------------------------------------------------------------

const briefWithPeople = {
  id: "brief-people",
  headline: "1 thing changed.",
  is_empty: false,
  shelf: {},
  sections: {
    changed: [
      {
        id: "item-1",
        section: "changed",
        text: "Meeting recorded: Standup",
        detail: null,
        source_ref: "meeting:m-1",
        priority: 50,
      },
    ],
    broke: [],
    waiting: [],
    decisions: [],
  },
  person_sections: [
    {
      relationship_id: "rel-ewa",
      display_name: "Ewa",
      they_owe_count: 2,
      stalest_age_days: 5,
      you_owe_count: 1,
      agenda_backlog: 3,
      next_one_on_one: { event_id: "ev-1", title: "Weekly 1:1", starts_at: "2026-09-01" },
    },
  ],
};

const briefWithUnavailablePeople = {
  ...briefWithPeople,
  person_sections: undefined,
  person_sections_state: "unavailable",
};

function mockBrief(brief: unknown = briefWithPeople) {
  apiFetch.mockImplementation((path: string) => {
    if (path === "/api/brief/latest") return Promise.resolve(brief);
    if (path === "/api/brief/generate") return Promise.resolve(brief);
    if (path.includes("/shelf")) return Promise.resolve({ ok: true });
    if (path.includes("/one-on-ones") && !path.includes("/agenda"))
      return Promise.resolve({ one_on_ones: [{ id: "session-1", state: "open" }] });
    if (path.includes("/agenda"))
      return Promise.resolve({ agenda_item: { id: "ai-1" } });
    return Promise.resolve({});
  });
}

function renderBriefView() {
  return render(
    <BriefView
      header={<div>Header</div>}
      onOpenFollowThrough={vi.fn()}
    />,
  );
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("BriefView person sections", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders person section with display name and signals", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByTestId("person-sections")).toBeInTheDocument();
    });
    expect(screen.getByText("Ewa")).toBeInTheDocument();
  });

  it("renders four signals for a person row", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Ewa")).toBeInTheDocument();
    });

    // Click to expand the person row.
    fireEvent.click(screen.getByText("Ewa"));

    await waitFor(() => {
      expect(screen.getByText(/They owe 2/)).toBeInTheDocument();
    });
    expect(screen.getByText(/You owe 1/)).toBeInTheDocument();
    expect(screen.getByText(/3 agenda/)).toBeInTheDocument();
    expect(screen.getByText(/Next: Weekly 1:1/)).toBeInTheDocument();
  });

  it("shows person verbs (Add to 1:1 agenda, Open person) when person selected", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Ewa")).toBeInTheDocument();
    });

    // Select the person.
    fireEvent.click(screen.getByText("Ewa"));

    await waitFor(() => {
      expect(screen.getByTestId("verb-add-agenda")).toBeInTheDocument();
    });
    expect(screen.getByTestId("verb-open-person")).toBeInTheDocument();
    expect(screen.getByText("Add to 1:1 agenda")).toBeInTheDocument();
    expect(screen.getByText("Open person")).toBeInTheDocument();
  });

  it("'Add to 1:1 agenda' calls the existing people agenda endpoint", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Ewa")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Ewa"));

    await waitFor(() => {
      expect(screen.getByTestId("verb-add-agenda")).toBeInTheDocument();
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("verb-add-agenda"));
    });

    // Verify it called the sessions endpoint first, then the agenda endpoint.
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/people/relationships/rel-ewa/one-on-ones",
    );
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/people/one-on-ones/session-1/agenda",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("'Open person' calls openSurfaceOr with people focus", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Ewa")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Ewa"));

    await waitFor(() => {
      expect(screen.getByTestId("verb-open-person")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("verb-open-person"));

    expect(openSurfaceOr).toHaveBeenCalledWith("people", "/people", "rel-ewa");
  });

  it("receipt items still show Acknowledge/Defer/Speak verbs", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Meeting recorded: Standup")).toBeInTheDocument();
    });

    // Select the receipt item.
    fireEvent.click(screen.getByText("Meeting recorded: Standup"));

    await waitFor(() => {
      expect(screen.getByText("Acknowledge")).toBeInTheDocument();
    });
    expect(screen.getByText("Defer")).toBeInTheDocument();
    expect(screen.getByText("Speak")).toBeInTheDocument();
  });

  it("renders L2 unavailable line when sidecar is closed", async () => {
    mockBrief(briefWithUnavailablePeople);
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByTestId("person-sections-unavailable")).toBeInTheDocument();
    });
    expect(screen.getByText("People sidecar unavailable")).toBeInTheDocument();
  });
});
