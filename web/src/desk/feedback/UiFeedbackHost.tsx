/** One owner feedback bundle: selected part, window image, words and/or audio. */
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { GuideNote, PadGadget } from "../surface";
import { openSurfaceOr } from "../shell";
import { TALK_STOP_EVENT } from "../components/MicButton";
import {
  audioBase64,
  captureWindowPng,
  FEEDBACK_MAX_MS,
  snapshotContext,
  startFeedbackAudio,
  newFeedbackId,
  type FeedbackAudioSession,
  type FeedbackContext,
} from "./capture";
import {
  bindUiFeedbackLauncher,
  hydrateUiFeedback,
  useUiFeedbackState,
  type FeedbackRequest,
} from "./runtime";

type Phase =
  | "idle"
  | "picking"
  | "preparing"
  | "ready"
  | "recording"
  | "saving"
  | "transcribing"
  | "saved"
  | "error";
interface Prepared {
  id: string;
  captured_at: string;
  context: FeedbackContext;
  screenshot_base64: string;
  audio_base64: string | null;
  words?: string;
}
interface Saved {
  success: boolean;
  directory?: string;
  transcript_status?: string;
  transcript?: string;
  transcript_error?: string;
}

export function UiFeedbackHost() {
  const capability = useUiFeedbackState();
  const [phase, setPhase] = useState<Phase>("idle");
  const [part, setPart] = useState<{
    owner: HTMLElement;
    target: HTMLElement | null;
  } | null>(null);
  const [words, setWords] = useState("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState<Saved | null>(null);
  const [request, setRequest] = useState<FeedbackRequest | undefined>();
  const requestRef = useRef<FeedbackRequest | undefined>(undefined);
  const payload = useRef<Prepared | null>(null);
  const audio = useRef<FeedbackAudioSession | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abort = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const saving = useRef(false);
  const stopRef = useRef<() => void>(() => undefined);
  const gestureCleanup = useRef<(() => void) | null>(null);
  useEffect(() => {
    void hydrateUiFeedback();
  }, []);
  const stopAudio = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    const recording = audio.current?.stop();
    audio.current = null;
    if (recording && payload.current)
      payload.current = {
        ...payload.current,
        audio_base64: audioBase64(recording.wav),
      };
    setPhase("ready");
  }, []);
  stopRef.current = stopAudio;
  const cancel = useCallback((wasSaved = false) => {
    generation.current++;
    abort.current?.abort();
    abort.current = null;
    gestureCleanup.current?.();
    gestureCleanup.current = null;
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    audio.current?.cancel();
    audio.current = null;
    payload.current = null;
    saving.current = false;
    const done = requestRef.current?.onFinish;
    requestRef.current = undefined;
    setPhase("idle");
    setWords("");
    setError("");
    setSaved(null);
    setRequest(undefined);
    setPart(null);
    done?.(wasSaved);
  }, []);
  const capture = useCallback((target: Element, event?: PointerEvent) => {
    if (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
      // Picking consumes the whole gesture: it never activates the part.
      const consume = (next: Event) => {
        if (!next.composedPath().includes(target)) return;
        next.preventDefault();
        next.stopImmediatePropagation();
        if (next.type === "click" || next.type === "pointercancel") {
          gestureCleanup.current?.();
          gestureCleanup.current = null;
        }
      };
      const clean = () => {
        document.removeEventListener("pointerup", consume, true);
        document.removeEventListener("click", consume, true);
        document.removeEventListener("pointercancel", consume, true);
      };
      gestureCleanup.current = clean;
      document.addEventListener("pointerup", consume, true);
      document.addEventListener("click", consume, true);
      document.addEventListener("pointercancel", consume, true);
    }
    const owner =
      target.closest<HTMLElement>('[data-layer="window"]') ??
      document.getElementById("desk-next") ??
      document.body;
    const run = ++generation.current;
    const controller = new AbortController();
    abort.current = controller;
    setPart({ owner, target: target as HTMLElement });
    try {
      const context = snapshotContext(target, owner, null);
      context.owner.hub_row = context.desk.windows[owner.id] ?? null;
      if (requestRef.current?.guide) context.guide = requestRef.current.guide;
      // Freeze now, before the guide grows into capture. This includes its
      // original words, note and ring. No hub read or microphone is needed.
      const picture = captureWindowPng(owner, controller.signal);
      setPart({ owner, target: target as HTMLElement });
      setPhase("preparing");
      setError("");
      void picture.then(
        (image) => {
          if (run !== generation.current) return;
          payload.current = {
            id: newFeedbackId(),
            captured_at: new Date().toISOString(),
            context,
            screenshot_base64: image,
            audio_base64: null,
          };
          setPhase("ready");
        },
        (cause) => {
          if (run === generation.current) {
            setError(readableError(cause));
            setPhase("error");
          }
        },
      );
    } catch (cause) {
      setError(readableError(cause));
      setPhase("error");
    }
  }, []);
  useEffect(
    () =>
      bindUiFeedbackLauncher((target, options) => {
        if (!capability.enabled) return;
        cancel();
        requestRef.current = options;
        setRequest(options);
        if (target) capture(target);
        else {
          const owner =
            document.querySelector<HTMLElement>(
              '.desk-window-shell.is-front[data-layer="window"]',
            ) ??
            document.getElementById("desk-next") ??
            document.body;
          setPart({ owner, target: null });
          setPhase("picking");
        }
      }),
    [capability.enabled, cancel, capture],
  );
  useEffect(() => {
    if (phase === "idle") return;
    const key = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !saving.current) {
        event.preventDefault();
        event.stopImmediatePropagation();
        cancel();
      }
    };
    const pick = (event: PointerEvent) => {
      const target = event
        .composedPath()
        .find((item): item is Element => item instanceof Element);
      if (
        phase === "picking" &&
        target &&
        !target.closest("[data-guide-layer],[data-ui-feedback]")
      )
        capture(target, event);
    };
    document.addEventListener("keydown", key, true);
    document.addEventListener("pointerdown", pick, true);
    return () => {
      document.removeEventListener("keydown", key, true);
      document.removeEventListener("pointerdown", pick, true);
    };
  }, [phase, capture, cancel]);
  useEffect(() => {
    const stop = () => {
      if (audio.current) stopRef.current();
    };
    window.addEventListener(TALK_STOP_EVENT, stop);
    return () => {
      window.removeEventListener(TALK_STOP_EVENT, stop);
      generation.current++;
      abort.current?.abort();
      audio.current?.cancel();
      if (timer.current) clearTimeout(timer.current);
      gestureCleanup.current?.();
    };
  }, []);
  const record = async () => {
    const run = generation.current;
    setError("");
    setPhase("preparing");
    try {
      const session = await startFeedbackAudio(abort.current?.signal, {
        local: Boolean(requestRef.current?.guide),
      });
      if (run !== generation.current) {
        session.cancel();
        return;
      }
      audio.current = session;
      setPhase("recording");
      session.onFloorLost(() => {
        if (run === generation.current) {
          stopAudio();
          setError("The microphone stopped. Save these words or record again.");
        }
      });
      timer.current = setTimeout(() => stopRef.current(), FEEDBACK_MAX_MS);
    } catch (cause) {
      if (run === generation.current) {
        setError(readableError(cause));
        setPhase("ready");
      }
    }
  };
  const save = async () => {
    if (saving.current || !payload.current) return;
    if (audio.current) stopAudio();
    if (!words.trim() && !payload.current.audio_base64) {
      setError("Type words or record them.");
      return;
    }
    const next =
      payload.current.words === undefined
        ? { ...payload.current, words: words.trim() }
        : payload.current;
    payload.current = next;
    saving.current = true;
    setPhase("saving");
    setError("");
    const run = generation.current;
    try {
      let result = await apiFetch<Saved>("/api/ui-feedback", {
        method: "POST",
        json: next,
      });
      if (result.success !== true)
        throw new Error(
          "Feedback was not saved on this device. Your words and window image are kept. Retry Save.",
        );
      if (run !== generation.current) return;
      if (next.audio_base64 && result.transcript_status !== "complete") {
        setPhase("transcribing");
        try {
          result = await apiFetch<Saved>(
            `/api/ui-feedback/${next.id}/transcribe`,
            { method: "POST" },
          );
        } catch {
          result = { ...result, transcript_status: "failed" };
        }
      }
      if (run !== generation.current) return;
      saving.current = false;
      if (requestRef.current?.onFinish) {
        cancel(true);
        return;
      }
      setSaved(result);
      setPhase("saved");
      if (result.transcript_status === "failed")
        setError("Transcript not saved. Feedback kept. Retry transcription.");
    } catch (cause) {
      if (run === generation.current) {
        saving.current = false;
        setError(readableError(cause));
        setPhase("error");
      }
    }
  };
  const retryTranscript = async () => {
    if (!payload.current || saving.current) return;
    saving.current = true;
    setPhase("transcribing");
    setError("");
    const run = generation.current;
    try {
      const result = await apiFetch<Saved>(
        `/api/ui-feedback/${payload.current.id}/transcribe`,
        { method: "POST" },
      );
      if (run !== generation.current) return;
      setSaved(result);
      if (result.transcript_status !== "complete")
        setError("Transcript not saved. Feedback kept. Retry transcription.");
    } catch {
      if (run === generation.current)
        setError("Transcript not saved. Feedback kept. Retry transcription.");
    } finally {
      if (run === generation.current) {
        saving.current = false;
        setPhase("saved");
      }
    }
  };
  if (!capability.enabled || phase === "idle" || !part) return null;
  const pending =
    phase === "preparing" || phase === "saving" || phase === "transcribing";
  const state =
    phase === "picking"
      ? "Select a part"
      : phase === "preparing"
        ? "Capturing"
        : phase === "recording"
          ? "Recording"
          : phase === "saving"
            ? "Saving"
            : phase === "transcribing"
              ? "Transcribing"
              : phase === "saved"
                ? "Saved."
                : "";
  const form = (
    <div className="guide-capture" data-ui-feedback="true" data-phase={phase}>
      {phase !== "picking" && phase !== "preparing" && phase !== "saved" ? (
        <PadGadget
          label="Feedback words"
          placeholder="Type what is off, or press Record."
          value={words}
          onChange={(value) => {
            setWords(value);
            if (payload.current && !saving.current)
              delete payload.current.words;
          }}
          disabled={pending}
          mic={false}
        />
      ) : null}
      {state ? (
        <span role="status" className="guide-capture-state">
          {state}
        </span>
      ) : null}
      {error ? (
        <span role="alert" className="guide-capture-state">
          {error}
        </span>
      ) : null}
      {saved?.transcript ? (
        <span className="guide-capture-transcript">{saved.transcript}</span>
      ) : null}
      <div className="guide-bar">
        {phase === "saved" ? (
          <>
            {saved?.transcript_status === "failed" ? (
              <Button
                dense
                variant="secondary"
                onClick={() => void retryTranscript()}
              >
                Retry transcription
              </Button>
            ) : null}
            {saved?.transcript_status === "failed" &&
            /unavailable|not_ready|route_member_missing|not_admitted|binding_/.test(
              saved.transcript_error ?? "",
            ) ? (
              <Button
                dense
                variant="secondary"
                onClick={() =>
                  openSurfaceOr("configure-settings", "/settings", "speak")
                }
              >
                Set up speech
              </Button>
            ) : null}
            {saved?.directory ? (
              <Button
                dense
                variant="secondary"
                onClick={() =>
                  void navigator.clipboard?.writeText(saved.directory!)
                }
              >
                Copy path
              </Button>
            ) : null}
            <Button
              dense
              variant="secondary"
              onClick={() => {
                const owner = part.owner;
                cancel();
                setPart({ owner, target: null });
                setPhase("picking");
              }}
            >
              New feedback
            </Button>
            <Button dense variant="primary" onClick={() => cancel(true)}>
              Done
            </Button>
          </>
        ) : (
          <>
            {!pending && phase !== "picking" && payload.current ? (
              <>
                <Button
                  dense
                  variant="secondary"
                  onClick={() => (audio.current ? stopAudio() : void record())}
                >
                  {phase === "recording" ? "Stop" : "Record"}
                </Button>
                <Button
                  dense
                  variant="primary"
                  onClick={() => void save()}
                  disabled={
                    !words.trim() &&
                    !payload.current?.audio_base64 &&
                    phase !== "recording"
                  }
                >
                  Save
                </Button>
              </>
            ) : null}
            <Button
              dense
              variant="secondary"
              disabled={saving.current}
              onClick={() => cancel()}
            >
              Cancel
            </Button>
          </>
        )}
      </div>
    </div>
  );
  if (request?.mount) return createPortal(form, request.mount);
  return (
    <GuideNote
      owner={part.owner}
      target={part.target === part.owner ? null : part.target}
      words={
        phase === "picking" ? "Select the part to report." : "Give feedback"
      }
      onStop={() => cancel()}
      focusNext={false}
      actions={<></>}
    >
      {form}
    </GuideNote>
  );
}
