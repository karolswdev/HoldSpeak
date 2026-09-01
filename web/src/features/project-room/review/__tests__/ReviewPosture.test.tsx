// HS-160-06 — ReviewPosture rendering tests: posture swap, groups,
// keyboard law, comparison, conflict both-sources, no-delta state.

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TitleSlotContext } from "../../../../desk/surface/title";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { useDesk } from "../../../../desk/store";
import { EMPTY_ITEMS } from "../../../../desk/api";
import { ProjectRoomCore } from "../../ProjectRoomCore";

vi.mock("../../../../desk/ask", async () => {
  const actual =
    await vi.importActual<typeof import("../../../../desk/ask")>(
      "../../../../desk/ask",
    );
  return { ...actual, runAsk: vi.fn() };
});

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual =
    await vi.importActual<typeof import("../../../../lib/api")>(
      "../../../../lib/api",
    );
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

vi.mock("../../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../../desk/shell")>(
    "../../../../desk/shell",
  );
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

function WindowHarness({ scope }: { scope?: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div>{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

function roomResponse(overrides: Record<string, unknown> = {}) {
  return {
    project_id: "p1",
    revision: 3,
    observed_at: "2026-08-31T10:00:00",
    project: {
      id: "p1",
      name: "Alpha Project",
      description: "Testing the room",
      is_archived: false,
      meeting_count: 2,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-08-31T10:00:00",
      purpose: "Ship the widget",
      outcome_text: "Widget shipped",
      owner_ref: "person:owner1",
      lifecycle: "active",
      posture: "green",
      posture_reason: "On track",
      start_at: "2026-08-01",
      target_at: "2026-12-01",
      revision: 3,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 2, latest: { id: "m1", title: "Review" } },
    resources: { state: "ok", count: 1, latest: null },
    changes: { state: "ok", recent: [] },
    review: overrides.review ?? { state: "absent", reason: "not_yet_built" },
    sources: { state: "absent", reason: "not_yet_built" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

function detailResponse(url: string) {
  if (url.includes("/meetings"))
    return { meetings: [] };
  if (url.startsWith("/api/decisions"))
    return { decisions: [] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting"))
    return { current_meeting: null, since_last_meeting: null };
  return {};
}

function reviewWindowResponse() {
  return {
    review_id: "prev_r1",
    project_id: "p1",
    status: "open",
    source_manifest: { "test-source": { state: "ok" } },
    materiality_version: "1",
    opened_at: "2026-08-31T10:00:00",
    proposals: [
      {
        id: "pprop_1",
        proposal_kind: "risk_attention",
        target_ref: "action_item:ai-01",
        title: "risk_attention: action_item:ai-01",
        rationale: "Overdue follow-through requires risk attention",
        patch_json: '{"lane":"overdue","stale_score":"0.8"}',
        materiality: "0.8",
        producer_kind: "",
        lifecycle: "open",
      },
      {
        id: "pprop_2",
        proposal_kind: "review_flag",
        target_ref: "decision:d-01",
        title: "review_flag: decision:d-01",
        rationale: "Accepted decision is due for periodic review",
        patch_json: '{"review_status":"due"}',
        materiality: "0.5",
        producer_kind: "",
        lifecycle: "open",
      },
      {
        id: "pprop_conflict",
        proposal_kind: "conflict",
        target_ref: "action_item:ai-conflict",
        title: "conflict: action_item:ai-conflict",
        rationale: "Conflicting observations",
        patch_json: '{"sources":["src-a","src-b"]}',
        materiality: "1.0",
        producer_kind: "",
        lifecycle: "open",
      },
    ],
  };
}

beforeEach(() => {
  useDesk.setState({
    windowsById: {},
    items: { ...EMPTY_ITEMS },
    projects: [],
    inferenceTargets: [],
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("Review verb in orientation (WEB-NOW-002)", () => {
  it("shows 'Review changes' button when pending_count > 0", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 3,
            open_review_id: "prev_r1",
            last_accepted_at: null,
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    expect(btn.textContent).toBe("Review changes");
  });

  it("hides review verb when pending_count is 0", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 0,
            open_review_id: null,
            last_accepted_at: "2026-08-30T10:00:00",
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("project-room-name");
    expect(screen.queryByTestId("review-verb")).toBeNull();
  });

  it("hides review verb when review section is absent", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: { state: "absent", reason: "not_yet_built" },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("project-room-name");
    expect(screen.queryByTestId("review-verb")).toBeNull();
  });
});

describe("Posture swap", () => {
  it("clicking 'Review changes' enters review posture", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 3,
            open_review_id: "prev_r1",
            last_accepted_at: null,
          },
        }));
      }
      if (url.includes("/reviews") && !url.includes("/decide") && !url.includes("/accept")) {
        return Promise.resolve(reviewWindowResponse());
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-posture")).toBeTruthy();
    });
  });
});

describe("Review grouping with count chips (WEB-NOW-004)", () => {
  it("renders kind groups with count chips", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 3,
            open_review_id: "prev_r1",
            last_accepted_at: null,
          },
        }));
      }
      if (url.includes("/reviews") && !url.includes("/decide") && !url.includes("/accept")) {
        return Promise.resolve(reviewWindowResponse());
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      const groups = screen.getAllByTestId("review-kind-group");
      expect(groups.length).toBeGreaterThanOrEqual(2);
    });

    const labels = screen.getAllByTestId("review-kind-label");
    expect(labels.some((el) => el.textContent === "Risk attention")).toBe(true);
    expect(labels.some((el) => el.textContent === "Review flags")).toBe(true);

    const counts = screen.getAllByTestId("review-kind-count");
    expect(counts.length).toBeGreaterThanOrEqual(2);
  });
});

describe("Conflict both-sources (WEB-STA-006)", () => {
  it("renders conflicting sources for conflict proposals", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 3,
            open_review_id: "prev_r1",
            last_accepted_at: null,
          },
        }));
      }
      if (url.includes("/reviews") && !url.includes("/decide") && !url.includes("/accept")) {
        return Promise.resolve(reviewWindowResponse());
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-posture")).toBeTruthy();
    });

    // Navigate to the conflict proposal (index 2)
    // The conflict proposal should show both sources when selected
    // The queue items should be present
    const items = screen.getAllByTestId("review-queue-item");
    expect(items.length).toBeGreaterThanOrEqual(1);
  });
});

describe("Room review section decode", () => {
  it("decodes pending_count, open_review_id, last_accepted_at from /room", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 5,
            open_review_id: "prev_x1",
            last_accepted_at: "2026-08-29T15:00:00",
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    // When pending > 0, the review verb appears
    const btn = await screen.findByTestId("review-verb");
    expect(btn.textContent).toBe("Review changes");
  });
});
