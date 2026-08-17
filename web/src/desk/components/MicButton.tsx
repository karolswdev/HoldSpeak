// HS-119-01: click-to-toggle mic with streaming transcription.
//
// Click once to start listening; streaming transcription fills the
// target field with progressive Whisper corrections; click again
// (or Enter/Escape) to stop. Every desk text input carries one.
//
// The hold-to-talk hotkey path (system-level) is unmodified — this
// is the browser surface only.
import "./speak-to-fill.css";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  speakToFillSupported,
  speakToFillUnsupportedReason,
  retryPendingTranscription,
  subscribeCaptureLevel,
} from "../../lib/speakToFill";
import {
  micStreamSupported,
  startStreamSession,
  type StreamSession,
  type StreamEvent,
  type VoiceCommandFired,
} from "../../lib/micStreamSession";
import { loadPendingVoice } from "../../lib/pendingVoice";
import { SYSTEM } from "../systemSprites";
import {
  DICTATION_FAILURES,
  dictationFailure,
  refusalCode,
  streamFailure,
  type DictationFailure,
  type StreamRefusal,
} from "../../lib/dictationRecovery";
import { VoiceProposalStrip } from "../voice/ProposalStrip";
import type { VoiceGrammar, VoiceProposal } from "../voice/grammar";
import { routeVoiceIntent } from "../voice/intentRouter";
import { play as sfx } from "../../lib/sfx";

export type MicState = "idle" | "listening" | "busy" | "failed";

export function MicButton({
  onText,
  label = "Speak",
  onFailure,
  draftScope,
  variant,
  onState,
  onLevel,
  grammar,
  surfaceKind,
  hasSelection = false,
  onProposalConfirm,
  pipeline,
  onCommand,
}: {
  onText: (text: string) => void;
  label?: string;
  onFailure?: (failure: DictationFailure) => void;
  draftScope?: string;
  grammar?: VoiceGrammar;
  surfaceKind?: string;
  hasSelection?: boolean;
  onProposalConfirm?: (proposal: VoiceProposal) => void | Promise<void>;
  variant?: "transport";
  onState?: (state: MicState) => void;
  onLevel?: (level: number) => void;
  /* HS-132-04 — a field mic is the user TYPING WITH THEIR VOICE: it
     transcribes verbatim, with no intent routing, enrichment, rewriting or
     journal row. Only a dictate-for-delivery surface (the Speak room's
     TALK transport key) asks for the pipeline, and that is the one pass
     the utterance gets — the delivery that follows sends `raw: true`. */
  pipeline?: boolean;
  /* HS-132-04 — a configured macro keyword CONSUMED the utterance on the
     server (it fired, once). Nothing is dictated as prose; a surface that
     shows receipts can name the command that ran. */
  onCommand?: (fired: VoiceCommandFired) => void;
}) {
  const pipelined = pipeline ?? variant === "transport";
  const [state, setState] = useState<MicState>("idle");
  const [failure, setFailure] = useState<DictationFailure | null>(null);
  /* HS-132-05 — the server's own name for the refusal, shown as WHAT. */
  const [failureCode, setFailureCode] = useState<string | null>(null);
  const [audioRetained, setAudioRetained] = useState(false);
  const [proposal, setProposal] = useState<VoiceProposal | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [receipt, setReceipt] = useState<{ text: string; scope: string } | null>(null);
  const [level, setLevel] = useState(0);
  const sessionRef = useRef<StreamSession | null>(null);
  const firedRef = useRef<VoiceCommandFired | null>(null);
  /* HS-132-05 — the session's OWN refusal. Once the server named a failure,
     the empty final that follows is a consequence of it, never "no words". */
  const refusedRef = useRef<StreamRefusal | null>(null);
  const startingRef = useRef(false);
  const onStateRef = useRef(onState);
  onStateRef.current = onState;
  const onLevelRef = useRef(onLevel);
  onLevelRef.current = onLevel;

  const go = useCallback((next: MicState) => {
    setState(next);
    onStateRef.current?.(next);
  }, []);

  useEffect(
    () =>
      subscribeCaptureLevel((l) => {
        setLevel(l);
        onLevelRef.current?.(l);
      }),
    [],
  );

  useEffect(() => {
    if (!draftScope) return;
    let mounted = true;
    void loadPendingVoice(draftScope).then((audio) => {
      if (!mounted || !audio) return;
      setAudioRetained(true);
      setFailure("transcription_failed");
      go("failed");
    });
    return () => {
      mounted = false;
    };
  }, [draftScope, go]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) return;
      if (sessionRef.current && (e.key === "Enter" || e.key === "Escape")) {
        e.preventDefault();
        void stopSession();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    return () => {
      sessionRef.current?.cancel();
      sessionRef.current = null;
    };
  }, []);

  const transport = variant === "transport";

  const captureSupported = speakToFillSupported() || micStreamSupported();
  if (!captureSupported && !audioRetained) {
    const reason =
      speakToFillUnsupportedReason() ??
      "This browser cannot capture microphone audio.";
    return (
      <button
        type="button"
        className={
          transport
            ? "desk-mic gadget-transport-key is-unsupported"
            : "desk-mic is-unsupported"
        }
        disabled
        title={reason}
        aria-label={`${label} (unavailable: ${reason})`}
        onClick={(e) => e.stopPropagation()}
      >
        <MicFace transport={transport} busy={false} />
      </button>
    );
  }

  const routeTranscript = async (text: string) => {
    if (!grammar) {
      onText(text);
      return;
    }
    const loadingProposal: VoiceProposal = {
      transcript: text,
      intentId: "classifying",
      verbId: null,
      params: {},
      confidence: 0,
      requiresLLM: false,
    };
    setProposal(loadingProposal);
    setClassifying(true);
    const next = await routeVoiceIntent({
      transcript: text,
      surfaceKind: surfaceKind ?? grammar.surfaceKind,
      selectionState: { hasSelection },
      grammar,
    });
    setClassifying(false);
    if (next.confidence >= 0.5) {
      setProposal(next);
      return;
    }
    setProposal(null);
    if (grammar.dictationFallback) onText(text);
  };

  const confirmProposal = async () => {
    if (!proposal || classifying) return;
    const armed = proposal;
    try {
      if (onProposalConfirm) await onProposalConfirm(armed);
      else onText(armed.transcript);
      setReceipt({ text: "DONE", scope: armed.requiresLLM ? "cloud" : "local" });
    } catch {
      setReceipt({ text: "ACTION FAILED", scope: "local" });
    }
  };

  const clearProposal = () => {
    setProposal(null);
    setClassifying(false);
    setReceipt(null);
  };

  /* HS-132-05 — the retained capture is real on the streaming path: the
     session persists what it sent before the final, so a failed utterance
     has audio behind the Retry the copy promises. */
  const markRetained = async (session: StreamSession | null) => {
    if (!draftScope || !session?.retained) return;
    try {
      if (await session.retained()) setAudioRetained(true);
    } catch {
      /* nothing claims retention it cannot prove */
    }
  };

  const fail = (category: DictationFailure, code: string | null) => {
    setFailure(category);
    setFailureCode(code);
    onFailure?.(category);
    sfx("error");
    go("failed");
  };

  const startSession = async () => {
    if (startingRef.current) return;
    startingRef.current = true;
    setFailure(null);
    setFailureCode(null);
    try {
      if (draftScope) {
        const recovered = await retryPendingTranscription(draftScope, {
          pipeline: pipelined,
        });
        if (recovered !== null) {
          setAudioRetained(false);
          if (recovered) {
            await routeTranscript(recovered);
            go("idle");
          } else {
            fail("no_speech", null);
          }
          return;
        }
      }

      firedRef.current = null;
      refusedRef.current = null;
      const onEvent = (event: StreamEvent) => {
        if (event.type === "final" && event.fired) {
          // a macro fired on the server: this utterance is spent as a command.
          firedRef.current = event.fired;
        } else if (event.type === "error") {
          // HS-132-05: the refusal arrives NAMED — reason, failure_category,
          // and the closed-interval marker — and it is shown by that name.
          refusedRef.current = event;
          fail(streamFailure(event), refusalCode(event));
          const session = sessionRef.current;
          sessionRef.current = null;
          void markRetained(session).then(() => session?.cancel());
        }
      };

      const session = await startStreamSession(onEvent, {
        pipeline: pipelined,
        retainScope: draftScope,
      });
      sessionRef.current = session;
      go("listening");
    } catch (error) {
      fail(dictationFailure(error), null);
    } finally {
      startingRef.current = false;
    }
  };

  const stopSession = async () => {
    const session = sessionRef.current;
    if (!session) return;
    sessionRef.current = null;
    go("busy");
    try {
      const text = await session.stop();
      const fired = firedRef.current;
      firedRef.current = null;
      if (fired) {
        // The hotkey path types NOTHING when a command consumes the utterance
        // (runtime/dictation_capture.py:117-173). Neither does this: no prose,
        // no delivery, and no "no speech" verdict on a command that ran.
        onCommand?.(fired);
        setAudioRetained(false);
        setFailure(null);
        setFailureCode(null);
        go("idle");
        return;
      }
      if (text) {
        await routeTranscript(text);
        setAudioRetained(false);
        setFailure(null);
        setFailureCode(null);
        go("idle");
      } else if (refusedRef.current) {
        // HS-132-05: the server already said what went wrong. An errored
        // session ends on its own failure — never on "No words were detected".
        await markRetained(session);
      } else {
        setAudioRetained(false);
        fail("no_speech", null);
      }
    } catch (error) {
      fail(dictationFailure(error), null);
      await markRetained(session);
    }
  };

  const toggle = () => {
    if (state === "listening") {
      sfx("key-up");
      void stopSession();
    } else if (state === "idle" || state === "failed") {
      sfx("key-down");
      void startSession();
    }
  };

  const listening = state === "listening";

  return (
    <>
      <button
        type="button"
        className={
          transport
            ? `desk-mic gadget-transport-key is-${state}`
            : `desk-mic is-${state}`
        }
        title={
          failure
            ? failureCode
              ? `${failureCode} · ${DICTATION_FAILURES[failure].message}`
              : DICTATION_FAILURES[failure].message
            : label
        }
        aria-label={
          audioRetained
            ? "Retry retained audio"
            : listening
              ? "Stop listening"
              : state === "failed"
                ? `${label} again`
                : label
        }
        aria-pressed={listening ? true : undefined}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          toggle();
        }}
      >
        <MicFace transport={transport} busy={state === "busy"} />
      </button>
      {listening && !transport ? (
        <span
          className="desk-mic-level"
          role="meter"
          aria-label="Audio level"
          aria-valuenow={Math.round(level * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{ "--mic-level": level } as React.CSSProperties}
        />
      ) : null}
      {failure && !transport ? (
        <span className="desk-mic-failure" role="status">
          {failureCode ? (
            <b className="desk-mic-failure-code">{failureCode}</b>
          ) : null}
          {failureCode ? " " : ""}
          {audioRetained ? "Captured audio is retained locally. " : ""}
          {DICTATION_FAILURES[failure].message}
        </span>
      ) : null}
      <VoiceProposalStrip
        proposal={proposal}
        pending={classifying}
        receipt={receipt}
        onConfirm={() => void confirmProposal()}
        onCancel={clearProposal}
      />
    </>
  );
}

function MicFace({ transport, busy }: { transport: boolean; busy: boolean }) {
  return (
    <>
      <span
        className={transport ? "gadget-transport-glyph" : undefined}
        aria-hidden="true"
      >
        {busy ? (
          "…"
        ) : (
          <img
            src={SYSTEM.micGlyph}
            alt=""
            width={16}
            height={16}
            className="desk-chrome-sprite"
            draggable={false}
          />
        )}
      </span>
      {transport ? <span className="gadget-transport-word">Talk</span> : null}
    </>
  );
}
