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
  onDismiss?: () => void | Promise<void>;
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
  const [handoffPending, setHandoffPending] = useState(false);
  const [handoffRunning, setHandoffRunning] = useState(false);
  const tracker = useRef<FirstValueTracker | null>(null);
  if (!tracker.current) tracker.current = new FirstValueTracker();
  const sessionRef = useRef<StreamSession | null>(null);
  const streamFailureRef = useRef<DictationFailure | null>(null);
  const startingRef = useRef(false);
  const captureStartedRef = useRef(false);
  const draftEdited = useRef(false);
  const actionRef = useRef<"keep" | "dismiss" | "copy" | null>(null);
  const transcriptReceivedRef = useRef(false);
  const handoffRef = useRef<{
    disposition: "completed" | "dismissed" | "needs_help";
    finishSuccess: boolean;
    noteId?: string;
  } | null>(null);
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
    transcriptReceivedRef.current = true;
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

  const completeHandoff = async () => {
    const handoff = handoffRef.current;
    if (!handoff || actionRef.current) return;
    actionRef.current = "dismiss";
    setHandoffRunning(true);
    setSaving(true);
    try {
      await apiFetch("/api/desk/seed", { method: "POST" });
      await refreshDesk();
      if (handoff.finishSuccess) await finishAttempt("success").catch(() => undefined);
      await apiFetch("/api/setup/onboarding", {
        method: "PUT",
        json: { disposition: handoff.disposition },
      });
      await (onDismiss ? onDismiss() : refreshDesk());
      // Once a note has custody of the text, there must not be a hidden
      // second copy in the local first-words draft.  Keep it through every
      // failed handoff, then clear only after the final authoritative refresh.
      if (handoff.disposition === "completed" || handoff.noteId) {
        clearPersisted();
      }
      if (handoff.noteId) {
        clearFirstValueKeepNoteId();
      }
      handoffRef.current = null;
      setHandoffPending(false);
    } catch (error) {
      setHandoffPending(true);
      setMessage(
        `Your sentence and Desk changes are still here. ${readableError(error)} Retry finishing your Desk.`,
      );
    } finally {
      actionRef.current = null;
      setSaving(false);
      setHandoffRunning(false);
    }
  };

  const beginHandoff = (
    disposition: "completed" | "dismissed" | "needs_help",
    { finishSuccess = false, noteId }: { finishSuccess?: boolean; noteId?: string } = {},
  ) => {
    if (actionRef.current || handoffRef.current) return;
    handoffRef.current = { disposition, finishSuccess, noteId };
    setHandoffRunning(true);
    void completeHandoff();
  };

  const dismiss = async (disposition: "dismissed" | "needs_help") => {
    if (disposition === "dismissed") void tracker.current?.event("continue_later_selected");
    if (actionRef.current || handoffRef.current) return;
    let noteId = keptNoteId;
    if (text.trim() && !noteId) {
      actionRef.current = "dismiss";
      setSaving(true);
      try {
        noteId = firstValueKeepNoteId();
        await apiFetch("/api/notes", {
          method: "POST",
          json: { id: noteId, title: "First dictation", body_markdown: text, tags: ["dictation"] },
        });
        stageFirstValueNoteOpen(`note:${noteId}`);
        setKeptNoteId(noteId);
      } catch (error) {
        setMessage(`Your text is still here. ${readableError(error)} Retry Continue later.`);
        actionRef.current = null;
        setSaving(false);
        return;
      }
      actionRef.current = null;
      setSaving(false);
    }
    beginHandoff(disposition, { noteId: noteId || undefined, finishSuccess: transcriptReceivedRef.current });
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
      stageFirstValueNoteOpen(`note:${createdId}`);
      setKeptNoteId(createdId);
      if (!transcriptReceivedRef.current) {
        setMessage("Kept as a note. Continue later when you are ready for your Desk.");
        return;
      }
      handoffRef.current = {
        disposition: "completed",
        finishSuccess: transcriptReceivedRef.current,
        noteId: createdId,
      };
      actionRef.current = null;
      void completeHandoff();
      return;
    } catch (error) {
      setMessage(
        confirmed
          ? "Kept as a note, but the Desk could not refresh. Retry Keep as Note to open it."
          : `Could not keep as a note. ${readableError(error)} Retry Keep as Note.`,
      );
    } finally {
      if (actionRef.current === "keep") actionRef.current = null;
      setSaving(false);
    }
  };

  const copy = async () => {
    if (!text.trim() || actionRef.current) return;
    actionRef.current = "copy";
    // This is an intent metric, not a clipboard-content metric: refusals are
    // still a real owner attempt and no phrase ever enters the event payload.
    void tracker.current?.event("copy_selected");
    try {
      await navigator.clipboard.writeText(text);
      if (transcriptReceivedRef.current) {
        handoffRef.current = { disposition: "completed", finishSuccess: true };
        actionRef.current = null;
        void completeHandoff();
      } else {
        setMessage("Copied to your clipboard.");
      }
    } catch {
      setMessage("Clipboard access was blocked. Select your text and copy it manually.");
    } finally {
      if (actionRef.current === "copy") actionRef.current = null;
    }
  };

  const supported = speakToFillSupported() || micStreamSupported();
  const canRetryRetainedAudio = recoveredAudioAvailable && state === "failed";
  const failureContract = failure ? DICTATION_FAILURES[failure] : null;
  const needsDraftCustody = Boolean(text.trim() && !keptNoteId);
  const Heading = embedded ? "h2" : "h1";
  return (
    <section className="desk-first-words" aria-labelledby="first-words-title">
      <span className="surface-eyebrow">Voice typing</span>
      <Heading id="first-words-title">Dictate one sentence</Heading>
      <p>Tap to speak, edit here, then use</p>
      <button
        type="button"
        className={`desk-first-talk is-${state}`}
        disabled={
          (!supported && !canRetryRetainedAudio) ||
          state === "transcribing" ||
          handoffRunning ||
          saving ||
          handoffPending ||
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
      {handoffPending ? (
        <Button
          onClick={() => void completeHandoff()}
          loading={saving}
          disabled={saving || handoffRunning}
        >
          Retry finishing your Desk
        </Button>
      ) : null}
      <div className="button-row">
        <Button
          disabled={!text.trim() || saving || handoffPending || handoffRunning}
          onClick={() => {
            void copy();
          }}
        >
          Copy
        </Button>
        <Button
          disabled={!text.trim() || Boolean(keptNoteId) || handoffPending || handoffRunning}
          loading={saving}
          onClick={() => {
            void keep();
          }}
        >
          Keep as Note
        </Button>
        {failureContract?.setup && !handoffPending && !saving && !handoffRunning ? (
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => {
              void tracker.current?.event("setup_selected");
              // HS-169-03 N-1: open the one-screen Door, not the old setup wizard.
              openSurfaceOr("project-setup", "/");
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
          disabled={saving || handoffPending || handoffRunning}
          onClick={() => {
            void dismiss("dismissed");
          }}
        >
          {needsDraftCustody ? "Save draft & continue" : "Continue later"}
        </Button>
        {failure ? (
          <Button
            variant="ghost"
            loading={saving}
            disabled={saving || handoffPending || handoffRunning}
            onClick={() => void dismiss("needs_help")}
          >
            {needsDraftCustody ? "Save draft & get help" : "I need help"}
          </Button>
        ) : null}
      </div>
    </section>
  );
}
