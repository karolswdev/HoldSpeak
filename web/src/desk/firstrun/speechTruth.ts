/* PHILO-17 speech — the meeting record's speech fact (pure; no React).
 *
 * A meeting recorded while the speech model was not on this device is
 * record-only with `transcription_status_detail.reason_code ===
 * "speech_not_set_up"` (holdspeak/meeting_session/session.py). Every face
 * that says "no transcript" says why. */

/** The words a meeting with no transcript carries when speech was missing. */
export const NO_TRANSCRIPT_SPEECH = "No transcript: speech is not set up";

function speechDetail(row: Record<string, unknown> | null | undefined): Record<string, unknown> | null {
  const detail = row?.transcription_status_detail;
  return typeof detail === "object" && detail !== null ? (detail as Record<string, unknown>) : null;
}

function intelState(row: Record<string, unknown> | null | undefined): string {
  const value = row?.intel_status;
  return typeof value === "object" && value !== null
    ? String((value as Record<string, unknown>).state ?? "")
    : String(value ?? "");
}

/** PHILO-17 transcribe: the kept audio of an audio-only meeting is being
 *  transcribed now (meeting_service.transcribe_saved: `intel_status` is
 *  `importing` while the meeting is still `record_only`). */
export function speechTranscribing(row: Record<string, unknown> | null | undefined): boolean {
  return (
    String(row?.transcription_status ?? "") === "record_only" &&
    intelState(row) === "importing" &&
    speechDetail(row)?.reason_code === "speech_not_set_up"
  );
}

/** The meeting record's reason, read from its `transcription_status_detail`.
 *  False while Transcribe runs: the transcript is on its way. */
export function speechWasMissing(row: Record<string, unknown> | null | undefined): boolean {
  return speechDetail(row)?.reason_code === "speech_not_set_up" && !speechTranscribing(row);
}

/** The last Transcribe's short cause (`NO SPEECH FOUND`), when it failed. */
export function transcribeLastError(row: Record<string, unknown> | null | undefined): string | null {
  const cause = speechDetail(row)?.last_error;
  return typeof cause === "string" && cause ? cause : null;
}

/** The meeting's own Transcribe readiness (Astra r2 on #1073): the hub's
 *  `transcribe_speech` on the meeting payload, read for the speech model the
 *  `meeting.transcribe` operation WILL use (its admitted route), not Config.
 *  null when the payload does not carry it. */
export function transcribeSpeechReady(row: Record<string, unknown> | null | undefined): boolean | null {
  const speech = row?.transcribe_speech;
  if (typeof speech !== "object" || speech === null) return null;
  return (speech as Record<string, unknown>).ready === true;
}

/** The one verb an audio-only meeting shows: `Transcribe` when the speech
 *  model Transcribe will use is ready (the meeting's own readiness; the
 *  setup read only when the payload does not carry it), `Set up speech`
 *  when the setup read says speech is not set up, else nothing. */
export function audioOnlyVerb(
  row: Record<string, unknown> | null | undefined,
  speech: { ready: boolean; notSetUp: boolean },
): "transcribe" | "set_up_speech" | null {
  if (!speechWasMissing(row)) return null;
  const ready = transcribeSpeechReady(row) ?? speech.ready;
  if (ready) return "transcribe";
  if (speech.notSetUp) return "set_up_speech";
  return null;
}
