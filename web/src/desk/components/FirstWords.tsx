import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { PadGadget } from "../surface/gadgets";
import { SurfaceState } from "../surface/Surface";
import { apiFetch, readableError } from "../../lib/api";
import { openSurfaceOr } from "../shell";
import {
  DICTATION_FAILURES,
  dictationFailure,
  type DictationFailure,
} from "../../lib/dictationRecovery";
import { useDurableDraft } from "../../lib/durableDraft";
import { loadPendingVoice } from "../../lib/pendingVoice";
import {
  retryPendingTranscription,
  speakToFillSupported,
} from "../../lib/speakToFill";
import {
  micStreamSupported,
  startStreamSession,
  type StreamSession,
} from "../../lib/micStreamSession";
import { FirstValueTracker } from "../firstValue";

type CaptureState =
  "idle" | "listening" | "transcribing" | "success" | "failed";
const micUnsupportedMessage =
  "Microphone capture is unavailable in this browser. No audio was recorded. Type below or open Setup.";
export function FirstWords({
  onDismiss,
  embedded = false,
}: {
  onDismiss?: () => void;
  embedded?: boolean;
}) {
  const {
    value: text,
    setDraft: setText,
    recovered,
    clearPersisted,
  } = useDurableDraft("first-words");
  const [state, setState] = useState<CaptureState>("idle");
  const [failure, setFailure] = useState<DictationFailure | null>(null);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const tracker = useRef<FirstValueTracker | null>(null);
  if (!tracker.current) tracker.current = new FirstValueTracker();
  const sessionRef = useRef<StreamSession | null>(null);
  const startingRef = useRef(false);
  const draftEdited = useRef(false);

  useEffect(() => {
    let mounted = true;
    void loadPendingVoice("first-words").then((audio) => {
      if (!mounted || !audio) return;
      setFailure("transcription_failed");
      setState("failed");
      setMessage("Captured audio was recovered on this browser for Retry.");
    });
    return () => {
      mounted = false;
    };
  }, []);

  const startAttempt = async () => {
    await tracker.current?.start("this_machine");
  };

  const finishAttempt = async (
    outcome: "success" | "failure",
    category?: DictationFailure,
  ) => {
    await tracker.current?.finish(outcome, category);
  };

  const fail = (category: DictationFailure) => {
    setFailure(category);
    setState("failed");
    void finishAttempt("failure", category).catch(() => undefined);
  };

  const acceptTranscript = async (result: string) => {
    const clean = result.trim();
    if (!clean) {
      fail("no_speech");
      return;
    }
    setText(clean);
    setState("success");
    setFailure(null);
    void tracker.current?.event("transcript_received");
    await finishAttempt("success").catch(() => undefined);
  };

  const begin = async () => {
    if (startingRef.current || state === "transcribing") return;
    startingRef.current = true;
    setFailure(null);
    setMessage("");
    try {
      await startAttempt();
      const recovered = await retryPendingTranscription("first-words");
      if (recovered !== null) {
        await acceptTranscript(recovered);
        return;
      }
      const session = await startStreamSession(() => {});
      sessionRef.current = session;
      setState("listening");
      void tracker.current?.event("capture_started");
    } catch (error) {
      fail(dictationFailure(error));
    } finally {
      startingRef.current = false;
    }
  };

  const stop = async () => {
    const session = sessionRef.current;
    if (!session) return;
    sessionRef.current = null;
    setState("transcribing");
    void tracker.current?.event("capture_released");
    try {
      const result = await session.stop();
      await acceptTranscript(result);
    } catch (error) {
      fail(dictationFailure(error));
      setMessage("Captured audio is retained on this browser for Retry.");
    }
  };

  const toggle = () => {
    if (state === "listening") void stop();
    else if (state === "idle" || state === "failed") void begin();
  };

  const dismiss = async (disposition: "dismissed" | "needs_help") => {
    setSaving(true);
    try {
      await apiFetch("/api/setup/onboarding", {
        method: "PUT",
        json: { disposition },
      });
      onDismiss?.();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setSaving(false);
    }
  };

  const keep = async () => {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await apiFetch("/api/notes", {
        method: "POST",
        json: {
          title: "First dictation",
          body_markdown: text,
          tags: ["dictation"],
        },
      });
      clearPersisted();
      setMessage("Kept as a note on your Desk.");
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setSaving(false);
    }
  };

  const supported = speakToFillSupported() || micStreamSupported();
  const failureContract = failure ? DICTATION_FAILURES[failure] : null;
  const Heading = embedded ? "h2" : "h1";
  return (
    <section className="desk-first-words" aria-labelledby="first-words-title">
      <span className="surface-eyebrow">Voice typing</span>
      <Heading id="first-words-title">Dictate one sentence</Heading>
      <p>Click to speak. Your words stay editable here before you use them.</p>
      <button
        type="button"
        className={`desk-first-talk is-${state}`}
        disabled={
          !supported ||
          state === "transcribing" ||
          Boolean(failureContract && !failureContract.retry)
        }
        aria-label={
          state === "listening"
            ? "Stop listening"
            : state === "failed" && failureContract?.retry
              ? "Click to retry dictation"
              : state === "failed"
                ? "Dictation unavailable until setup is fixed"
                : "Click to dictate"
        }
        onClick={(event) => {
          event.preventDefault();
          toggle();
        }}
      >
        {state === "listening"
          ? "Listening… click to stop"
          : state === "transcribing"
            ? "Transcribing…"
            : state === "failed" && failureContract?.retry
              ? "Click to retry"
              : state === "failed"
                ? "Open Setup to continue"
                : "Click to speak"}
      </button>
      {!supported ? <SurfaceState error={micUnsupportedMessage} /> : null}
      {failureContract ? (
        <SurfaceState
          error={failureContract.message}
          onRetry={failureContract.retry ? toggle : undefined}
        />
      ) : recovered ? (
        <p className="surface-receipt-line" role="status">
          Recovered your local draft after relaunch. It remains editable below.
        </p>
      ) : null}
      <PadGadget
        label="Your dictated text"
        rows={4}
        value={text}
        mic={false}
        onChange={(next) => {
          setText(next);
          if (!draftEdited.current) {
            draftEdited.current = true;
            void tracker.current?.event("draft_edited");
          }
        }}
        placeholder="Transcribed text appears here. You can also type."
      />
      {message ? (
        <p className="surface-receipt-line" role="status">
          {message}
        </p>
      ) : null}
      <div className="button-row">
        <Button
          disabled={!text.trim()}
          onClick={() => {
            void tracker.current?.event("copy_selected");
            void navigator.clipboard.writeText(text);
          }}
        >
          Copy
        </Button>
        <Button
          disabled={!text.trim()}
          loading={saving}
          onClick={() => {
            void tracker.current?.event("keep_selected");
            void keep();
          }}
        >
          Keep as Note
        </Button>
        {!failureContract || failureContract.setup ? (
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => {
              void tracker.current?.event("setup_selected");
              openSurfaceOr("configure-setup", "/setup");
            }}
          >
            Setup
          </button>
        ) : null}
      </div>
      {state === "success" ? (
        <div className="desk-first-success">
          <strong>Dictation is ready on this machine.</strong>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => openSurfaceOr("configure-runs-on", "/profiles")}
          >
            Configure rewrite destination
          </button>
        </div>
      ) : null}
      <div className="button-row">
        <Button
          variant="ghost"
          loading={saving}
          onClick={() => {
            void tracker.current?.event("continue_later_selected");
            void dismiss("dismissed");
          }}
        >
          Continue later
        </Button>
        {failure ? (
          <Button
            variant="ghost"
            loading={saving}
            onClick={() => void dismiss("needs_help")}
          >
            I need help
          </Button>
        ) : null}
      </div>
    </section>
  );
}
