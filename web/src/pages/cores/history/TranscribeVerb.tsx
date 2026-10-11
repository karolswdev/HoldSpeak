// PHILO-17 transcribe — the one verb of a meeting saved with its audio only.
//
// A meeting recorded while speech was not set up keeps its audio and says
// "NO TRANSCRIPT · SPEECH NOT SET UP" (#1066). Once speech is set up, it
// shows ONE verb, `Transcribe` (POST /api/meetings/{id}/transcribe, the
// `meeting.transcribe` operation). While speech is still not set up, the
// record shows the existing `Set up speech` verb instead (SpeechSetup).
// The speech read is the one truth (`whisper_models.speech_readiness`,
// GET /api/setup/local-ai), and it is read only for an audio-only meeting.
import { useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { StateChip } from "../../../desk/surface";
import { SpeechSetup, useSpeechSetup } from "../../../desk/firstrun/SpeechSetup";
import { audioOnlyVerb, speechWasMissing, transcribeLastError } from "../../../desk/firstrun/speechTruth";

export function AudioOnlyVerb({
  row,
  onTranscribe,
  setUpSpeech = false,
  otherwise = null,
  testId = "transcribe",
}: {
  row: Record<string, unknown>;
  /** What the host shows when this meeting has no audio-only verb (the
   *  list row's `Open`). */
  otherwise?: ReactNode;
  /** Starts Transcribe on the hub; resolves when the hub said yes. */
  onTranscribe: (id: string) => Promise<unknown>;
  /** The record offers `Set up speech` when speech is not ready; the list
   *  row does not (its token already says why). */
  setUpSpeech?: boolean;
  testId?: string;
}) {
  // Read speech only for a meeting that needs it (no read for the rest).
  if (!speechWasMissing(row)) return <>{otherwise}</>;
  return (
    <AudioOnlyVerbRead row={row} onTranscribe={onTranscribe} setUpSpeech={setUpSpeech} otherwise={otherwise} testId={testId} />
  );
}

function AudioOnlyVerbRead({
  row,
  onTranscribe,
  setUpSpeech,
  otherwise,
  testId,
}: {
  row: Record<string, unknown>;
  onTranscribe: (id: string) => Promise<unknown>;
  setUpSpeech: boolean;
  otherwise: ReactNode;
  testId: string;
}) {
  const speech = useSpeechSetup();
  const [busy, setBusy] = useState(false);
  const [refused, setRefused] = useState(false);
  const verb = audioOnlyVerb(row, speech);
  const lastError = transcribeLastError(row);
  if (verb === "set_up_speech") {
    return setUpSpeech ? <SpeechSetup setup={speech} bare primary={false} testId={`${testId}-speech-setup`} /> : <>{otherwise}</>;
  }
  if (verb !== "transcribe") return <>{otherwise}</>;
  return (
    <span className="meetings-transcribe" data-testid={testId}>
      {refused ? (
        <StateChip state="failure" label="CAN'T TRANSCRIBE" data-testid={`${testId}-refused`} />
      ) : lastError ? (
        <StateChip state="failure" label={`LAST ERROR · ${lastError}`} data-testid={`${testId}-last-error`} />
      ) : null}
      <Button
        dense
        variant="secondary"
        loading={busy}
        disabled={busy}
        data-testid={`${testId}-verb`}
        onClick={(event: React.MouseEvent) => {
          event.stopPropagation();
          setBusy(true);
          setRefused(false);
          void onTranscribe(String(row.id ?? ""))
            .catch(() => setRefused(true))
            .finally(() => setBusy(false));
        }}
      >
        Transcribe
      </Button>
    </span>
  );
}
