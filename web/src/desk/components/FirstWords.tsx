import { useEffect, useRef, useState } from "react";
import {
  Button,
  InlineMessage,
  TextArea,
} from "../../components/signal/Signal";
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
  cancelCapture,
  retryPendingTranscription,
  speakToFillSupported,
  startCapture,
  stopAndTranscribe,
} from "../../lib/speakToFill";
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
  const listening = useRef(false);
  const holding = useRef(false);
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
    if (listening.current || state === "transcribing") return;
    holding.current = true;
    setFailure(null);
    setMessage("");
    try {
      await startAttempt();
      const recovered = await retryPendingTranscription("first-words");
      if (recovered !== null) {
        await acceptTranscript(recovered);
        return;
      }
      await startCapture();
      if (!holding.current) {
        await cancelCapture();
        fail("unknown");
        return;
      }
      listening.current = true;
      setState("listening");
      void tracker.current?.event("capture_started");
    } catch (error) {
      fail(dictationFailure(error));
    }
  };

  const stop = async () => {
    holding.current = false;
    if (!listening.current) return;
    listening.current = false;
    setState("transcribing");
    void tracker.current?.event("capture_released");
    try {
      await acceptTranscript(await stopAndTranscribe("first-words"));
    } catch (error) {
      fail(dictationFailure(error));
      setMessage("Captured audio is retained on this browser for Retry.");
    }
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

  const supported = speakToFillSupported();
  const failureContract = failure ? DICTATION_FAILURES[failure] : null;
  const Heading = embedded ? "h2" : "h1";
  return (
    <section className="desk-first-words" aria-labelledby="first-words-title">
      <span className="signal-eyebrow">Dictation</span>
      <Heading id="first-words-title">Dictate one sentence</Heading>
      <p>Hold to speak. Your words stay editable here before you use them.</p>
      <button
        type="button"
        className={`desk-first-talk is-${state}`}
        disabled={
          !supported ||
          state === "transcribing" ||
          Boolean(failureContract && !failureContract.retry)
        }
        aria-label={
          state === "failed" && failureContract?.retry
            ? "Hold to retry dictation"
            : state === "failed"
              ? "Dictation unavailable until setup is fixed"
              : "Hold to dictate"
        }
        onPointerDown={(event) => {
          event.preventDefault();
          void begin();
        }}
        onPointerUp={() => void stop()}
        onPointerLeave={() => {
          if (holding.current) void stop();
        }}
        onKeyDown={(event) => {
          if ((event.key === " " || event.key === "Enter") && !event.repeat) {
            event.preventDefault();
            void begin();
          }
        }}
        onKeyUp={(event) => {
          if (event.key === " " || event.key === "Enter") {
            event.preventDefault();
            void stop();
          }
        }}
      >
        {state === "listening"
          ? "Listening… release when done"
          : state === "transcribing"
            ? "Transcribing…"
            : state === "failed" && failureContract?.retry
              ? "Hold to retry"
              : state === "failed"
                ? "Open Setup to continue"
                : "Hold to speak"}
      </button>
      {!supported ? (
        <InlineMessage tone="error">{micUnsupportedMessage}</InlineMessage>
      ) : null}
      {failureContract ? (
        <InlineMessage tone="error">{failureContract.message}</InlineMessage>
      ) : recovered ? (
        <InlineMessage tone="info">
          Recovered your local draft after relaunch. It remains editable below.
        </InlineMessage>
      ) : null}
      <TextArea
        aria-label="Your dictated text"
        rows={4}
        value={text}
        onChange={(event) => {
          setText(event.target.value);
          if (!draftEdited.current) {
            draftEdited.current = true;
            void tracker.current?.event("draft_edited");
          }
        }}
        placeholder="Transcribed text appears here. You can also type."
      />
      {message ? <InlineMessage tone="info">{message}</InlineMessage> : null}
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
