import { websocketUrl, websocketProtocols } from "./auth";
import {
  beginHold,
  endHold,
  abortHold,
  micCaptureSupported,
  subscribeCaptureLevel,
} from "./micSession";
import { toWav16kMono } from "./speakToFill";

export type StreamEvent =
  | { type: "partial"; text: string }
  | { type: "final"; text: string }
  | { type: "error"; error: string };

export type StreamSession = {
  stop(): Promise<string>;
  cancel(): void;
};

const CHUNK_INTERVAL_MS = 600;

export function micStreamSupported(): boolean {
  return micCaptureSupported() && typeof WebSocket !== "undefined";
}

export async function startStreamSession(
  onEvent: (event: StreamEvent) => void,
): Promise<StreamSession> {
  await beginHold();

  const ws = new WebSocket(
    websocketUrl("/ws/dictation/stream"),
    websocketProtocols(),
  );

  let chunkTimer = 0;
  let stopped = false;
  let finalText = "";
  let wsOpen = false;

  const pendingFinal = new Promise<string>((resolve) => {
    ws.addEventListener("message", (event) => {
      if (typeof event.data !== "string") return;
      try {
        const msg = JSON.parse(event.data) as StreamEvent;
        if (msg.type === "final") {
          finalText = msg.text;
          resolve(msg.text);
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
        abortHold();
        onEvent({ type: "error", error: "Connection lost." });
      }
      resolve(finalText);
    });
    ws.addEventListener("error", () => {
      if (!stopped) {
        onEvent({ type: "error", error: "Connection error." });
      }
    });
  });

  const sendChunks = () => {
    if (stopped || !wsOpen) return;
    const captured = endHold();
    if (captured?.chunks.length) {
      const wav = toWav16kMono(captured.chunks, captured.rate);
      const pcmBytes = new Uint8Array(wav, 44);
      ws.send(pcmBytes.buffer.slice(pcmBytes.byteOffset, pcmBytes.byteOffset + pcmBytes.byteLength));
    }
    if (!stopped) {
      void beginHold();
    }
  };

  ws.addEventListener("open", () => {
    wsOpen = true;
    if (stopped) {
      ws.close();
      return;
    }
    chunkTimer = window.setInterval(sendChunks, CHUNK_INTERVAL_MS);
  });

  return {
    async stop(): Promise<string> {
      if (stopped) return finalText;
      stopped = true;
      window.clearInterval(chunkTimer);

      const captured = endHold();
      if (captured?.chunks.length && wsOpen) {
        const wav = toWav16kMono(captured.chunks, captured.rate);
        const pcmBytes = new Uint8Array(wav, 44);
        ws.send(pcmBytes.buffer.slice(pcmBytes.byteOffset, pcmBytes.byteOffset + pcmBytes.byteLength));
      }

      if (wsOpen) {
        ws.send(JSON.stringify({ type: "end" }));
      } else {
        abortHold();
        ws.close();
        return "";
      }

      const text = await pendingFinal;
      ws.close();
      return text;
    },
    cancel() {
      if (stopped) return;
      stopped = true;
      window.clearInterval(chunkTimer);
      abortHold();
      ws.close();
    },
  };
}

export { subscribeCaptureLevel };
