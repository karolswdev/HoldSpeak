// HS-154-02 — the hands-free utterance loop.
//
// A small state machine over the EXISTING pieces: the energy VAD
// (lib/vad via lib/micSession's startOpenMic), the 16 kHz WAV encoder
// (lib/speakToFill's toWav16kMono + transcribeWav), and the composer's
// own send function (passed as onSubmit). The call loop:
//
//   start(threadId, {onSubmit, onError})
//     → opens a mic session with the energy VAD (startOpenMic)
//     → each VAD utterance → encode → transcribe → onSubmit(text)
//     → empty/whitespace transcripts are dropped (zero onSubmit calls)
//     → exactly one submit per utterance (guard double-fires)
//
//   stop()
//     → closes the mic session (stopOpenMic)
//     → cancels any in-flight transcribe
//     → returns to idle (never wedges)
//
// Error law: mic permission denied or transcribe failure emits a typed
// onError event so the caller renders through the existing in-flow
// error row pattern. The loop returns to listening state, never wedges.
//
// Laws: click-to-toggle (no push-to-talk), Art. IV, Art. VII (no modals).

import { startOpenMic, stopOpenMic } from "./micSession";
import { toWav16kMono, transcribeWav } from "./speakToFill";
import type { DictationFailure } from "./dictationRecovery";
import { dictationFailure } from "./dictationRecovery";

// ── types ───────────────────────────────────────────────────────────

export type CallLoopState = "idle" | "listening" | "transcribing";

export interface CallLoopError {
  failure: DictationFailure;
  message: string;
}

export interface CallLoopCallbacks {
  /** Called with the non-empty transcript text. Exactly one call per
   *  utterance; empty/whitespace transcripts are dropped. */
  onSubmit: (text: string) => void;
  /** A mic or transcribe error. The loop survives and returns to
   *  listening for the next utterance. */
  onError: (error: CallLoopError) => void;
  /** Optional state change listener. */
  onStateChange?: (state: CallLoopState) => void;
}

// ── the loop ────────────────────────────────────────────────────────

let loopState: CallLoopState = "idle";
let loopCallbacks: CallLoopCallbacks | null = null;
let inflight: AbortController | null = null;
/** Guard: true while an utterance is being processed (encode →
 *  transcribe → submit). Prevents double-fires from rapid VAD events. */
let processing = false;

function setState(next: CallLoopState): void {
  if (loopState === next) return;
  loopState = next;
  loopCallbacks?.onStateChange?.(next);
}

/** Start the hands-free utterance loop on a thread.
 *
 *  Opens the mic session with the energy VAD. Each endpoint-detected
 *  utterance is transcribed through the existing
 *  `/api/dictation/transcribe` path and, if non-empty, handed to
 *  `onSubmit` — the SAME composer send function the typed-text path
 *  uses. */
export async function startCallLoop(
  callbacks: CallLoopCallbacks,
): Promise<void> {
  if (loopState !== "idle") return;
  loopCallbacks = callbacks;
  processing = false;

  try {
    await startOpenMic(async (segment) => {
      // Guard: one utterance at a time
      if (processing) return;
      processing = true;
      setState("transcribing");

      const controller = new AbortController();
      inflight = controller;

      try {
        const audio = toWav16kMono(segment.chunks, segment.rate);
        // Abort guard: if stop() was called while encoding, bail
        if (controller.signal.aborted) return;

        const text = (await transcribeWav(audio)).trim();

        // Abort guard: stop() may have fired during the fetch
        if (controller.signal.aborted) return;

        if (text) {
          callbacks.onSubmit(text);
        }
      } catch (error: unknown) {
        // Abort guard: a cancelled fetch throws, but stop() already
        // handled the teardown — swallow it silently.
        if (controller.signal.aborted) return;

        const failure = dictationFailure(error);
        const message =
          error instanceof Error ? error.message : "Transcription failed";
        callbacks.onError({ failure, message });
      } finally {
        if (!controller.signal.aborted) {
          inflight = null;
          processing = false;
          // Return to listening for the next utterance (if still running)
          if (loopState !== "idle") {
            setState("listening");
          }
        }
      }
    });

    setState("listening");
  } catch (error: unknown) {
    // Mic permission denied or unsupported browser
    const failure = dictationFailure(error);
    const message =
      error instanceof Error ? error.message : "Microphone access denied";
    callbacks.onError({ failure, message });
    setState("idle");
    loopCallbacks = null;
  }
}

/** Stop the hands-free loop. Closes the mic session and cancels any
 *  in-flight transcription. The loop returns to idle. */
export function stopCallLoop(): void {
  // Cancel in-flight work first
  if (inflight) {
    inflight.abort();
    inflight = null;
  }
  processing = false;
  stopOpenMic();
  setState("idle");
  loopCallbacks = null;
}

/** The current state of the call loop. */
export function callLoopState(): CallLoopState {
  return loopState;
}
