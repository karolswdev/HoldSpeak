import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { EgressChip } from "../surface/gadgets";
import { TALK_STOP_EVENT } from "../components/MicButton";
import {
  audioBase64,
  canonicalWindowRow,
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
} from "./runtime";
import "./feedback.css";

type Phase = "idle" | "picking" | "preparing" | "recording" | "saving" | "saved" | "error";

interface PreparedFeedback {
  id: string;
  capturedAt: string;
  context: FeedbackContext;
  screenshotBase64: string;
  audioBase64: string | null;
  audioDurationMs: number;
  directory?: string;
  files?: string[];
}

function targetElement(event: PointerEvent): Element | null {
  const first = event.composedPath().find((value): value is Element => value instanceof Element);
  return first ?? (event.target instanceof Element ? event.target : null);
}

function ownerRoot(target: Element): Element {
  return target.closest("[data-layer='window']") ?? document.getElementById("desk-next") ?? document.body;
}

function errorText(error: unknown): string {
  return readableError(error) || (error instanceof Error ? error.message : "Capture stopped. The window is unchanged. Select an element.");
}

export function UiFeedbackHost() {
  const capability = useUiFeedbackState();
  const [phase, setPhase] = useState<Phase>("idle");
  const [prepared, setPrepared] = useState<PreparedFeedback | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [audioReady, setAudioReady] = useState(false);
  const generation = useRef(0);
  const preparationAbort = useRef<AbortController | null>(null);
  const audio = useRef<FeedbackAudioSession | null>(null);
  const autoStop = useRef<ReturnType<typeof setTimeout> | null>(null);
  const payload = useRef<PreparedFeedback | null>(null);
  const gestureCleanup = useRef<(() => void) | null>(null);
  const stopAndSaveRef = useRef<() => Promise<void>>(async () => undefined);

  useEffect(() => {
    void hydrateUiFeedback();
  }, []);

  const clearTimer = useCallback(() => {
    if (autoStop.current !== null) clearTimeout(autoStop.current);
    autoStop.current = null;
  }, []);

  const cancelCurrent = useCallback(() => {
    generation.current += 1;
    preparationAbort.current?.abort();
    preparationAbort.current = null;
    gestureCleanup.current?.();
    gestureCleanup.current = null;
    clearTimer();
    audio.current?.cancel();
    audio.current = null;
    setAudioReady(false);
    payload.current = null;
    setPrepared(null);
    setError("");
    setStatus("");
    setPhase("idle");
  }, [clearTimer]);

  const beginPicking = useCallback(() => {
    if (!capability.enabled) return;
    cancelCurrent();
    setPhase("picking");
    setStatus("Select an element");
  }, [cancelCurrent, capability.enabled]);

  useEffect(() => bindUiFeedbackLauncher(beginPicking), [beginPicking]);

  useEffect(() => {
    if (phase !== "picking") return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      cancelCurrent();
    };
    const onPointer = (event: PointerEvent) => {
      const target = targetElement(event);
      if (!target || target.closest("[data-ui-feedback]")) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      const gesturePointer = event.pointerId;
      const inGesture = (candidate: Event): boolean => {
        if (candidate.type.startsWith("pointer") && (candidate as PointerEvent).pointerId !== gesturePointer) return false;
        return candidate.composedPath().includes(target) || candidate.target === target;
      };
      const consumeGesture = (candidate: Event) => {
        if (!inGesture(candidate)) return;
        candidate.preventDefault();
        candidate.stopImmediatePropagation();
        if (candidate.type === "click" || candidate.type === "change" || candidate.type === "pointercancel") {
          gestureCleanup.current?.();
          gestureCleanup.current = null;
        }
      };
      const cleanupGesture = () => {
        document.removeEventListener("pointerup", consumeGesture, true);
        document.removeEventListener("pointercancel", consumeGesture, true);
        document.removeEventListener("click", consumeGesture, true);
        document.removeEventListener("change", consumeGesture, true);
      };
      gestureCleanup.current?.();
      gestureCleanup.current = cleanupGesture;
      document.addEventListener("pointerup", consumeGesture, true);
      document.addEventListener("pointercancel", consumeGesture, true);
      document.addEventListener("click", consumeGesture, true);
      document.addEventListener("change", consumeGesture, true);
      const current = ++generation.current;
      const root = ownerRoot(target);
      const ownerId = root.getAttribute("data-layer") === "window" ? root.id || null : null;
      let context: FeedbackContext;
      try {
        context = snapshotContext(target, root, null);
      } catch (cause) {
        cleanupGesture();
        gestureCleanup.current = null;
        setError(errorText(cause));
        setStatus("");
        setPhase("error");
        return;
      }
      const id = newFeedbackId();
      const capturedAt = new Date().toISOString();
      const controller = new AbortController();
      preparationAbort.current = controller;
      setPhase("preparing");
      setStatus("Capturing");
      void (async () => {
        const hubRowTask = canonicalWindowRow(ownerId);
        const image = await captureWindowPng(root);
        if (current !== generation.current || controller.signal.aborted) {
          return;
        }
        if (typeof image !== "string") {
          setError("Window image failed. The window is unchanged. Select an element.");
          setStatus("");
          setPhase("error");
          return;
        }
        const hubRow = await hubRowTask;
        if (current !== generation.current || controller.signal.aborted) return;
        context.owner.hub_row = hubRow;
        const next: PreparedFeedback = {
          id,
          capturedAt,
          context,
          screenshotBase64: image,
          audioBase64: null,
          audioDurationMs: 0,
        };
        payload.current = next;
        setPrepared(next);
        setAudioReady(false);
        setStatus("Starting recording");
        setPhase("preparing");
        let audioSession: FeedbackAudioSession;
        try {
          audioSession = await startFeedbackAudio(controller.signal);
        } catch (cause) {
          if (current !== generation.current || controller.signal.aborted) return;
          preparationAbort.current = null;
          setError(errorText(cause));
          setStatus("");
          setPhase("error");
          return;
        }
        if (current !== generation.current || controller.signal.aborted) {
          audioSession.cancel();
          return;
        }
        preparationAbort.current = null;
        audio.current = audioSession;
        setAudioReady(true);
        setStatus("");
        setPhase("recording");
        audio.current.onFloorLost(() => {
          if (current !== generation.current) return;
          setError("The microphone stopped. Save this recording.");
          setStatus("");
        });
        autoStop.current = setTimeout(() => void stopAndSaveRef.current(), FEEDBACK_MAX_MS);
      })().catch((cause) => {
        if (current !== generation.current) return;
        audio.current?.cancel();
        preparationAbort.current = null;
        setAudioReady(false);
        setError(errorText(cause));
        setStatus("");
        setPhase("error");
      });
    };
    document.addEventListener("keydown", onKey, true);
    document.addEventListener("pointerdown", onPointer, true);
    return () => {
      document.removeEventListener("keydown", onKey, true);
      document.removeEventListener("pointerdown", onPointer, true);
    };
  }, [cancelCurrent, phase]);

  const stopAndSave = useCallback(async () => {
    const current = payload.current;
    const saveGeneration = generation.current;
    if (!current || phase === "saving" || phase === "saved") return;
    clearTimer();
    let next = current;
    if (!current.audioBase64) {
      const captured = audio.current?.stop() ?? null;
      if (!captured) {
        setError("No audio was captured. Try again.");
        setPhase("error");
        return;
      }
      next = { ...current, audioBase64: audioBase64(captured.wav), audioDurationMs: captured.durationMs };
    }
    audio.current = null;
    setAudioReady(false);
    payload.current = next;
    setPrepared(next);
    setPhase("saving");
    setError("");
    try {
      const result = await apiFetch<{ success?: boolean; id?: string; directory?: string; files?: string[] }>("/api/ui-feedback", {
        method: "POST",
        json: {
          id: next.id,
          captured_at: next.capturedAt,
          context: next.context,
          audio_base64: next.audioBase64,
          screenshot_base64: next.screenshotBase64,
        },
      });
      if (result.success !== true) throw new Error("Feedback was not saved on this device. Your recording and window image are kept. Retry Save.");
      if (saveGeneration !== generation.current || payload.current?.id !== next.id) return;
      const saved = { ...next, directory: result.directory, files: result.files };
      payload.current = saved;
      setPrepared(saved);
      setStatus(result.directory ?? next.id);
      setPhase("saved");
    } catch (cause) {
      if (saveGeneration !== generation.current || payload.current?.id !== next.id) return;
      setError(errorText(cause));
      setStatus("");
      setPhase("error");
    }
  }, [clearTimer, phase]);

  stopAndSaveRef.current = stopAndSave;

  useEffect(() => {
    const stopAsked = () => {
      if (audio.current) void stopAndSaveRef.current();
    };
    window.addEventListener(TALK_STOP_EVENT, stopAsked);
    return () => window.removeEventListener(TALK_STOP_EVENT, stopAsked);
  }, []);

  useEffect(() => () => {
    generation.current += 1;
    gestureCleanup.current?.();
    clearTimer();
    preparationAbort.current?.abort();
    audio.current?.cancel();
  }, [clearTimer]);

  if (!capability.enabled || phase === "idle") return null;
  const selectedName = prepared?.context.owner.name ?? "Desk";
  const copyPath = () => {
    if (prepared?.directory) void navigator.clipboard?.writeText(prepared.directory);
  };
  const retry = () => {
    if (prepared?.audioBase64) {
      void stopAndSave();
      return;
    }
    beginPicking();
  };
  return (
    <aside className="desk-next hs-feedback-strip" data-ui-feedback="true" role="status" aria-live="polite">
      <div className="hs-feedback-identity">
        <span className="hs-feedback-caption">{phase === "picking" ? "SELECT" : phase === "preparing" ? "CAPTURING" : phase === "recording" ? "RECORDING" : phase === "saving" ? "SAVING" : phase === "saved" ? "SAVED" : "RETRY"}</span>
        <strong>{phase === "picking" ? status : selectedName}</strong>
        {error ? <span className="hs-feedback-error">{error}</span> : null}
      </div>
      <EgressChip label={window.location.hostname} scope={/^(localhost|127\.0\.0\.1|\[::1\])$/.test(window.location.hostname) ? "local" : "remote"} title="Feedback files stay on this hub." />
      {phase === "picking" || phase === "preparing" ? (
        <Button variant="secondary" onClick={cancelCurrent}>Cancel</Button>
      ) : phase === "recording" && audioReady ? (
        <span className="hs-feedback-verbs">
          <Button variant="primary" onClick={() => void stopAndSave()}>Stop and save</Button>
          <Button variant="secondary" onClick={cancelCurrent}>Cancel</Button>
        </span>
      ) : phase === "recording" ? (
        <Button variant="secondary" onClick={cancelCurrent}>Cancel</Button>
      ) : phase === "saving" ? (
        <span className="hs-feedback-caption">Saving</span>
      ) : phase === "saved" ? (
        <span className="hs-feedback-verbs">
          {prepared?.directory ? <Button variant="secondary" onClick={copyPath}>Copy path</Button> : null}
          <Button variant="primary" onClick={beginPicking}>New feedback</Button>
        </span>
      ) : (
        <span className="hs-feedback-verbs">
          <Button variant="primary" onClick={retry}>Retry</Button>
          <Button variant="secondary" onClick={cancelCurrent}>Cancel</Button>
        </span>
      )}
    </aside>
  );
}
