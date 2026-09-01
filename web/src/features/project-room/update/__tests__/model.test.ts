// HS-162-05 -- Update model unit tests: decode, provenance, lifecycle.
// Fixture shapes mined from tests/integration/test_update_routes.py.

import { describe, expect, it } from "vitest";
import {
  decodeClaim,
  decodeUpdate,
  generatorLabel,
  lifecycleLabel,
  lifecycleTone,
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
