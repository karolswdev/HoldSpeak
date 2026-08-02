// HS-112-06 — the open mic's transcription leg.
//
// The session (lib/micSession) says WHERE an utterance starts and ends;
// this is the thin seam that turns each segment into words: the same
// 16 kHz mono WAV encoder and the same `/api/dictation/transcribe`
// route a held TALK uses. Delivery is NOT here — the caller hands the
// text to the exact HS-112-02 contract the release path uses, so an
// ambient utterance and a held one are indistinguishable downstream.
//
// An empty transcript is dropped silently: silence misread as speech
// must never spend a delivery, a journal row, or a receipt.

import { startOpenMic, stopOpenMic } from "./micSession";
import { toWav16kMono, transcribeWav } from "./speakToFill";
import type { VadTuning } from "./vad";

export async function openMicListen(
  handlers: {
    onText: (text: string) => void;
    onRefusal: (error: unknown) => void;
  },
  tuning?: Partial<VadTuning>,
): Promise<void> {
  await startOpenMic(async (segment) => {
    try {
      const audio = toWav16kMono(segment.chunks, segment.rate);
      const text = (await transcribeWav(audio)).trim();
      if (text) handlers.onText(text);
    } catch (error) {
      handlers.onRefusal(error);
    }
  }, tuning);
}

/** The one verb: the stream is dropped, the device released. */
export function openMicDrop(): void {
  stopOpenMic();
}
