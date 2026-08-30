// HS-154-04 — auto-speak: sentence-boundary streaming → TTS.
//
// As deltas arrive during a streaming turn, this module accumulates
// text and feeds completed sentences to the D1 TTS seam
// (`enqueueSentence`). The tail is flushed at turn_done. Only active
// when call mode is ON.
//
// Barge-in: when the owner starts talking (callLoop state →
// "transcribing") or clicks the chip/glyph, bargeIn() stops TTS and
// blocks all further enqueues for that turn.
//
// Replay tracking: tracks which message is "active" in the TTS
// pipeline so the speaker glyph knows which row to highlight.

import { enqueueSentence, stop, speak, onStateChange } from "../lib/tts";

// ── sentence boundary ─────────────────────────────────────────────

/** Minimum character count before we consider a sentence boundary real.
 *  Prevents splitting on abbreviations like "Dr." or "U.S." */
const MIN_SENTENCE_LEN = 20;

/** Split the buffer at sentence boundaries. Returns [sentences, remainder]. */
function splitSentences(buf: string): [string[], string] {
  const sentences: string[] = [];
  let remaining = buf;

  // eslint-disable-next-line no-constant-condition
  while (true) {
    // Look for a sentence-ending punctuation followed by whitespace.
    const match = remaining.match(/[.!?]\s/);
    if (!match || match.index === undefined) break;

    const end = match.index + 1; // include the punctuation
    const candidate = remaining.slice(0, end).trim();

    if (candidate.length >= MIN_SENTENCE_LEN) {
      sentences.push(candidate);
      remaining = remaining.slice(end).trimStart();
    } else {
      // Too short — might be an abbreviation; keep accumulating.
      break;
    }
  }

  return [sentences, remaining];
}

// ── module state ──────────────────────────────────────────────────

let buffer = "";
let currentMessageId: string | null = null;
/** Turns that were barged (no further enqueues). */
const bargedTurns = new Set<string>();
/** Turns that had at least one sentence auto-spoken (no re-speak on completion). */
const autoSpokenTurns = new Set<string>();
/** Whether call mode is active. */
let callActive = false;
/** Which message is currently being spoken (auto-speak or replay).
 *  Speaker glyphs check this to show their active state. */
let activeSpeakerId: string | null = null;

// Subscribe to TTS state changes: clear activeSpeakerId when idle.
onStateChange((s) => {
  if (s === "idle") {
    activeSpeakerId = null;
  }
});

// ── public API ────────────────────────────────────────────────────

/** Set whether auto-speak is active (call mode ON/OFF). */
export function setCallActive(active: boolean): void {
  callActive = active;
  if (!active) {
    buffer = "";
    currentMessageId = null;
  }
}

/** Feed a streaming delta chunk. Enqueues completed sentences. */
export function feedDelta(messageId: string, text: string): void {
  if (!callActive) return;
  if (bargedTurns.has(messageId)) return;

  // New turn — flush any leftover from a previous message.
  if (currentMessageId !== null && currentMessageId !== messageId) {
    if (buffer.trim() && !bargedTurns.has(currentMessageId)) {
      enqueueSentence(buffer.trim());
      autoSpokenTurns.add(currentMessageId);
      activeSpeakerId = currentMessageId;
    }
    buffer = "";
  }

  currentMessageId = messageId;
  buffer += text;

  // Drain completed sentences.
  const [sentences, remainder] = splitSentences(buffer);
  for (const s of sentences) {
    enqueueSentence(s);
    autoSpokenTurns.add(messageId);
    activeSpeakerId = messageId;
  }
  buffer = remainder;
}

/** Flush the remaining buffer at turn_done. */
export function flushTurn(messageId: string): void {
  if (currentMessageId === messageId && buffer.trim() && !bargedTurns.has(messageId)) {
    enqueueSentence(buffer.trim());
    autoSpokenTurns.add(messageId);
    activeSpeakerId = messageId;
  }
  buffer = "";
  if (currentMessageId === messageId) {
    currentMessageId = null;
  }
}

/** Barge-in: stop TTS, block further enqueues for the current turn. */
export function bargeIn(): void {
  if (currentMessageId) {
    bargedTurns.add(currentMessageId);
  }
  stop();
  buffer = "";
  activeSpeakerId = null;
}

/** Was this message already auto-spoken? (Prevents double-speak.) */
export function wasAutoSpoken(messageId: string): boolean {
  return autoSpokenTurns.has(messageId);
}

/** Replay a finished message via the speaker glyph (manual click).
 *  speak() internally calls stop() which fires the idle listener that
 *  clears activeSpeakerId. So we set activeSpeakerId AFTER speak()
 *  returns -- stop() has already run at that point, and the async
 *  speakOne that fires later will find activeSpeakerId set. */
export function replayMessage(messageId: string, text: string): void {
  speak(text);
  activeSpeakerId = messageId;
}

/** Stop any current replay/auto-speak. */
export function stopReplay(): void {
  stop();
  activeSpeakerId = null;
}

/** Which message is currently being spoken? */
export function getActiveSpeakerId(): string | null {
  return activeSpeakerId;
}

/** Whether call mode is currently active. */
export function isCallActive(): boolean {
  return callActive;
}

// ── test helpers ──────────────────────────────────────────────────

/** Reset all internal state (tests only). */
export function _resetForTest(): void {
  buffer = "";
  currentMessageId = null;
  bargedTurns.clear();
  autoSpokenTurns.clear();
  callActive = false;
  activeSpeakerId = null;
}

/** Read the current buffer (tests only). */
export function _getBuffer(): string {
  return buffer;
}

/** Expose splitSentences for unit testing. */
export { splitSentences as _splitSentences };
