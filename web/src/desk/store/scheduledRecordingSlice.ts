/** Scheduled recording slice (HS-136-03): schedule CRUD, arming countdown
 * state from conductor broadcasts, and the create-window lifecycle. */
import { apiFetch } from "../../lib/api";
import type { DeskState, ScheduledArmingState, ScheduledRecording, SliceCreator } from "./types";

export type ScheduledRecordingSlice = Pick<
  DeskState,
  | "scheduledRecordings"
  | "scheduledArming"
  | "scheduleCreateWindow"
  | "loadSchedules"
  | "createSchedule"
  | "deleteSchedule"
  | "cancelArmedSchedule"
  | "applyScheduledRecordingEvent"
  | "openScheduleCreate"
  | "closeScheduleCreate"
>;

/** How long (ms) a terminal outcome badge lingers on the hero. */
const OUTCOME_LINGER_MS = 6000;

export const createScheduledRecordingSlice: SliceCreator<ScheduledRecordingSlice> = (set, get) => ({
  scheduledRecordings: [],
  scheduledArming: null,
  scheduleCreateWindow: null,

  async loadSchedules() {
    try {
      const res = await apiFetch<{ success: boolean; schedules: ScheduledRecording[] }>(
        "/api/scheduled-recordings",
      );
      if (res.success && Array.isArray(res.schedules)) {
        set({ scheduledRecordings: res.schedules });
      }
    } catch {
      /* silent: the lane shows whatever it has */
    }
  },

  async createSchedule(input) {
    try {
      await apiFetch<{ success: boolean; schedule: ScheduledRecording }>(
        "/api/scheduled-recordings",
        { method: "POST", json: input },
      );
      await get().loadSchedules();
      return true;
    } catch {
      return false;
    }
  },

  async deleteSchedule(id) {
    try {
      await apiFetch(`/api/scheduled-recordings/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      set((s) => ({
        scheduledRecordings: s.scheduledRecordings.filter((r) => r.id !== id),
      }));
    } catch {
      /* silent */
    }
  },

  async cancelArmedSchedule(id) {
    try {
      await apiFetch(`/api/scheduled-recordings/${encodeURIComponent(id)}/cancel`, {
        method: "POST",
      });
      return true;
    } catch {
      return false;
    }
  },

  applyScheduledRecordingEvent(type, data) {
    const scheduleId = String(data.schedule_id ?? "");
    const title = String(data.title ?? "");

    if (type === "scheduled_recording.arming") {
      const arming: ScheduledArmingState = {
        scheduleId,
        title,
        countdownSeconds: Number(data.countdown_seconds ?? 10),
        fireAt: Number(data.fire_at ?? 0) * 1000,
        outcome: null,
      };
      set({ scheduledArming: arming });
      return;
    }

    if (type === "scheduled_recording.cancelled") {
      const current = get().scheduledArming;
      if (current && current.scheduleId === scheduleId) {
        set({ scheduledArming: { ...current, outcome: "cancelled" } });
        window.setTimeout(() => {
          if (get().scheduledArming?.scheduleId === scheduleId)
            set({ scheduledArming: null });
        }, OUTCOME_LINGER_MS);
      }
      void get().loadSchedules();
      return;
    }

    if (type === "scheduled_recording.refused") {
      const current = get().scheduledArming;
      const reason = String(data.reason ?? "");
      if (current && current.scheduleId === scheduleId) {
        set({ scheduledArming: { ...current, outcome: "refused", outcomeReason: reason } });
      } else {
        set({
          scheduledArming: {
            scheduleId, title, countdownSeconds: 0, fireAt: 0,
            outcome: "refused", outcomeReason: reason,
          },
        });
      }
      window.setTimeout(() => {
        if (get().scheduledArming?.scheduleId === scheduleId)
          set({ scheduledArming: null });
      }, OUTCOME_LINGER_MS);
      void get().loadSchedules();
      return;
    }

    if (type === "scheduled_recording.missed") {
      set({
        scheduledArming: {
          scheduleId, title, countdownSeconds: 0, fireAt: 0,
          outcome: "missed",
        },
      });
      window.setTimeout(() => {
        if (get().scheduledArming?.scheduleId === scheduleId)
          set({ scheduledArming: null });
      }, OUTCOME_LINGER_MS);
      void get().loadSchedules();
      return;
    }

    if (type === "scheduled_recording.started") {
      const current = get().scheduledArming;
      if (current && current.scheduleId === scheduleId) {
        set({ scheduledArming: { ...current, outcome: "started" } });
        window.setTimeout(() => {
          if (get().scheduledArming?.scheduleId === scheduleId)
            set({ scheduledArming: null });
        }, OUTCOME_LINGER_MS);
      }
      void get().loadSchedules();
      return;
    }

    if (type === "scheduled_recording.stopped") {
      void get().loadSchedules();
      return;
    }
  },

  openScheduleCreate(origin) {
    set({ scheduleCreateWindow: { origin: origin ?? null } });
  },

  closeScheduleCreate() {
    set({ scheduleCreateWindow: null });
  },
});
