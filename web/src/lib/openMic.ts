// HS-112-06 — the open mic's floor claim and transcription leg.
//
// The session (lib/micSession) says WHERE an utterance starts and ends;
// this is the seam around it: it takes the audio floor before the first
// frame (lib/audioFloor — the same arbiter the hotkey, the meeting
// recorder and the wake listener claim), heartbeats while it listens,
// and turns each segment into words through the same 16 kHz mono WAV
// encoder and `/api/dictation/transcribe` route a held TALK uses.
//
// Delivery is NOT here — the caller hands the text to the exact
// HS-112-02 contract the release path uses, so an ambient utterance and
// a held one are indistinguishable downstream.
//
// An empty transcript is dropped silently: silence misread as speech
// must never spend a delivery, a journal row, or a receipt.

import {
  FLOOR_RENEW_MS,
  FloorHeldError,
  claimAudioFloor,
  releaseAudioFloor,
  renewAudioFloor,
} from "./audioFloor";
import { startOpenMic, stopOpenMic } from "./micSession";
import {
  closeMicInterval,
  micIntervalClosed,
  openMicInterval,
  toWav16kMono,
  transcribeWav,
} from "./speakToFill";
import type { VadTuning } from "./vad";

let heartbeat: ReturnType<typeof setInterval> | null = null;

function stopHeartbeat(): void {
  if (heartbeat !== null) clearInterval(heartbeat);
  heartbeat = null;
}

export async function openMicListen(
  handlers: {
    onText: (text: string) => void;
    onRefusal: (error: unknown) => void;
    /** The floor was taken away mid-session — the mic is already dropped. */
    onFloorLost?: (error: FloorHeldError) => void;
    /** The server's admitted interval ended — the mic is already dropped and a
     *  fresh click is required (HS-131-09, Sol Amendment 3). */
    onIntervalClosed?: (error: unknown) => void;
  },
  tuning?: Partial<VadTuning>,
): Promise<void> {
  // The floor first: a refused claim never opens the device at all.
  await claimAudioFloor();
  try {
    // Then the authority: one admitted server-side interval covers every
    // utterance of this click-to-toggle session.
    await openMicInterval();
  } catch (error) {
    void releaseAudioFloor();
    throw error;
  }
  try {
    await startOpenMic(async (segment) => {
      try {
        const audio = toWav16kMono(segment.chunks, segment.rate);
        const text = (await transcribeWav(audio)).trim();
        if (text) handlers.onText(text);
      } catch (error) {
        if (micIntervalClosed(error)) {
          // One visible interval never crosses authority epochs: it goes down.
          openMicDrop();
          if (handlers.onIntervalClosed) handlers.onIntervalClosed(error);
          else handlers.onRefusal(error);
          return;
        }
        handlers.onRefusal(error);
      }
    }, tuning);
  } catch (error) {
    void releaseAudioFloor();
    throw error;
  }
  stopHeartbeat();
  heartbeat = setInterval(() => {
    void renewAudioFloor().then((kept) => {
      if (kept) return;
      // Lost the floor (a meeting took it, or the lease lapsed): the mic
      // goes down first, then the room is told by name.
      openMicDrop();
      handlers.onFloorLost?.(new FloorHeldError("another owner"));
    });
  }, FLOOR_RENEW_MS);
}

/** The one verb: the stream is dropped, the device released, floor freed. */
export function openMicDrop(): void {
  stopHeartbeat();
  stopOpenMic();
  void closeMicInterval();
  void releaseAudioFloor();
}
