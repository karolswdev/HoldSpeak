// PARKED (HS-170-04)
// HS-135-11 -- the capture hero: the Chair's heart.
//
// TAP = start meeting recording (the existing Record Orb verb from the
// shared store). Recording state lives IN the hero (elapsed + stop verb)
// and stays consistent with the dock orb (same store slices).
//
// Voice trigger: with the hero mic open, a spoken "start meeting" (matched
// against the MicButton transcription output) starts recording. The match
// set is small and named in code.
//
// Ask AI: one tap from the Chair via a Button species verb.
//
// The accent gradient is permitted HERE (and on the Record Orb) ONLY
// (counsel ruling E.4).
//
// L4 note: sounds land in story 12. If sfx.ts exists at SHIP time, the
// integration point is: sfx("latch") on recording start, sfx("key-down")
// on hero key press, sfx("key-up") on hero key release.

import "./hero.css";
import { useEffect, useState, useCallback, useRef } from "react";
import { useDesk } from "../../store";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import { Button } from "../../../components/signal/Signal";
import { SYSTEM } from "../../systemSprites";
import { play as sfx } from "../../../lib/sfx";
import { useDeskWriteReceipt } from "../../hooks/useWriteReceipt";

// ---- voice command match set ------------------------------------------------

/** The small, named set of transcription phrases that trigger recording.
 *  Case-insensitive, trimmed, exact match. Near-misses do NOT trigger. */
export const VOICE_RECORD_COMMANDS: readonly string[] = [
  "start meeting",
  "start recording",
  "record meeting",
] as const;

/** Test whether a transcript matches the recording voice command set. */
export function matchesRecordCommand(transcript: string): boolean {
  const normalized = transcript.trim().toLowerCase();
  return VOICE_RECORD_COMMANDS.some((cmd) => normalized === cmd);
}

// ---- scheduled recording broadcast event handling ---------------------------

// ---- the hero ---------------------------------------------------------------

export interface CaptureHeroProps {
  /** Called when the Ask AI verb is tapped. Opens the existing Ask panel. */
  onAskAI: () => void;
}

export function CaptureHero({ onAskAI }: CaptureHeroProps) {
  const recording = useDesk((s) => s.recording);
  const startedAt = useDesk((s) => s.recordingStartedAt);
  const arming = useDesk((s) => s.scheduledArming);
  const [elapsed, setElapsed] = useState("");
  const [countdown, setCountdown] = useState<number | null>(null);
  const { receipt } = useDeskWriteReceipt();
  const startRecording = () => useDesk.getState().startRecording();
  const stopRecording = () => useDesk.getState().stopRecording();

  // Elapsed timer: identical logic to RecordOrb for consistency.
  useEffect(() => {
    if (recording !== "recording" || startedAt == null) {
      setElapsed("");
      return;
    }
    const t = window.setInterval(() => {
      const s = Math.floor((Date.now() - startedAt) / 1000);
      setElapsed(`${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`);
    }, 1000);
    return () => window.clearInterval(t);
  }, [recording, startedAt]);

  // ---- scheduled recording broadcast subscription --------------------------
  // Each subscribe call uses a string literal so the frame-registry scanner
  // recognizes these as live consumers (holdspeak/realtime_frames.py).
  const { subscribe } = useRuntimeBus();
  useEffect(() => {
    const handler = (frame: { type: string; data: unknown }) => {
      useDesk.getState().applyScheduledRecordingEvent(
        frame.type,
        frame.data as Record<string, unknown>,
      );
    };
    const unsubs = [
      subscribe("scheduled_recording.arming", handler),
      subscribe("scheduled_recording.cancelled", handler),
      subscribe("scheduled_recording.missed", handler),
      subscribe("scheduled_recording.refused", handler),
      subscribe("scheduled_recording.started", handler),
      subscribe("scheduled_recording.stopped", handler),
    ];
    return () => unsubs.forEach((u) => u());
  }, [subscribe]);

  // ---- arming countdown timer (hub-authoritative, display only) -----------
  useEffect(() => {
    if (!arming || arming.outcome) {
      setCountdown(null);
      return;
    }
    const tick = () => {
      const remaining = Math.max(0, Math.ceil((arming.fireAt - Date.now()) / 1000));
      setCountdown(remaining);
    };
    tick();
    const t = window.setInterval(tick, 250);
    return () => window.clearInterval(t);
  }, [arming]);

  const isRecording = recording === "recording";
  const isBusy = recording === "busy";

  // ---- voice trigger: the hero mic transcription handler --------------------
  // When the hero mic is open and the user speaks a recording command, start
  // recording. This is NOT a wake-word system -- it reuses MicButton's
  // transcription output.
  const micListeningRef = useRef(false);
  const [micListening, setMicListening] = useState(false);

  const handleMicText = useCallback(
    (text: string) => {
      if (matchesRecordCommand(text) && recording === "idle") {
        sfx("latch");
        void startRecording();
      }
      // Non-matching transcriptions are ignored (the hero mic is for
      // commands, not dictation).
    },
    [recording],
  );

  const handleMicState = useCallback(
    (state: "idle" | "listening" | "busy" | "failed") => {
      micListeningRef.current = state === "listening";
      setMicListening(state === "listening");
    },
    [],
  );

  // ---- hero key press/release -----------------------------------------------
  const handleKeyClick = () => {
    if (isBusy) return;
    if (isRecording) {
      sfx("key-up");
      void stopRecording();
    } else if (recording === "idle") {
      sfx("latch");
      void startRecording();
    }
  };

  return (
    <div className="capture-hero" data-testid="capture-hero">
      {receipt}
      {/* Recording state: elapsed + stop verb (rendered IN the hero). */}
      {isRecording ? (
        <div className="capture-hero-recording" data-testid="capture-hero-recording">
          <span className="capture-hero-elapsed" data-testid="capture-hero-elapsed">
            {elapsed || "0:00"}
          </span>
          <Button
            variant="danger"
            dense
            onClick={() => {
              sfx("key-up");
              void stopRecording();
            }}
            aria-label="Stop recording"
            data-testid="capture-hero-stop"
          >
            Stop
          </Button>
        </div>
      ) : null}

      {/* HS-136-03: arming countdown -- shows when the conductor is counting
           down to a scheduled recording fire. */}
      {arming && !arming.outcome && countdown !== null ? (
        <div className="capture-hero-arming" data-testid="capture-hero-arming">
          <span className="capture-hero-arming-label">
            Recording in {countdown}s
          </span>
          <Button
            variant="danger"
            dense
            onClick={() => void useDesk.getState().cancelArmedSchedule(arming.scheduleId)}
            data-testid="capture-hero-cancel-armed"
          >
            Cancel
          </Button>
        </div>
      ) : null}

      {/* HS-136-03: arming outcome -- shows the terminal state honestly. */}
      {arming?.outcome ? (
        <div
          className="capture-hero-arming-outcome"
          data-testid="capture-hero-arming-outcome"
          data-outcome={arming.outcome}
        >
          <span className="capture-hero-arming-label">
            {arming.outcome === "started"
              ? `${arming.title || "Scheduled recording"} started`
              : arming.outcome === "cancelled"
                ? "Scheduled recording cancelled"
                : arming.outcome === "refused"
                  ? `Recording refused${arming.outcomeReason ? `: ${arming.outcomeReason}` : ""}`
                  : arming.outcome === "missed"
                    ? "Scheduled recording missed"
                    : null}
          </span>
        </div>
      ) : null}

      {/* The hero instrument key: TransportKey species at hero scale. */}
      <button
        type="button"
        className="capture-hero-key"
        data-active={isRecording || undefined}
        disabled={isBusy}
        onClick={handleKeyClick}
        aria-label={isRecording ? "Stop recording" : "Record a meeting"}
        title={isRecording ? "Stop recording" : "Record a meeting"}
        data-testid="capture-hero-key"
      >
        <span className="capture-hero-glyph" aria-hidden="true">
          <img
            src={SYSTEM.micGlyph}
            alt=""
            width={16}
            height={16}
            className="desk-chrome-sprite"
            draggable={false}
          />
        </span>
        <span className="capture-hero-word">
          {isRecording ? "REC" : "MIC"}
        </span>
      </button>

      {/* Ask AI verb: Button species, one-tap access. */}
      <Button
        variant="ghost"
        onClick={onAskAI}
        aria-label="Ask AI"
        data-testid="capture-hero-ask"
      >
        Ask AI
      </Button>

      {/* HS-136-03: Schedule verb -- opens the in-world create window. */}
      <Button
        variant="ghost"
        onClick={() => useDesk.getState().openScheduleCreate()}
        aria-label="Schedule recording"
        data-testid="capture-hero-schedule"
      >
        Schedule
      </Button>

      {/* The hero mic: invisible MicButton for voice command capture.
          Only rendered when NOT recording (recording is the hero's
          primary state; the mic is for triggering it). */}
      {!isRecording ? (
        <HeroMic
          onText={handleMicText}
          onState={handleMicState}
          listening={micListening}
        />
      ) : null}
    </div>
  );
}

// ---- hero mic (voice command listener) --------------------------------------

import { MicButton, type MicState } from "../../components/MicButton";

function HeroMic({
  onText,
  onState,
  listening,
}: {
  onText: (text: string) => void;
  onState: (state: MicState) => void;
  listening: boolean;
}) {
  return (
    <MicButton
      onText={onText}
      label="Speak a command"
      variant="transport"
      onState={onState}
    />
  );
}
