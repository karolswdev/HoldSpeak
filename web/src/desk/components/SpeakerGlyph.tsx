/** HS-154-04 — the speaker glyph on every assistant message.
 *
 * Click replays the message's text via the D1 seam (`speak`).
 * Click while speaking stops. Active/speaking visual state.
 * Works with the call OFF (replay is always available).
 * Desk tokens; focusable; Enter/Space toggles.
 *
 * No modals. No prose. No window test hooks. */

import { useCallback, useEffect, useState } from "react";
import { onStateChange, type TtsState } from "../../lib/tts";
import {
  replayMessage,
  stopReplay,
  getActiveSpeakerId,
} from "../autoSpeak";

export interface SpeakerGlyphProps {
  /** The message ID this glyph belongs to. */
  messageId: string;
  /** The full text of the message to speak on click. */
  text: string;
}

export function SpeakerGlyph({ messageId, text }: SpeakerGlyphProps) {
  const [ttsState, setTtsState] = useState<TtsState>("idle");

  useEffect(() => {
    return onStateChange(setTtsState);
  }, []);

  const isSpeaking =
    ttsState === "speaking" && getActiveSpeakerId() === messageId;

  const handleClick = useCallback(() => {
    if (isSpeaking) {
      stopReplay();
    } else {
      replayMessage(messageId, text);
    }
  }, [isSpeaking, messageId, text]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClick();
      }
    },
    [handleClick],
  );

  // Do not render if there is no text to speak.
  if (!text.trim()) return null;

  return (
    <button
      type="button"
      className={`thread-speaker-glyph${isSpeaking ? " thread-speaker-glyph--active" : ""}`}
      data-testid="speaker-glyph"
      data-speaking={isSpeaking ? "true" : "false"}
      data-message-id={messageId}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={isSpeaking ? "Stop speaking" : "Speak message"}
      tabIndex={0}
      title={isSpeaking ? "Stop" : "Speak"}
    >
      {isSpeaking ? "■" : "▶"}
    </button>
  );
}
