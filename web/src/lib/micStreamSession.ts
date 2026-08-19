import { websocketUrl, websocketProtocols } from "./auth";
import {
  beginHold,
  endHold,
  drainHold,
  abortHold,
  micCaptureSupported,
  subscribeCaptureLevel,
} from "./micSession";
import { toWav16kMono, wavFromPcm16 } from "./speakToFill";
import { clearPendingVoice, savePendingVoice } from "./pendingVoice";

/* HS-132-04 — a configured macro keyword fires ONCE, on the server's
   dictate-for-delivery leg (the same seam the pipeline runs on), exactly as
   the hotkey path and the remote relay do. The command CONSUMED the
   utterance: the final carries no text and nothing is delivered as prose. */
export type VoiceCommandFired = {
  keyword: string;
  kind: string;
  preview: string;
  ok: boolean;
  error?: string;
};

/* HS-132-05 — a refusal arrives NAMED. The server sends `reason`,
   `failure_category` and (Sol Amendment 3) `mic_interval: "closed"`; the
   client carries all three to the failure registry instead of reading
   `error` and calling everything unknown. */
export type StreamRefusalEvent = {
  type: "error";
  error: string;
  reason?: string;
  failure_category?: string;
  mic_interval?: string;
};

/* HS-132-05 — there is no "partial" event any more. Every 600 ms chunk used
   to take its own full Whisper pass, on the same transcription lock the
   hotkey needs, and the result had no consumer anywhere in the app. One
   utterance is now one transcription pass; the chunks are still shipped as
   they are captured (bounded memory, and each one heartbeats the server's
   audio-floor lease). */
export type StreamEvent =
  | { type: "final"; text: string; fired?: VoiceCommandFired }
  | StreamRefusalEvent;

export type StreamSession = {
  stop(): Promise<string>;
  cancel(): void;
  /** HS-132-05 — true once this session's audio is retained on this device
   *  for Retry. Resolves after the retention write settles, so a surface
   *  never claims retention it cannot prove. */
  retained(): Promise<boolean>;
};

const CHUNK_INTERVAL_MS = 600;

/** The retained buffer is capped where the pending-voice store is
 *  (16 MB ≈ 8 minutes of 16 kHz mono 16-bit, the same cap
 *  `/api/dictation/transcribe` enforces). Past that nothing is retained and
 *  nothing says it was. */
const RETAIN_MAX_BYTES = 16_000_000;

export function micStreamSupported(): boolean {
  return micCaptureSupported() && typeof WebSocket !== "undefined";
}

/* HS-132-04 — the socket declares what kind of utterance it carries.
   `pipeline: false` (a speak-to-fill: any desk field mic) transcribes
   VERBATIM — no intent routing, no enrichment, no rewriting, no journal
   row. `pipeline: true` is the dictate-for-delivery surface (the Speak
   room's TALK key), and it is the ONE pipeline pass that utterance gets:
   the delivery that follows sends `raw: true`. */
export async function startStreamSession(
  onEvent: (event: StreamEvent) => void,
  {
    pipeline = false,
    retainScope = "",
  }: { pipeline?: boolean; retainScope?: string } = {},
): Promise<StreamSession> {
  await beginHold();

  const ws = new WebSocket(
    websocketUrl("/ws/dictation/stream"),
    websocketProtocols(),
  );

  let chunkTimer = 0;
  let stopped = false;
  let finalText = "";
  let finalSeen = false;
  let refused = false;
  let wsOpen = false;

  /* HS-132-05 — the retained capture. What goes on the wire is kept here so
     a failed utterance really can be retried from this device (the
     "Captured audio is retained locally." promise had no writer on this
     path before). */
  let retainedParts: Uint8Array[] = [];
  let retainedBytes = 0;
  let overflowed = false;
  let retaining: Promise<boolean> = Promise.resolve(false);

  const keep = (pcm: ArrayBuffer): void => {
    if (!retainScope || overflowed) return;
    if (retainedBytes + pcm.byteLength > RETAIN_MAX_BYTES) {
      // Longer than the transcribe contract accepts: retaining it would be a
      // Retry button that 413s. Say nothing rather than promise wrongly.
      retainedParts = [];
      retainedBytes = 0;
      overflowed = true;
      return;
    }
    retainedParts.push(new Uint8Array(pcm));
    retainedBytes += pcm.byteLength;
  };

  const persist = async (): Promise<boolean> => {
    if (!retainScope || overflowed || !retainedBytes) return false;
    const merged = new Uint8Array(retainedBytes);
    let at = 0;
    retainedParts.forEach((part) => {
      merged.set(part, at);
      at += part.byteLength;
    });
    await savePendingVoice(
      retainScope,
      wavFromPcm16(new Int16Array(merged.buffer, 0, merged.byteLength >> 1)),
    );
    return true;
  };

  /** Everything captured so far, kept, without ending the hold. */
  const drainInto = (captured: ReturnType<typeof drainHold>): ArrayBuffer | null => {
    if (!captured?.chunks.length) return null;
    const wav = toWav16kMono(captured.chunks, captured.rate);
    const view = new Uint8Array(wav, 44);
    const pcm = view.buffer.slice(
      view.byteOffset,
      view.byteOffset + view.byteLength,
    );
    keep(pcm);
    return pcm;
  };

  const pendingFinal = new Promise<string>((resolve) => {
    ws.addEventListener("message", (event) => {
      if (typeof event.data !== "string") return;
      try {
        const msg = JSON.parse(event.data) as StreamEvent;
        if (msg.type === "final") {
          finalSeen = true;
          finalText = msg.text;
          resolve(msg.text);
        }
        if (msg.type === "error") {
          // The utterance failed on the server: keep its audio before the
          // socket tears the capture down, so Retry has something to retry.
          refused = true;
          drainInto(drainHold());
          retaining = persist();
        }
        onEvent(msg);
      } catch {
        // ignore malformed
      }
    });
    ws.addEventListener("close", () => {
      wsOpen = false;
      if (!stopped) {
        stopped = true;
        window.clearInterval(chunkTimer);
        // A socket that dropped mid-utterance is a failure too: retain first,
        // abandon the hold second.
        if (!refused) {
          drainInto(drainHold());
          retaining = persist();
        }
        abortHold();
        if (!refused) {
          // A named refusal already told the user WHAT happened; a generic
          // "connection lost" must never overwrite it.
          onEvent({ type: "error", error: "Connection lost." });
        }
      }
      // A server refusal can close while stop() is waiting for its final.
      // Resolve that wait with the empty final so the caller can preserve the
      // named refusal rather than hanging or inventing a second failure.
      resolve(finalText);
    });
    ws.addEventListener("error", () => {
      if (!stopped && !refused) {
        onEvent({ type: "error", error: "Connection error." });
      }
    });
  });

  const sendChunks = () => {
    if (stopped || !wsOpen) return;
    // HS-132-05: DRAIN, never end-and-rebegin. The hold stays held for the
    // whole capture — the phase lamp reads held and the level meter stays
    // live instead of being zeroed ~1.6×/s.
    const pcm = drainInto(drainHold());
    if (pcm) ws.send(pcm);
  };

  ws.addEventListener("open", () => {
    wsOpen = true;
    if (stopped) {
      ws.close();
      return;
    }
    // Declared before the first frame, so the server never has to guess
    // whether this utterance is prose for a field or one for delivery.
    ws.send(JSON.stringify({ type: "start", pipeline }));
    chunkTimer = window.setInterval(sendChunks, CHUNK_INTERVAL_MS);
  });

  return {
    async stop(): Promise<string> {
      if (stopped) return finalText;
      stopped = true;
      window.clearInterval(chunkTimer);

      const captured = endHold();
      const tail = drainInto(captured);
      if (tail && wsOpen) ws.send(tail);

      // Persisted at the final send: from here on the utterance is in the
      // server's hands, and if it fails the audio is already on this device.
      retaining = persist();
      await retaining.catch(() => false);

      if (wsOpen) {
        ws.send(JSON.stringify({ type: "end" }));
      } else {
        abortHold();
        ws.close();
        return "";
      }

      const text = await pendingFinal;
      ws.close();
      if (finalSeen && retainScope) {
        // The server answered — empty final included ("no words"). There is
        // nothing left to retry, so the retained copy goes.
        retaining = Promise.resolve(false);
        await clearPendingVoice(retainScope).catch(() => undefined);
      }
      return text;
    },
    cancel() {
      if (stopped) return;
      stopped = true;
      window.clearInterval(chunkTimer);
      abortHold();
      ws.close();
    },
    retained(): Promise<boolean> {
      return retaining.catch(() => false);
    },
  };
}

export { subscribeCaptureLevel };
