/** HS-154-03 -- the ONE call-mode chip in the thread head.
 *
 * States:  OFF | LISTENING | THINKING | SPEAKING
 *
 * Only ON/OFF persists (call_mode 0/1 on the thread row).
 * THINKING is derived: a turn is streaming on this thread.
 * SPEAKING is derived: the TTS seam is in "speaking" state.
 * LISTENING is the resting state when the call is ON.
 *
 * ONE click in any non-OFF state stops everything:
 *   tts.stop(), loop.stop() (mic closed), PATCH call_mode=0.
 * Clicking when OFF starts: PATCH call_mode=1, wireCallLoop → LISTENING.
 *
 * Keyboard reachable: focusable, Enter/Space stops (or starts).
 * No modal. Desk tokens. */

import { useCallback, useEffect, useRef, useState } from "react";
import { onStateChange as ttsOnStateChange, stop as ttsStop, type TtsState } from "../../lib/tts";
import { wireCallLoop, type CallLoopWiring } from "../callLoopWiring";
import { patchThread } from "../threads";

// ── types ────────────────────────────────────────────────────────────

export type CallChipState = "off" | "listening" | "thinking" | "speaking";

// ── labels ───────────────────────────────────────────────────────────

const LABELS: Record<CallChipState, string> = {
  off: "CALL",
  listening: "LISTENING",
  thinking: "THINKING",
  speaking: "SPEAKING",
};

// ── component ────────────────────────────────────────────────────────

export interface CallChipProps {
  threadId: string;
  /** The persisted call_mode from the server (0 = off, 1 = on). */
  callMode: number;
  /** Whether a turn is currently streaming on this thread. */
  isStreaming: boolean;
  /** Callback to reload the thread detail after a patch. */
  onReload?: () => void;
}

export function CallChip({ threadId, callMode, isStreaming, onReload }: CallChipProps) {
  const [ttsState, setTtsState] = useState<TtsState>("idle");
  const loopRef = useRef<CallLoopWiring | null>(null);

  // Subscribe to TTS state changes.
  useEffect(() => {
    const unsub = ttsOnStateChange(setTtsState);
    return unsub;
  }, []);

  // Derive the visible chip state.
  const deriveState = useCallback((): CallChipState => {
    if (callMode !== 1) return "off";
    if (ttsState === "speaking") return "speaking";
    if (isStreaming) return "thinking";
    return "listening";
  }, [callMode, ttsState, isStreaming]);

  const chipState = deriveState();

  // When call_mode=1 arrives (initial load or patch), start the loop.
  useEffect(() => {
    if (callMode === 1 && loopRef.current === null) {
      const loop = wireCallLoop(
        threadId,
        (_err) => {
          // Error surfaces through the existing in-flow error row;
          // the chip does not render errors itself.
        },
      );
      loopRef.current = loop;
      void loop.start();
    }
    // When call_mode flips to 0 externally, stop the loop.
    if (callMode === 0 && loopRef.current !== null) {
      loopRef.current.stop();
      loopRef.current = null;
    }
  }, [callMode, threadId]);

  // Clean up on unmount.
  useEffect(() => {
    return () => {
      if (loopRef.current) {
        loopRef.current.stop();
        loopRef.current = null;
      }
    };
  }, []);

  const handleClick = useCallback(() => {
    if (chipState === "off") {
      // Start: PATCH call_mode=1, then the useEffect above starts the loop.
      void patchThread(threadId, { call_mode: 1 }).then(() => {
        onReload?.();
      });
    } else {
      // Stop everything in any non-OFF state.
      ttsStop();
      if (loopRef.current) {
        loopRef.current.stop();
        loopRef.current = null;
      }
      void patchThread(threadId, { call_mode: 0 }).then(() => {
        onReload?.();
      });
    }
  }, [chipState, threadId, onReload]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClick();
      }
    },
    [handleClick],
  );

  return (
    <button
      type="button"
      className={`thread-call-chip thread-call-chip--${chipState}`}
      data-testid="call-chip"
      data-call-state={chipState}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`Call: ${chipState}`}
      tabIndex={0}
    >
      {LABELS[chipState]}
    </button>
  );
}
