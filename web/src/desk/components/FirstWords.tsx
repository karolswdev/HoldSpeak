import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { PadGadget } from "../surface/gadgets";
import { SurfaceState } from "../surface/Surface";
import { apiFetch, readableError } from "../../lib/api";
import { openSurfaceOr } from "../shell";
import {
  DICTATION_FAILURES,
  dictationFailure,
  streamFailure,
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
import { useDesk } from "../store";
import {
  clearFirstValueKeepNoteId,
  firstValueKeepNoteId,
  FirstValueTracker,
  stageFirstValueNoteOpen,
} from "../firstValue";

type CaptureState =
  "idle" | "listening" | "transcribing" | "success" | "failed";
const micUnsupportedMessage =
  "Microphone capture is unavailable in this browser. No audio was recorded. Type below instead.";
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
  const [recoveredAudioAvailable, setRecoveredAudioAvailable] = useState(false);
  const [retentionPending, setRetentionPending] = useState(false);
  const [saving, setSaving] = useState(false);
  const [keptNoteId, setKeptNoteId] = useState("");
  const tracker = useRef<FirstValueTracker | null>(null);
  if (!tracker.current) tracker.current = new FirstValueTracker();
  const sessionRef = useRef<StreamSession | null>(null);
  const streamFailureRef = useRef<DictationFailure | null>(null);
  const startingRef = useRef(false);
  const captureStartedRef = useRef(false);
  const draftEdited = useRef(false);
  const actionRef = useRef<"keep" | "dismiss" | null>(null);
  const refreshDesk = useDesk((desk) => desk.refresh);

  useEffect(() => {
    let mounted = true;
    void loadPendingVoice("first-words").then((audio) => {
      // Do not let an asynchronous startup recovery replace a capture the
      // owner began while IndexedDB was answering.
      if (!mounted || !audio || captureStartedRef.current) return;
      setRecoveredAudioAvailable(true);
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

  const receiptForRetainedAudio = (session: StreamSession) => {
    setRetentionPending(true);
    void session
      .retained()
      .then((retained) => {
        if (retained) {
          setRecoveredAudioAvailable(true);
          setMessage(
            "Captured audio is retained on this browser. Retry to transcribe it without recording again.",
          );
        }
      })
      .catch(() => undefined)
      .finally(() => {
        setRetentionPending(false);
      });
  };

  const acceptTranscript = async (result: string) => {
    const clean = result.trim();
    if (!clean) {
      fail("no_speech");
      return;
    }
    setText(clean);
    setRecoveredAudioAvailable(false);
    setState("success");
    setFailure(null);
    void tracker.current?.event("transcript_received");
  };

  const begin = async () => {
    if (startingRef.current || state === "transcribing") return;
    startingRef.current = true;
    captureStartedRef.current = true;
    setFailure(null);
    setMessage("");
    streamFailureRef.current = null;
    try {
      await startAttempt();
      const recovered = await retryPendingTranscription("first-words");
      if (recovered !== null) {
        setRecoveredAudioAvailable(false);
        await acceptTranscript(recovered);
        return;
      }
      setRecoveredAudioAvailable(false);
      const session = await startStreamSession(
        (event) => {
          if (event.type !== "error") return;
          const category = streamFailure(event);
          streamFailureRef.current = category;
          setRetentionPending(true);
          fail(category);
          const active = sessionRef.current;
          if (active) {
            sessionRef.current = null;
            receiptForRetainedAudio(active);
            active.cancel();
          }
        },
        { retainScope: "first-words" },
      );
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
      if (streamFailureRef.current) {
        receiptForRetainedAudio(session);
        return;
      }
      await acceptTranscript(result);
    } catch (error) {
      fail(dictationFailure(error));
      receiptForRetainedAudio(session);
    }
  };

  const toggle = () => {
    if (state === "listening") void stop();
    else if (state === "idle" || state === "failed") void begin();
  };

  const dismiss = async (disposition: "dismissed" | "needs_help") => {
    if (actionRef.current) return;
    actionRef.current = "dismiss";
    setSaving(true);
    if (disposition === "dismissed") {
      void tracker.current?.event("continue_later_selected");
    }
    try {
      await apiFetch("/api/setup/onboarding", {
        method: "PUT",
        json: { disposition },
      });
      onDismiss?.();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      actionRef.current = null;
      setSaving(false);
    }
  };

  const keep = async () => {
    if (!text.trim() || keptNoteId || actionRef.current) return;
    actionRef.current = "keep";
    setSaving(true);
    void tracker.current?.event("keep_selected");
    const noteId = firstValueKeepNoteId();
    let confirmed = false;
    try {
      const result = await apiFetch<{ note?: { id?: string } }>("/api/notes", {
        method: "POST",
        json: {
          id: noteId,
          title: "First dictation",
          body_markdown: text,
          tags: ["dictation"],
        },
      });
      confirmed = true;
      const createdId = String(result.note?.id || noteId);
      await refreshDesk();
      stageFirstValueNoteOpen(`note:${createdId}`);
      clearPersisted();
      clearFirstValueKeepNoteId();
      setKeptNoteId(createdId);
      setMessage("Kept as a note. It will open when your Desk is ready.");
    } catch (error) {
      setMessage(
        confirmed
          ? "Kept as a note, but the Desk could not refresh. Retry Keep as Note to open it."
          : `Could not keep as a note. ${readableError(error)} Retry Keep as Note.`,
      );
    } finally {
      actionRef.current = null;
      setSaving(false);
    }
  };

  const copy = async () => {
    if (!text.trim() || actionRef.current) return;
    // This is an intent metric, not a clipboard-content metric: refusals are
    // still a real owner attempt and no phrase ever enters the event payload.
    void tracker.current?.event("copy_selected");
    try {
      await navigator.clipboard.writeText(text);
      setMessage("Copied to your clipboard.");
    } catch {
      setMessage("Clipboard access was blocked. Select your text and copy it manually.");
    }
  };

  const supported = speakToFillSupported() || micStreamSupported();
  const canRetryRetainedAudio = recoveredAudioAvailable && state === "failed";
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
          (!supported && !canRetryRetainedAudio) ||
          state === "transcribing" ||
          retentionPending ||
          Boolean(failureContract && !failureContract.retry)
        }
        aria-label={
          state === "listening"
            ? "Stop listening"
            : retentionPending
              ? "Saving audio for Retry"
            : state === "failed" && failureContract?.retry
              ? "Click to retry dictation"
              : state === "failed"
                ? "Voice typing unavailable"
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
            : retentionPending
              ? "Saving audio for Retry…"
            : state === "failed" && failureContract?.retry
              ? "Click to retry"
              : state === "failed"
                ? "Voice typing unavailable"
                : "Click to speak"}
      </button>
      {!supported && state !== "success" && !recoveredAudioAvailable ? (
        <SurfaceState error={micUnsupportedMessage} />
      ) : null}
      {failureContract ? (
        <SurfaceState
          error={failureContract.message}
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
          disabled={!text.trim() || saving}
          onClick={() => {
            void copy();
          }}
        >
          Copy
        </Button>
        <Button
          disabled={!text.trim() || Boolean(keptNoteId)}
          loading={saving}
          onClick={() => {
            void keep();
          }}
        >
          Keep as Note
        </Button>
        {failureContract?.setup ? (
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
      <div className="button-row">
        <Button
          variant="ghost"
          loading={saving}
          disabled={saving}
          onClick={() => {
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
