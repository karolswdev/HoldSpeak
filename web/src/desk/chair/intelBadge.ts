// HS-170-04 — intelligence badge helper (promoted from the parked MeetingsLane).

/** Truthful intel/action badge for a finished meeting.  Maps the wire's
 *  intelStatus string to the same vocabulary the HistoryCore catalog uses
 *  (stateToken in history/helpers.ts), compressed to a lane-width token. */
export function intelBadge(status: string | null | undefined): string {
  if (!status) return "SAVED";
  const s = String(status).toLowerCase();
  const map: Record<string, string> = {
    complete: "RAN",
    // HS-201-04: the bound executor writes `ready` when a real run
    // finishes (holdspeak/db/intel.py, "Meeting intelligence ready.");
    // `complete` is the seeded/legacy word. The catalog already read both
    // as RAN (history/helpers.ts); the Chair read `ready` as SAVED, so a
    // summary that had just run looked like one that never did.
    ready: "RAN",
    running: "RUNNING",
    queued: "QUEUED",
    pending: "QUEUED",
    error: "FAILED",
    failed: "FAILED",
    // PHILO-6-01: the import worker writes `import_failed` when the file
    // gives no transcript (holdspeak/services/meeting_service.py,
    // `_set_import_status`). It fell to the SAVED fallback below, so a
    // failed import looked like a saved meeting on the Arrival.
    import_failed: "FAILED",
    partial: "PARTIAL",
    skipped: "SKIPPED",
    disabled: "OFF",
  };
  return map[s] ?? "SAVED";
}
