/** PHILO-14 A5 — the outcome of a Cancel on the ARMED row (Astra r1, P1-2).
 *
 *  A refused Cancel is named on the row (`NOT CANCELLED · <reason>`, Retry);
 *  a cancelled recording leaves a receipt line in the drawer
 *  (`CANCELLED · <meeting> · hh:mm`) that stays after the row is gone. Both
 *  read the real store: `cancelArmedSchedule`'s result and the hub's
 *  `scheduled_recording.cancelled` event (`scheduledRecordingSlice.ts`).
 */
import { create } from "zustand";
import { useDesk } from "../store";

interface ArmingOutcomeState {
  /** The refusal of the last Cancel, by schedule. */
  refusal: { scheduleId: string; reason: string } | null;
  /** The last cancelled recording: its receipt line. */
  receipt: string | null;
  busy: boolean;
}

export const useArmingOutcome = create<ArmingOutcomeState>(() => ({
  refusal: null,
  receipt: null,
  busy: false,
}));

function clock(at: Date): string {
  return `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
}

/** Cancel the arming recording; a refusal stays on its row by name. */
export async function cancelArming(scheduleId: string): Promise<void> {
  if (useArmingOutcome.getState().busy) return;
  useArmingOutcome.setState({ busy: true });
  try {
    const result = await useDesk.getState().cancelArmedSchedule(scheduleId);
    useArmingOutcome.setState({
      refusal: result.ok ? null : { scheduleId, reason: result.reason || "the hub refused" },
    });
  } finally {
    useArmingOutcome.setState({ busy: false });
  }
}

// The hub's `scheduled_recording.cancelled` sets the arming's outcome; the
// receipt is written here, once, so it outlives the row (and the window).
useDesk.subscribe((state, prev) => {
  const now = state.scheduledArming;
  const before = prev.scheduledArming;
  if (now?.outcome === "cancelled" && before?.outcome !== "cancelled") {
    useArmingOutcome.setState({
      receipt: `CANCELLED · ${now.title || "Scheduled recording"} · ${clock(new Date())}`,
      refusal: null,
    });
  } else if (now && !now.outcome && (!before || before.scheduleId !== now.scheduleId)) {
    // A new recording arms: the last receipt and refusal are history.
    useArmingOutcome.setState({ receipt: null, refusal: null });
  }
});
