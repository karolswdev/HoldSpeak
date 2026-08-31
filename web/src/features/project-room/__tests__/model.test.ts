// HS-158-05 — model decode tests: good/bad payloads for the pure
// composition seams and field decoders.  Does NOT duplicate the
// projectMemoryCore.test.tsx tests (those test the rendered UI).

import { describe, expect, it } from "vitest";
import {
  composeProjectTimeline,
  decodeDecision,
  decodeMeeting,
  decodeProject,
  lifecycleLabel,
} from "../model";

describe("composeProjectTimeline", () => {
  it("interleaves meetings, decisions, and only promoted artifacts newest-down", () => {
    const rows = composeProjectTimeline(
      [{ id: "m1", title: "Review", started_at: "2026-07-28T10:00:00Z" }],
      [{ id: "d1", text: "Accept", decided_at: "2026-07-29T10:00:00Z" }],
      [
        { id: "a1", title: "Promoted", status: "promoted", created_at: "2026-07-27T10:00:00Z" },
        { id: "a2", title: "Ordinary", status: "complete", created_at: "2026-07-30T10:00:00Z" },
      ],
    );
    expect(rows.map((r) => `${r.kind}:${r.id}`)).toEqual([
      "decision:d1",
      "meeting:m1",
      "artifact:a1",
    ]);
  });

  it("returns an empty array when all inputs are empty", () => {
    expect(composeProjectTimeline([], [], [])).toEqual([]);
  });

  it("recognises promotion_state and promoted_at as promotion signals", () => {
    const rows = composeProjectTimeline([], [], [
      { id: "a1", promotion_state: "promoted" },
      { id: "a2", promoted_at: "2026-08-01T00:00:00Z" },
      { id: "a3", status: "draft" },
    ]);
    expect(rows.map((r) => r.id)).toEqual(["a2", "a1"]);
  });

  it("falls back to created_at when the primary date is missing", () => {
    const rows = composeProjectTimeline(
      [{ id: "m1", created_at: "2026-07-01T00:00:00Z" }],
      [{ id: "d1", created_at: "2026-07-02T00:00:00Z" }],
      [],
    );
    expect(rows[0].id).toBe("d1");
    expect(rows[0].occurredAt).toBe("2026-07-02T00:00:00Z");
    expect(rows[1].occurredAt).toBe("2026-07-01T00:00:00Z");
  });

  it("uses fallback titles for missing fields", () => {
    const rows = composeProjectTimeline(
      [{ id: "m1" }],
      [{ id: "d1" }],
      [{ id: "a1", status: "promoted" }],
    );
    expect(rows.find((r) => r.kind === "meeting")?.title).toBe("Meeting");
    expect(rows.find((r) => r.kind === "decision")?.title).toBe("Decision");
    expect(rows.find((r) => r.kind === "artifact")?.title).toBe("Artifact");
  });

  it("uses artifact_type as title fallback when title is missing", () => {
    const rows = composeProjectTimeline([], [], [
      { id: "a1", status: "promoted", artifact_type: "ADR" },
    ]);
    expect(rows[0].title).toBe("ADR");
  });

  it("preserves the original row reference", () => {
    const meeting = { id: "m1", title: "Original", extra: 42, started_at: "2026-01-01" };
    const rows = composeProjectTimeline([meeting], [], []);
    expect(rows[0].row).toBe(meeting);
  });
});

describe("lifecycleLabel", () => {
  it("capitalises the lifecycle value", () => {
    expect(lifecycleLabel({ lifecycle: "recorded" })).toBe("Recorded");
    expect(lifecycleLabel({ lifecycle: "accepted" })).toBe("Accepted");
    expect(lifecycleLabel({ lifecycle: "rejected" })).toBe("Rejected");
  });

  it("handles superseded specifically", () => {
    expect(lifecycleLabel({ lifecycle: "superseded" })).toBe("Superseded");
  });

  it("defaults to 'Recorded' when lifecycle is missing", () => {
    expect(lifecycleLabel({})).toBe("Recorded");
  });
});

describe("decodeProject", () => {
  it("extracts id and name from a well-formed payload", () => {
    expect(decodeProject({ id: "p1", name: "My project", extra: true })).toEqual({
      id: "p1",
      name: "My project",
    });
  });

  it("returns empty strings for missing fields", () => {
    expect(decodeProject({})).toEqual({ id: "", name: "" });
  });

  it("coerces non-string values", () => {
    expect(decodeProject({ id: 42, name: null })).toEqual({ id: "42", name: "" });
  });
});

describe("decodeMeeting", () => {
  it("extracts timeline-relevant fields", () => {
    expect(decodeMeeting({ id: "m1", title: "Standup", started_at: "2026-08-01T09:00:00Z" })).toEqual({
      id: "m1",
      title: "Standup",
      startedAt: "2026-08-01T09:00:00Z",
    });
  });

  it("falls back to created_at and 'Meeting' title", () => {
    expect(decodeMeeting({ id: "m2", created_at: "2026-08-02T00:00:00Z" })).toEqual({
      id: "m2",
      title: "Meeting",
      startedAt: "2026-08-02T00:00:00Z",
    });
  });

  it("returns safe defaults for a fully empty row", () => {
    const result = decodeMeeting({});
    expect(result.id).toBe("");
    expect(result.title).toBe("Meeting");
    expect(result.startedAt).toBe("");
  });
});

describe("decodeDecision", () => {
  it("extracts display-relevant fields", () => {
    expect(decodeDecision({
      id: "d1",
      text: "Ship it",
      lifecycle: "accepted",
      decided_at: "2026-08-01T10:00:00Z",
      rationale: "Because it works",
    })).toEqual({
      id: "d1",
      text: "Ship it",
      lifecycle: "accepted",
      decidedAt: "2026-08-01T10:00:00Z",
      rationale: "Because it works",
    });
  });

  it("returns safe defaults for a fully empty row", () => {
    const result = decodeDecision({});
    expect(result.id).toBe("");
    expect(result.text).toBe("Decision");
    expect(result.lifecycle).toBe("recorded");
    expect(result.decidedAt).toBe("");
    expect(result.rationale).toBe("");
  });
});
