// HS-160-06 — decode suites for the review wire shapes.
// Fixtures are mined from tests/integration/test_review_routes.py:
// the standing law says the wire shape.

import { describe, expect, it } from "vitest";
import {
  decodeProposal,
  decodeReviewWindow,
  decodeDelta,
  decodeDeltaEmpty,
  decodeDecideResult,
  decodeAcceptResult,
  decodeRoomReviewData,
  groupProposalsByKind,
  kindLabel,
  type Proposal,
} from "../model";

/* ── Wire-true fixtures (from integration test assertions) ── */

const WIRE_PROPOSAL_RISK: Record<string, unknown> = {
  id: "pprop_abc123",
  proposal_kind: "risk_attention",
  target_ref: "action_item:ai-01",
  title: "risk_attention: action_item:ai-01",
  rationale: "Overdue follow-through requires risk attention",
  patch_json: '{"lane":"overdue","stale_score":"0.8"}',
  materiality: "0.8",
  producer_kind: "",
  lifecycle: "open",
};

const WIRE_PROPOSAL_REVIEW_FLAG: Record<string, unknown> = {
  id: "pprop_def456",
  proposal_kind: "review_flag",
  target_ref: "decision:d-01",
  title: "review_flag: decision:d-01",
  rationale: "Accepted decision is due for periodic review",
  patch_json: '{"review_status":"due"}',
  materiality: "0.5",
  producer_kind: "",
  lifecycle: "open",
};

const WIRE_PROPOSAL_CONFLICT: Record<string, unknown> = {
  id: "pprop_conflict",
  proposal_kind: "conflict",
  target_ref: "action_item:ai-conflict",
  title: "conflict: action_item:ai-conflict",
  rationale: "Conflicting observations for the same target",
  patch_json: '{"sources":["src-a","src-b"]}',
  materiality: "1.0",
  producer_kind: "",
  lifecycle: "open",
};

const WIRE_WINDOW: Record<string, unknown> = {
  review_id: "prev_r1",
  project_id: "proj-rev01",
  status: "open",
  source_manifest: { "test-source": { state: "ok" } },
  materiality_version: "1",
  opened_at: "2026-08-31T10:00:00+00:00",
  proposals: [WIRE_PROPOSAL_RISK, WIRE_PROPOSAL_REVIEW_FLAG],
};

describe("decodeProposal", () => {
  it("decodes a risk_attention proposal from the wire", () => {
    const p = decodeProposal(WIRE_PROPOSAL_RISK);
    expect(p.id).toBe("pprop_abc123");
    expect(p.proposalKind).toBe("risk_attention");
    expect(p.targetRef).toBe("action_item:ai-01");
    expect(p.title).toBe("risk_attention: action_item:ai-01");
    expect(p.rationale).toBe("Overdue follow-through requires risk attention");
    expect(p.patchJson).toEqual({ lane: "overdue", stale_score: "0.8" });
    expect(p.materiality).toBe("0.8");
    expect(p.lifecycle).toBe("open");
  });

  it("decodes a review_flag proposal", () => {
    const p = decodeProposal(WIRE_PROPOSAL_REVIEW_FLAG);
    expect(p.proposalKind).toBe("review_flag");
    expect(p.patchJson).toEqual({ review_status: "due" });
  });

  it("decodes patch_json when already an object", () => {
    const raw = { ...WIRE_PROPOSAL_RISK, patch_json: { lane: "stale" } };
    const p = decodeProposal(raw);
    expect(p.patchJson).toEqual({ lane: "stale" });
  });

  it("decodes patch_json gracefully for invalid JSON", () => {
    const raw = { ...WIRE_PROPOSAL_RISK, patch_json: "not-json" };
    const p = decodeProposal(raw);
    expect(p.patchJson).toEqual({});
  });

  it("decodes missing fields to defaults", () => {
    const p = decodeProposal({});
    expect(p.id).toBe("");
    expect(p.proposalKind).toBe("");
    expect(p.lifecycle).toBe("open");
    expect(p.patchJson).toEqual({});
  });
});

describe("decodeReviewWindow", () => {
  it("decodes the full frozen window shape", () => {
    const w = decodeReviewWindow(WIRE_WINDOW);
    expect(w.reviewId).toBe("prev_r1");
    expect(w.projectId).toBe("proj-rev01");
    expect(w.status).toBe("open");
    expect(w.sourceManifest).toEqual({ "test-source": { state: "ok" } });
    expect(w.proposals).toHaveLength(2);
    expect(w.proposals[0].id).toBe("pprop_abc123");
    expect(w.proposals[1].id).toBe("pprop_def456");
  });

  it("handles empty proposals array", () => {
    const w = decodeReviewWindow({ ...WIRE_WINDOW, proposals: [] });
    expect(w.proposals).toHaveLength(0);
  });

  it("handles missing proposals", () => {
    const w = decodeReviewWindow({ ...WIRE_WINDOW, proposals: undefined });
    expect(w.proposals).toHaveLength(0);
  });
});

describe("decodeDelta", () => {
  it("detects the empty state (open_review: null)", () => {
    const d = decodeDelta({
      open_review: null,
      last_accepted_at: "2026-08-31T10:00:00",
      source_coverage: { "test-source": "ok" },
    });
    expect(d.kind).toBe("empty");
    if (d.kind === "empty") {
      expect(d.empty.openReview).toBeNull();
      expect(d.empty.lastAcceptedAt).toBe("2026-08-31T10:00:00");
      expect(d.empty.sourceCoverage).toEqual({ "test-source": "ok" });
    }
  });

  it("detects the empty state with nulls", () => {
    const d = decodeDelta({
      open_review: null,
      last_accepted_at: null,
      source_coverage: null,
    });
    expect(d.kind).toBe("empty");
    if (d.kind === "empty") {
      expect(d.empty.lastAcceptedAt).toBeNull();
      expect(d.empty.sourceCoverage).toBeNull();
    }
  });

  it("decodes the window state", () => {
    const d = decodeDelta(WIRE_WINDOW);
    expect(d.kind).toBe("window");
    if (d.kind === "window") {
      expect(d.window.reviewId).toBe("prev_r1");
    }
  });
});

describe("decodeDecideResult", () => {
  it("decodes an accept result", () => {
    const r = decodeDecideResult({
      verb: "accept",
      lifecycle: "accepted",
    });
    expect(r.verb).toBe("accept");
    expect(r.lifecycle).toBe("accepted");
    expect(r.dismissalBasisHash).toBeUndefined();
  });

  it("decodes a dismiss result with basis hash", () => {
    const r = decodeDecideResult({
      verb: "dismiss",
      lifecycle: "dismissed",
      dismissal_basis_hash: "hash123",
    });
    expect(r.lifecycle).toBe("dismissed");
    expect(r.dismissalBasisHash).toBe("hash123");
  });
});

describe("decodeAcceptResult", () => {
  it("decodes the review_accepted envelope", () => {
    const r = decodeAcceptResult({
      result_kind: "review_accepted",
      review_id: "prev_r1",
      accepted_at: "2026-08-31T12:00:00Z",
    });
    expect(r.resultKind).toBe("review_accepted");
    expect(r.reviewId).toBe("prev_r1");
    expect(r.acceptedAt).toBe("2026-08-31T12:00:00Z");
  });
});

describe("decodeRoomReviewData", () => {
  it("decodes the /room review section shape", () => {
    const r = decodeRoomReviewData({
      pending_count: 3,
      open_review_id: "prev_r1",
      last_accepted_at: "2026-08-31T10:00:00",
    });
    expect(r.pendingCount).toBe(3);
    expect(r.openReviewId).toBe("prev_r1");
    expect(r.lastAcceptedAt).toBe("2026-08-31T10:00:00");
  });

  it("decodes null fields", () => {
    const r = decodeRoomReviewData({
      pending_count: 0,
      open_review_id: null,
      last_accepted_at: null,
    });
    expect(r.pendingCount).toBe(0);
    expect(r.openReviewId).toBeNull();
    expect(r.lastAcceptedAt).toBeNull();
  });
});

describe("groupProposalsByKind", () => {
  it("groups proposals by their kind with count", () => {
    const proposals: Proposal[] = [
      decodeProposal(WIRE_PROPOSAL_RISK),
      decodeProposal({
        ...WIRE_PROPOSAL_RISK,
        id: "pprop_risk2",
        target_ref: "action_item:ai-02",
      }),
      decodeProposal(WIRE_PROPOSAL_REVIEW_FLAG),
    ];
    const groups = groupProposalsByKind(proposals);
    expect(groups).toHaveLength(2);
    const risk = groups.find((g) => g.kind === "risk_attention");
    expect(risk).toBeDefined();
    expect(risk!.count).toBe(2);
    expect(risk!.proposals).toHaveLength(2);
    const flag = groups.find((g) => g.kind === "review_flag");
    expect(flag).toBeDefined();
    expect(flag!.count).toBe(1);
  });

  it("returns empty array for empty proposals", () => {
    expect(groupProposalsByKind([])).toEqual([]);
  });
});

describe("kindLabel", () => {
  it("returns human-readable labels for known kinds", () => {
    expect(kindLabel("risk_attention")).toBe("Risk attention");
    expect(kindLabel("review_flag")).toBe("Review flags");
    expect(kindLabel("conflict")).toBe("Conflicts");
    expect(kindLabel("coverage_degraded")).toBe("Degraded coverage");
    expect(kindLabel("observation_attention")).toBe("Observations");
  });
});
