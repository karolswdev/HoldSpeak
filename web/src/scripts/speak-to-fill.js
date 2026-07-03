// HS-78-02: speak-to-fill — the browser mic feeding the hub's transcriber.
//
// Hold to talk, release to fill: capture via getUserMedia + an
// AudioContext tap, resample to 16 kHz mono, build one WAV in the browser,
// POST it to /api/dictation/transcribe (the runtime's OWN local Whisper —
// nothing egresses, nothing persists), and hand the text back. No confirm
// step (the owner's steer: "we need to be able to just talk to this
// stuff").
//
// This helper is the ONE place the web calls getUserMedia for speech
// (the desk lock allows imports of this module but never direct calls;
// the Record orb still drives the HUB recorder for meetings).

let active = null; // { stream, ctx, source, node, chunks, rate }

export function speakToFillSupported() {
  return (
    typeof navigator !== "undefined" &&
    !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) &&
    typeof window !== "undefined" &&
    !!(window.AudioContext || window.webkitAudioContext)
  );
}

/** Start capturing. Throws if the mic is denied or unavailable. */
export async function startCapture() {
  if (active) await cancelCapture();
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const Ctx = window.AudioContext || window.webkitAudioContext;
  const ctx = new Ctx();
  const source = ctx.createMediaStreamSource(stream);
  // A ScriptProcessor tap: deprecated but universally shipped, and the
  // capture is short-lived (a spoken phrase, not a meeting).
  const node = ctx.createScriptProcessor(4096, 1, 1);
  const chunks = [];
  node.onaudioprocess = (e) => {
    chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
  };
  source.connect(node);
  node.connect(ctx.destination);
  active = { stream, ctx, source, node, chunks, rate: ctx.sampleRate };
}

function teardown() {
  if (!active) return null;
  const { stream, ctx, source, node, chunks, rate } = active;
  try { source.disconnect(); node.disconnect(); } catch (_e) { /* torn */ }
  for (const t of stream.getTracks()) t.stop();
  try { ctx.close(); } catch (_e) { /* closed */ }
  active = null;
  return { chunks, rate };
}

export async function cancelCapture() {
  teardown();
}

function toWav16kMono(chunks, sourceRate) {
  let length = 0;
  for (const c of chunks) length += c.length;
  const joined = new Float32Array(length);
  let off = 0;
  for (const c of chunks) { joined.set(c, off); off += c.length; }
  // Linear resample to 16 kHz.
  const ratio = sourceRate / 16000;
  const outLen = Math.max(1, Math.floor(joined.length / ratio));
  const pcm = new Int16Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const pos = i * ratio;
    const i0 = Math.floor(pos);
    const i1 = Math.min(i0 + 1, joined.length - 1);
    const frac = pos - i0;
    const sample = joined[i0] * (1 - frac) + joined[i1] * frac;
    pcm[i] = Math.max(-32768, Math.min(32767, Math.round(sample * 32767)));
  }
  const buf = new ArrayBuffer(44 + pcm.length * 2);
  const view = new DataView(buf);
  const writeStr = (o, str) => { for (let i = 0; i < str.length; i++) view.setUint8(o + i, str.charCodeAt(i)); };
  writeStr(0, "RIFF");
  view.setUint32(4, 36 + pcm.length * 2, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);      // PCM
  view.setUint16(22, 1, true);      // mono
  view.setUint32(24, 16000, true);  // rate
  view.setUint32(28, 32000, true);  // byte rate
  view.setUint16(32, 2, true);      // block align
  view.setUint16(34, 16, true);     // bits
  writeStr(36, "data");
  view.setUint32(40, pcm.length * 2, true);
  new Int16Array(buf, 44).set(pcm);
  return buf;
}

/** Stop capturing, transcribe on the hub, return the text ("" on silence).
 * Throws on transport/route failure so callers can show an honest state. */
export async function stopAndTranscribe() {
  const captured = teardown();
  if (!captured || captured.chunks.length === 0) return "";
  const wav = toWav16kMono(captured.chunks, captured.rate);
  const res = await fetch("/api/dictation/transcribe", {
    method: "POST",
    headers: { "Content-Type": "application/octet-stream" },
    body: wav,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || !body.success) {
    throw new Error(String(body.error || `HTTP ${res.status}`));
  }
  return String(body.text || "");
}
