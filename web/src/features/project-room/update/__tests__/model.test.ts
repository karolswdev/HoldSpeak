// HS-162-05 -- Update model unit tests: decode, provenance, lifecycle.
// Fixture shapes mined from tests/integration/test_update_routes.py.

import { describe, expect, it } from "vitest";
import {
  claimChipTitle,
  decodeClaim,
  decodeUpdate,
  generatorLabel,
  humanFallbackReason,
  lifecycleLabel,
  lifecycleTone,
  provenancePhrase,
  refChipLabel,
  refKind,
  sectionLabel,
} from "../model";

describe("decodeClaim", () => {
  it("decodes a verified claim", () => {
    const raw = {
      span_id: "s_progress_1",
      text: "Widget on track",
      refs: ["action_item:ai-01"],
      section: "progress",
    };
    const claim = decodeClaim(raw);
    expect(claim.spanId).toBe("s_progress_1");
    expect(claim.text).toBe("Widget on track");
    expect(claim.refs).toEqual(["action_item:ai-01"]);
    expect(claim.section).toBe("progress");
    expect(claim.verified).toBe(true);
  });

  it("decodes an unverified claim (verified: false)", () => {
    const raw = {
      span_id: "s_risks_1",
      text: "Unverified risk",
      refs: [],
      section: "risks_blockers",
      verified: false,
    };
    const claim = decodeClaim(raw);
    expect(claim.verified).toBe(false);
    expect(claim.refs).toEqual([]);
  });

  it("defaults verified to true when omitted", () => {
    const claim = decodeClaim({ span_id: "x", text: "t", refs: [], section: "s" });
    expect(claim.verified).toBe(true);
  });
});

describe("decodeUpdate", () => {
  it("decodes a draft update from the wire", () => {
    const raw = {
      id: "pupd-01",
      project_id: "p1",
      project_revision: 5,
      review_id: null,
      lifecycle: "draft",
      draft_revision: 1,
      body_md: "## Progress\n",
      claims_json: JSON.stringify([
        { span_id: "s1", text: "t", refs: ["action_item:ai-01"], section: "progress" },
      ]),
      source_manifest_json: "{}",
      generator: "deterministic",
      created_at: "2026-08-31T10:00:00",
      updated_at: "2026-08-31T10:00:00",
      published_at: null,
    };
    const update = decodeUpdate(raw);
    expect(update.id).toBe("pupd-01");
    expect(update.lifecycle).toBe("draft");
    expect(update.claims.length).toBe(1);
    expect(update.claims[0].refs).toEqual(["action_item:ai-01"]);
    expect(update.generator).toBe("deterministic");
    expect(update.fallbackReason).toBeNull();
    expect(update.publishedAt).toBeNull();
  });

  it("decodes a published update with published_at", () => {
    const raw = {
      id: "pupd-02",
      project_id: "p1",
      project_revision: 6,
      lifecycle: "published",
      draft_revision: 1,
      body_md: "## Progress\n",
      claims_json: "[]",
      source_manifest_json: "{}",
      generator: "deterministic",
      created_at: "2026-08-31T10:00:00",
      updated_at: "2026-08-31T12:00:00",
      published_at: "2026-08-31T12:00:00",
    };
    const update = decodeUpdate(raw);
    expect(update.lifecycle).toBe("published");
    expect(update.publishedAt).toBe("2026-08-31T12:00:00");
  });

  it("decodes fallback_reason when present", () => {
    const raw = {
      id: "pupd-03",
      project_id: "p1",
      lifecycle: "draft",
      draft_revision: 1,
      body_md: "## Progress\n",
      claims_json: "[]",
      source_manifest_json: "{}",
      generator: "deterministic",
      fallback_reason: "model_unavailable",
      created_at: "2026-08-31T10:00:00",
      updated_at: "2026-08-31T10:00:00",
    };
    const update = decodeUpdate(raw);
    expect(update.fallbackReason).toBe("model_unavailable");
  });

  it("handles claims_json as empty string", () => {
    const raw = {
      id: "pupd-04",
      project_id: "p1",
      lifecycle: "draft",
      draft_revision: 1,
      body_md: "",
      claims_json: "",
      source_manifest_json: "{}",
      generator: "deterministic",
      created_at: "2026-08-31T10:00:00",
      updated_at: "2026-08-31T10:00:00",
    };
    const update = decodeUpdate(raw);
    expect(update.claims).toEqual([]);
  });
});

describe("generatorLabel", () => {
  it("labels deterministic", () => {
    expect(generatorLabel("deterministic")).toBe("Deterministic");
  });

  it("labels model with assignment", () => {
    expect(generatorLabel("model:gpt-4o")).toBe("Model (gpt-4o)");
  });

  it("passes through unknown generators", () => {
    expect(generatorLabel("custom")).toBe("custom");
  });
});

describe("provenancePhrase", () => {
  it("labels deterministic as 'Deterministic draft'", () => {
    expect(provenancePhrase("deterministic")).toBe("Deterministic draft");
  });
  it("labels model as 'Model draft' (no assignment id)", () => {
    expect(provenancePhrase("model:gpt-4o")).toBe("Model draft");
  });
  it("labels unknown generator with draft suffix", () => {
    expect(provenancePhrase("custom")).toBe("custom draft");
  });
});

describe("lifecycleLabel", () => {
  it("labels draft", () => {
    expect(lifecycleLabel("draft")).toBe("Draft");
  });
  it("labels published", () => {
    expect(lifecycleLabel("published")).toBe("Published");
  });
  it("labels superseded", () => {
    expect(lifecycleLabel("superseded")).toBe("Superseded");
  });
});

describe("lifecycleTone", () => {
  it("returns ok for published", () => {
    expect(lifecycleTone("published")).toBe("ok");
  });
  it("returns danger for superseded", () => {
    expect(lifecycleTone("superseded")).toBe("danger");
  });
  it("returns undefined for draft", () => {
    expect(lifecycleTone("draft")).toBeUndefined();
  });
});

describe("refKind", () => {
  it("classifies action_item as item", () => {
    expect(refKind("action_item:ai-01")).toBe("item");
  });
  it("classifies decision", () => {
    expect(refKind("decision:d-01")).toBe("decision");
  });
  it("classifies meeting", () => {
    expect(refKind("meeting:m-01")).toBe("meeting");
  });
  it("classifies artifact", () => {
    expect(refKind("artifact:art-01")).toBe("artifact");
  });
  it("classifies risk as item", () => {
    expect(refKind("risk:r-01")).toBe("item");
  });
  it("classifies generic item prefix as item", () => {
    expect(refKind("item:x")).toBe("item");
  });
  it("classifies unknown prefix as unknown", () => {
    expect(refKind("blah:x")).toBe("unknown");
  });
  it("classifies bare string as unknown", () => {
    expect(refKind("nocolon")).toBe("unknown");
  });
});

describe("sectionLabel", () => {
  it("labels progress", () => {
    expect(sectionLabel("progress")).toBe("Progress");
  });
  it("labels risks_blockers", () => {
    expect(sectionLabel("risks_blockers")).toBe("Risks & blockers");
  });
  it("labels unknown sections with humanization", () => {
    expect(sectionLabel("some_new_section")).toBe("Some new section");
  });
});

describe("refChipLabel", () => {
  it("labels action_item refs as 'Open action item'", () => {
    expect(refChipLabel("action_item:ai-01")).toBe("Open action item");
  });
  it("labels decision refs as 'Open decision'", () => {
    expect(refChipLabel("decision:d-01")).toBe("Open decision");
  });
  it("labels meeting refs as 'Open meeting'", () => {
    expect(refChipLabel("meeting:m-01")).toBe("Open meeting");
  });
  it("labels artifact refs as 'Open artifact'", () => {
    expect(refChipLabel("artifact:art-01")).toBe("Open artifact");
  });
  it("labels risk refs as 'Open risk'", () => {
    expect(refChipLabel("risk:r-01")).toBe("Open risk");
  });
  it("labels milestone refs as 'Open milestone'", () => {
    expect(refChipLabel("milestone:ms-01")).toBe("Open milestone");
  });
  it("labels generic item refs as 'Open item'", () => {
    expect(refChipLabel("item:pitem_abc123")).toBe("Open item");
  });
  it("labels unknown prefix as 'Open'", () => {
    expect(refChipLabel("blah:x")).toBe("Open");
  });
  it("labels bare string as 'Open'", () => {
    expect(refChipLabel("nocolon")).toBe("Open");
  });
  it("never returns a raw hash id", () => {
    const label = refChipLabel("action_item:pitem_eea3e49373694e4ab9f86fa8efd8c53e");
    expect(label).toBe("Open action item");
    expect(label).not.toMatch(/[0-9a-f]{16,}/);
  });
});

describe("humanFallbackReason", () => {
  it("humanizes model_unavailable", () => {
    expect(humanFallbackReason("model_unavailable")).toBe(
      "Model unavailable -- drafted deterministically",
    );
  });
  it("humanizes no_output", () => {
    expect(humanFallbackReason("no_output")).toBe(
      "Model produced no output -- drafted deterministically",
    );
  });
  it("humanizes unparseable_output", () => {
    expect(humanFallbackReason("unparseable_output")).toBe(
      "Model output unusable -- drafted deterministically",
    );
  });
  it("handles unknown codes with generic phrasing", () => {
    const result = humanFallbackReason("some_new_code");
    expect(result).toBe("Fallback: some new code -- drafted deterministically");
  });
  it("returns null for null input", () => {
    expect(humanFallbackReason(null)).toBeNull();
  });
});

describe("claimChipTitle", () => {
  it("returns the claim text as-is when short enough", () => {
    expect(claimChipTitle("Widget development on track")).toBe("Widget development on track");
  });
  it("truncates long text at a word boundary with ellipsis", () => {
    expect(claimChipTitle("Three milestones completed this sprint")).toBe(
      "Three milestones completed this…",
    );
  });
  it("strips a Kind: prefix", () => {
    expect(claimChipTitle("Dependency: Infrastructure load")).toBe("Infrastructure load");
  });
  it("strips a Kind [severity]: prefix", () => {
    expect(claimChipTitle("Risk [critical]: PCI deadline")).toBe("PCI deadline");
  });
  it("strips Action item [high]: prefix", () => {
    expect(claimChipTitle("Action item [high]: Review docs")).toBe("Review docs");
  });
  it("returns null for empty string", () => {
    expect(claimChipTitle("")).toBeNull();
  });
  it("returns null for undefined", () => {
    expect(claimChipTitle(undefined)).toBeNull();
  });
  it("returns null for whitespace-only", () => {
    expect(claimChipTitle("   ")).toBeNull();
  });
  it("handles text that is exactly the prefix", () => {
    // If stripping leaves nothing, return null
    expect(claimChipTitle("Risk:")).toBeNull();
  });
});
