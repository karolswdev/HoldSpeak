import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { DotWord, ToolGlyph, Toolbar } from "../surface/kit";
import { openSurfaceOr } from "../shell";
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

type Phase = "idle" | "picking" | "preparing" | "recording" | "saving" | "transcribing" | "saved" | "error";
type TranscriptStatus = "pending" | "complete" | "failed";

interface PreparedFeedback {
  id: string;
  capturedAt: string;
  context: FeedbackContext;
  screenshotBase64: string;
  audioBase64: string | null;
  audioDurationMs: number;
  directory?: string;
  files?: string[];
  transcriptStatus?: TranscriptStatus;
  transcript?: string;
  transcriptError?: string;
  egressBoundary?: string;
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

function transcriptFailureText(reason: unknown): string {
  const value = String(reason ?? "").toLowerCase();
  if (value.includes("no_speech")) return "No speech was found.";
  if (
    value.includes("unavailable") ||
    value.includes("not_ready") ||
    value.includes("route_member_missing") ||
    value.includes("not_admitted") ||
    value.includes("binding_")
  ) {
    return "Speech is not set up.";
  }
  return "Transcript unavailable.";
}

/** W3-A: the sheet stands above the dock AND above the front window's status
 *  bar. Its seat is the dock reserve + 8 px; when the front window's status
 *  bar lies in that band (a phone sheet ends at the dock, so its bar does),
 *  the sheet lifts to 8 px above the bar. It pushes nothing. */
function useSeatAboveStatusBar(active: boolean) {
  const ref = useRef<HTMLElement | null>(null);
  const [bottom, setBottom] = useState<number | null>(null);
  useLayoutEffect(() => {
    if (!active) return;
    const place = () => {
      const sheet = ref.current;
      if (!sheet) return;
      const dock = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--desk-dock-h")) || 0;
      const seat = dock + 8;
      const box = sheet.getBoundingClientRect();
      const low = window.innerHeight - seat;
      const high = low - box.height;
      let next = seat;
      const fronts = document.querySelectorAll<HTMLElement>(".desk-window-shell.is-front");
      for (const front of fronts) {
        for (const bar of front.querySelectorAll<HTMLElement>(".kit-statusbar")) {
          const b = bar.getBoundingClientRect();
          if (!b.width || !b.height) continue;
          if (b.right <= box.left || b.left >= box.right) continue;
          if (b.bottom <= high || b.top >= low) continue;
          next = Math.max(next, Math.ceil(window.innerHeight - b.top + 8));
        }
      }
      setBottom((current) => {
        const value = next === seat ? null : next;
        return current === value ? current : value;
      });
    };
    place();
    const again = () => requestAnimationFrame(place);
    window.addEventListener("resize", again);
    document.addEventListener("pointerup", again, true);
    const observer = typeof ResizeObserver === "function" ? new ResizeObserver(again) : null;
    if (observer && ref.current) observer.observe(ref.current);
    return () => {
      window.removeEventListener("resize", again);
      document.removeEventListener("pointerup", again, true);
      observer?.disconnect();
    };
  }, [active]);
  return { ref, style: bottom === null ? undefined : { bottom } };
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
  const seat = useSeatAboveStatusBar(capability.enabled && phase !== "idle");

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

  const captureTarget = useCallback((target: Element, event?: PointerEvent) => {
    if (event) {
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
    } else {
      gestureCleanup.current?.();
      gestureCleanup.current = null;
    }
    const current = ++generation.current;
    const root = ownerRoot(target);
    const ownerId = root.getAttribute("data-layer") === "window" ? root.id || null : null;
    let context: FeedbackContext;
    try {
      context = snapshotContext(target, root, null);
    } catch (cause) {
      gestureCleanup.current?.();
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
      const image = await captureWindowPng(root, controller.signal);
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
  }, []);

  const beginFeedback = useCallback((target?: Element) => {
    if (!capability.enabled) return;
    if (!target) {
      beginPicking();
      return;
    }
    cancelCurrent();
    captureTarget(target);
  }, [beginPicking, cancelCurrent, capability.enabled, captureTarget]);

  useEffect(() => bindUiFeedbackLauncher(beginFeedback), [beginFeedback]);

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
      captureTarget(target, event);
    };
    document.addEventListener("keydown", onKey, true);
    document.addEventListener("pointerdown", onPointer, true);
    return () => {
      document.removeEventListener("keydown", onKey, true);
      document.removeEventListener("pointerdown", onPointer, true);
    };
  }, [cancelCurrent, captureTarget, phase]);

  const transcribeSaved = useCallback(async (saved: PreparedFeedback, runGeneration: number) => {
    if (runGeneration !== generation.current || payload.current?.id !== saved.id) return;
    setPhase("transcribing");
    setError("");
    try {
      const result = await apiFetch<{
        success?: boolean;
        id?: string;
        directory?: string;
        files?: string[];
        transcript_status?: TranscriptStatus;
        transcript?: string;
        transcript_error?: string;
        egress_boundary?: string;
        reason?: string;
      }>(`/api/ui-feedback/${saved.id}/transcribe`, { method: "POST" });
      if (runGeneration !== generation.current || payload.current?.id !== saved.id) return;
      const transcriptStatus = result.transcript_status ?? "failed";
      const next: PreparedFeedback = {
        ...saved,
        directory: result.directory ?? saved.directory,
        files: result.files ?? saved.files,
        transcriptStatus,
        transcript: result.transcript,
        transcriptError: result.transcript_error ?? result.reason,
        egressBoundary: result.egress_boundary,
      };
      payload.current = next;
      setPrepared(next);
      setStatus(next.directory ?? next.id);
      if (transcriptStatus === "complete") {
        setPhase("saved");
        return;
      }
      setError(transcriptFailureText(next.transcriptError));
      setPhase("saved");
    } catch (cause) {
      if (runGeneration !== generation.current || payload.current?.id !== saved.id) return;
      const failed = { ...saved, transcriptStatus: "failed" as const, transcriptError: cause instanceof Error ? cause.message : "transcription_failed" };
      payload.current = failed;
      setPrepared(failed);
      setStatus(saved.directory ?? saved.id);
      setError(transcriptFailureText(failed.transcriptError));
      setPhase("saved");
    }
  }, []);

  const stopAndSave = useCallback(async () => {
    const current = payload.current;
    const saveGeneration = generation.current;
    if (!current || phase === "saving" || phase === "transcribing" || phase === "saved") return;
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
      const result = await apiFetch<{ success?: boolean; id?: string; directory?: string; files?: string[]; transcript_status?: TranscriptStatus; egress_boundary?: string }>("/api/ui-feedback", {
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
      const saved = {
        ...next,
        directory: result.directory,
        files: result.files,
        transcriptStatus: result.transcript_status ?? "pending",
        egressBoundary: result.egress_boundary,
      };
      payload.current = saved;
      setPrepared(saved);
      setStatus(result.directory ?? next.id);
      setPhase("transcribing");
      void transcribeSaved(saved, saveGeneration);
    } catch (cause) {
      if (saveGeneration !== generation.current || payload.current?.id !== next.id) return;
      setError(errorText(cause));
      setStatus("");
      setPhase("error");
    }
  }, [clearTimer, phase, transcribeSaved]);

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
    if (prepared?.audioBase64 && prepared.directory) {
      void transcribeSaved(prepared, generation.current);
      return;
    }
    if (prepared?.audioBase64) {
      void stopAndSave();
      return;
    }
    beginPicking();
  };
  // W3-A (window grammar): the sheet is a 36 px toolbar (the verbs) with the
  // state as a dot and a word at its right end, and one quiet line under it:
  // what the feedback is about, the transcript, or the reason it stopped.
  // No mono caps, no route chip (UX-CANON A.9): the speech route is the
  // hover title of the transcript state.
  const boundary = prepared?.egressBoundary ?? "";
  const boundaryWords: Record<string, string> = {
    same_device: "this device",
    local: "this device",
    private_network: "the private network",
    mesh: "the mesh",
    cloud: "the cloud",
  };
  const routeTitle = boundary
    ? `Speech used ${boundaryWords[boundary] ?? boundary}. The feedback files stay on this hub.`
    : "The feedback files stay on this hub.";
  const state: { word: string; tone: "ok" | "warn" | "fail" | "info" | "ask" | "idle" } =
    phase === "picking" ? { word: status || "Select an element", tone: "info" }
    : phase === "preparing" ? { word: "Capturing", tone: "info" }
    : phase === "recording" ? { word: "Recording", tone: "fail" }
    : phase === "saving" ? { word: "Saving", tone: "info" }
    : phase === "transcribing" ? { word: "Transcribing", tone: "info" }
    : phase === "saved" ? { word: "Saved", tone: "ok" }
    : { word: "Not saved", tone: "fail" };
  const speechFailed = phase === "saved" && prepared?.transcriptStatus === "failed";
  const speechNotSetUp = speechFailed && transcriptFailureText(prepared?.transcriptError) === "Speech is not set up.";
  const transcript = phase === "saved" && prepared?.transcriptStatus === "complete" ? (prepared.transcript ?? "").trim() : "";
  return (
    <aside ref={seat.ref} style={seat.style} className="desk-next hs-feedback-strip" data-ui-feedback="true" data-phase={phase} role="status" aria-live="polite">
      <Toolbar label="Feedback" className="hs-feedback-toolbar">
        {phase === "picking" || phase === "preparing" ? (
          <Button dense variant="secondary" onClick={cancelCurrent}>Cancel</Button>
        ) : phase === "recording" && audioReady ? (
          <>
            <Button dense variant="primary" onClick={() => void stopAndSave()}><ToolGlyph kind="done" />Stop and save</Button>
            <Button dense variant="ghost" onClick={cancelCurrent}>Cancel</Button>
          </>
        ) : phase === "recording" ? (
          <Button dense variant="ghost" onClick={cancelCurrent}>Cancel</Button>
        ) : phase === "saving" || phase === "transcribing" ? null : phase === "saved" ? (
          <>
            <Button dense variant="primary" onClick={beginPicking}><ToolGlyph kind="new" />New feedback</Button>
            {speechFailed ? (
              <Button dense variant="ghost" className="hs-feedback-verb" title="Retry transcription" onClick={retry}>
                <ToolGlyph kind="retry" /><span className="hs-feedback-verb-label">Retry transcription</span>
              </Button>
            ) : null}
            {prepared?.directory ? (
              <Button dense variant="ghost" className="hs-feedback-verb is-glyph" title={`Copy path · ${prepared.directory}`} onClick={copyPath}>
                <ToolGlyph kind="copy" /><span className="hs-feedback-verb-label">Copy path</span>
              </Button>
            ) : null}
            <Button dense variant="ghost" onClick={cancelCurrent}>Done</Button>
          </>
        ) : (
          <>
            <Button dense variant="primary" onClick={retry}><ToolGlyph kind="retry" />Retry</Button>
            {prepared?.directory ? (
              <Button dense variant="ghost" className="hs-feedback-verb is-glyph" title={`Copy path · ${prepared.directory}`} onClick={copyPath}>
                <ToolGlyph kind="copy" /><span className="hs-feedback-verb-label">Copy path</span>
              </Button>
            ) : null}
            <Button dense variant="ghost" onClick={cancelCurrent}>Cancel</Button>
          </>
        )}
      </Toolbar>
      <div className="hs-feedback-line">
        <DotWord tone={state.tone} className="hs-feedback-state">{state.word}</DotWord>
        {phase === "picking" ? null : <span className="hs-feedback-about">{selectedName}</span>}
        {speechFailed ? (
          <span className="hs-feedback-speech">
            <DotWord tone="warn">Speech unavailable</DotWord>
            {error && !speechNotSetUp ? <span className="hs-feedback-reason">{error}</span> : null}
            {speechNotSetUp ? (
              <Button dense variant="ghost" title={error || undefined} onClick={() => openSurfaceOr("configure-settings", "/settings", "speak")}>Set up speech</Button>
            ) : null}
          </span>
        ) : phase === "saved" ? (
          <span className="hs-feedback-speech" title={routeTitle}>
            <DotWord tone="ok">Transcript saved</DotWord>
          </span>
        ) : error ? <span className="hs-feedback-error">{error}</span> : null}
        {transcript ? <span className="hs-feedback-transcript">{transcript}</span> : null}
      </div>
    </aside>
  );
}
