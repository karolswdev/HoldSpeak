/** PHILO-13-13 H-C3 — the Dock's small live-state projection.
 *
 * The Dock does not own a second meeting, send, People or Project store. It
 * reduces authenticated runtime frames into short lived marks and uses the
 * existing reads for the durable answer. Keeping this reducer pure makes the
 * frame boundary testable without pretending that a fake frame is a producer
 * proof.
 */

export type DockSendOutcome = "sent" | "failed" | "unknown";

export interface DockRecording {
  meetingId: string;
  startedAt: string | null;
}

export interface DockLiveState {
  recording: DockRecording | null;
  readyMeetingIds: string[];
  sendOutcome: DockSendOutcome | null;
}

export const EMPTY_DOCK_LIVE: DockLiveState = {
  recording: null,
  readyMeetingIds: [],
  sendOutcome: null,
};

export interface DockFrame {
  type: string;
  data: unknown;
}

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? value as Record<string, unknown> : {};
}

function text(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function frameMeetingId(data: unknown): string {
  const value = record(data);
  const nested = record(value.meeting);
  return text(value.meeting_id) || text(value.schedule_id) || text(value.id) ||
    text(nested.meeting_id) || text(nested.schedule_id) || text(nested.id);
}

function frameTime(data: unknown): string | null {
  const value = record(data);
  return text(value.started_at) || text(value.startedAt) || text(value.recorded_at) || null;
}

function frameOutcome(data: unknown): DockSendOutcome | null {
  const value = record(data);
  const raw = text(value.state) || text(value.outcome) || text(value.status) || text(value.op);
  return raw === "sent" || raw === "failed" || raw === "unknown" ? raw : null;
}

function confirmed(data: unknown): boolean {
  const value = record(data);
  const status = text(value.status) || text(value.state) || text(value.outcome);
  if (["refused", "rejected", "failed", "denied"].includes(status)) return false;
  if ("confirmed" in value) return value.confirmed === true;
  if ("accepted" in value) return value.accepted === true;
  // A meeting_started or scheduled_recording.started frame is itself the
  // authenticated hub confirmation when it carries no duplicate flag.
  return true;
}

/** Apply one authenticated frame. Unknown frames leave the snapshot intact. */
export function reduceDockFrame(
  state: DockLiveState,
  frame: DockFrame,
): DockLiveState {
  const meetingId = frameMeetingId(frame.data);
  switch (frame.type) {
    case "meeting_started":
    case "scheduled_recording.started":
      if (!confirmed(frame.data) || !meetingId) return state;
      return {
        ...state,
        recording: { meetingId, startedAt: frameTime(frame.data) },
      };
    case "stopped":
    case "scheduled_recording.stopped":
      if (!meetingId || state.recording?.meetingId === meetingId)
        return { ...state, recording: null };
      return state;
    case "scheduled_recording.refused":
      // A refusal is an answer that no recording started. It never creates REC.
      return state;
    case "intel_complete":
    case "aftercare_ready":
      return meetingId && !state.readyMeetingIds.includes(meetingId)
        ? { ...state, readyMeetingIds: [...state.readyMeetingIds, meetingId] }
        : state;
    case "desk_changed": {
      const value = record(frame.data);
      const kind = text(value.kind);
      if (kind !== "send") return state;
      const outcome = frameOutcome(value);
      return outcome ? { ...state, sendOutcome: outcome } : state;
    }
    default:
      return state;
  }
}

export interface DockSendRead {
  state?: string | null;
  settled_at?: string | null;
  dispatch_seq?: number | null;
  created_at?: string | null;
}

/** Pick the latest terminal send from the existing channel read. */
export function latestSendOutcome(
  sends: readonly DockSendRead[],
): DockSendOutcome | null {
  const terminal = sends.filter((send) =>
    send.state === "sent" || send.state === "failed" || send.state === "unknown",
  );
  terminal.sort((left, right) => {
    const timestamp = String(right.settled_at || right.created_at || "")
      .localeCompare(String(left.settled_at || left.created_at || ""));
    if (timestamp) return timestamp;
    return Number(right.dispatch_seq ?? -1) - Number(left.dispatch_seq ?? -1);
  });
  const outcome = terminal[0]?.state;
  return outcome === "sent" || outcome === "failed" || outcome === "unknown" ? outcome : null;
}

export interface DockRelationshipRead {
  id?: string;
  next_one_on_one?: unknown;
  nextOneOnOne?: unknown;
  brief?: DockRelationshipRead;
  relationship?: DockRelationshipRead;
}

/** Read the B4 relationship contract without crossing the People boundary. */
export function nextOneOnOneLabel(
  relationships: readonly DockRelationshipRead[],
): string | null {
  const values = relationships
    .map((relationship) => {
      const brief = relationship.brief;
      const detail = relationship.relationship;
      return relationship.next_one_on_one ?? relationship.nextOneOnOne ??
        brief?.next_one_on_one ?? brief?.nextOneOnOne ??
        detail?.next_one_on_one ?? detail?.nextOneOnOne;
    })
    .filter((value) => value !== null && value !== undefined && value !== "")
    .map((value) => {
      if (typeof value === "string") return value;
      const row = record(value);
      return text(row.starts_at) || text(row.startsAt) || text(row.start) || text(row.date);
    })
    .filter(Boolean)
    .sort();
  return values[0] || null;
}

/** One A2 membership count per active project; zero stays absent. */
export function projectNeedsYouCounts(
  items: readonly { projectId?: string | null; project_id?: string | null }[],
): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const item of items) {
    const id = text(item.projectId) || text(item.project_id);
    if (id) counts[id] = (counts[id] || 0) + 1;
  }
  return counts;
}

export function dockStateLabel(outcome: DockSendOutcome | null): string | null {
  if (outcome === "sent") return "SENT";
  if (outcome === "failed") return "SEND FAILED";
  if (outcome === "unknown") return "UNKNOWN";
  return null;
}

export function formatDockTime(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
