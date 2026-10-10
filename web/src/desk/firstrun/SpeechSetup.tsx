/* PHILO-17 speech — one speech-readiness truth on every face that needs it.
 *
 * A fresh desk without the speech (Whisper) model told the owner "READY"
 * on Speak, "Listening for speech" on Record, "TOOL INCOMPATIBLE" on Runs
 * on and "PASS" on Setup, and lost his first meeting. The truth is the
 * hub's `speech` read on GET /api/setup/local-ai (`whisper_models.
 * speech_readiness`, disk only). When the model is not here, each face says
 * "Speech is not set up" and offers ONE verb, "Set up speech · <size>",
 * which runs the same speech-only download the first-run page runs
 * (`useLocalAi().startSpeech`, POST /api/setup/local-ai {only: ["whisper"]}).
 *
 * The row draws nothing while the read is pending, when it cannot be read,
 * and when speech is ready: no decorative "all fine" row. */
import { useEffect, useRef } from "react";
import { Button } from "../../components/signal/Signal";
import { EgressChip, StateChip } from "../surface";
import { formatBytes, groupsOf, planSteps, sourceHost, speechReady, useLocalAi } from "./localAi";
import "./speechSetup.css";

export function useSpeechSetup() {
  const ai = useLocalAi();
  const status = ai.read.kind === "ok" ? ai.read.status : null;
  const ready = speechReady(status);
  const whisper = groupsOf(status).find((group) => group.key === "whisper");
  // The hub's own size of what is missing; the Whisper rows as a fallback.
  const bytes = status?.speech?.bytes || (whisper && !whisper.onDevice ? whisper.bytes : 0);
  return {
    ai,
    status,
    /** True only after a read: the speech model is on this device. */
    ready,
    /** True only after a read that names the speech model: it is not here. */
    notSetUp: Boolean(status?.speech) && !ready,
    /** Setup can get the model (a pinned model): the verb is real. */
    canSetUp: status !== null && status.speech?.state !== "not_covered" && bytes > 0,
    bytes,
  };
}

export type SpeechSetupState = ReturnType<typeof useSpeechSetup>;

/** The row: "Speech is not set up" + "Set up speech · <size>". */
export function SpeechSetup({
  setup,
  onReady,
  testId = "speech-setup",
  bare = false,
}: {
  setup: SpeechSetupState;
  /** Called once when speech turns ready after this row was drawn. */
  onReady?: () => void;
  testId?: string;
  /** The host row already says "Speech is not set up": draw the verb only. */
  bare?: boolean;
}) {
  const { ai, status, notSetUp, canSetUp, bytes } = setup;
  const wasMissing = useRef(false);
  useEffect(() => {
    if (notSetUp) wasMissing.current = true;
    else if (setup.ready && wasMissing.current) {
      wasMissing.current = false;
      onReady?.();
    }
  }, [notSetUp, setup.ready, onReady]);

  if (!status || !notSetUp) return null;
  const running = status.state === "downloading";
  const failed = status.state === "failed";
  const step = running ? planSteps(status, ai.rate, ["whisper"]).find((s) => s.id === "whisper") : undefined;
  const host = ai.host || sourceHost(status);
  return (
    <div className="speech-setup" role="status" data-testid={testId} data-speech-state={status.speech?.state ?? "unknown"}>
      {bare ? null : (
        <span className="speech-setup-line" data-testid={`${testId}-line`}>
          Speech is not set up
        </span>
      )}
      {failed ? <StateChip state="failure" label="CAN'T DOWNLOAD" /> : null}
      {!canSetUp && !running ? <span className="surface-token" data-chip="">MODEL NOT IN SETUP</span> : null}
      <span className="speech-setup-verbs">
        {running ? (
          <>
            <span className="surface-token" data-chip="" data-testid={`${testId}-progress`}>
              {step?.rate ?? "SETTING UP"}
            </span>
            <Button dense variant="ghost" disabled={ai.busy} onClick={() => void ai.cancel()}>
              Stop
            </Button>
          </>
        ) : canSetUp ? (
          <>
            {host ? <EgressChip label={host} scope="cloud" /> : null}
            <Button
              dense
              variant="primary"
              loading={ai.busy}
              disabled={ai.busy}
              onClick={() => void ai.startSpeech()}
              data-testid={`${testId}-verb`}
            >
              {`Set up speech · ${formatBytes(bytes)}`}
            </Button>
          </>
        ) : null}
      </span>
    </div>
  );
}

export { NO_TRANSCRIPT_SPEECH, speechWasMissing } from "./speechTruth";
