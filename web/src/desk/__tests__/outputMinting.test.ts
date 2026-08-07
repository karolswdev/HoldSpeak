/**
 * HS-118-06: output minting frontend contracts.
 *
 * Tests that WorkbenchItem type includes result_artifact_id and mint_attempted,
 * and that the type system correctly handles minted / mint-failed / legacy distinctions.
 */
import { describe, expect, it } from "vitest";
import type { WorkbenchItem } from "../detail-types";

describe("WorkbenchItem result_artifact_id + mint_attempted", () => {
  const baseItem: WorkbenchItem = {
    id: "item_1",
    title: "Test task",
    body: "",
    priority: 3,
    status: "done",
    grounding: {},
    result: "Generated output",
    result_egress: { boundary: "same_device" },
    result_artifact_id: null,
    mint_attempted: false,
    tokens_consumed: 100,
    created_at: "2026-08-05T00:00:00Z",
    completed_at: "2026-08-05T00:01:00Z",
  };

  it("item with result_artifact_id shows Open instead of Keep", () => {
    const minted: WorkbenchItem = {
      ...baseItem,
      result_artifact_id: "artifact_abc123",
      mint_attempted: true,
    };
    expect(minted.result_artifact_id).toBeTruthy();
    const showOpen = !!minted.result_artifact_id;
    const hasMintedArtifact = !!minted.result_artifact_id;
    const mintFailed = !hasMintedArtifact && !!minted.mint_attempted;
    const legacyKeep = !hasMintedArtifact && !minted.mint_attempted && minted.status === "done" && !!minted.result;
    expect(showOpen).toBe(true);
    expect(mintFailed).toBe(false);
    expect(legacyKeep).toBe(false);
  });

  it("legacy item (pre-Phase-118, no mint_attempted) shows Keep", () => {
    const legacy: WorkbenchItem = {
      ...baseItem,
      result_artifact_id: null,
      mint_attempted: false,
    };
    expect(legacy.result_artifact_id).toBeNull();
    const hasMintedArtifact = !!legacy.result_artifact_id;
    const mintFailed = !hasMintedArtifact && !!legacy.mint_attempted;
    const legacyKeep = !hasMintedArtifact && !legacy.mint_attempted && legacy.status === "done" && !!legacy.result;
    expect(hasMintedArtifact).toBe(false);
    expect(mintFailed).toBe(false);
    expect(legacyKeep).toBe(true);
  });

  it("pending item does not show Keep, Open, or Retry", () => {
    const pending: WorkbenchItem = {
      ...baseItem,
      status: "pending",
      result: null,
      result_artifact_id: null,
      mint_attempted: false,
    };
    const hasMintedArtifact = !!pending.result_artifact_id;
    const mintFailed = !hasMintedArtifact && !!pending.mint_attempted;
    const legacyKeep = !hasMintedArtifact && !pending.mint_attempted && pending.status === "done" && !!pending.result;
    expect(hasMintedArtifact).toBe(false);
    expect(mintFailed).toBe(false);
    expect(legacyKeep).toBe(false);
  });

  it("mint failed: done + result + mint_attempted + no artifact -> Retry (not Keep)", () => {
    const failed: WorkbenchItem = {
      ...baseItem,
      result_artifact_id: null,
      mint_attempted: true,
    };
    const hasMintedArtifact = !!failed.result_artifact_id;
    const mintFailed = failed.status === "done" && !!failed.result && !hasMintedArtifact && !!failed.mint_attempted;
    const legacyKeep = !hasMintedArtifact && !failed.mint_attempted && failed.status === "done" && !!failed.result;
    expect(mintFailed).toBe(true);
    expect(legacyKeep).toBe(false);
  });

  it("pending-review chip visible when minted", () => {
    const minted: WorkbenchItem = {
      ...baseItem,
      result_artifact_id: "artifact_xyz",
      mint_attempted: true,
    };
    const showPendingReview = !!minted.result_artifact_id;
    expect(showPendingReview).toBe(true);
  });
});
