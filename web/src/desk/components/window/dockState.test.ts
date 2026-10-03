import { describe, expect, it } from "vitest";
import {
  dockStateLabel,
  EMPTY_DOCK_LIVE,
  formatDockTime,
  latestSendOutcome,
  latestSendSettle,
  nextOneOnOneLabel,
  projectNeedsYouCounts,
  reduceDockFrame,
} from "./dockState";

describe("H-C3 Dock live reducer", () => {
  it("shows REC only after the hub confirms a meeting start", () => {
    const refused = reduceDockFrame(EMPTY_DOCK_LIVE, {
      type: "scheduled_recording.refused",
      data: { meeting_id: "m1", status: "refused" },
    });
    expect(refused.recording).toBeNull();
    const started = reduceDockFrame(refused, {
      type: "meeting_started",
      data: { id: "m1", confirmed: true, started_at: "2026-10-02T12:00:00Z" },
    });
    expect(started.recording).toEqual({
      meetingId: "m1",
      startedAt: "2026-10-02T12:00:00Z",
    });
  });

  it.each([
    ["sent", "SENT"],
    ["failed", "SEND FAILED"],
    ["unknown", "UNKNOWN"],
  ] as const)("maps a settled send outcome: %s", (state, label) => {
    const next = reduceDockFrame(EMPTY_DOCK_LIVE, {
      type: "desk_changed",
      data: { kind: "send", id: "send-1", op: state },
    });
    expect(next.sendOutcome).toBe(state);
    expect(dockStateLabel(next.sendOutcome)).toBe(label);
  });

  it("keeps the one membership meaning and suppresses zero project badges", () => {
    expect(projectNeedsYouCounts([
      { projectId: "p1" },
      { project_id: "p1" },
      { projectId: "p2" },
      { projectId: null },
    ])).toEqual({ p1: 2, p2: 1 });
  });

  it("reads the earliest B4 next one-to-one and terminal send", () => {
    expect(nextOneOnOneLabel([
      { brief: { next_one_on_one: { starts_at: "2026-10-03T15:00:00Z" } } },
      { nextOneOnOne: { startsAt: "2026-10-02T14:00:00Z" } },
    ])).toBe("2026-10-02T14:00:00Z");
    expect(latestSendOutcome([
      { state: "sent", dispatch_seq: 3 },
      { state: "failed", dispatch_seq: 4 },
      { state: "dispatching", dispatch_seq: 5 },
    ])).toBe("failed");
  });

  it("settles recording and marks a ready meeting", () => {
    let next = reduceDockFrame(EMPTY_DOCK_LIVE, {
      type: "meeting_started",
      data: { meeting_id: "m1", confirmed: true },
    });
    next = reduceDockFrame(next, { type: "aftercare_ready", data: { meeting_id: "m1" } });
    next = reduceDockFrame(next, { type: "stopped", data: { meeting_id: "m1" } });
    expect(next.recording).toBeNull();
    expect(next.readyMeetingIds).toEqual(["m1"]);
  });

  it("uses the meeting id carried by an intel completion frame", () => {
    const next = reduceDockFrame(EMPTY_DOCK_LIVE, {
      type: "intel_complete",
      data: { meeting_id: "m-intel", summary: "Ready" },
    });
    expect(next.readyMeetingIds).toEqual(["m-intel"]);
  });

  it("removes a meeting after its durable readiness is read", () => {
    const next = reduceDockFrame(
      { ...EMPTY_DOCK_LIVE, readyMeetingIds: ["m-read", "m-keep"] },
      { type: "desk_changed", data: { kind: "meeting_ready_read", id: "m-read" } },
    );
    expect(next.readyMeetingIds).toEqual(["m-keep"]);
  });

  it("uses the scheduled recording id and the terminal timestamp", () => {
    const started = reduceDockFrame(EMPTY_DOCK_LIVE, {
      type: "scheduled_recording.started",
      data: { schedule_id: "schedule-1", at: "2026-10-02T12:00:00Z" },
    });
    expect(started.recording?.meetingId).toBe("schedule-1");
    expect(latestSendOutcome([
      { state: "sent", dispatch_seq: 8, settled_at: "2026-10-02T10:00:00Z" },
      { state: "failed", dispatch_seq: 2, settled_at: "2026-10-02T11:00:00Z" },
    ])).toBe("failed");
  });
});

describe("C3-W the SENT time (board C1-8a)", () => {
  it("reads a settled send's time as 24-hour hh:mm", () => {
    // A local wall-clock instant: the Dock prints the owner's local time.
    const at = new Date(2026, 9, 3, 14, 2).toISOString();
    expect(formatDockTime(at)).toBe("14:02");
    expect(dockStateLabel("sent", at)).toBe("SENT 14:02");
    // Only SENT carries the time; the other outcomes read as drawn (C1-8b).
    expect(dockStateLabel("failed", at)).toBe("SEND FAILED");
    expect(dockStateLabel("unknown", at)).toBe("UNKNOWN");
    expect(dockStateLabel("sent")).toBe("SENT");
  });

  it("keeps the latest terminal send's settle time", () => {
    expect(latestSendSettle([
      { state: "sent", settled_at: "2026-10-03T12:00:00Z" },
      { state: "sent", settled_at: "2026-10-03T13:00:00Z" },
      { state: "dispatching", created_at: "2026-10-03T14:00:00Z" },
    ])).toEqual({ outcome: "sent", at: "2026-10-03T13:00:00Z" });
    expect(latestSendSettle([])).toBeNull();
  });
});
