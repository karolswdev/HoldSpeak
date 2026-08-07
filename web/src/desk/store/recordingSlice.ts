/** Recording slice (HS-117-02): recording state, external flag,
 * started-at timestamp, and the three recording actions. */
import { apiRequest } from "../../lib/api";
import type { DeskState, SliceCreator } from "./types";

/** Meetings on the desk when a local recording started (NEW-beat diff). */
let meetingsBeforeRecording = new Set<string>();

export type RecordingSlice = Pick<
  DeskState,
  | "recording"
  | "recordingExternal"
  | "recordingStartedAt"
  | "applyRecordingActivity"
  | "startRecording"
  | "stopRecording"
>;

export const createRecordingSlice: SliceCreator<RecordingSlice> = (set, get) => ({
  recording: "idle",
  recordingExternal: false,
  recordingStartedAt: null,

  applyRecordingActivity(activity) {
    if (!activity || typeof activity !== "object") return;
    const s = String("state" in activity ? activity.state || "" : "").toLowerCase();
    if (s === "meeting_live") {
      const started = get().recording === "recording";
      set({
        recording: "recording",
        recordingExternal: started
          ? get().recordingExternal
          : get().recordingStartedAt == null,
        recordingStartedAt: get().recordingStartedAt ?? Date.now(),
      });
    } else if (s === "idle" || s === "complete") {
      if (get().recording === "recording")
        set({
          recording: "idle",
          recordingExternal: false,
          recordingStartedAt: null,
        });
    }
  },

  async startRecording() {
    if (get().recording !== "idle") return;
    set({ recording: "busy", recordingStartedAt: Date.now() });
    meetingsBeforeRecording = new Set(
      get().items.meeting.map((m) => String(m.id)),
    );
    try {
      await apiRequest("/api/meeting/start", { method: "POST" });
      set({ recording: "recording", recordingExternal: false });
    } catch {
      set({ recording: "idle", recordingStartedAt: null });
    }
  },

  async stopRecording() {
    if (get().recording !== "recording") return;
    set({ recording: "busy" });
    try {
      await apiRequest("/api/meeting/stop", { method: "POST" });
    } catch {
      /* the state frame settles the orb either way */
    }
    set({
      recording: "idle",
      recordingExternal: false,
      recordingStartedAt: null,
    });
    await get().refresh();
    const after = get().items.meeting.map((m) => String(m.id));
    const fresh = after.find((id) => !meetingsBeforeRecording.has(id));
    if (fresh) get().markNew(fresh);
  },
});
