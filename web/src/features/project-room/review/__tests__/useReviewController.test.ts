// HS-160-06 — controller tests: queue, disposition, undo, exhausted, posture swap.

import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useReviewController } from "../useReviewController";
import type { RoomReviewData } from "../model";

// Mock the API module
vi.mock("../api", () => ({
  fetchDelta: vi.fn(),
  openReview: vi.fn(),
  decideProposal: vi.fn(),
  acceptReview: vi.fn(),
}));

import * as reviewApi from "../api";

const MOCK_WINDOW = {
  reviewId: "prev_r1",
  projectId: "proj-1",
  status: "open",
  sourceManifest: { "test-source": { state: "ok" } },
  materialityVersion: "1",
  openedAt: "2026-08-31T10:00:00",
  proposals: [
    {
      id: "pprop_1",
      proposalKind: "risk_attention" as const,
      targetRef: "action_item:ai-01",
      title: "risk_attention: action_item:ai-01",
      rationale: "Overdue follow-through",
      patchJson: { lane: "overdue" },
      materiality: "0.8",
      producerKind: "",
      lifecycle: "open" as const,
    },
    {
      id: "pprop_2",
      proposalKind: "risk_attention" as const,
      targetRef: "action_item:ai-02",
      title: "risk_attention: action_item:ai-02",
      rationale: "Stale follow-through",
      patchJson: { lane: "stale" },
      materiality: "0.5",
      producerKind: "",
      lifecycle: "open" as const,
    },
    {
      id: "pprop_3",
      proposalKind: "review_flag" as const,
      targetRef: "decision:d-01",
      title: "review_flag: decision:d-01",
      rationale: "Decision due for review",
      patchJson: { review_status: "due" },
      materiality: "0.3",
      producerKind: "",
      lifecycle: "open" as const,
    },
  ],
};

const REVIEW_SECTION_WITH_PENDING: RoomReviewData = {
  pendingCount: 3,
  openReviewId: "prev_r1",
  lastAcceptedAt: null,
};

const REVIEW_SECTION_IDLE: RoomReviewData = {
  pendingCount: 0,
  openReviewId: null,
  lastAcceptedAt: "2026-08-30T10:00:00",
};

const onRefresh = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(reviewApi.openReview).mockResolvedValue(MOCK_WINDOW);
  vi.mocked(reviewApi.decideProposal).mockResolvedValue({
    verb: "accept",
    lifecycle: "accepted",
  });
  vi.mocked(reviewApi.acceptReview).mockResolvedValue({
    resultKind: "review_accepted",
    reviewId: "prev_r1",
    acceptedAt: "2026-08-31T12:00:00Z",
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("useReviewController — primary verb (WEB-NOW-002)", () => {
  it("shows 'Review changes' when pending_count > 0", () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    expect(result.current.primaryVerb).toBe("Review changes");
    expect(result.current.hasPending).toBe(true);
  });

  it("shows null when pending_count is 0", () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_IDLE, onRefresh),
    );
    expect(result.current.primaryVerb).toBeNull();
    expect(result.current.hasPending).toBe(false);
  });

  it("shows null when review section is absent", () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", null, onRefresh),
    );
    expect(result.current.primaryVerb).toBeNull();
  });
});

describe("useReviewController — enter/exit (posture swap)", () => {
  it("starts in off posture", () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    expect(result.current.posture).toBe("off");
  });

  it("opens a review and enters active posture", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    expect(result.current.posture).toBe("active");
    expect(result.current.window).toBeTruthy();
    expect(result.current.window!.reviewId).toBe("prev_r1");
    expect(result.current.openProposals).toHaveLength(3);
    expect(reviewApi.openReview).toHaveBeenCalledWith("proj-1");
  });

  it("exits review posture and refreshes room", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    act(() => {
      result.current.exitReview();
    });
    expect(result.current.posture).toBe("off");
    expect(result.current.window).toBeNull();
    expect(onRefresh).toHaveBeenCalled();
  });
});

describe("useReviewController — queue navigation", () => {
  it("starts at index 0", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    expect(result.current.selectedIndex).toBe(0);
    expect(result.current.selectedProposal!.id).toBe("pprop_1");
  });

  it("navigates forward with selectNext", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    act(() => result.current.selectNext());
    expect(result.current.selectedIndex).toBe(1);
    expect(result.current.selectedProposal!.id).toBe("pprop_2");
  });

  it("navigates backward with selectPrev", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    act(() => result.current.selectNext());
    act(() => result.current.selectPrev());
    expect(result.current.selectedIndex).toBe(0);
  });

  it("clamps at boundaries", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    act(() => result.current.selectPrev());
    expect(result.current.selectedIndex).toBe(0);
    act(() => result.current.selectNext());
    act(() => result.current.selectNext());
    act(() => result.current.selectNext());
    act(() => result.current.selectNext());
    expect(result.current.selectedIndex).toBe(2);
  });
});

describe("useReviewController — dispositions", () => {
  it("accept removes proposal from open queue", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    await act(async () => {
      await result.current.acceptProposal("pprop_1");
    });
    expect(result.current.dispositions.has("pprop_1")).toBe(true);
    expect(result.current.dispositions.get("pprop_1")!.verb).toBe("accept");
    expect(result.current.openProposals.some((p) => p.id === "pprop_1")).toBe(false);
    expect(reviewApi.decideProposal).toHaveBeenCalledWith(
      "proj-1", "prev_r1", "pprop_1",
      { verb: "accept", patch: undefined, deferred_until: undefined },
    );
  });

  it("dismiss adds to undo stack", async () => {
    vi.mocked(reviewApi.decideProposal).mockResolvedValue({
      verb: "dismiss",
      lifecycle: "dismissed",
      dismissalBasisHash: "hash123",
    });
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    await act(async () => {
      await result.current.dismissProposal("pprop_1");
    });
    expect(result.current.undoStack).toHaveLength(1);
    expect(result.current.undoStack[0].proposalId).toBe("pprop_1");
    expect(result.current.undoStack[0].verb).toBe("dismiss");
  });

  it("defer records the deferred_until", async () => {
    vi.mocked(reviewApi.decideProposal).mockResolvedValue({
      verb: "defer",
      lifecycle: "deferred",
    });
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    await act(async () => {
      await result.current.deferProposal("pprop_1", "2099-12-31");
    });
    expect(result.current.dispositions.get("pprop_1")!.verb).toBe("defer");
    expect(result.current.dispositions.get("pprop_1")!.deferredUntil).toBe("2099-12-31");
  });
});

describe("useReviewController — undo dismiss", () => {
  it("undoes last dismiss and restores proposal to queue", async () => {
    vi.mocked(reviewApi.decideProposal).mockResolvedValue({
      verb: "dismiss",
      lifecycle: "dismissed",
    });
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    await act(async () => {
      await result.current.dismissProposal("pprop_1");
    });
    expect(result.current.undoStack).toHaveLength(1);
    expect(result.current.dispositions.has("pprop_1")).toBe(true);

    act(() => {
      result.current.undoLastDismiss();
    });
    expect(result.current.undoStack).toHaveLength(0);
    expect(result.current.dispositions.has("pprop_1")).toBe(false);
    expect(result.current.exhausted).toBe(false);
  });
});

describe("useReviewController — exhausted and finish", () => {
  it("marks exhausted when all proposals are decided", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    await act(async () => {
      await result.current.acceptProposal("pprop_1");
    });
    await act(async () => {
      await result.current.acceptProposal("pprop_2");
    });
    await act(async () => {
      await result.current.acceptProposal("pprop_3");
    });
    expect(result.current.exhausted).toBe(true);
    expect(result.current.allDecided).toBe(true);
  });

  it("finishReview calls acceptReview and sets checkpointed", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    // Decide all
    await act(async () => {
      await result.current.acceptProposal("pprop_1");
    });
    await act(async () => {
      await result.current.acceptProposal("pprop_2");
    });
    await act(async () => {
      await result.current.acceptProposal("pprop_3");
    });
    await act(async () => {
      await result.current.finishReview();
    });
    expect(result.current.checkpointed).toBe(true);
    expect(result.current.acceptedAt).toBe("2026-08-31T12:00:00Z");
    expect(reviewApi.acceptReview).toHaveBeenCalledWith("proj-1", "prev_r1");
    expect(onRefresh).toHaveBeenCalled();
  });

  it("dispositionSummary counts correctly", async () => {
    vi.mocked(reviewApi.decideProposal)
      .mockResolvedValueOnce({ verb: "accept", lifecycle: "accepted" })
      .mockResolvedValueOnce({ verb: "dismiss", lifecycle: "dismissed" })
      .mockResolvedValueOnce({ verb: "defer", lifecycle: "deferred" });
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    await act(async () => {
      await result.current.acceptProposal("pprop_1");
    });
    await act(async () => {
      await result.current.dismissProposal("pprop_2");
    });
    await act(async () => {
      await result.current.deferProposal("pprop_3");
    });
    const summary = result.current.dispositionSummary();
    expect(summary.accept).toBe(1);
    expect(summary.dismiss).toBe(1);
    expect(summary.defer).toBe(1);
  });
});

describe("useReviewController — editing", () => {
  it("startEdit populates editingPatch from selected proposal", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    act(() => result.current.startEdit());
    expect(result.current.editingPatch).toEqual({ lane: "overdue" });
  });

  it("updateEditField changes a field", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    act(() => result.current.startEdit());
    act(() => result.current.updateEditField("lane", "critical"));
    expect(result.current.editingPatch!.lane).toBe("critical");
  });

  it("cancelEdit clears the editing state", async () => {
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    act(() => result.current.startEdit());
    act(() => result.current.cancelEdit());
    expect(result.current.editingPatch).toBeNull();
  });

  it("editAcceptProposal sends the edited patch", async () => {
    vi.mocked(reviewApi.decideProposal).mockResolvedValue({
      verb: "edit_accept",
      lifecycle: "accepted",
    });
    const { result } = renderHook(() =>
      useReviewController("proj-1", REVIEW_SECTION_WITH_PENDING, onRefresh),
    );
    await act(async () => {
      await result.current.enterReview();
    });
    await act(async () => {
      await result.current.editAcceptProposal("pprop_1", { lane: "critical" });
    });
    expect(reviewApi.decideProposal).toHaveBeenCalledWith(
      "proj-1", "prev_r1", "pprop_1",
      { verb: "edit_accept", patch: { lane: "critical" }, deferred_until: undefined },
    );
  });
});

describe("useReviewController — five-proposals-no-pointer (WEB-SCN-003)", () => {
  it("can decide five proposals using only the controller API (no mouse)", async () => {
    const fiveProposals = Array.from({ length: 5 }, (_, i) => ({
      id: `pprop_${i + 1}`,
      proposalKind: "risk_attention" as const,
      targetRef: `action_item:ai-${i + 1}`,
      title: `risk_attention: action_item:ai-${i + 1}`,
      rationale: `Follow-through ${i + 1}`,
      patchJson: { lane: "overdue" },
      materiality: String(1 - i * 0.1),
      producerKind: "",
      lifecycle: "open" as const,
    }));
    vi.mocked(reviewApi.openReview).mockResolvedValue({
      ...MOCK_WINDOW,
      proposals: fiveProposals,
    });

    const { result } = renderHook(() =>
      useReviewController("proj-1", { ...REVIEW_SECTION_WITH_PENDING, pendingCount: 5 }, onRefresh),
    );

    // Enter
    await act(async () => {
      await result.current.enterReview();
    });
    expect(result.current.openProposals).toHaveLength(5);

    // Accept first (keyboard A)
    await act(async () => {
      await result.current.acceptProposal("pprop_1");
    });
    expect(result.current.openProposals).toHaveLength(4);

    // Navigate to next (keyboard J) then dismiss (keyboard X)
    await act(async () => {
      await result.current.dismissProposal("pprop_2");
    });
    expect(result.current.openProposals).toHaveLength(3);
    expect(result.current.undoStack).toHaveLength(1);

    // Defer third (keyboard L)
    await act(async () => {
      await result.current.deferProposal("pprop_3", "2099-12-31");
    });
    expect(result.current.openProposals).toHaveLength(2);

    // Accept fourth
    await act(async () => {
      await result.current.acceptProposal("pprop_4");
    });

    // Accept fifth
    await act(async () => {
      await result.current.acceptProposal("pprop_5");
    });
    expect(result.current.openProposals).toHaveLength(0);
    expect(result.current.exhausted).toBe(true);
    expect(result.current.allDecided).toBe(true);

    // Finish (keyboard Cmd+Enter)
    await act(async () => {
      await result.current.finishReview();
    });
    expect(result.current.checkpointed).toBe(true);

    // Verify disposition summary
    const summary = result.current.dispositionSummary();
    expect(summary.accept).toBe(3);
    expect(summary.dismiss).toBe(1);
    expect(summary.defer).toBe(1);
  });
});
