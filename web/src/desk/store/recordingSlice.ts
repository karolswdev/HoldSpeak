/** Recording slice (HS-117-02): recording state, external flag,
 * started-at timestamp, and the three recording actions. */
import { apiRequest } from "../../lib/api";
import { clearWriteFailure, reportWriteFailure } from "../hooks/useWriteReceipt";
import type { DeskState, RecordingStartContext, SliceCreator } from "./types";

/** Meetings on the desk when a local recording started (NEW-beat diff). */
let meetingsBeforeRecording = new Set<string>();

/** PHILO-13-04 (A3) — why a start did not record, in plain words, and
 * whether pressing Record again can help. The hub's own text never reaches
 * the face (`POST /api/meeting/start`, holdspeak/web/routes/meetings/live.py:
 * 501 = this hub has no recorder; 404 = the chosen microphone is gone). */
export function recordStartRefusal(status: number | null): {
  reason: string;
  retry: boolean;
} {
  if (status === null) return { reason: "HUB UNREACHABLE", retry: true };
  if (status === 501) return { reason: "NO RECORDER ON THIS HUB", retry: false };
  if (status === 409) return { reason: "MEETING CONTEXT EXPIRED", retry: false };
  if (status === 404) return { reason: "MICROPHONE NOT FOUND", retry: false };
  return { reason: "THE HUB DID NOT START IT", retry: true };
}

export type RecordingSlice = Pick<
  DeskState,
  | "recording"
  | "recordingExternal"
  | "recordingStartedAt"
  | "liveMeetingId"
  | "recordingEpoch"
  | "applyRecordingActivity"
  | "applyRecordingSnapshot"
  | "startRecording"
  | "stopRecording"
>;

export const createRecordingSlice: SliceCreator<RecordingSlice> = (set, get) => {
  /** PHILO-17 (Astra r2): ONE freshness rule for the recording state. Every
   * transition moves the epoch; a read asked before the last transition (a
   * slow `/api/state`) is older than what the desk knows and is dropped. */
  const move = (patch: Partial<DeskState>) =>
    set({ ...patch, recordingEpoch: get().recordingEpoch + 1 });
  return {
  recording: "idle",
  recordingEpoch: 0,
  recordingExternal: false,
  recordingStartedAt: null,
  liveMeetingId: null,

  applyRecordingSnapshot(activity, askedAt, liveMeetingId) {
    // A snapshot asked before the last transition is stale (a Start or a
    // Stop happened while it was in flight): it never moves the desk.
    if (askedAt !== get().recordingEpoch) return;
    get().applyRecordingActivity(activity);
    if (liveMeetingId && get().recording === "recording" && !get().liveMeetingId) set({ liveMeetingId });
  },

  applyRecordingActivity(activity) {
    if (!activity || typeof activity !== "object") return;
    const s = String("state" in activity ? activity.state || "" : "").toLowerCase();
    if (s === "meeting_live") {
      const started = get().recording === "recording";
      if (started) return; // no transition: the epoch stays
      move({
        recording: "recording",
        recordingExternal: started
          ? get().recordingExternal
          : get().recordingStartedAt == null,
        recordingStartedAt: get().recordingStartedAt ?? Date.now(),
      });
    } else if (s === "idle" || s === "complete") {
      if (get().recording === "recording")
        move({
          recording: "idle",
          recordingExternal: false,
          recordingStartedAt: null,
          liveMeetingId: null,
        });
    }
  },

  async startRecording(context?: RecordingStartContext) {
    if (get().recording !== "idle") return;
    const calendarEventId = context?.calendarEventId.trim() || "";
    move({ recording: "busy", recordingStartedAt: Date.now() });
    meetingsBeforeRecording = new Set(
      get().items.meeting.map((m) => String(m.id)),
    );
    const refuse = (status: number | null, cause: unknown) => {
      move({ recording: "idle", recordingStartedAt: null });
      const why = recordStartRefusal(status);
      reportWriteFailure(
        "START RECORDING",
        cause,
        why.retry ? () => void get().startRecording(context) : undefined,
        undefined,
        `NOT RECORDING · ${why.reason}`,
      );
    };
    let res: Response;
    try {
      res = await apiRequest("/api/meeting/start", {
        method: "POST",
        ...(calendarEventId
          ? {
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ calendar_event_id: calendarEventId }),
            }
          : {}),
      });
    } catch (error) {
      refuse(null, error);
      return;
    }
    // A refused start resolves: only `ok` is a recording (J2-01).
    if (!res.ok) {
      refuse(res.status, res);
      return;
    }
    clearWriteFailure();
    // The canonical meeting opener hosts this record inside Meetings with
    // Back (owner decision 2026-10-13). Stop keeps the same saved record.
    let meetingId = "";
    try {
      const body = (await res.json()) as { meeting?: { id?: unknown; meeting_id?: unknown } | null };
      meetingId = String(body?.meeting?.id ?? body?.meeting?.meeting_id ?? "");
    } catch {
      // No body: the recorder runs; the window opens from the Meetings list.
    }
    move({ recording: "recording", recordingExternal: false, liveMeetingId: meetingId || null });
    if (meetingId) get().openPullout(`meeting:${meetingId}`);
  },

  async stopRecording() {
    if (get().recording !== "recording") return;
    move({ recording: "busy" });
    try {
      const res = await apiRequest("/api/meeting/stop", { method: "POST" });
      // 409 = nothing is live on the hub: idle is the truth. Any other
      // refusal leaves the meeting recording, with its Retry.
      if (!res.ok && res.status !== 409) throw res;
      clearWriteFailure();
    } catch (error) {
      move({ recording: "recording" });
      reportWriteFailure(
        "STOP RECORDING",
        error,
        () => void get().stopRecording(),
        undefined,
        error instanceof Response
          ? "STILL RECORDING · THE HUB DID NOT STOP IT"
          : "STILL RECORDING · HUB UNREACHABLE",
      );
      // The retry is only honest while this session remains stoppable.  Do
      // not fall through to the idle/reset path: that would make its retry
      // closure silently no-op.
      return;
    }
    move({
      recording: "idle",
      recordingExternal: false,
      recordingStartedAt: null,
      liveMeetingId: null,
    });
    await get().refresh();
    const after = get().items.meeting.map((m) => String(m.id));
    const fresh = after.find((id) => !meetingsBeforeRecording.has(id));
    if (fresh) get().markNew(fresh);
  },
};
};
