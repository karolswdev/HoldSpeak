/* PHILO-17 speech — the meeting record's speech fact (pure; no React).
 *
 * A meeting recorded while the speech model was not on this device is
 * record-only with `transcription_status_detail.reason_code ===
 * "speech_not_set_up"` (holdspeak/meeting_session/session.py). Every face
 * that says "no transcript" says why. */

/** The words a meeting with no transcript carries when speech was missing. */
export const NO_TRANSCRIPT_SPEECH = "No transcript: speech is not set up";

/** The meeting record's reason, read from its `transcription_status_detail`. */
export function speechWasMissing(row: Record<string, unknown> | null | undefined): boolean {
  const detail = row?.transcription_status_detail;
  return (
    typeof detail === "object" &&
    detail !== null &&
    (detail as Record<string, unknown>).reason_code === "speech_not_set_up"
  );
}
