// HS-158-05 — model decode tests: good/bad payloads for the pure
// composition seams and field decoders.  Does NOT duplicate the
// projectMemoryCore.test.tsx tests (those test the rendered UI).

import { describe, expect, it } from "vitest";
import {
  composeProjectTimeline,
  decodeDecision,
  decodeMeeting,
  decodeProject,
  decodeRoomSnapshot,
  lifecycleLabel,
} from "../model";
import type { RoomSnapshot } from "../model";

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

/* ── RoomSnapshot decode (HS-158-05 adoption, WEB-ARC-004) ── */

/** A well-formed /room response with all ok sections. */
function okRoomPayload(): Record<string, unknown> {
  return {
    project_id: "proj-abc",
    revision: 3,
    observed_at: "2026-08-31T10:00:00",
    project: {
      id: "proj-abc",
      name: "Alpha",
      description: "A test project",
      is_archived: false,
      meeting_count: 2,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-08-31T10:00:00",
      purpose: "Ship it",
      outcome_text: "Shipped",
      owner_ref: "person:owner1",
      lifecycle: "active",
      posture: "green",
      posture_reason: "On track",
      start_at: "2026-08-01",
      target_at: "2026-12-01",
      revision: 3,
    },
    items: {
      state: "ok",
      focus: [
        {
          id: "item-1",
          project_id: "proj-abc",
          item_type: "risk",
          title: "Dependency risk",
          severity: "high",
          due_at: "2026-09-01",
          sort_key: 1.0,
          created_at: "2026-08-15T00:00:00",
        },
      ],
      totals_by_type: { risk: 3, milestone: 2 },
      total: 5,
    },
    meetings: {
      state: "ok",
      count: 2,
      latest: { id: "m1", title: "Review" },
    },
    resources: {
      state: "ok",
      count: 1,
      latest: { id: "r1", ref: "note:abc" },
    },
    changes: {
      state: "ok",
      recent: [{ id: "chg-1", field: "name", old: "A", new: "Alpha" }],
    },
    review: { state: "absent", reason: "not_yet_built" },
    sources: { state: "absent", reason: "not_yet_built" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

describe("decodeRoomSnapshot", () => {
  it("decodes a well-formed room response with all ok sections", () => {
    const snap = decodeRoomSnapshot(okRoomPayload());
    expect(snap.projectId).toBe("proj-abc");
    expect(snap.revision).toBe(3);
    expect(snap.observedAt).toBe("2026-08-31T10:00:00");
    expect(snap.project.name).toBe("Alpha");
    expect(snap.project.purpose).toBe("Ship it");
    expect(snap.project.lifecycle).toBe("active");
    expect(snap.project.posture).toBe("green");
    expect(snap.project.postureReason).toBe("On track");
    expect(snap.project.isArchived).toBe(false);
    expect(snap.project.meetingCount).toBe(2);
  });

  it("decodes ok items section with focus items and totals", () => {
    const snap = decodeRoomSnapshot(okRoomPayload());
    expect(snap.items.state).toBe("ok");
    if (snap.items.state !== "ok") throw new Error("expected ok");
    expect(snap.items.focus).toHaveLength(1);
    expect(snap.items.focus[0].id).toBe("item-1");
    expect(snap.items.focus[0].itemType).toBe("risk");
    expect(snap.items.focus[0].severity).toBe("high");
    expect(snap.items.focus[0].dueAt).toBe("2026-09-01");
    expect(snap.items.totalsByType).toEqual({ risk: 3, milestone: 2 });
    expect(snap.items.total).toBe(5);
  });

  it("decodes degraded sections with error_code", () => {
    const raw = okRoomPayload();
    raw.items = { state: "degraded", error_code: "items_read_failed" };
    const snap = decodeRoomSnapshot(raw);
    expect(snap.items.state).toBe("degraded");
    if (snap.items.state !== "degraded") throw new Error("expected degraded");
    expect(snap.items.error_code).toBe("items_read_failed");
  });

  it("decodes absent sections with reason", () => {
    const snap = decodeRoomSnapshot(okRoomPayload());
    expect(snap.review.state).toBe("absent");
    if (snap.review.state !== "absent") throw new Error("expected absent");
    expect(snap.review.reason).toBe("not_yet_built");
    expect(snap.sources.state).toBe("absent");
    expect(snap.updates.state).toBe("absent");
    expect(snap.steward.state).toBe("absent");
  });

  it("handles missing/null orientation fields gracefully", () => {
    const raw = okRoomPayload();
    (raw.project as Record<string, unknown>).purpose = null;
    (raw.project as Record<string, unknown>).posture = undefined;
    (raw.project as Record<string, unknown>).lifecycle = null;
    const snap = decodeRoomSnapshot(raw);
    expect(snap.project.purpose).toBeNull();
    expect(snap.project.posture).toBeNull();
    expect(snap.project.lifecycle).toBeNull();
  });

  it("returns safe defaults for a completely empty payload", () => {
    const snap = decodeRoomSnapshot({});
    expect(snap.projectId).toBe("");
    expect(snap.revision).toBe(0);
    expect(snap.project.name).toBe("");
    expect(snap.items.state).toBe("absent");
    expect(snap.meetings.state).toBe("absent");
  });

  it("decodes ok meetings and resources sections", () => {
    const snap = decodeRoomSnapshot(okRoomPayload());
    expect(snap.meetings.state).toBe("ok");
    if (snap.meetings.state !== "ok") throw new Error("expected ok");
    expect(snap.meetings.count).toBe(2);
    expect(snap.meetings.latest).toEqual({ id: "m1", title: "Review" });

    expect(snap.resources.state).toBe("ok");
    if (snap.resources.state !== "ok") throw new Error("expected ok");
    expect(snap.resources.count).toBe(1);
  });

  it("decodes ok changes section", () => {
    const snap = decodeRoomSnapshot(okRoomPayload());
    expect(snap.changes.state).toBe("ok");
    if (snap.changes.state !== "ok") throw new Error("expected ok");
    expect(snap.changes.recent).toHaveLength(1);
  });

  it("mixed states: items ok, meetings degraded, rest absent", () => {
    const raw = okRoomPayload();
    raw.meetings = { state: "degraded", error_code: "meetings_read_failed" };
    const snap = decodeRoomSnapshot(raw);
    expect(snap.items.state).toBe("ok");
    expect(snap.meetings.state).toBe("degraded");
    expect(snap.review.state).toBe("absent");
    // A degraded section never blanks an ok section
    if (snap.items.state !== "ok") throw new Error("items should stay ok");
    expect(snap.items.total).toBe(5);
  });
});
