import { apiFetch } from "./api";
import {
  clearPendingVoice,
  loadPendingVoice,
  savePendingVoice,
} from "./pendingVoice";

type Capture = {
  stream: MediaStream;
  context: AudioContext;
  source: MediaStreamAudioSourceNode;
  node: ScriptProcessorNode;
  chunks: Float32Array[];
  rate: number;
};

let active: Capture | null = null;

type AudioWindow = Window &
  typeof globalThis & { webkitAudioContext?: typeof AudioContext };

export function speakToFillSupported(): boolean {
  const audioWindow = window as AudioWindow;
  return (
    typeof navigator.mediaDevices?.getUserMedia === "function" &&
    ("AudioContext" in window ||
      typeof audioWindow.webkitAudioContext === "function")
  );
}

export async function startCapture(): Promise<void> {
  if (active) await cancelCapture();
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioWindow = window as AudioWindow;
  const Context = window.AudioContext || audioWindow.webkitAudioContext;
  if (!Context)
    throw new Error("Audio capture is not supported by this browser.");
  const context = new Context();
  const source = context.createMediaStreamSource(stream);
  const node = context.createScriptProcessor(4096, 1, 1);
  const chunks: Float32Array[] = [];
  node.onaudioprocess = (event) =>
    chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
  source.connect(node);
  node.connect(context.destination);
  active = { stream, context, source, node, chunks, rate: context.sampleRate };
}

function teardown(): Pick<Capture, "chunks" | "rate"> | null {
  if (!active) return null;
  const { stream, context, source, node, chunks, rate } = active;
  try {
    source.disconnect();
    node.disconnect();
  } catch {
    /* already torn down */
  }
  stream.getTracks().forEach((track) => track.stop());
  void context.close().catch(() => undefined);
  active = null;
  return { chunks, rate };
}

export async function cancelCapture(): Promise<void> {
  teardown();
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
  const captured = teardown();
  if (!captured?.chunks.length) return "";
  const audio = toWav16kMono(captured.chunks, captured.rate);
  if (scope) await savePendingVoice(scope, audio);
  const text = await transcribeWav(audio);
  if (scope) await clearPendingVoice(scope);
  return text;
}
