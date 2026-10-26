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
import { DotWord } from "../surface/kit";
import { formatBytes, groupsOf, planSteps, sourceHost, speechReady, useLocalAi } from "./localAi";
import "./speechSetup.css";

/** One window's speech setup started or finished: every face reads again. */
export const SPEECH_SETUP_EVENT = "hs:speech-setup";

function announceSpeechSetup(): void {
  try {
    window.dispatchEvent(new Event(SPEECH_SETUP_EVENT));
  } catch {
    // no window (a test without a DOM): nothing to tell
  }
}

export function useSpeechSetup() {
  const ai = useLocalAi();
  // Astra r1 (finding 5): setup done in another window, or outside this
  // browser, reaches this face: read again on the setup event and on focus.
  const refresh = ai.refresh;
  useEffect(() => {
    const again = () => void refresh();
    const visible = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    window.addEventListener(SPEECH_SETUP_EVENT, again);
    window.addEventListener("focus", again);
    document.addEventListener("visibilitychange", visible);
    return () => {
      window.removeEventListener(SPEECH_SETUP_EVENT, again);
      window.removeEventListener("focus", again);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [refresh]);
  return speechSetupOf(ai);
}

/** The speech-setup state from a `useLocalAi()` the face already holds
 *  (first run's First words card shares its Local AI read). */
export function speechSetupOf(ai: ReturnType<typeof useLocalAi>) {
  const status = ai.read.kind === "ok" ? ai.read.status : null;
  const ready = speechReady(status);
  const whisper = groupsOf(status).find((group) => group.key === "whisper");
  // The hub's own size of what is missing; the Whisper rows as a fallback.
  const bytes = status?.speech?.bytes ?? (whisper && !whisper.onDevice ? whisper.bytes : 0);
  const speechState = status?.speech?.state;
  return {
    ai,
    status,
    /** True only after a read: the speech model is on this device. */
    ready,
    /** True only after a read that names the speech model: it is not here. */
    notSetUp: Boolean(status?.speech) && !ready,
    /** Setup can get the model (a pinned model): the verb is real. */
    canSetUp:
      status !== null && speechState !== "not_covered" && speechState !== "backend_unavailable" && bytes > 0,
    bytes,
  };
}

export type SpeechSetupState = ReturnType<typeof speechSetupOf>;

/** The row: "Speech is not set up" + "Set up speech · <size>". */
export function SpeechSetup({
  setup,
  onReady,
  testId = "speech-setup",
  bare = false,
  primary = true,
  toolbar = false,
}: {
  setup: SpeechSetupState;
  /** Called once when speech turns ready after this row was drawn. */
  onReady?: () => void;
  testId?: string;
  /** The host row already says "Speech is not set up": draw the verb only. */
  bare?: boolean;
  /** One primary per face: the verb is primary only on Speak, where it is
   *  the face's one job. Live meeting (Start meeting), Runs on (Add) and
   *  Setup (Test runtime) keep their own primary; there it is secondary. */
  primary?: boolean;
  /** Window grammar (2026-10-24; UX-CANON A.9 as amended 2026-10-25): the
   *  row is a toolbar item. The verb only, the quiet secondary form; the
   *  download host goes to the verb's hover title (no host chip); a state is
   *  a dot and a word (no mono caps chip). The host face says "Speech not
   *  set up" in its status bar. */
  toolbar?: boolean;
}) {
  const { ai, status, notSetUp, canSetUp, bytes } = setup;
  const wasMissing = useRef(false);
  useEffect(() => {
    if (notSetUp) wasMissing.current = true;
    else if (setup.ready && wasMissing.current) {
      wasMissing.current = false;
      announceSpeechSetup();
      onReady?.();
    }
  }, [notSetUp, setup.ready, onReady]);

  // While the first read is out the row is not drawn, but the face is still
  // reading: it says so (aria-busy), so nothing reads it as settled before the
  // row lands and moves what is under it (the desk sweep's still fence).
  if (ai.read.kind === "loading") return <span hidden aria-busy="true" data-testid={`${testId}-reading`} />;
  if (!status || !notSetUp) return null;
  const running = status.state === "downloading";
  const failed = status.state === "failed";
  const step = running ? planSteps(status, ai.rate, ["whisper"]).find((s) => s.id === "whisper") : undefined;
  const host = ai.host || sourceHost(status);
  if (toolbar) {
    return (
      <span className="speech-setup" data-variant="toolbar" role="status" data-testid={testId} data-speech-state={status.speech?.state ?? "unknown"}>
        {failed ? <DotWord tone="fail">Can't download</DotWord> : null}
        {!canSetUp && !running ? (
          <DotWord tone="warn">
            {status.speech?.state === "backend_unavailable" ? "Speech library missing" : "Speech model not in Setup"}
          </DotWord>
        ) : null}
        {running ? (
          <>
            <DotWord tone="info" data-testid={`${testId}-progress`}>{step?.rate ?? "Setting up speech"}</DotWord>
            <Button dense variant="secondary" disabled={ai.busy} onClick={() => void ai.cancel()}>
              Stop
            </Button>
          </>
        ) : canSetUp ? (
          <Button
            dense
            variant="secondary"
            loading={ai.busy}
            disabled={ai.busy}
            title={host ? `Downloads from ${host.toLowerCase()}` : undefined}
            onClick={() => void ai.startSpeech().then(announceSpeechSetup)}
            data-testid={`${testId}-verb`}
          >
            {`Set up speech · ${formatBytes(bytes)}`}
          </Button>
        ) : null}
      </span>
    );
  }
  return (
    <div className="speech-setup" role="status" data-testid={testId} data-speech-state={status.speech?.state ?? "unknown"}>
      {bare ? null : (
        <span className="speech-setup-line" data-testid={`${testId}-line`}>
          Speech is not set up
        </span>
      )}
      {failed ? <StateChip state="failure" label="CAN'T DOWNLOAD" /> : null}
      {!canSetUp && !running ? (
        <span className="surface-token" data-chip="">
          {status.speech?.state === "backend_unavailable" ? "SPEECH LIBRARY MISSING" : "MODEL NOT IN SETUP"}
        </span>
      ) : null}
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
              variant={primary ? "primary" : "secondary"}
              loading={ai.busy}
              disabled={ai.busy}
              onClick={() => void ai.startSpeech().then(announceSpeechSetup)}
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
