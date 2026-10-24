export type MeetingSaveStatus = "saved" | "partial" | "failed" | "unknown";

export interface MeetingStopOutcome {
  captureStopped: boolean | null;
  meetingId: string;
  databaseSaved: boolean | null;
  jsonSaved: boolean | null;
  captureStatus: string;
  saveStatus: MeetingSaveStatus;
  saveError: string;
  deviceCleanupError: string;
  recoveryAvailable: boolean;
}

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function text(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function booleanFact(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

export function parseMeetingStopOutcome(
  value: unknown,
  fallbackMeetingId = "",
): MeetingStopOutcome {
  const payload = record(value);
  const meeting = record(payload.meeting);
  const save = record(payload.save);
  const meetingId =
    text(meeting.id) ||
    text(meeting.meeting_id) ||
    text(payload.meeting_id) ||
    fallbackMeetingId;
  const databaseSaved = booleanFact(save.database_saved);
  const jsonSaved = booleanFact(save.json_saved);
  const captureStatus = text(meeting.capture_status).toLowerCase();
  const saveError = text(payload.save_error);
  const deviceCleanupError = text(payload.device_cleanup_error);
  const recoveryFact =
    typeof payload.capture_recovery_available === "boolean"
      ? payload.capture_recovery_available
      : null;
  const status = text(payload.status).toLowerCase();
  const captureStopped =
    status === "stopped" || status === "meeting_stopped"
      ? true
      : status === "recording" || status === "stopping"
        ? false
        : null;

  let saveStatus: MeetingSaveStatus = "unknown";
  const bothSaveFactsPresent = databaseSaved !== null && jsonSaved !== null;
  if (databaseSaved === true && jsonSaved === true && !saveError) {
    saveStatus = "saved";
  } else if (
    (bothSaveFactsPresent && (databaseSaved === true || jsonSaved === true)) ||
    (saveError && (databaseSaved === true || jsonSaved === true))
  ) {
    saveStatus = "partial";
  } else if (
    (bothSaveFactsPresent && databaseSaved === false && jsonSaved === false) ||
    (saveError && databaseSaved !== true && jsonSaved !== true)
  ) {
    saveStatus = "failed";
  }

  return {
    captureStopped,
    meetingId,
    databaseSaved,
    jsonSaved,
    saveStatus,
    saveError,
    deviceCleanupError,
    // The existing recovery door repairs a durable capture checkpoint. It
    // does not retry JSON/aftercare on an already-finalized row.
    recoveryAvailable:
      recoveryFact === true
        ? Boolean(meetingId && databaseSaved === false && jsonSaved === true)
        : recoveryFact === false
          ? false
          : Boolean(
              meetingId &&
                databaseSaved === false &&
                jsonSaved === true &&
                captureStatus === "recoverable",
            ),
    captureStatus,
  };
}

export function meetingStopReceiptLabel(outcome: MeetingStopOutcome): string {
  if (outcome.saveStatus === "saved") {
    return outcome.deviceCleanupError
      ? "STOPPED · SAVED · AUDIO DEVICE CLEANUP FAILED"
      : "Meeting saved";
  }
  if (outcome.saveStatus === "partial") return "STOPPED · PARTLY SAVED";
  if (outcome.saveStatus === "failed") return "STOPPED · SAVE FAILED";
  return "STOPPED · SAVE STATUS UNKNOWN";
}
