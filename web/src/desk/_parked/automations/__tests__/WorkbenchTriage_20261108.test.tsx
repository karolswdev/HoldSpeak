// HS-118-09 — Artifact triage: triage strip renders for pending-review
// items, batch triage banner shows with 2+ pending-review items, correct
// chips show for each triage state.
import { describe, expect, it, vi } from "vitest";
import type { WorkbenchItem } from "../detail-types";

// Test the triage derivation logic that determines what UI to show.
// This mirrors the logic in WorkbenchItemCard.

function deriveTriageState(item: WorkbenchItem) {
  const hasMintedArtifact = !!item.result_artifact_id;
  const isPendingReview =
    hasMintedArtifact && item.artifact_status === "pending-review";
  const wasAccepted =
    hasMintedArtifact && item.artifact_status === "draft";
  const wasRejected =
    item.status === "dismissed" &&
    !hasMintedArtifact &&
    item.artifact_status === "rejected";
  const mintFailed =
    item.status === "done" &&
    !!item.result &&
    !hasMintedArtifact &&
    !!item.mint_attempted;

  return { isPendingReview, wasAccepted, wasRejected, mintFailed };
}

function makePendingReviewItem(overrides: Partial<WorkbenchItem> = {}): WorkbenchItem {
  return {
    id: "wbi-1",
    title: "Test item",
    body: "",
    priority: 3,
    status: "done",
    grounding: {},
    result: "Agent output",
    result_egress: null,
    result_artifact_id: "art-1",
    artifact_status: "pending-review",
    mint_attempted: true,
    tokens_consumed: 100,
    created_at: "2026-01-01T00:00:00Z",
    completed_at: "2026-01-01T00:01:00Z",
    ...overrides,
  };
}

describe("triage strip derivation", () => {
  it("shows triage strip for pending-review artifact", () => {
    const item = makePendingReviewItem();
    const state = deriveTriageState(item);
    expect(state.isPendingReview).toBe(true);
    expect(state.wasAccepted).toBe(false);
    expect(state.wasRejected).toBe(false);
  });

  it("shows accepted chip after accept", () => {
    const item = makePendingReviewItem({ artifact_status: "draft" });
    const state = deriveTriageState(item);
    expect(state.isPendingReview).toBe(false);
    expect(state.wasAccepted).toBe(true);
  });

  it("shows rejected chip after reject", () => {
    const item = makePendingReviewItem({
      status: "dismissed",
      result_artifact_id: null,
      artifact_status: "rejected",
    });
    const state = deriveTriageState(item);
    expect(state.isPendingReview).toBe(false);
    expect(state.wasRejected).toBe(true);
  });

  it("item without artifact is not triageable", () => {
    const item = makePendingReviewItem({
      result_artifact_id: null,
      artifact_status: null,
    });
    const state = deriveTriageState(item);
    expect(state.isPendingReview).toBe(false);
    expect(state.wasAccepted).toBe(false);
    expect(state.wasRejected).toBe(false);
  });

  it("mint failed item is not triageable", () => {
    const item = makePendingReviewItem({
      result_artifact_id: null,
      artifact_status: null,
      mint_attempted: true,
    });
    const state = deriveTriageState(item);
    expect(state.isPendingReview).toBe(false);
    expect(state.mintFailed).toBe(true);
  });

  it("reworked item returns to pending, triageable again with new artifact", () => {
    // After rework: item is pending, no artifact
    const reworkedItem = makePendingReviewItem({
      status: "pending",
      result: null,
      result_artifact_id: null,
      artifact_status: null,
      body: "Original task\n\n[REFINEMENT]\nMake it shorter",
    });
    const state1 = deriveTriageState(reworkedItem);
    expect(state1.isPendingReview).toBe(false);

    // After re-run with new artifact: triageable again
    const retriedItem = makePendingReviewItem({
      result_artifact_id: "art-2",
      artifact_status: "pending-review",
      body: "Original task\n\n[REFINEMENT]\nMake it shorter",
    });
    const state2 = deriveTriageState(retriedItem);
    expect(state2.isPendingReview).toBe(true);
  });
});

describe("batch triage derivation", () => {
  it("counts pending-review items correctly", () => {
    const items: WorkbenchItem[] = [
      makePendingReviewItem({ id: "wbi-1" }),
      makePendingReviewItem({ id: "wbi-2" }),
      makePendingReviewItem({ id: "wbi-3", artifact_status: "draft" }), // already accepted
      makePendingReviewItem({ id: "wbi-4", result_artifact_id: null }), // no artifact
    ];
    const pendingReviewItems = items.filter(
      (i) => !!i.result_artifact_id && i.artifact_status === "pending-review",
    );
    expect(pendingReviewItems.length).toBe(2);
  });

  it("shows batch banner with 2+ pending-review items", () => {
    const items: WorkbenchItem[] = [
      makePendingReviewItem({ id: "wbi-1" }),
      makePendingReviewItem({ id: "wbi-2" }),
    ];
    const pendingReviewItems = items.filter(
      (i) => !!i.result_artifact_id && i.artifact_status === "pending-review",
    );
    expect(pendingReviewItems.length).toBeGreaterThanOrEqual(2);
  });

  it("hides batch banner with 0 or 1 pending-review items", () => {
    const items: WorkbenchItem[] = [
      makePendingReviewItem({ id: "wbi-1" }),
      makePendingReviewItem({ id: "wbi-2", artifact_status: "draft" }),
    ];
    const pendingReviewItems = items.filter(
      (i) => !!i.result_artifact_id && i.artifact_status === "pending-review",
    );
    expect(pendingReviewItems.length).toBeLessThan(2);
  });
});

describe("triage verb visibility", () => {
  it("hides Re-run/Dismiss/Remove when pending-review", () => {
    const item = makePendingReviewItem();
    const state = deriveTriageState(item);
    // When isPendingReview, Re-run/Dismiss/Remove should be hidden
    expect(state.isPendingReview).toBe(true);
    // The UI logic: !isPendingReview && (item.status === "done" || item.status === "failed")
    const showRerun = !state.isPendingReview && (item.status === "done" || item.status === "failed");
    expect(showRerun).toBe(false);
  });

  it("shows Re-run/Remove when not pending-review", () => {
    const item = makePendingReviewItem({ artifact_status: "draft" });
    const state = deriveTriageState(item);
    expect(state.isPendingReview).toBe(false);
    const showRerun = !state.isPendingReview && (item.status === "done" || item.status === "failed");
    expect(showRerun).toBe(true);
  });
});
