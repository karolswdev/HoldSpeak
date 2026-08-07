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
} from "../../lib/micStreamSession";
import { loadPendingVoice } from "../../lib/pendingVoice";
import { SYSTEM } from "../systemSprites";
import {
  DICTATION_FAILURES,
  dictationFailure,
  type DictationFailure,
} from "../../lib/dictationRecovery";
import { VoiceProposalStrip } from "../voice/ProposalStrip";
import type { VoiceGrammar, VoiceProposal } from "../voice/grammar";
import { routeVoiceIntent } from "../voice/intentRouter";

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
  onPartial,
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
  onPartial?: (text: string) => void;
}) {
  const [state, setState] = useState<MicState>("idle");
  const [failure, setFailure] = useState<DictationFailure | null>(null);
  const [audioRetained, setAudioRetained] = useState(false);
  const [proposal, setProposal] = useState<VoiceProposal | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [receipt, setReceipt] = useState<{ text: string; scope: string } | null>(null);
  const [level, setLevel] = useState(0);
  const sessionRef = useRef<StreamSession | null>(null);
  const startingRef = useRef(false);
  const onStateRef = useRef(onState);
  onStateRef.current = onState;
  const onLevelRef = useRef(onLevel);
  onLevelRef.current = onLevel;
  const onPartialRef = useRef(onPartial);
  onPartialRef.current = onPartial;

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

  const startSession = async () => {
    if (startingRef.current) return;
    startingRef.current = true;
    setFailure(null);
    try {
      if (draftScope) {
        const recovered = await retryPendingTranscription(draftScope);
        if (recovered !== null) {
          setAudioRetained(false);
          if (recovered) {
            await routeTranscript(recovered);
            go("idle");
          } else {
            setFailure("no_speech");
            onFailure?.("no_speech");
            go("failed");
          }
          return;
        }
      }

      const onEvent = (event: StreamEvent) => {
        if (event.type === "partial") {
          onPartialRef.current?.(event.text);
        } else if (event.type === "error") {
          const category = dictationFailure(new Error(event.error));
          setFailure(category);
          onFailure?.(category);
          go("failed");
          sessionRef.current = null;
        }
      };

      const session = await startStreamSession(onEvent);
      sessionRef.current = session;
      go("listening");
    } catch (error) {
      const category = dictationFailure(error);
      setFailure(category);
      onFailure?.(category);
      go("failed");
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
      if (text) {
        await routeTranscript(text);
        setAudioRetained(false);
        setFailure(null);
        go("idle");
      } else {
        setAudioRetained(false);
        setFailure("no_speech");
        onFailure?.("no_speech");
        go("failed");
      }
    } catch (error) {
      const category = dictationFailure(error);
      setFailure(category);
      onFailure?.(category);
      go("failed");
    }
  };

  const toggle = () => {
    if (state === "listening") {
      void stopSession();
    } else if (state === "idle" || state === "failed") {
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
        title={failure ? DICTATION_FAILURES[failure].message : label}
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
