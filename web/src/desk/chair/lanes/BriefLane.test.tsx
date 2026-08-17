// HS-135-07 -- Brief lane tests: seeded data renders headline + counts +
// items; maxItems caps; header-click opens Intelligence/Brief; per-item
// Acknowledge/Defer verbs fire the shelf API; never-false-clear (the
// Phase-132 fence mirrored at the lane level).

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BriefLane } from "./BriefLane";

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

vi.mock("../../intelligenceAttention", async () => {
  const actual = await vi.importActual<typeof import("../../intelligenceAttention")>(
    "../../intelligenceAttention",
  );
  return {
    ...actual,
    refreshIntelligenceAttention: vi.fn(),
  };
});

// ---------------------------------------------------------------------------
// fixtures -- mirrored from IntelligenceTruth.test.tsx
// ---------------------------------------------------------------------------

const briefWithItems = {
  id: "brief-1",
  headline: "3 things changed.",
  is_empty: false,
  shelf: {} as Record<string, string>,
  sections: {
    changed: [
      {
        id: "item-changed-1",
        section: "changed",
        text: "Meeting recorded: Launch review",
        detail: "45 min",
        source_ref: "meeting:meeting-1",
        priority: 50,
      },
      {
        id: "item-changed-2",
        section: "changed",
        text: "Deadline moved: Q3 report",
        detail: null,
        source_ref: null,
        priority: 40,
      },
    ],
    broke: [
      {
        id: "item-broke-1",
        section: "broke",
        text: "CI pipeline failing",
        detail: "3 runs",
        source_ref: null,
        priority: 90,
      },
    ],
    waiting: [],
    decisions: [],
  },
};

const emptyBrief = {
  id: "brief-2",
  headline: "",
  is_empty: true,
  shelf: {},
  sections: { changed: [], broke: [], waiting: [], decisions: [] },
};

function mockBrief(brief: unknown = briefWithItems) {
  apiFetch.mockImplementation((path: string) => {
    if (path === "/api/brief/latest") return Promise.resolve(brief);
    if (path.includes("/shelf")) return Promise.resolve({});
    return Promise.resolve({});
  });
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function renderLane(
  props: Partial<React.ComponentProps<typeof BriefLane>> = {},
) {
  const onOpenInWindow = vi.fn();
  const result = render(
    <BriefLane onOpenInWindow={onOpenInWindow} {...props} />,
  );
  return { ...result, onOpenInWindow };
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("BriefLane", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // -- seeded data rendering -----------------------------------------------

  describe("seeded fixture renders headline + counts + items", () => {
    it("shows the headline with the untriaged count", async () => {
      mockBrief();
      renderLane();
      await waitFor(() => {
        expect(screen.getByText("3 things waiting")).toBeInTheDocument();
      });
    });

    it("shows Changed/Broke/Waiting/Decisions counts", async () => {
      mockBrief();
      renderLane();
      await waitFor(() => {
        expect(screen.getByText("3 things waiting")).toBeInTheDocument();
      });
      expect(screen.getByText(/Changed 02/)).toBeInTheDocument();
      expect(screen.getByText(/Broke 01/)).toBeInTheDocument();
      expect(screen.getByText(/Waiting 00/)).toBeInTheDocument();
      expect(screen.getByText(/Decisions 00/)).toBeInTheDocument();
    });

    it("renders brief items with their section labels", async () => {
      mockBrief();
      renderLane();
      await waitFor(() => {
        expect(
          screen.getByText("Meeting recorded: Launch review"),
        ).toBeInTheDocument();
      });
      expect(screen.getByText("Deadline moved: Q3 report")).toBeInTheDocument();
      expect(screen.getByText("CI pipeline failing")).toBeInTheDocument();
    });

    it("shows the header badge count", async () => {
      mockBrief();
      renderLane();
      await waitFor(() => {
        expect(screen.getByLabelText("Open BRIEF")).toBeInTheDocument();
      });
      expect(screen.getByLabelText("Open BRIEF").textContent).toBe("03");
    });
  });

  // -- maxItems ------------------------------------------------------------

  it("caps visible items at maxItems", async () => {
    mockBrief();
    renderLane({ maxItems: 2 });
    await waitFor(() => {
      expect(
        screen.getByText("Meeting recorded: Launch review"),
      ).toBeInTheDocument();
    });
    // Only first 2 items visible.
    expect(
      screen.getByText("Meeting recorded: Launch review"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Deadline moved: Q3 report"),
    ).toBeInTheDocument();
    // Third item overflows.
    expect(screen.queryByText("CI pipeline failing")).not.toBeInTheDocument();
    // Footer overflow.
    expect(screen.getByText(/1 more/)).toBeInTheDocument();
  });

  // -- header-click opens Intelligence/Brief --------------------------------

  it("header click opens Intelligence on the Brief wing", async () => {
    mockBrief();
    renderLane();
    await waitFor(() => {
      expect(screen.getByLabelText("Open BRIEF")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByLabelText("Open BRIEF"));
    expect(openIntelligence).toHaveBeenCalledWith({ view: "brief" });
  });

  // -- verb persistence (mock the shelf action) ----------------------------

  describe("per-item Acknowledge/Defer verbs", () => {
    it("Acknowledge fires the shelf API with acknowledged state", async () => {
      mockBrief();
      renderLane();
      await waitFor(() => {
        expect(
          screen.getByText("Meeting recorded: Launch review"),
        ).toBeInTheDocument();
      });
      const ackBtn = screen.getByLabelText(
        "Acknowledge Meeting recorded: Launch review",
      );
      await act(async () => {
        fireEvent.click(ackBtn);
      });
      expect(apiFetch).toHaveBeenCalledWith(
        "/api/brief/items/item-changed-1/shelf",
        { method: "POST", json: { state: "acknowledged" } },
      );
    });

    it("Defer fires the shelf API with deferred state", async () => {
      mockBrief();
      renderLane();
      await waitFor(() => {
        expect(
          screen.getByText("Meeting recorded: Launch review"),
        ).toBeInTheDocument();
      });
      const deferBtn = screen.getByLabelText(
        "Defer Meeting recorded: Launch review",
      );
      await act(async () => {
        fireEvent.click(deferBtn);
      });
      expect(apiFetch).toHaveBeenCalledWith(
        "/api/brief/items/item-changed-1/shelf",
        { method: "POST", json: { state: "deferred" } },
      );
    });

    it("toggling a verb clears it (sends null state)", async () => {
      mockBrief({
        ...briefWithItems,
        shelf: { "item-changed-1": "acknowledged" },
      });
      renderLane();
      await waitFor(() => {
        expect(
          screen.getByText("Meeting recorded: Launch review"),
        ).toBeInTheDocument();
      });
      // Click Acknowledge again to toggle off.
      const ackBtn = screen.getByLabelText(
        "Acknowledge Meeting recorded: Launch review",
      );
      await act(async () => {
        fireEvent.click(ackBtn);
      });
      expect(apiFetch).toHaveBeenCalledWith(
        "/api/brief/items/item-changed-1/shelf",
        { method: "POST", json: { state: null } },
      );
    });

    it("shows shelf state in the item detail", async () => {
      mockBrief({
        ...briefWithItems,
        shelf: { "item-changed-1": "acknowledged" },
      });
      renderLane();
      await waitFor(() => {
        expect(
          screen.getByText("Meeting recorded: Launch review"),
        ).toBeInTheDocument();
      });
      expect(screen.getByText(/acknowledged/)).toBeInTheDocument();
    });
  });

  // -- empty state honest ---------------------------------------------------

  it("renders nothing when brief is null", async () => {
    mockBrief(null);
    const { container } = renderLane();
    await waitFor(() => {
      // Loading spinner disappears.
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    // No lane content rendered.
    expect(container.querySelector(".surface-section")).toBeNull();
    expect(screen.queryByText("things waiting")).not.toBeInTheDocument();
  });

  it("renders nothing when brief is empty", async () => {
    mockBrief(emptyBrief);
    const { container } = renderLane();
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    expect(container.querySelector(".surface-section")).toBeNull();
    expect(screen.queryByText("things waiting")).not.toBeInTheDocument();
  });

  // -- never-false-clear (Phase-132 fence mirrored at the lane) -----------

  describe("HS-132-08 the lane never announces a false all clear", () => {
    it("the lane renders content when items exist, never says ALL CLEAR", async () => {
      mockBrief();
      renderLane();
      await waitFor(() => {
        expect(screen.getByText("3 things waiting")).toBeInTheDocument();
      });
      // Items are visible.
      expect(
        screen.getByText("Meeting recorded: Launch review"),
      ).toBeInTheDocument();
      // Never shows ALL CLEAR.
      expect(screen.queryByText(/ALL CLEAR/i)).toBeNull();
    });

    it("a brief with items can never render as null/absent", async () => {
      mockBrief();
      const { container } = renderLane();
      await waitFor(() => {
        expect(screen.getByText("3 things waiting")).toBeInTheDocument();
      });
      // The section is rendered (not null).
      expect(container.querySelector(".surface-section")).not.toBeNull();
    });

    it("all items shelved still renders the lane (not clear), says everything triaged", async () => {
      mockBrief({
        ...briefWithItems,
        shelf: {
          "item-changed-1": "acknowledged",
          "item-changed-2": "deferred",
          "item-broke-1": "acknowledged",
        },
      });
      const { container } = renderLane();
      await waitFor(() => {
        // The brief has items even though all are triaged.
        expect(screen.getByText("Everything triaged")).toBeInTheDocument();
      });
      // The section is rendered (NOT null -- the lane never disappears
      // while the brief has items, even if all are triaged).
      expect(container.querySelector(".surface-section")).not.toBeNull();
      // Items are visible with their shelf states.
      expect(
        screen.getByText("Meeting recorded: Launch review"),
      ).toBeInTheDocument();
      // Never says ALL CLEAR.
      expect(screen.queryByText(/ALL CLEAR/i)).toBeNull();
    });
  });
});
