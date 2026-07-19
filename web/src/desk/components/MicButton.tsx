// HS-78-02: the speak-to-fill mic — hold to talk, release to fill.
//
// Every desk text input carries one (the standing voice-first rule, now on
// the web): press and hold, speak, release; the transcript lands in the
// field through onText with NO confirm step. Capture + transcription live
// in the shared helper (the hub's own local Whisper; nothing egresses).
import { useEffect, useRef, useState } from "react";
// @ts-ignore — plain ESM shared helper (the one browser-mic call site).
import {
  cancelCapture,
  speakToFillSupported,
  speakToFillUnsupportedReason,
  startCapture,
  stopAndTranscribe,
  retryPendingTranscription,
} from "../../lib/speakToFill";
import { loadPendingVoice } from "../../lib/pendingVoice";
import {
  DICTATION_FAILURES,
  dictationFailure,
  type DictationFailure,
} from "../../lib/dictationRecovery";

export function MicButton({
  onText,
  label = "Hold to talk",
  onFailure,
  draftScope,
}: {
  onText: (text: string) => void;
  label?: string;
  onFailure?: (failure: DictationFailure) => void;
  draftScope?: string;
}) {
  const [state, setState] = useState<"idle" | "listening" | "busy" | "failed">(
    "idle",
  );
  const [failure, setFailure] = useState<DictationFailure | null>(null);
  const [audioRetained, setAudioRetained] = useState(false);
  const holding = useRef(false);

  useEffect(() => {
    if (!draftScope) return;
    let mounted = true;
    void loadPendingVoice(draftScope).then((audio) => {
      if (!mounted || !audio) return;
      setAudioRetained(true);
      setFailure("transcription_failed");
      setState("failed");
    });
    return () => {
      mounted = false;
    };
  }, [draftScope]);

  // HS-100-06: a mic that cannot capture is visible, disabled, and says
  // why — it never vanishes silently (Article VI; the LAN-origin trap).
  const captureSupported = speakToFillSupported();
  if (!captureSupported && !audioRetained) {
    const reason =
      speakToFillUnsupportedReason() ??
      "This browser cannot capture microphone audio.";
    return (
      <button
        type="button"
        className="desk-mic is-unsupported"
        disabled
        title={reason}
        aria-label={`${label} (unavailable: ${reason})`}
        onClick={(e) => e.stopPropagation()}
      >
        <span aria-hidden="true">🎙</span>
      </button>
    );
  }

  const start = async () => {
    holding.current = true;
    setFailure(null);
    try {
      if (draftScope) {
        const recovered = await retryPendingTranscription(draftScope);
        if (recovered !== null) {
          setAudioRetained(false);
          if (recovered) {
            onText(recovered);
            setState("idle");
          } else {
            setFailure("no_speech");
            onFailure?.("no_speech");
            setState("failed");
          }
          return;
        }
      }
      await startCapture();
      if (!holding.current) {
        await cancelCapture();
        return;
      }
      setState("listening");
    } catch (error) {
      const category = dictationFailure(error);
      setFailure(category);
      onFailure?.(category);
      setState("failed");
    }
  };

  const stop = async () => {
    holding.current = false;
    if (state !== "listening") return;
    setState("busy");
    try {
      const text = await stopAndTranscribe(draftScope);
      if (text) {
        onText(text);
        setAudioRetained(false);
        setFailure(null);
        setState("idle");
      } else {
        setAudioRetained(false);
        setFailure("no_speech");
        onFailure?.("no_speech");
        setState("failed");
      }
    } catch (error) {
      const category = dictationFailure(error);
      if (draftScope) setAudioRetained(true);
      setFailure(category);
      onFailure?.(category);
      setState("failed");
    }
  };

  return (
    <>
      <button
        type="button"
        className={`desk-mic is-${state}`}
        title={failure ? DICTATION_FAILURES[failure].message : label}
        aria-label={
          audioRetained
            ? "Retry retained audio"
            : state === "failed"
              ? `${label} again`
              : label
        }
        onPointerDown={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void start();
        }}
        onPointerUp={(e) => {
          e.stopPropagation();
          void stop();
        }}
        onPointerLeave={() => {
          if (holding.current) void stop();
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <span aria-hidden="true">{state === "busy" ? "…" : "🎙"}</span>
      </button>
      {failure ? (
        <span className="desk-mic-failure" role="status">
          {audioRetained ? "Captured audio is retained locally. " : ""}
          {DICTATION_FAILURES[failure].message}
        </span>
      ) : null}
    </>
  );
}
