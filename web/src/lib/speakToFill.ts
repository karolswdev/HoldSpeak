import { apiFetch } from "./api";
import {
  abortHold,
  beginHold,
  endHold,
  micCaptureReason,
  micCaptureSupported,
  subscribeCaptureLevel,
} from "./micSession";
import {
  clearPendingVoice,
  loadPendingVoice,
  savePendingVoice,
} from "./pendingVoice";

/* HS-112-06 — the hold path is now a TENANT of the one Desk mic session
   (lib/micSession): the same grant, the same AudioWorklet, the same
   level tap the open mic uses. This module keeps the speak-to-fill
   contract every text field calls (start / stop-and-transcribe) and the
   WAV encoding; it no longer owns a stream. */

/* HS-111-02 — the level tap: the capture stream reports its own RMS
   level (0..1) to any listening meter (the cockpit's LedMeter). The tap
   now lives with the session that owns the frames; re-exported here so
   every existing meter subscribes exactly as before. */
export { subscribeCaptureLevel };

export function speakToFillSupported(): boolean {
  return micCaptureSupported();
}

/** Why capture is unavailable, or null when it is available. One answer
 *  for the whole Desk — it lives with the session that owns the device. */
export function speakToFillUnsupportedReason(): string | null {
  return micCaptureReason();
}

export async function startCapture(): Promise<void> {
  await beginHold();
}

export async function cancelCapture(): Promise<void> {
  abortHold();
}

export function toWav16kMono(
  chunks: Float32Array[],
  sourceRate: number,
): ArrayBuffer {
  const joined = new Float32Array(
    chunks.reduce((length, chunk) => length + chunk.length, 0),
  );
  let offset = 0;
  chunks.forEach((chunk) => {
    joined.set(chunk, offset);
    offset += chunk.length;
  });
  const ratio = sourceRate / 16_000;
  const pcm = new Int16Array(Math.max(1, Math.floor(joined.length / ratio)));
  for (let index = 0; index < pcm.length; index += 1) {
    const position = index * ratio;
    const left = Math.floor(position);
    const right = Math.min(left + 1, joined.length - 1);
    const sample =
      joined[left] * (1 - (position - left)) +
      joined[right] * (position - left);
    pcm[index] = Math.max(-32768, Math.min(32767, Math.round(sample * 32767)));
  }
  const buffer = new ArrayBuffer(44 + pcm.length * 2);
  const view = new DataView(buffer);
  const word = (at: number, value: string) =>
    [...value].forEach((character, index) =>
      view.setUint8(at + index, character.charCodeAt(0)),
    );
  word(0, "RIFF");
  view.setUint32(4, 36 + pcm.length * 2, true);
  word(8, "WAVE");
  word(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, 16_000, true);
  view.setUint32(28, 32_000, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  word(36, "data");
  view.setUint32(40, pcm.length * 2, true);
  new Int16Array(buffer, 44).set(pcm);
  return buffer;
}

export async function transcribeWav(audio: ArrayBuffer): Promise<string> {
  const result = await apiFetch<{ success?: boolean; text?: string }>(
    "/api/dictation/transcribe",
    {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: audio,
    },
  );
  return String(result.text ?? "");
}

export async function retryPendingTranscription(
  scope: string,
): Promise<string | null> {
  const audio = await loadPendingVoice(scope);
  if (!audio) return null;
  const text = await transcribeWav(audio);
  await clearPendingVoice(scope);
  return text;
}

export async function stopAndTranscribe(scope?: string): Promise<string> {
  const captured = endHold();
  if (!captured?.chunks.length) return "";
  const audio = toWav16kMono(captured.chunks, captured.rate);
  if (scope) await savePendingVoice(scope, audio);
  const text = await transcribeWav(audio);
  if (scope) await clearPendingVoice(scope);
  return text;
}
