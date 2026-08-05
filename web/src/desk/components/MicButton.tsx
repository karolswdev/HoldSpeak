// HS-78-02: the speak-to-fill mic — hold to talk, release to fill.
//
// Every desk text input carries one (the standing voice-first rule, now on
// the web): press and hold, speak, release; the transcript lands in the
// field through onText with NO confirm step. Capture + transcription live
// in the shared helper (the hub's own local Whisper; nothing egresses).
//
// HS-111-02: the cockpit's TALK key is THIS button wearing the transport
// face (variant="transport") — same capture path, same 4-state machine;
// the instrument strip reads the machine through onState and the capture
// level through onLevel (the analyser tap lives in lib/speakToFill).
import "./speak-to-fill.css";
import { useEffect, useRef, useState } from "react";
import {
  cancelCapture,
  speakToFillSupported,
  speakToFillUnsupportedReason,
  startCapture,
  stopAndTranscribe,
  retryPendingTranscription,
  subscribeCaptureLevel,
} from "../../lib/speakToFill";
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
  label = "Hold to talk",
  onFailure,
  draftScope,
  variant,
  onState,
  onLevel,
  grammar,
  surfaceKind,
  hasSelection = false,
  onProposalConfirm,
}: {
  onText: (text: string) => void;
  label?: string;
  onFailure?: (failure: DictationFailure) => void;
  draftScope?: string;
  /** When supplied, transcript is classified before it can change the surface. */
  grammar?: VoiceGrammar;
  /** The focused surface's identity; defaults to the supplied grammar's kind. */
  surfaceKind?: string;
  hasSelection?: boolean;
  /** Executes only after the user confirms the armed proposal. */
  onProposalConfirm?: (proposal: VoiceProposal) => void | Promise<void>;
  /** "transport" — the 48×48 momentary TALK key (glyph over mono word,
   * held = inverted video). Default: the compact in-well mic. */
  variant?: "transport";
  /** The 4-state machine, reported outward (the cockpit's STATE register). */
  onState?: (state: MicState) => void;
  /** Capture level 0..1 while listening (feeds a LedMeter). */
  onLevel?: (level: number) => void;
}) {
  const [state, setState] = useState<MicState>("idle");
  const [failure, setFailure] = useState<DictationFailure | null>(null);
  const [audioRetained, setAudioRetained] = useState(false);
  const [proposal, setProposal] = useState<VoiceProposal | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [receipt, setReceipt] = useState<{ text: string; scope: string } | null>(null);
  const holding = useRef(false);
  const onStateRef = useRef(onState);
  onStateRef.current = onState;
  const onLevelRef = useRef(onLevel);
  onLevelRef.current = onLevel;

  const go = (next: MicState) => {
    setState(next);
    onStateRef.current?.(next);
  };

  useEffect(
    () =>
      subscribeCaptureLevel((level) => {
        onLevelRef.current?.(level);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draftScope]);

  const transport = variant === "transport";
  const face = (
    <>
      <span
        className={transport ? "gadget-transport-glyph" : undefined}
        aria-hidden="true"
      >
        {/* HS-111-09 — the mic is a 16px system sprite (integer-true),
            not the 🎙 emoji: the highest-traffic icon on the desk. */}
        {state === "busy" ? (
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
        {face}
      </button>
    );
  }

  const routeTranscript = async (text: string) => {
    if (!grammar) {
      onText(text);
      return;
    }
    // The strip appears while the (only when needed) classifier is working;
    // the transcript itself is still never an instruction until Confirm.
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

  const start = async () => {
    holding.current = true;
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
      await startCapture();
      if (!holding.current) {
        await cancelCapture();
        return;
      }
      go("listening");
    } catch (error) {
      const category = dictationFailure(error);
      setFailure(category);
      onFailure?.(category);
      go("failed");
    }
  };

  const stop = async () => {
    holding.current = false;
    if (state !== "listening") return;
    go("busy");
    try {
      const text = await stopAndTranscribe(draftScope);
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
      if (draftScope) setAudioRetained(true);
      setFailure(category);
      onFailure?.(category);
      go("failed");
    }
  };

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
            : state === "failed"
              ? `${label} again`
              : label
        }
        aria-pressed={transport ? state === "listening" : undefined}
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
        {face}
      </button>
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
