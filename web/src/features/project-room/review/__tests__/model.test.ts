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
  proposalAnchor,
  humanFields,
  machineAttrs,
  renderValue,
  materialityLevel,
  materialityTone,
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

/* ── Beauty-pass utilities (HS-160-06 defects 1-7) ── */

describe("proposalAnchor (defect 1: plain-words anchor)", () => {
  it("returns a plain-words headline for risk_attention", () => {
    const p = decodeProposal(WIRE_PROPOSAL_RISK);
    const anchor = proposalAnchor(p);
    expect(anchor.headline).toBe("Overdue commitment needs attention");
    expect(anchor.headline).not.toContain("risk_attention");
    expect(anchor.headline).not.toContain("action_item:");
  });

  it("extracts subject from patch text field", () => {
    const p = decodeProposal({
      ...WIRE_PROPOSAL_RISK,
      patch_json: '{"text":"Update PCI compliance docs","card_id":"ai-01","lane":"overdue"}',
    });
    const anchor = proposalAnchor(p);
    expect(anchor.subject).toBe("Update PCI compliance docs");
  });

  it("falls back to target_ref tail when no text in patch", () => {
    const p = decodeProposal({
      ...WIRE_PROPOSAL_RISK,
      patch_json: '{"lane":"overdue"}',
    });
    const anchor = proposalAnchor(p);
    expect(anchor.subject).toBe("ai-01");
  });

  it("returns review_flag headline for review_flag kind", () => {
    const p = decodeProposal(WIRE_PROPOSAL_REVIEW_FLAG);
    const anchor = proposalAnchor(p);
    expect(anchor.headline).toBe("Decision due for review");
    expect(anchor.headline).not.toContain("review_flag");
  });

  it("returns conflict headline for conflict kind", () => {
    const p = decodeProposal(WIRE_PROPOSAL_CONFLICT);
    const anchor = proposalAnchor(p);
    expect(anchor.headline).toBe("Conflicting sources detected");
  });
});

describe("humanFields (defect 4: human field labels, machine ids hidden)", () => {
  it("returns human fields in display order, skipping machine ids", () => {
    const fields = humanFields({
      card_id: "ai-01",
      text: "Update PCI docs",
      owner: "karol",
      due: "2026-08-17",
      lane: "overdue",
    });
    // Machine field card_id must be absent
    expect(fields.find((f) => f.key === "card_id")).toBeUndefined();
    // Human fields present in order
    const keys = fields.map((f) => f.key);
    expect(keys).toEqual(["text", "owner", "due", "lane"]);
    // Labels are humanized
    expect(fields[0].label).toBe("Text");
    expect(fields[1].label).toBe("Owner");
  });

  it("omits _id and _ref keys", () => {
    const fields = humanFields({
      decision_id: "dec-01",
      text: "Adopt event sourcing",
      source_ref: "m-delta-001",
    });
    expect(fields.find((f) => f.key === "decision_id")).toBeUndefined();
    expect(fields.find((f) => f.key === "source_ref")).toBeUndefined();
    expect(fields).toHaveLength(1);
    expect(fields[0].key).toBe("text");
  });
});

describe("machineAttrs (defect 4: machine ids in data-attrs)", () => {
  it("extracts machine keys as data-attrs", () => {
    const attrs = machineAttrs({
      card_id: "ai-01",
      text: "Update PCI docs",
      decision_id: "dec-01",
    });
    expect(attrs["data-card-id"]).toBe("ai-01");
    expect(attrs["data-decision-id"]).toBe("dec-01");
    // Non-machine keys not included
    expect(attrs["data-text"]).toBeUndefined();
  });
});

describe("renderValue (defect 3: nested object rendering)", () => {
  it("renders strings as-is", () => {
    expect(renderValue("hello")).toBe("hello");
  });

  it("renders numbers", () => {
    expect(renderValue(0.8)).toBe("0.8");
  });

  it("renders null/undefined as empty string", () => {
    expect(renderValue(null)).toBe("");
    expect(renderValue(undefined)).toBe("");
  });

  it("renders arrays joined with commas", () => {
    expect(renderValue(["a", "b", "c"])).toBe("a, b, c");
  });

  it("renders {code, message} objects as 'code: message'", () => {
    expect(renderValue({ code: "E001", message: "Not found" })).toBe("E001: Not found");
  });

  it("renders generic objects as compact key:value", () => {
    expect(renderValue({ lane: "overdue", score: 0.8 })).toBe("lane: overdue, score: 0.8");
  });

  it("never produces [object Object]", () => {
    const result = renderValue({ nested: { deep: true } });
    expect(result).not.toContain("[object Object]");
    expect(result).toContain("nested:");
  });
});

describe("materialityLevel + materialityTone (defect 6)", () => {
  it("classifies >= 0.7 as High with warn tone", () => {
    expect(materialityLevel("0.8")).toBe("High");
    expect(materialityLevel("0.7")).toBe("High");
    expect(materialityLevel("1.0")).toBe("High");
    expect(materialityTone("High")).toBe("warn");
  });

  it("classifies >= 0.45 as Medium with no tone", () => {
    expect(materialityLevel("0.5")).toBe("Medium");
    expect(materialityLevel("0.45")).toBe("Medium");
    expect(materialityTone("Medium")).toBeUndefined();
  });

  it("classifies < 0.45 as Low with no tone", () => {
    expect(materialityLevel("0.3")).toBe("Low");
    expect(materialityLevel("0")).toBe("Low");
    expect(materialityTone("Low")).toBeUndefined();
  });

  it("handles NaN gracefully", () => {
    expect(materialityLevel("not-a-number")).toBe("Low");
  });

  it("handles numeric input", () => {
    expect(materialityLevel(0.8)).toBe("High");
    expect(materialityLevel(0.5)).toBe("Medium");
    expect(materialityLevel(0.2)).toBe("Low");
  });
});
