// HS-170-04 — intelligence badge helper (promoted from the parked MeetingsLane).

/** Truthful intel/action badge for a finished meeting.  Maps the wire's
 *  intelStatus string to the same vocabulary the HistoryCore catalog uses
 *  (stateToken in history/helpers.ts), compressed to a lane-width token. */
export function intelBadge(status: string | null | undefined): string {
  if (!status) return "SAVED";
  const s = String(status).toLowerCase();
  const map: Record<string, string> = {
    complete: "RAN",
    running: "RUNNING",
    queued: "QUEUED",
    pending: "QUEUED",
    error: "FAILED",
    failed: "FAILED",
    partial: "PARTIAL",
    skipped: "SKIPPED",
    disabled: "OFF",
  };
  return map[s] ?? "SAVED";
}
